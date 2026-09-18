#!/usr/bin/env python3
"""seo_intel storage layer: schema, upserts and run accounting.

Why this module exists
----------------------
The Search Console and (later) GA4 loaders must agree on one schema and one
definition of a successful load. Putting both here — rather than in the
fetchers — means the database layout is versioned with the code that reads
it, and `--init` makes provisioning reproducible instead of something that
happened once by hand on a server.

Database isolation is deliberate (V2.3 §9): this owns a dedicated
`seo_intel` database and never touches `content_studio`, `slh` or
`csmanual3`.

Scope for P2.0: tables and loaders only. No crawler, no opportunity engine,
no dashboard — those are P2.1+ and nothing here presumes them.
"""

import os
import sys

DEFAULT_DB = "seo_intel"

# Status values used in seo_runs.status. Kept as constants so the reporting
# side never has to guess at a string.
STATUS_SUCCESS = "success"   # every fetched row validated and was written
STATUS_PARTIAL = "partial"   # fetched, but some rows failed validation
STATUS_SKIPPED = "skipped"   # nothing fetched: not an error (e.g. no credentials)
STATUS_FAILED = "failed"     # the run itself broke

# ── Schema ───────────────────────────────────────────────────────────────
# `date` is quoted throughout: it is a type name in Postgres, and a quoted
# identifier removes any doubt about which one the parser is looking at.
#
# Columns beyond the V2.3 §9 minimum, and why:
#   * updated_at on the fact tables — an upsert that cannot be distinguished
#     from the original insert makes a stale row invisible.
#   * rows_written / rows_rejected on seo_runs — rows_fetched alone cannot
#     tell "fetched and stored" apart from "fetched and silently dropped",
#     which is exactly the failure §11 asks the loader to prevent.
#   * notes on seo_runs — where a skip or a rejection set is explained
#     without pretending it was an error.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS seo_gsc_daily (
    id           bigserial PRIMARY KEY,
    "date"       date        NOT NULL,
    query        text        NOT NULL,
    page         text        NOT NULL,
    clicks       integer     NOT NULL,
    impressions  integer     NOT NULL,
    ctr          real        NOT NULL,
    position     real        NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT seo_gsc_daily_key UNIQUE ("date", query, page),
    CONSTRAINT seo_gsc_daily_clicks      CHECK (clicks >= 0),
    CONSTRAINT seo_gsc_daily_impressions CHECK (impressions >= 0),
    CONSTRAINT seo_gsc_daily_ctr         CHECK (ctr >= 0 AND ctr <= 1),
    CONSTRAINT seo_gsc_daily_position    CHECK (position > 0)
);

CREATE INDEX IF NOT EXISTS seo_gsc_daily_date_idx  ON seo_gsc_daily ("date" DESC);
CREATE INDEX IF NOT EXISTS seo_gsc_daily_page_idx  ON seo_gsc_daily (page);
CREATE INDEX IF NOT EXISTS seo_gsc_daily_query_idx ON seo_gsc_daily (query);

-- GA4 rollup. Designed ahead of the credentials so the shape is agreed
-- before anyone writes to it; it stays empty until a GA4 data stream and a
-- read credential both exist. No placeholder rows, ever.
CREATE TABLE IF NOT EXISTS seo_analytics_daily (
    id                bigserial PRIMARY KEY,
    "date"            date        NOT NULL,
    page              text        NOT NULL,
    sessions          integer     NOT NULL DEFAULT 0,
    users             integer     NOT NULL DEFAULT 0,
    pageviews         integer     NOT NULL DEFAULT 0,
    engaged_sessions  integer     NOT NULL DEFAULT 0,
    cta_clicks        integer     NOT NULL DEFAULT 0,
    enquiries         integer     NOT NULL DEFAULT 0,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT seo_analytics_daily_key UNIQUE ("date", page)
);

CREATE INDEX IF NOT EXISTS seo_analytics_daily_date_idx ON seo_analytics_daily ("date" DESC);

CREATE TABLE IF NOT EXISTS seo_runs (
    id            bigserial PRIMARY KEY,
    source        text        NOT NULL CHECK (source IN ('gsc', 'ga4')),
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    status        text        NOT NULL,
    rows_fetched  integer     NOT NULL DEFAULT 0,
    rows_written  integer     NOT NULL DEFAULT 0,
    rows_rejected integer     NOT NULL DEFAULT 0,
    error_message text,
    notes         text
);

CREATE INDEX IF NOT EXISTS seo_runs_source_started_idx ON seo_runs (source, started_at DESC);
"""

UPSERT_GSC_SQL = """
INSERT INTO seo_gsc_daily ("date", query, page, clicks, impressions, ctr, position)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ("date", query, page) DO UPDATE SET
    clicks      = EXCLUDED.clicks,
    impressions = EXCLUDED.impressions,
    ctr         = EXCLUDED.ctr,
    position    = EXCLUDED.position,
    updated_at  = now()
