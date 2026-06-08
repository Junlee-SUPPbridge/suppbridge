#!/usr/bin/env python3
"""
SuppBridge GSC Data Fetcher
============================
Uses Google Search Console API with service account authentication.
Pull real SEO data: indexed pages, search queries, click data, ranking positions.

Setup: See GSC-API-SETUP.md for service account configuration.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
KEY_PATH = os.path.join(SCRIPT_DIR, "gsc-service-account.json")
CACHE_DIR = os.path.join(PROJECT_DIR, ".workbuddy", "gsc-cache")
SITE_URL = "https://www.suppbridge.com/"  # URL prefix property (domain property doesn't support SA)

# ============================================================
# Auth
# ============================================================

def get_service():
    """Build authenticated Search Console service object."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("[ERROR] Missing packages. Run:")
        print("  pip install google-auth google-api-python-client google-auth-httplib2")
        sys.exit(1)

    if not os.path.exists(KEY_PATH):
        print(f"[ERROR] Service account key not found: {KEY_PATH}")
        print("See GSC-API-SETUP.md for instructions.")
        sys.exit(1)

    with open(KEY_PATH) as f:
        key_data = json.load(f)

    creds = service_account.Credentials.from_service_account_info(
        key_data,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    return build("searchconsole", "v1", credentials=creds)

# ============================================================
# Data Fetchers
# ============================================================

def fetch_index_status(service):
    """Get indexed / not-indexed page counts."""
    print("\n" + "=" * 60)
    print("INDEX STATUS REPORT")
    print("=" * 60)

    # Indexed pages count
    try:
        result = service.urlInspection().index().inspect(
            body={"inspectionUrl": "https://suppbridge.com/", "siteUrl": SITE_URL}
        ).execute()
        insp = result.get("inspectionResult", {}).get("indexStatusResult", {})
        print(f"\n  Homepage .......... {insp.get('coverageState', 'unknown')}")
    except Exception as e:
        print(f"\n  Homepage .......... [error] {e}")

    return True


def fetch_search_performance(service, days=28):
    """Pull search analytics: queries, clicks, impressions, CTR, position."""
    print("\n" + "=" * 60)
    print(f"SEARCH PERFORMANCE (last {days} days)")
    print("=" * 60)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    request = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query"],
        "rowLimit": 50,
        "startRow": 0,
    }

    try:
        response = service.searchanalytics().query(
            siteUrl=SITE_URL, body=request
        ).execute()

        rows = response.get("rows", [])
        if not rows:
            print("\n  (No search data yet — site may be too new)")
            return None

        total_clicks = sum(r["clicks"] for r in rows)
        total_impressions = sum(r["impressions"] for r in rows)
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
        avg_pos = sum(r["position"] * r["impressions"] for r in rows) / total_impressions if total_impressions else 0

        print(f"\n  Total Clicks .... {total_clicks}")
        print(f"  Total Impressions. {total_impressions}")
        print(f"  Avg CTR ......... {avg_ctr:.1f}%")
        print(f"  Avg Position .... {avg_pos:.1f}")
        print(f"\n  {'Query':45s} {'Clicks':>7s} {'Impr':>7s} {'CTR':>6s} {'Pos':>5s}")
        print("  " + "-" * 72)

        for row in rows[:20]:
            query = row["keys"][0][:43]
            clicks = row["clicks"]
            imps = row["impressions"]
            ctr = (clicks / imps * 100) if imps else 0
            pos = row["position"]
            print(f"  {query:45s} {clicks:>7d} {imps:>7d} {ctr:>5.1f}% {pos:>5.1f}")

        return {
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": avg_ctr,
            "avg_position": avg_pos,
            "top_queries": rows[:10],
        }

    except Exception as e:
        print(f"\n  [ERROR] {e}")
        return None


def fetch_sitemap_status(service):
    """Check sitemap submission status."""
    print("\n" + "=" * 60)
    print("SITEMAP STATUS")
    print("=" * 60)

    sitemaps = [
        "https://suppbridge.com/sitemap.xml",
        "https://suppbridge.com/blog/sitemap.xml",
    ]

    active_sitemaps = []
    for sm in sitemaps:
        try:
            result = service.sitemaps().get(
                siteUrl=SITE_URL, feedpath=sm
            ).execute()
            print(f"\n  {sm}")
            print(f"    Submitted: {result.get('contents', [{}])[0].get('submitted', '?')}")
            print(f"    Indexed:   {result.get('contents', [{}])[0].get('indexed', '?')}")
            active_sitemaps.append(sm)
        except Exception:
            print(f"\n  {sm}")
            print(f"    Status: NOT SUBMITTED — submit in GSC panel")

    if not active_sitemaps:
        print("\n  ⚠️  No sitemaps submitted. Google may discover pages slowly.")

    return active_sitemaps


def fetch_page_queries(service, page_path, days=28):
    """Get queries driving traffic to a specific page."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    full_url = f"https://suppbridge.com{page_path}"
    request = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query"],
        "dimensionFilterGroups": [{
            "filters": [{
                "dimension": "page",
                "operator": "equals",
                "expression": full_url
            }]
        }],
        "rowLimit": 25,
        "startRow": 0,
    }

    try:
        response = service.searchanalytics().query(
            siteUrl=SITE_URL, body=request
        ).execute()
        return response.get("rows", [])
    except Exception:
        return []


# ============================================================
# Report Builder
# ============================================================

def build_report(service):
    """Generate full SEO report from GSC data."""
    perf = fetch_search_performance(service)
    sitemaps = fetch_sitemap_status(service)
    fetch_index_status(service)

    # Build daily monitoring data
    report = {
        "date": datetime.now().isoformat(),
        "search_performance": perf,
        "active_sitemaps": sitemaps,
    }

    # Cache for later comparison
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"gsc-{datetime.now().strftime('%Y-%m-%d')}.json")
    with open(cache_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  [Report cached to {cache_file}]")

    return report


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SuppBridge GSC Data Fetcher")
    parser.add_argument("--perf", action="store_true", help="Fetch search performance only")
    parser.add_argument("--sitemaps", action="store_true", help="Check sitemap status only")
    parser.add_argument("--index", action="store_true", help="Check index status only")
    parser.add_argument("--full", action="store_true", help="Generate full report")
    parser.add_argument("--days", type=int, default=28, help="Days of data (default: 28)")

    args = parser.parse_args()
    svc = get_service()

    if args.perf:
        fetch_search_performance(svc, days=args.days)
    elif args.sitemaps:
        fetch_sitemap_status(svc)
    elif args.index:
        fetch_index_status(svc)
    else:
        build_report(svc)
