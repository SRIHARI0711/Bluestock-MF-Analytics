
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_DIR / "data" / "raw" / "02_nav_history.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "clean_nav_history.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load source data
df = pd.read_csv(RAW_FILE)

print("Original shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nMissing values before cleaning:")
print(df.isna().sum())

# 2. Validate required columns
required_columns = {"amfi_code", "date", "nav"}
missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# 3. Standardise and validate data types
df["amfi_code"] = df["amfi_code"].astype("string").str.strip()
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

# 4. Remove rows with invalid identifiers or dates
invalid_keys = (
    df["amfi_code"].isna()
    | df["amfi_code"].eq("")
    | df["date"].isna()
)

print("\nRows with invalid fund codes or dates:", invalid_keys.sum())
df = df.loc[~invalid_keys].copy()

# 5. Report duplicate fund-date combinations
duplicate_keys = df.duplicated(
    subset=["amfi_code", "date"], keep=False
)
print("Rows involved in duplicate fund-date combinations:",
      duplicate_keys.sum())

# Remove exact duplicate rows first
df = df.drop_duplicates()

# If a fund has multiple different NAVs for the same date,
# stop rather than arbitrarily selecting a value.
conflicts = df.duplicated(
    subset=["amfi_code", "date"], keep=False
)

if conflicts.any():
    print("\nConflicting fund-date records:")
    print(
        df.loc[conflicts]
        .sort_values(["amfi_code", "date"])
        .head(20)
    )
    raise ValueError(
        "Resolve conflicting NAV records before continuing."
    )

# 6. Validate NAV > 0
invalid_nav = df["nav"].isna() | (df["nav"] <= 0)
print("Rows with missing, non-numeric or non-positive NAV:",
      invalid_nav.sum())

df = df.loc[~invalid_nav].copy()

# 7. Sort chronologically
df = df.sort_values(
    ["amfi_code", "date"]
).reset_index(drop=True)

# 8. Preserve actual NAV observations.
# Do not fill weekends or holidays into this raw-observation table.
# Calendar expansion and forward-filling can be done separately
# when a downstream analysis explicitly requires a daily calendar.

# 9. Save cleaned data
df["date"] = df["date"].dt.strftime("%Y-%m-%d")
df.to_csv(OUTPUT_FILE, index=False)

print("\nNAV cleaning completed.")
print("Cleaned shape:", df.shape)
print("Output:", OUTPUT_FILE)
print("Remaining missing values:")
print(df.isna().sum())
print("Remaining exact duplicates:", df.duplicated().sum())
print(
    "NAV values all positive:",
    (pd.to_numeric(df["nav"]) > 0).all()
)
print(
    "Fund-date combinations unique:",
    not df.duplicated(["amfi_code", "date"]).any()
)