"""

# Adapter for the GA4 side (V2.3 §9 / §13). Written now, called only once a
# GA4 read credential exists — deliberately not wired to a fake source.
UPSERT_ANALYTICS_SQL = """
INSERT INTO seo_analytics_daily
    ("date", page, sessions, users, pageviews, engaged_sessions, cta_clicks, enquiries)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ("date", page) DO UPDATE SET
    sessions         = EXCLUDED.sessions,
    users            = EXCLUDED.users,
    pageviews        = EXCLUDED.pageviews,
    engaged_sessions = EXCLUDED.engaged_sessions,
    cta_clicks       = EXCLUDED.cta_clicks,
    enquiries        = EXCLUDED.enquiries,
    updated_at       = now()
"""


def connect(dsn):
    """Open a psycopg2 connection. Imported lazily so --help works without it."""
    try:
        import psycopg2
    except ImportError:
        sys.exit("[ERROR] psycopg2 is required: pip install psycopg2-binary")
    return psycopg2.connect(dsn)


def apply_schema(conn):
    """Create the tables if they are missing. Idempotent by construction."""
    with conn, conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)


def normalize_dsn(dsn):
    """Accept the SQLAlchemy-style DSNs already used on this server.

    The neighbouring projects store `postgresql+asyncpg://…` in their .env.
    Rather than demand a second spelling of the same connection, translate
    it — and re-point container-internal hostnames at the published port,
    because this service runs on the host, not inside the compose network.
    """
    if not dsn:
        return dsn
    out = dsn
    for driver in ("+asyncpg", "+psycopg2", "+psycopg"):
        out = out.replace(f"postgresql{driver}://", "postgresql://")
    if "://" in out:
        scheme, rest = out.split("://", 1)
        creds, _, hostpart = rest.rpartition("@")
        host, _, tail = hostpart.partition("/")
        hostname, _, port = host.partition(":")
        # The compose service name resolves only inside the docker network;
        # this script runs on the host, where the port is published on
        # loopback. Rewrite both, or the connection fails with a DNS error
        # that looks like the database is down.
        if hostname in ("postgres", "localhost", "127.0.0.1"):
            hostname, port = "127.0.0.1", "5433"
        elif port == "5432":
            port = "5433"
        host = f"{hostname}:{port}" if port else hostname
        out = f"{scheme}://{creds}@{host}/{tail}" if creds else f"{scheme}://{host}/{tail}"
    return out


def dsn_from_env(default_db=DEFAULT_DB):
    """Resolve the DSN.

    Order: SEO_INTEL_DSN (this project's own variable, used as given) →
    DATABASE_URL (the spelling the neighbouring projects already export, with
    the database name swapped for ours) → a local default. Nothing is
    hard-coded with a password: the credential stays in the environment.
    """
    explicit = os.environ.get("SEO_INTEL_DSN")
    if explicit:
        return normalize_dsn(explicit)

    shared = os.environ.get("DATABASE_URL")
    if shared:
        base, _, _ = normalize_dsn(shared).rpartition("/")
        return f"{base}/{default_db}"

    return f"postgresql://slh@127.0.0.1:5433/{default_db}"


def start_run(conn, source):
    with conn, conn.cursor() as cur:
        cur.execute("INSERT INTO seo_runs (source, status) VALUES (%s, %s) RETURNING id",
                    (source, STATUS_FAILED))
        return cur.fetchone()[0]


def finish_run(conn, run_id, status, rows_fetched=0, rows_written=0,
               rows_rejected=0, error_message=None, notes=None):
    with conn, conn.cursor() as cur:
        cur.execute(
            """UPDATE seo_runs
                  SET finished_at = now(), status = %s, rows_fetched = %s,
                      rows_written = %s, rows_rejected = %s,
                      error_message = %s, notes = %s
                WHERE id = %s""",
            (status, rows_fetched, rows_written, rows_rejected,
             error_message, notes, run_id),
        )


def upsert_gsc_rows(conn, rows):
    """rows = [(date, query, page, clicks, impressions, ctr, position), ...]"""
    if not rows:
        return 0
    with conn, conn.cursor() as cur:
        cur.executemany(UPSERT_GSC_SQL, rows)
    return len(rows)


def upsert_analytics_rows(conn, rows):
    """rows = [(date, page, sessions, users, pageviews, engaged, cta, enquiries), ...]"""
    if not rows:
        return 0
    with conn, conn.cursor() as cur:
        cur.executemany(UPSERT_ANALYTICS_SQL, rows)
    return len(rows)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="seo_intel schema provisioning")
    parser.add_argument("--init", action="store_true", help="create the tables (idempotent)")
    parser.add_argument("--dsn", default=None, help="override the connection string")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"database name (default {DEFAULT_DB})")
    args = parser.parse_args()

    if not args.init:
        parser.print_help()
        return 0

    dsn = args.dsn or dsn_from_env(args.db)
    conn = connect(dsn)
    apply_schema(conn)
    with conn.cursor() as cur:
        cur.execute("""SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public' ORDER BY 1""")
        tables = [r[0] for r in cur.fetchall()]
    conn.close()
    print("seo_intel schema applied. Tables: " + ", ".join(tables))
    return 0


if __name__ == "__main__":
    sys.exit(main())
