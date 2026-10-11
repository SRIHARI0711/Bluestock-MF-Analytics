
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
                    print("Unexpected API response:", data)
                    continue

                matches = [
                    item for item in data
                    if "schemeCode" in item and "schemeName" in item
                ]

                for item in matches:
                    row = {
                        "search_term": term,
                        "scheme_code": item["schemeCode"],
                        "scheme_name": item["schemeName"],
                    }
                    results.append(row)
                    print(
                        f"  {row['scheme_code']} | "
                        f"{row['scheme_name']}"
                    )

                if not matches:
                    print("  No matching schemes returned.")

            except (requests.RequestException, ValueError) as error:
                print(f"  Search failed: {error}")

            time.sleep(1)

    if results:
        df = pd.DataFrame(results)
        output_path = RAW_DIR / "scheme_code_search_results.csv"
        df.to_csv(output_path, index=False)
        print(f"\nResults saved to: {output_path}")
    else:
        print("\nNo results collected. Check the API response.")


if __name__ == "__main__":
    main()
