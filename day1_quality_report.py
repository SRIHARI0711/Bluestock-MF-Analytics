#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Day 1 Data Quality Summary Reporter
====================================================================
Cross-validates AMFI scheme codes between Fund Master, NAV History, and SIP datasets.
Outputs summary metrics to reports/day1_data_quality_summary.csv.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

funds = pd.read_csv(RAW_DIR / "01_fund_master.csv")
nav = pd.read_csv(RAW_DIR / "02_nav_history.csv")
sip = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")

fund_codes = set(
    pd.to_numeric(funds["amfi_code"], errors="coerce")
    .dropna().astype(int)
)
nav_codes = set(
    pd.to_numeric(nav["amfi_code"], errors="coerce")
    .dropna().astype(int)
)

report = [
    ("Fund master rows", len(funds)),
    ("Fund houses", funds["fund_house"].nunique()),
    ("Unique fund-master scheme codes", len(fund_codes)),
    ("NAV history rows", len(nav)),
    ("Unique NAV scheme codes", len(nav_codes)),
    ("Scheme codes matched", len(fund_codes & nav_codes)),
    ("Fund-master codes missing from NAV", len(fund_codes - nav_codes)),
    ("NAV missing cells", int(nav.isna().sum().sum())),
    ("NAV duplicate rows", int(nav.duplicated().sum())),
    ("SIP dataset rows", len(sip)),
    ("SIP missing cells", int(sip.isna().sum().sum())),
    ("SIP rows containing missing values", int(sip.isna().any(axis=1).sum())),
]

report_df = pd.DataFrame(report, columns=["Metric", "Value"])
output = REPORT_DIR / "day1_data_quality_summary.csv"
report_df.to_csv(output, index=False)

print(report_df.to_string(index=False))
print(f"\nSaved report: {output.resolve()}")

print("\nCaveat:")
print(
    "Code coverage validates identifiers only. "
    "Live API scheme identities require separate verification."
)
