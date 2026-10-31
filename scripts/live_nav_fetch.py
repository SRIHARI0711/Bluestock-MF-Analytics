#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Live NAV Fetcher
===================================================
Fetches daily NAV records and scheme metadata directly from the public mfapi.in API.
Saves raw CSV and JSON responses to data/raw/ with audit trail.
"""

from pathlib import Path
import json
import time
import pandas as pd
import requests

# Set project paths using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Scheme codes supplied in the capstone instructions
SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip",
    120503: "ICICI Bluechip",
    118632: "Nippon Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}

API_BASE = "https://api.mfapi.in/mf"


def fetch_scheme(session: requests.Session, code: int, requested_name: str) -> dict:
    """Fetch NAV history and metadata for a single scheme code."""
    url = f"{API_BASE}/{code}"
    print(f"Fetching AMFI Code {code} ({requested_name})...")

    response = session.get(url, timeout=60)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "SUCCESS":
        raise ValueError(f"API returned status {payload.get('status')} for code {code}")

    meta = payload.get("meta", {})
    records = payload.get("data", [])

    if not meta or not records:
        raise ValueError(f"Missing scheme metadata or NAV records for code {code}")

    actual_code = int(meta.get("scheme_code", code))

    # Keep original date and NAV representations
    df = pd.DataFrame(records)
    df.insert(0, "scheme_code", actual_code)
    df.insert(1, "requested_label", requested_name)
    df.insert(2, "scheme_name", meta.get("scheme_name", ""))
    df.insert(3, "fund_house", meta.get("fund_house", ""))

    csv_path = RAW_DIR / f"live_nav_{code}.csv"
    df.to_csv(csv_path, index=False)

    # Save complete API response for auditability
    json_path = RAW_DIR / f"live_nav_{code}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    latest_rec = records[0] if records else {"date": "N/A", "nav": "N/A"}
    oldest_rec = records[-1] if records else {"date": "N/A", "nav": "N/A"}

    return {
        "scheme_code": actual_code,
        "scheme_name": meta.get("scheme_name", requested_name),
        "fund_house": meta.get("fund_house", ""),
        "scheme_type": meta.get("scheme_type", ""),
        "scheme_category": meta.get("scheme_category", ""),
        "total_records": len(records),
        "latest_date": latest_rec.get("date"),
        "latest_nav": latest_rec.get("nav"),
        "oldest_date": oldest_rec.get("date"),
        "oldest_nav": oldest_rec.get("nav"),
        "status": "SUCCESS"
    }


def main():
    print("=" * 70)
    print("BLUESTOCK MF ANALYTICS — LIVE NAV DATA INGESTION (mfapi.in)")
    print("=" * 70)

    session = requests.Session()
    session.headers.update({"User-Agent": "Bluestock-MF-Analytics/1.0"})

    summary_records = []
    for code, name in SCHEMES.items():
        try:
            res = fetch_scheme(session, code, name)
            summary_records.append(res)
            print(f"  -> Successfully ingested {res['total_records']:,} NAV records (Latest NAV: {res['latest_nav']} on {res['latest_date']})")
            time.sleep(0.5)  # Respect API rate limits
        except Exception as e:
            print(f"  -> [ERROR] Failed to fetch {code} ({name}): {e}")
            summary_records.append({
                "scheme_code": code,
                "scheme_name": name,
                "status": f"FAILED: {e}"
            })

    summary_df = pd.DataFrame(summary_records)
    summary_path = RAW_DIR / "live_nav_fetch_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print("\nSummary saved to:", summary_path)
    print("=" * 70)


if __name__ == "__main__":
    main()
