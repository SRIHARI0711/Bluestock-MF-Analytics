
from pathlib import Path

import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_DIR / "data" / "processed" / "clean_nav_history.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "daily_nav_calendar.csv"

# Load the cleaned, observed NAV history
df = pd.read_csv(SOURCE_FILE)

required_columns = {"amfi_code", "date", "nav"}
missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(f"Missing columns: {sorted(missing_columns)}")

df["date"] = pd.to_datetime(df["date"], errors="raise")
df["nav"] = pd.to_numeric(df["nav"], errors="raise")
df = df.sort_values(["amfi_code", "date"]).copy()

# Validate source observations
if df.duplicated(["amfi_code", "date"]).any():
    raise ValueError("Duplicate fund-date records exist.")

if df["nav"].isna().any() or (df["nav"] <= 0).any():
    raise ValueError("NAV contains missing or non-positive values.")

daily_frames = []

# Expand each fund separately so values never cross fund boundaries
for amfi_code, fund_df in df.groupby("amfi_code", sort=True):
    fund_df = fund_df.sort_values("date").copy()
    fund_df = fund_df.set_index("date")

    # Calendar begins at the first actual observation for this fund
    calendar = pd.date_range(
        start=fund_df.index.min(),
        end=fund_df.index.max(),
        freq="D"
    )

    # Mark which calendar dates have actual source observations
    actual_dates = calendar.isin(fund_df.index)

    # Reindex to all calendar dates, then carry the last observed NAV forward
    expanded = fund_df.reindex(calendar)
    expanded["nav"] = expanded["nav"].ffill()

    expanded["amfi_code"] = amfi_code
    expanded["is_actual_nav"] = actual_dates

    expanded.index.name = "date"
    daily_frames.append(expanded.reset_index())

# Combine the daily calendar for all funds
daily_nav = pd.concat(daily_frames, ignore_index=True)
daily_nav = daily_nav[
    ["amfi_code", "date", "nav", "is_actual_nav"]
].sort_values(["amfi_code", "date"])

# Final validation
if daily_nav["nav"].isna().any():
    raise ValueError("Daily calendar contains NAV values that could not be filled.")

if (daily_nav["nav"] <= 0).any():
    raise ValueError("Daily calendar contains non-positive NAV values.")

if daily_nav.duplicated(["amfi_code", "date"]).any():
    raise ValueError("Duplicate fund-date records exist in daily calendar.")

# Save separately; do not overwrite the observed NAV history
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
daily_nav.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d")

print("=" * 65)
print("DAILY NAV CALENDAR CREATED")
print("=" * 65)
print("Original observed rows:", len(df))
print("Daily calendar rows:", len(daily_nav))
print("Actual NAV observations:", int(daily_nav["is_actual_nav"].sum()))
print("Carried-forward NAV values:", int((~daily_nav["is_actual_nav"]).sum()))
print("Unique funds:", daily_nav["amfi_code"].nunique())
print("Missing NAV values:", int(daily_nav["nav"].isna().sum()))
print("Duplicate fund-date pairs:",
      int(daily_nav.duplicated(["amfi_code", "date"]).sum()))
print("Output:", OUTPUT_FILE)
print("\nFirst 10 rows:")
print(daily_nav.head(10).to_string(index=False))

# Additional validation: confirm each fund starts with an actual observation.
first_rows = daily_nav.groupby("amfi_code", sort=False).head(1)

print("\nAdditional validation")
print("Every fund starts with an actual observation:",
      bool(first_rows["is_actual_nav"].all()))

# Show the actual and carried-forward NAV counts by fund.
print("\nNAV calendar counts by fund:")
print(
    daily_nav.groupby("amfi_code")["is_actual_nav"]
    .agg(
        calendar_rows="size",
        actual_observations="sum"
    )
    .assign(
        carried_forward=lambda x:
            x["calendar_rows"] - x["actual_observations"]
    )
    .head(10)
    .to_string()
)
