#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Day 1 Data Ingestion Inspector
================================================================
Scans and profiles all raw CSV files in data/raw/, inspecting shapes,
data types, null cells, and duplicate rows, generating day1_dataset_inspection.csv.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

csv_files = sorted(RAW_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in {RAW_DIR}"
    )

summary = []

for file_path in csv_files:
    print("\n" + "=" * 80)
    print(f"DATASET: {file_path.name}")
    print("=" * 80)

    try:
        df = pd.read_csv(file_path)

        print("\nShape (rows, columns):")
        print(df.shape)

        print("\nData types:")
        print(df.dtypes)

        print("\nFirst 5 rows:")
        print(df.head().to_string())

        print("\nMissing values by column:")
        print(df.isna().sum())

        print("\nDuplicate rows:")
        print(df.duplicated().sum())

        summary.append({
            "file_name": file_path.name,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "missing_cells": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "status": "loaded"
        })

    except Exception as error:
        print(f"ERROR loading {file_path.name}: {error}")

        summary.append({
            "file_name": file_path.name,
            "rows": None,
            "columns": None,
            "missing_cells": None,
            "duplicate_rows": None,
            "status": f"failed: {error}"
        })

summary_df = pd.DataFrame(summary)

output_path = REPORT_DIR / "day1_dataset_inspection.csv"
summary_df.to_csv(output_path, index=False)

print("\n" + "=" * 80)
print("FINAL DATASET INSPECTION SUMMARY")
print("=" * 80)
print(summary_df.to_string(index=False))
print(f"\nSummary saved to: {output_path}")
