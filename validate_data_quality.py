#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Data Quality Validator
========================================================
Validates scheme master codes against NAV history records, performs null audits,
duplicate checks, and generates data quality summary reports in reports/.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def validate_data():
    """Performs validation checks between fund master and NAV history datasets."""
    funds = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    nav = pd.read_csv(RAW_DIR / "02_nav_history.csv")

    print("=" * 70)
    print("1. FUND MASTER OVERVIEW")
    print("=" * 70)
    print(f"Fund records: {len(funds)}")

    for column in ["fund_house", "category", "sub_category", "risk_category", "plan"]:
        if column in funds.columns:
            print(f"\nUnique {column} values:")
            print(sorted(funds[column].dropna().astype(str).unique()))

    print("\n" + "=" * 70)
    print("2. NAV HISTORY SCHEMA")
    print("=" * 70)
    print("NAV columns:", nav.columns.tolist())
    print("NAV shape:", nav.shape)

    print("\n" + "=" * 70)
    print("3. SCHEME CODE VALIDATION")
    print("=" * 70)

    if "amfi_code" not in funds.columns:
        raise ValueError("Fund master is missing the amfi_code column.")

    candidate_columns = ["amfi_code", "scheme_code", "schemeCode", "scheme_id", "scheme"]
    nav_code_column = next((column for column in candidate_columns if column in nav.columns), None)

    if nav_code_column is None:
        raise ValueError("No recognized scheme-code column found in NAV history.")

    fund_codes = set(pd.to_numeric(funds["amfi_code"], errors="coerce").dropna().astype("int64"))
    nav_codes = set(pd.to_numeric(nav[nav_code_column], errors="coerce").dropna().astype("int64"))

    matched_codes = sorted(fund_codes & nav_codes)
    missing_codes = sorted(fund_codes - nav_codes)

    print(f"NAV identifier column: {nav_code_column}")
    print(f"Unique fund-master codes: {len(fund_codes)}")
    print(f"Unique NAV-history codes: {len(nav_codes)}")
    print(f"Codes present in both: {len(matched_codes)}")
    print(f"Fund-master codes absent from NAV history: {len(missing_codes)}")

    funds["nav_history_match"] = pd.to_numeric(funds["amfi_code"], errors="coerce").isin(nav_codes)
    funds.to_csv(REPORT_DIR / "scheme_code_validation.csv", index=False)

    summary = pd.DataFrame([
        {"check": "Fund master records", "result": len(funds)},
        {"check": "Unique fund-master codes", "result": len(fund_codes)},
        {"check": "Unique NAV-history codes", "result": len(nav_codes)},
        {"check": "Matching scheme codes", "result": len(matched_codes)},
        {"check": "Codes absent from NAV history", "result": len(missing_codes)},
        {"check": "NAV missing cells", "result": int(nav.isna().sum().sum())},
        {"check": "NAV duplicate rows", "result": int(nav.duplicated().sum())},
    ])

    print("\n" + "=" * 70)
    print("4. DATA QUALITY SUMMARY")
    print("=" * 70)
    print(summary.to_string(index=False))

    summary.to_csv(REPORT_DIR / "day1_data_quality_summary.csv", index=False)
    print("\nData quality summary saved in reports/.")


if __name__ == "__main__":
    validate_data()
