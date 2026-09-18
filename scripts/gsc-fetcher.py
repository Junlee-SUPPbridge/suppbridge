#!/usr/bin/env python3
"""SuppBridge — Google Search Console fetcher and seo_intel loader.

Replaces the print-only version of this script. That one reported numbers to
a terminal and cached JSON under .workbuddy/; nothing it produced could be
queried, compared or trusted later. This one validates every row the API
returns and lands it in the dedicated `seo_intel` database, so P2.1 and P2.2
have a real foundation to build on.

Setup: see GSC-API-SETUP.md for the Google-side steps (project, API, service
account, GSC user). Credentials live OUTSIDE this repository — see
CREDENTIAL_PATHS below. A key in scripts/ is a leak waiting to happen and is
only tolerated as a documented legacy fallback.

Usage
-----
    python3 scripts/gsc-fetcher.py --init-db          # create tables
    python3 scripts/gsc-fetcher.py --dry-run          # fetch + validate, no writes
    python3 scripts/gsc-fetcher.py                    # first sync: last 7 days
    python3 scripts/gsc-fetcher.py --days 28

Design notes
------------
* **The API response is not trusted.** Every row is checked (counts
  non-negative, ctr inside 0–1, position > 0, page on our own domain, date
  parseable) before it can reach the database. Rejected rows are counted in
  seo_runs, never silently dropped.
* **Missing credentials are a skip, not a crash.** The daily timer must not
  report a failure every night for a configuration that has not been made
  yet; it records status='skipped' with the reason. `--strict` turns that
  into a non-zero exit for anyone who wants it.
* **Runs are auditable.** Each execution writes one seo_runs row, so "did
  yesterday's sync actually happen, and did it store what it fetched" is a
  query rather than a guess.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from urllib.parse import quote, urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

import seo_intel_store as store  # noqa: E402

# ── Configuration ────────────────────────────────────────────────────────
# Domain property, per V2.3 §5: it covers suppbridge.com AND
# www.suppbridge.com in one place, which is why the canonical tag does not
# need to change for Search Console's benefit.
DEFAULT_PROPERTY = "sc-domain:suppbridge.com"

# Credential lookup order. The server path comes first on purpose: the
# repository must never be the place a key lives.
CREDENTIAL_PATHS = (
    "/etc/suppbridge/seo-intel/gsc-service-account.json",
)

# Legacy location, kept only so an existing local setup keeps working. Using
# it prints a warning.
LEGACY_CREDENTIAL_PATH = os.path.join(SCRIPT_DIR, "gsc-service-account.json")

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

OWN_DOMAINS = {"suppbridge.com", "www.suppbridge.com"}
DEFAULT_DAYS = 7
DEFAULT_ROW_LIMIT = 25000

# REST endpoint for the Search Analytics query. Used directly instead of the
# discovery client; see build_service().
SEARCHANALYTICS_URL = ("https://searchconsole.googleapis.com/webmasters/v3"
                       "/sites/{site}/searchAnalytics/query")

# Generous but finite. Without it a blocked egress path turns a 30-second
# sync into a job that hangs until the timer's next fire.
HTTP_TIMEOUT = 60

# Unauthenticated endpoint used only to answer "can this process reach
# Google at all, through this path". A token request would also work but
# costs a round trip to oauth2 and tells you less about Search Console.
EGRESS_PROBE_URL = ("https://searchconsole.googleapis.com/$discovery/rest"
                    "?version=v1")

# Short: probes run once per execution, but a dead proxy must not be allowed
# to eat the whole HTTP_TIMEOUT before the next candidate gets a turn.
PROBE_TIMEOUT = 15

# Hard ceiling on a probe. requests' timeout does NOT cover DNS resolution,
# and on a host whose DNS or direct route to Google is a black hole a
# "direct" candidate can hang for minutes while the timeout never fires.
# The probe therefore runs on a daemon thread and is abandoned if it has not
# answered in this many seconds; a hung path is reported as a failed path.
PROBE_HARD_TIMEOUT = PROBE_TIMEOUT + 5

# Console /api/health re-probes on every hit. A hung direct candidate would
# otherwise spawn one stuck thread per page refresh, so results are reused
# for this long. A proxy swap is picked up within a minute.
PROBE_CACHE_TTL = 60


class GscApiError(RuntimeError):
    """A non-200 from Search Console, with the status kept intact."""


def resolve_property(explicit=None):
    return explicit or os.environ.get("GSC_PROPERTY") or DEFAULT_PROPERTY


def resolve_credentials(explicit=None):
    """Return (path, is_legacy) or (None, False)."""
    if explicit:
        return (explicit if os.path.exists(explicit) else None), False
    env = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if env and os.path.exists(env):
        return env, False
    for path in CREDENTIAL_PATHS:
        if os.path.exists(path):
            return path, False
    if os.path.exists(LEGACY_CREDENTIAL_PATH):
        return LEGACY_CREDENTIAL_PATH, True
    return None, False


def build_service(cred_path):
    """Build an authenticated Search Console client.

    Deliberately NOT googleapiclient.discovery: discovery is built on
    httplib2, and httplib2 ignores HTTP_PROXY / HTTPS_PROXY. On a host that
    can only reach Google through a local proxy that difference is fatal --
    discovery hangs until it times out while requests succeeds immediately.
    google.auth's AuthorizedSession is a requests.Session, so it honours the
    standard proxy environment variables.

    Imports are lazy so `--help` and `--dry-run` work on a machine without
    the Google client libraries installed.
    """
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
    except ImportError:
        sys.exit("[ERROR] Missing packages. Run:\n"
                 "  pip install google-auth")

    with open(cred_path, encoding="utf-8") as f:
        info = json.load(f)
    if "private_key" not in info or "client_email" not in info:
        sys.exit(f"[ERROR] {cred_path} is not a service-account key file.")
    creds = service_account.Credentials.from_service_account_info(info, scopes=[SCOPE])
    return AuthorizedSession(creds)


# ── Egress ───────────────────────────────────────────────────────────────
# This host reaches Google through a proxy that is not under our control
# (a local mihomo today, possibly a VPN tunnel tomorrow). The proxy is
# therefore treated as a *candidate list*, not a constant:
#
#   SEO_INTEL_PROXY_CANDIDATES=http://127.0.0.1:7891,socks5://10.0.0.9:1080
#
# Each is probed in order and the first that answers is used, so adding or
# replacing a VPN is a one-line change in proxy.env -- no unit edit, no
# code edit -- and a proxy that dies overnight no longer looks like a
# credentials failure.

def proxy_candidates():
    """Ordered list of proxy URLs; None in the list means 'direct'."""
    raw = os.environ.get("SEO_INTEL_PROXY_CANDIDATES", "")
    parsed = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        parsed.append(None if item.lower() in {"direct", "none", "off"} else item)
    if parsed:
        return parsed
    ambient = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
               or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"))
    if ambient and ambient.strip():
        return [ambient.strip()]
    return [None]


def _request_probe(proxy, timeout, out):
    """Body of the probe, run on a thread so it can be abandoned."""
    import requests  # lazy: --help must work without it

    proxies = {"https": proxy, "http": proxy} if proxy else None
    try:
        response = requests.get(EGRESS_PROBE_URL, proxies=proxies, timeout=timeout)
        # 401/403 would still mean "we got there", but for an unauthenticated
        # discovery document anything but 2xx/3xx means the path is wrong.
        out["ok"] = response.status_code < 400
        out["detail"] = f"HTTP {response.status_code}"
    except Exception as exc:  # noqa: BLE001 - the failure text is the point
        out["ok"] = False
        out["detail"] = f"{type(exc).__name__}: {str(exc)[:160]}"


def probe_egress(proxy, timeout=PROBE_TIMEOUT):
    """Return (ok, detail) for one candidate path, always within ~timeout+5s.

    The work runs on a daemon thread because requests' own timeout does not
    cover DNS or a black-holed route: measured on this host, a 'direct'
    candidate took 2m03s to fail while nominally having a 15s timeout. A
    path that cannot be abandoned is worse than a path that fails fast.
    """
    import threading  # lazy, same reason as requests

    out = {}
    thread = threading.Thread(target=_request_probe, args=(proxy, timeout, out),
                              daemon=True)
    thread.start()
    thread.join(PROBE_HARD_TIMEOUT)
    if thread.is_alive():
        return False, (f"no answer within {PROBE_HARD_TIMEOUT}s "
                       f"(hung route: {proxy or 'direct'})")
    return out.get("ok", False), out.get("detail", "probe produced no result")


_PROBE_CACHE = {"at": 0.0, "value": None}


def choose_proxy(use_cache=True):
    """Pick the first candidate that can actually reach Search Console.

    Returns (chosen_proxy_or_None, tried) where `tried` is a list of
    {"proxy", "ok", "detail"} dicts, so a failure message can say which
    paths were attempted instead of just 'timed out'.

    `use_cache` exists for the console: /api/health probes on every page
    load, and a hung candidate would otherwise leave a stuck thread behind
    each time. Freshness is a minute, which is well inside "I just changed
    the VPN and want to see it".
    """
    import time  # lazy

    if use_cache and _PROBE_CACHE["value"] is not None:
        if time.monotonic() - _PROBE_CACHE["at"] < PROBE_CACHE_TTL:
            return _PROBE_CACHE["value"]

    tried = []
    chosen = None
    for proxy in proxy_candidates():
        ok, detail = probe_egress(proxy)
        tried.append({"proxy": proxy or "direct", "ok": ok, "detail": detail})
        if ok:
            chosen = proxy
            break

    _PROBE_CACHE["at"] = time.monotonic()
    _PROBE_CACHE["value"] = (chosen, tried)
    return chosen, tried


def format_tried(tried):
    return "; ".join(f"{t['proxy']} -> {'ok' if t['ok'] else t['detail']}"
                     for t in tried)


def proxy_hint():
    """One line explaining how this process will reach Google.

    Printed on failure, because 'timed out' on a proxied host sends people
    looking at credentials when the real problem is egress.
    """
    return ("candidates: " + format_tried(choose_proxy()[1])
            + " — set SEO_INTEL_PROXY_CANDIDATES (comma separated) in proxy.env")


# ── Fetch ────────────────────────────────────────────────────────────────

def fetch_rows(session, prop, start, end, row_limit, proxy=None):
    """Pull date/query/page rows, paging until the API stops returning data.

    Paging matters: a single request caps at row_limit, and silently
    truncating a month of data would look exactly like a quiet month.

    Calls the REST endpoint directly (see build_service for why discovery is
    not used). The siteUrl is percent-encoded: 'sc-domain:suppbridge.com'
    contains a colon that must not survive as a path separator.

    `proxy` is passed per-request rather than left to the environment so the
    candidate that was probed is the candidate that is used.
    """
    url = SEARCHANALYTICS_URL.format(site=quote(prop, safe=""))
    proxies = {"https": proxy, "http": proxy} if proxy else None
    rows = []
    start_row = 0
    while True:
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["date", "query", "page"],
            "rowLimit": row_limit,
            "startRow": start_row,
            # final: only data Google considers settled. A daily sync has no
            # reason to store numbers that will still move.
            "dataState": "final",
        }
        response = session.post(url, json=body, timeout=HTTP_TIMEOUT, proxies=proxies)
        if response.status_code != 200:
            raise GscApiError(
                f"HTTP {response.status_code} from Search Console: "
                f"{response.text[:400]}")
        batch = response.json().get("rows", [])
        rows.extend(batch)
        if len(batch) < row_limit:
            break
        start_row += row_limit
    return rows


# ── Validate ─────────────────────────────────────────────────────────────

def validate_row(row):
    """Return (clean_tuple, None) or (None, reason).

    This is the boundary V2.3 §11 asks for: the API is an external system,
    and its output does not enter the database until it has been checked.
    """
    keys = row.get("keys") or []
    if len(keys) != 3:
        return None, f"expected 3 dimension keys, got {len(keys)}"
    raw_date, query, page = (str(k) for k in keys)

    try:
        datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        return None, f"unparseable date {raw_date!r}"

    parsed = urlparse(page)
    if parsed.scheme != "https" or parsed.netloc not in OWN_DOMAINS:
        return None, f"page not on suppbridge.com: {page!r}"
    if not query.strip():
        return None, "empty query"

    clicks = row.get("clicks", 0)
    impressions = row.get("impressions", 0)
    ctr = row.get("ctr", 0.0)
    position = row.get("position", 0.0)

    if clicks < 0:
        return None, f"negative clicks ({clicks})"
    if impressions < 0:
        return None, f"negative impressions ({impressions})"
    if not 0.0 <= ctr <= 1.0:
        return None, f"ctr out of range ({ctr})"
    if position <= 0:
        return None, f"position must be > 0 ({position})"
    if clicks > impressions:
        return None, f"clicks ({clicks}) exceed impressions ({impressions})"

    return (raw_date, query, page, int(clicks), int(impressions),
            float(ctr), float(position)), None


def validate_rows(raw_rows):
    """Split raw API rows into clean rows and rejection reasons."""
    clean, rejects = [], []
    for row in raw_rows:
        ok, reason = validate_row(row)
        if ok:
            clean.append(ok)
        else:
            rejects.append(reason)
    return clean, rejects


# ── Report ───────────────────────────────────────────────────────────────

def print_report(prop, start, end, raw_count, clean, rejects, top=20):
    pages = {r[2] for r in clean}
    queries = {r[1] for r in clean}
    clicks = sum(r[3] for r in clean)
    impressions = sum(r[4] for r in clean)

    print("GSC connection: PASS")
    print()
    print("Property:")
    print(prop)
    print()
    print("Date range:")
    print(f"{start.isoformat()} → {end.isoformat()}")
    print()
    print("Rows fetched:")
    print(raw_count)
    print()
    print("Rows accepted / rejected:")
    print(f"{len(clean)} / {len(rejects)}")
    print()
    print("Pages:")
    print(len(pages))
    print()
    print("Queries:")
    print(len(queries))
    print()
    print("Clicks:")
    print(clicks)
    print()
    print("Impressions:")
    print(impressions)
    print()

    if rejects:
        print("Rejected rows (first 5 reasons):")
        for reason in rejects[:5]:
            print(f"  - {reason}")
        print()

    head = f"{'query':38s} {'page':34s} {'clicks':>7s} {'impr':>7s} {'ctr':>7s} {'pos':>6s}"
    print(head)
    print("-" * len(head))
    for r in sorted(clean, key=lambda x: (-x[3], -x[4]))[:top]:
        _, query, page, c, i, ctr, pos = r
        path = urlparse(page).path or "/"
        print(f"{query[:36]:38s} {path[:32]:34s} {c:>7d} {i:>7d} {ctr * 100:>6.2f}% {pos:>6.1f}")


def print_blocked(reason):
    print("GSC connection: BLOCKED")
    print()
    print(reason)
    print()
    print("No data was fetched and nothing was written. To unblock, follow")
    print("scripts/GSC-API-SETUP.md and place the service-account key at:")
    for path in CREDENTIAL_PATHS:
        print(f"  {path}")
    print("  (owner: the user running the sync, mode 600)")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SuppBridge GSC fetcher → seo_intel")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"days of history to pull (default {DEFAULT_DAYS})")
    parser.add_argument("--property", default=None,
                        help=f"GSC property (default {DEFAULT_PROPERTY})")
    parser.add_argument("--credentials", default=None, help="path to the service-account JSON")
    parser.add_argument("--dsn", default=None, help="PostgreSQL DSN for seo_intel")
    parser.add_argument("--row-limit", type=int, default=DEFAULT_ROW_LIMIT)
    parser.add_argument("--top", type=int, default=20, help="rows to print (default 20)")
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch and validate, but write nothing")
    parser.add_argument("--init-db", action="store_true",
                        help="create the seo_intel tables and exit")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero when blocked instead of skipping")
    parser.add_argument("--egress-check", action="store_true",
                        help="only test which proxy path reaches Search "
                             "Console; touches no credentials and no database")
    args = parser.parse_args()

    if args.egress_check:
        proxy, tried = choose_proxy()
        for item in tried:
            mark = "OK  " if item["ok"] else "FAIL"
            print(f"{mark} {item['proxy']:40s} {item['detail']}")
        ok = any(t["ok"] for t in tried)
        print()
        print(f"Egress: {'PASS' if ok else 'FAIL'} (chosen: {proxy or 'direct'})")
        return 0 if ok else 1

    if args.init_db:
        conn = store.connect(args.dsn or store.dsn_from_env())
        store.apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute("""SELECT table_name FROM information_schema.tables
                            WHERE table_schema = 'public' ORDER BY 1""")
            print("seo_intel schema applied. Tables: " +
                  ", ".join(r[0] for r in cur.fetchall()))
        conn.close()
        return 0

    prop = resolve_property(args.property)
    start = date.today() - timedelta(days=args.days)
    end = date.today()

    cred_path, is_legacy = resolve_credentials(args.credentials)
    if not cred_path:
        print_blocked("No service-account credentials found.")
        if not args.dry_run:
            _record_skip(args.dsn)
        return 1 if args.strict else 0
    if is_legacy:
        print("[WARN] Using the legacy in-repo key at scripts/gsc-service-account.json.")
        print("       Move it to /etc/suppbridge/seo-intel/ so a stray `git add` cannot leak it.")
        print()

    # Egress is resolved before the database is touched: if no path reaches
    # Google, the run is recorded as a failure with the reason, and nothing
    # downstream has to guess whether it was credentials or the network.
    proxy, tried = choose_proxy()
    if not any(t["ok"] for t in tried):
        message = "no egress path to Search Console: " + format_tried(tried)
        print("GSC connection: FAILED")
        print(message)
        print("Fix: put a working proxy in SEO_INTEL_PROXY_CANDIDATES "
              "(proxy.env) and re-run `gsc-fetcher.py --egress-check`.")
        if not args.dry_run:
            try:
                conn = store.connect(args.dsn or store.dsn_from_env())
                store.apply_schema(conn)
                run_id = store.start_run(conn, "gsc")
                store.finish_run(conn, run_id, store.STATUS_FAILED,
                                 error_message=message[:2000])
                conn.close()
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] Could not record the failed run: {exc}")
        return 1

    print(f"Egress: {proxy or 'direct'} ({tried[-1]['detail']})")
    if len(tried) > 1:
        print(f"        skipped: {format_tried(tried[:-1])}")
    print()

    session = build_service(cred_path)

    conn = None
    run_id = None
    if not args.dry_run:
        conn = store.connect(args.dsn or store.dsn_from_env())
        store.apply_schema(conn)
        run_id = store.start_run(conn, "gsc")

    try:
        raw_rows = fetch_rows(session, prop, start, end, args.row_limit, proxy=proxy)
    except Exception as exc:  # noqa: BLE001 - the message is the product here
        message = f"{type(exc).__name__}: {exc}"
        print("GSC connection: FAILED")
        print(message)
        # A timeout here is almost always egress, not credentials, and the
        # two look identical otherwise. Say which one it is.
        print(f"Egress: {proxy_hint()}")
        if conn:
            store.finish_run(conn, run_id, store.STATUS_FAILED,
                             error_message=message[:2000])
            conn.close()
        return 1

    clean, rejects = validate_rows(raw_rows)

    status = store.STATUS_SUCCESS if not rejects else store.STATUS_PARTIAL
    written = 0
    if conn:
        try:
            written = store.upsert_gsc_rows(conn, clean)
            store.finish_run(
                conn, run_id, status,
                rows_fetched=len(raw_rows), rows_written=written,
                rows_rejected=len(rejects),
                notes=(f"property={prop} range={start}..{end}"
                       + (f"; rejected: {'; '.join(sorted(set(rejects))[:5])}" if rejects else "")),
            )
        finally:
            conn.close()

    print_report(prop, start, end, len(raw_rows), clean, rejects, args.top)
    print()
    if args.dry_run:
        print(f"DRY RUN — {len(clean)} validated rows, nothing written.")
    else:
        print(f"Stored: {written} rows into seo_intel.seo_gsc_daily (run id {run_id}).")
    return 0


def _record_skip(dsn):
    """Log the skip so the scheduler's history is honest, and never crash."""
    try:
        conn = store.connect(dsn or store.dsn_from_env())
        run_id = store.start_run(conn, "gsc")
        store.finish_run(conn, run_id, store.STATUS_SKIPPED,
                         notes="credentials not configured; see scripts/GSC-API-SETUP.md")
        conn.close()
    except Exception as exc:  # noqa: BLE001 - a skip must not become a failure
        print(f"[WARN] Could not record the skipped run: {exc}")


if __name__ == "__main__":
    sys.exit(main())
