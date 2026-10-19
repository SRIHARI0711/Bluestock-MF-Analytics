
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_DIR / "data" / "raw" / "07_scheme_performance.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "clean_scheme_performance.csv"
ANOMALY_FILE = OUTPUT_DIR / "scheme_performance_anomalies.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW_FILE)

print("Original shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nMissing values before cleaning:")
print(df.isna().sum())

if "amfi_code" not in df.columns:
    raise ValueError("Required column 'amfi_code' is missing.")

df["amfi_code"] = df["amfi_code"].astype("string").str.strip()

# Convert known performance metrics to numeric where present.
numeric_columns = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct",
    "benchmark_3yr_pct",
    "alpha",
    "beta",
    "sharpe_ratio",
    "sortino_ratio",
    "std_dev_ann_pct",
    "max_drawdown_pct",
    "expense_ratio_pct",
    "morningstar_rating",
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Required metric columns must exist for this cleaning task.
required_metrics = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct",
    "expense_ratio_pct",
]

missing_metrics = set(required_metrics) - set(df.columns)
if missing_metrics:
    raise ValueError(f"Missing expected columns: {missing_metrics}")

# Flag numeric conversion failures and missing metric values.
df["flag_missing_or_invalid_metric"] = df[
    required_metrics
].isna().any(axis=1)

# Flag negative Sharpe ratios.
if "sharpe_ratio" in df.columns:
    df["flag_negative_sharpe"] = df["sharpe_ratio"] < 0
else:
    df["flag_negative_sharpe"] = False

# Flag expense ratios outside the requested range.
df["flag_expense_ratio_out_of_range"] = (
    df["expense_ratio_pct"].notna()
    & ~df["expense_ratio_pct"].between(0.1, 2.5)
)

# Flag unusual returns for review; negative returns can be legitimate.
return_columns = [
    c for c in [
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
    ] if c in df.columns
]

df["flag_unusual_return"] = False

for col in return_columns:
    df["flag_unusual_return"] |= (
        df[col].notna()
        & ~df[col].between(-100, 200)
    )

# Report duplicate scheme keys.
print(
    "\nDuplicate AMFI code rows:",
    df.duplicated(["amfi_code"], keep=False).sum()
)

if df["amfi_code"].isna().any() or df["amfi_code"].eq("").any():
    raise ValueError("Missing or blank AMFI codes require investigation.")

# Keep anomalies for review; do not silently discard them.
flag_columns = [
    "flag_missing_or_invalid_metric",
    "flag_negative_sharpe",
    "flag_expense_ratio_out_of_range",
    "flag_unusual_return",
]

print("\nAnomaly flag counts:")
for col in flag_columns:
    print(f"{col}: {int(df[col].sum())}")

# Save all rows with validation flags.
df.to_csv(OUTPUT_FILE, index=False)

# Save rows requiring review.
anomalies = df.loc[df[flag_columns].any(axis=1)].copy()
anomalies.to_csv(ANOMALY_FILE, index=False)

print("\nCleaned dataset shape:", df.shape)
print("Rows flagged for review:", len(anomalies))
print("Cleaned output:", OUTPUT_FILE)
print("Anomaly report:", ANOMALY_FILE)
print("\nRemaining missing values:")
print(df.isna().sum())
