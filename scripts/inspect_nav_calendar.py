
from pathlib import Path
import pandas as pd

# Locate the project and source dataset
project_dir = Path(__file__).resolve().parent.parent
source_file = project_dir / "data" / "raw" / "02_nav_history.csv"

if not source_file.exists():
    raise FileNotFoundError(f"Source dataset not found: {source_file}")

# Load the original NAV data
df = pd.read_csv(source_file)

print("=" * 65)
print("NAV CALENDAR INSPECTION")
print("=" * 65)

print("\nOriginal column names:")
print(df.columns.tolist())

# Confirm the expected columns before analysis
required_columns = {"amfi_code", "date", "nav"}
missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(
        f"Expected columns not found: {sorted(missing_columns)}. "
        f"Available columns: {df.columns.tolist()}"
    )

# Parse dates and NAV values
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

print("\nSource rows:", len(df))
print("Unique funds:", df["amfi_code"].nunique())
print("Date range:", df["date"].min(), "to", df["date"].max())
print("Invalid or missing dates:", df["date"].isna().sum())
print("Missing or non-numeric NAV:", df["nav"].isna().sum())
print(
    "Duplicate fund-date pairs:",
    df.duplicated(["amfi_code", "date"]).sum()
)

print("\nFirst 10 observations:")
print(
    df.sort_values(["amfi_code", "date"])
      .head(10)
      .to_string(index=False)
)

# Inspect missing calendar dates for one fund.
valid_funds = df.loc[df["amfi_code"].notna(), "amfi_code"]

if valid_funds.empty:
    raise ValueError("No valid fund codes were found.")

fund_code = valid_funds.iloc[0]

fund = df[
    (df["amfi_code"] == fund_code) &
    (df["date"].notna())
].sort_values("date")

if fund.empty:
    raise ValueError(f"No valid dates found for fund {fund_code}.")

calendar = pd.date_range(
    start=fund["date"].min(),
    end=fund["date"].max(),
    freq="D"
)

observed_dates = pd.DatetimeIndex(fund["date"].unique())
missing_dates = calendar.difference(observed_dates)

print("\n" + "=" * 65)
print("CALENDAR COVERAGE FOR ONE FUND")
print("=" * 65)
print("Sample fund code:", fund_code)
print("First observed date:", fund["date"].min().date())
print("Last observed date:", fund["date"].max().date())
print("Observed dates:", len(observed_dates))
print("Calendar days:", len(calendar))
print("Dates without an observation:", len(missing_dates))
print(
    "First 15 missing calendar dates:",
    missing_dates[:15].strftime("%Y-%m-%d").tolist()
)

print("\nInspection completed. No source data was modified.")
