
from pathlib import Path
import json
import time

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Scheme codes supplied in the capstone instructions.
SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip",
    120503: "ICICI Bluechip",
    118632: "Nippon Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}

API_BASE = "https://api.mfapi.in/mf"


def fetch_scheme(session, code, requested_name):
    url = f"{API_BASE}/{code}"

    print(f"\nFetching code {code}: {requested_name}")

    response = session.get(url, timeout=60)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "SUCCESS":
        raise ValueError(f"API status: {payload.get('status')}")

    meta = payload.get("meta", {})
    records = payload.get("data", [])

    if not meta or not records:
        raise ValueError("Missing scheme metadata or NAV records")

    actual_code = int(meta["scheme_code"])
    if actual_code != code:
        raise ValueError(
            f"Requested code {code}, API returned {actual_code}"
        )

    # Keep the API's original date and NAV representations.
    df = pd.DataFrame(records)
    df.insert(0, "scheme_code", code)
    df.insert(1, "requested_label", requested_name)
    df.insert(2, "scheme_name", meta.get("scheme_name"))
    df.insert(3, "fund_house", meta.get("fund_house"))

    csv_path = RAW_DIR / f"live_nav_{code}.csv"
    df.to_csv(csv_path, index=False)

    # Save the complete API response separately for traceability.
    json_path = RAW_DIR / f"live_nav_{code}.json"
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    print(f"Actual scheme name: {meta.get('scheme_name')}")
    print(f"Fund house: {meta.get('fund_house')}")
    print(f"NAV records: {len(df):,}")
    print(f"CSV saved: {csv_path.name}")
    print(f"JSON saved: {json_path.name}")

    return {
        "scheme_code": code,
        "requested_label": requested_name,
        "actual_scheme_name": meta.get("scheme_name"),
        "fund_house": meta.get("fund_house"),
        "nav_records": len(df),
        "status": "SUCCESS",
    }


def main():
    results = []

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "Bluestock-MF-Analytics/1.0"
        })

        for code, name in SCHEMES.items():
            try:
                result = fetch_scheme(session, code, name)
                results.append(result)

            except (
                requests.RequestException,
                ValueError,
                KeyError,
                TypeError,
            ) as error:
                print(f"FAILED for {code}: {error}")
                results.append({
                    "scheme_code": code,
                    "requested_label": name,
                    "actual_scheme_name": None,
                    "fund_house": None,
                    "nav_records": 0,
                    "status": f"FAILED: {error}",
                })

            time.sleep(1)

    summary = pd.DataFrame(results)
    summary_path = RAW_DIR / "live_nav_fetch_summary.csv"
    summary.to_csv(summary_path, index=False)

    print("\n" + "=" * 70)
    print("LIVE NAV FETCH SUMMARY")
    print("=" * 70)
    print(summary.to_string(index=False))
    print(f"\nSummary saved: {summary_path}")

    if (summary["status"] != "SUCCESS").any():
        raise SystemExit(
            "Some schemes failed. Review the summary before proceeding."
        )


if __name__ == "__main__":
    main()
