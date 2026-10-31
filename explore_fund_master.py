#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Fund Master Explorer
======================================================
Inspects schema and records of 01_fund_master.csv, searching for
core fund families (HDFC, SBI, ICICI, Nippon, Axis, Kotak).
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "data" / "raw" / "01_fund_master.csv"

df = pd.read_csv(FILE_PATH)

print("\nFUND MASTER COLUMNS")
print(df.columns.tolist())

print("\nALL 40 FUND RECORDS")
print(df.to_string(index=False))

# Search for the six intended fund families using all text columns.
search_terms = [
    "HDFC",
    "SBI",
    "ICICI",
    "Nippon",
    "Axis",
    "Kotak",
]

text = df.fillna("").astype(str).agg(" ".join, axis=1)

for term in search_terms:
    matches = df[text.str.contains(term, case=False, regex=False)]

    print(f"\n{'=' * 60}")
    print(f"MATCHES FOR: {term}")
    print(f"{'=' * 60}")

    if matches.empty:
        print("No matching rows in fund master.")
    else:
        print(matches.to_string(index=False))
