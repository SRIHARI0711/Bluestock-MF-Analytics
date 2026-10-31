#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — AMFI Scheme Code Finder
=========================================================
Queries mfapi.in search API to locate scheme codes and identifiers for marquee AMFI funds.
"""

from pathlib import Path
import time

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_TERMS = [
    "HDFC Top 100",
    "SBI Bluechip",
    "ICICI Prudential Bluechip",
    "Nippon India Large Cap",
    "Axis Bluechip",
    "Kotak Bluechip",
]

API_URL = "https://api.mfapi.in/mf/search"


def main():
    results = []

    with requests.Session() as session:
        for term in SEARCH_TERMS:
            print(f"\nSearching: {term}")

            try:
                response = session.get(
                    API_URL,
                    params={"q": term},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, list):
                    print("  Invalid response payload.")
                    continue

                print(f"  Found {len(data)} results.")

                for item in data[:5]:
                    code = item.get("schemeCode")
                    name = item.get("schemeName")
                    print(f"    {code} - {name}")

                    results.append({
                        "search_term": term,
                        "scheme_code": code,
                        "scheme_name": name,
                    })

            except Exception as error:
                print(f"  Search failed: {error}")

            time.sleep(0.5)

    if results:
        df = pd.DataFrame(results)
        output = RAW_DIR / "candidate_schemes.csv"
        df.to_csv(output, index=False)
        print(f"\nSaved candidates to {output}")


if __name__ == "__main__":
    main()
