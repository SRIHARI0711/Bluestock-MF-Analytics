
from pathlib import Path
import pandas as pd
import numpy as np

# --------------------------------------------------
# 1. Paths
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2. Helper functions
# --------------------------------------------------
def load_csv(filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    df = pd.read_csv(path)
    print(f"\n{'=' * 60}")
    print(f"Processing: {filename}")
    print("Original shape:", df.shape)

    return df


def require_columns(df, columns, filename):
    missing = set(columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"{filename} is missing columns: {missing}"
        )


def save_cleaned(df, filename):
    output = PROCESSED_DIR / filename
    df.to_csv(output, index=False)

    print("Cleaned shape:", df.shape)
    print("Missing values:", int(df.isna().sum().sum()))
    print("Saved:", output)


def parse_date_column(df, column, filename):
    df[column] = pd.to_datetime(
        df[column], errors="coerce"
    )

    invalid = int(df[column].isna().sum())
    print(f"Invalid {column} values:", invalid)

    if invalid:
        raise ValueError(
            f"{filename}: investigate invalid {column} values."
        )


def validate_unique_key(df, columns, filename):
    duplicates = int(
        df.duplicated(subset=columns, keep=False).sum()
    )

    print(f"Duplicate key rows ({columns}):", duplicates)

    if duplicates:
        raise ValueError(
            f"{filename}: duplicate business keys require review."
        )


def validate_required_values(df, columns, filename):
    missing = int(df[columns].isna().sum().sum())

    if missing:
        raise ValueError(
            f"{filename}: {missing} missing required values."
        )


# --------------------------------------------------
# 3. Fund master
# --------------------------------------------------
filename = "01_fund_master.csv"
df = load_csv(filename)

require_columns(
    df,
    [
        "amfi_code", "fund_house", "scheme_name",
        "category", "sub_category", "plan",
        "launch_date", "expense_ratio_pct",
        "exit_load_pct", "min_sip_amount",
        "min_lumpsum_amount"
    ],
    filename
)

df["amfi_code"] = df["amfi_code"].astype("string").str.strip()

for col in [
    "fund_house", "scheme_name", "category",
    "sub_category", "plan", "benchmark",
    "fund_manager", "risk_category", "sebi_category_code"
]:
    if col in df.columns:
        df[col] = df[col].astype("string").str.strip()

parse_date_column(df, "launch_date", filename)

numeric_cols = [
    "expense_ratio_pct", "exit_load_pct",
    "min_sip_amount", "min_lumpsum_amount"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

validate_required_values(
    df,
    ["amfi_code", "fund_house", "scheme_name",
     "category", "launch_date"] + numeric_cols,
    filename
)

if (df[numeric_cols] < 0).any().any():
    raise ValueError("Fund master contains negative numeric values.")

validate_unique_key(df, ["amfi_code"], filename)

df["launch_date"] = df["launch_date"].dt.strftime("%Y-%m-%d")
save_cleaned(df, "clean_fund_master.csv")


# --------------------------------------------------
# 4. AUM by fund house
# --------------------------------------------------
filename = "03_aum_by_fund_house.csv"
df = load_csv(filename)

require_columns(
    df,
    ["date", "fund_house", "aum_lakh_crore",
     "aum_crore", "num_schemes"],
    filename
)

parse_date_column(df, "date", filename)
df["fund_house"] = df["fund_house"].astype("string").str.strip()

for col in ["aum_lakh_crore", "aum_crore", "num_schemes"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

validate_required_values(
    df,
    ["date", "fund_house", "aum_lakh_crore",
     "aum_crore", "num_schemes"],
    filename
)

if (df[["aum_lakh_crore", "aum_crore", "num_schemes"]] < 0).any().any():
    raise ValueError("AUM dataset contains negative values.")

validate_unique_key(df, ["date", "fund_house"], filename)

df = df.sort_values(["fund_house", "date"])
df["date"] = df["date"].dt.strftime("%Y-%m-%d")
save_cleaned(df, "clean_aum_by_fund_house.csv")


# --------------------------------------------------
# 5. Monthly SIP inflows
# --------------------------------------------------
filename = "04_monthly_sip_inflows.csv"
df = load_csv(filename)

require_columns(
    df,
    [
        "month", "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore", "yoy_growth_pct"
    ],
    filename
)

df["month"] = pd.to_datetime(
    df["month"].astype("string").str.strip(),
    format="%Y-%m",
    errors="coerce"
)

numeric_cols = [
    "sip_inflow_crore",
    "active_sip_accounts_crore",
    "new_sip_accounts_lakh",
    "sip_aum_lakh_crore",
    "yoy_growth_pct"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

validate_required_values(
    df,
    [
        "month", "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore"
    ],
    filename
)

validate_unique_key(df, ["month"], filename)

# Calculate missing YoY growth only when the same
# month in the previous year exists.
df = df.sort_values("month").reset_index(drop=True)

df["yoy_growth_pct"] = df["yoy_growth_pct"].fillna(
    df["sip_inflow_crore"].pct_change(periods=12) * 100
)

print(
    "YoY growth values still missing:",
    int(df["yoy_growth_pct"].isna().sum())
)

df["month"] = df["month"].dt.strftime("%Y-%m")
save_cleaned(df, "clean_monthly_sip_inflows.csv")


# --------------------------------------------------
# 6. Category inflows
# --------------------------------------------------
filename = "05_category_inflows.csv"
df = load_csv(filename)

require_columns(
    df, ["month", "category", "net_inflow_crore"], filename
)

df["month"] = pd.to_datetime(
    df["month"].astype("string").str.strip(),
    format="%Y-%m",
    errors="coerce"
)

df["category"] = df["category"].astype("string").str.strip()
df["net_inflow_crore"] = pd.to_numeric(
    df["net_inflow_crore"], errors="coerce"
)

validate_required_values(
    df, ["month", "category", "net_inflow_crore"], filename
)

validate_unique_key(df, ["month", "category"], filename)

df = df.sort_values(["month", "category"])
df["month"] = df["month"].dt.strftime("%Y-%m")
save_cleaned(df, "clean_category_inflows.csv")


# --------------------------------------------------
# 7. Industry folio count
# --------------------------------------------------
filename = "06_industry_folio_count.csv"
df = load_csv(filename)

folio_cols = [
    "total_folios_crore", "equity_folios_crore",
    "debt_folios_crore", "hybrid_folios_crore",
    "others_folios_crore"
]

require_columns(df, ["month"] + folio_cols, filename)

df["month"] = pd.to_datetime(
    df["month"].astype("string").str.strip(),
    format="%Y-%m",
    errors="coerce"
)

for col in folio_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

validate_required_values(df, ["month"] + folio_cols, filename)
validate_unique_key(df, ["month"], filename)

if (df[folio_cols] < 0).any().any():
    raise ValueError("Folio counts cannot be negative.")

df = df.sort_values("month")
df["month"] = df["month"].dt.strftime("%Y-%m")
save_cleaned(df, "clean_industry_folio_count.csv")


# --------------------------------------------------
# 8. Portfolio holdings
# --------------------------------------------------
filename = "09_portfolio_holdings.csv"
df = load_csv(filename)

require_columns(
    df,
    [
        "amfi_code", "stock_symbol", "stock_name",
        "sector", "weight_pct", "market_value_cr",
        "current_price_inr", "portfolio_date"
    ],
    filename
)

for col in ["amfi_code", "stock_symbol", "stock_name", "sector"]:
    df[col] = df[col].astype("string").str.strip()

parse_date_column(df, "portfolio_date", filename)

for col in ["weight_pct", "market_value_cr", "current_price_inr"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

validate_required_values(
    df,
    [
        "amfi_code", "stock_symbol", "stock_name", "sector",
        "portfolio_date", "weight_pct", "market_value_cr",
        "current_price_inr"
    ],
    filename
)

if (df[["weight_pct", "market_value_cr", "current_price_inr"]] < 0).any().any():
    raise ValueError("Portfolio holdings contain negative values.")

if (df["weight_pct"] > 100).any():
    raise ValueError("Portfolio holding weights exceed 100%.")

validate_unique_key(
    df,
    ["amfi_code", "stock_symbol", "portfolio_date"],
    filename
)

df = df.sort_values(["amfi_code", "portfolio_date", "stock_symbol"])
df["portfolio_date"] = df["portfolio_date"].dt.strftime("%Y-%m-%d")
save_cleaned(df, "clean_portfolio_holdings.csv")


# --------------------------------------------------
# 9. Benchmark indices
# --------------------------------------------------
filename = "10_benchmark_indices.csv"
df = load_csv(filename)

require_columns(df, ["date", "index_name", "close_value"], filename)

parse_date_column(df, "date", filename)
df["index_name"] = df["index_name"].astype("string").str.strip()
df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")

validate_required_values(
    df, ["date", "index_name", "close_value"], filename
)

if (df["close_value"] <= 0).any():
    raise ValueError("Benchmark closing values must be positive.")

validate_unique_key(df, ["date", "index_name"], filename)

df = df.sort_values(["index_name", "date"])
df["date"] = df["date"].dt.strftime("%Y-%m-%d")
save_cleaned(df, "clean_benchmark_indices.csv")


# --------------------------------------------------
# 10. Completion summary
# --------------------------------------------------
print("\n" + "=" * 60)
print("REMAINING DATASET CLEANING COMPLETED")
print("=" * 60)

print("Processed files:")
for path in sorted(PROCESSED_DIR.glob("clean_*.csv")):
    print(f"{path.name}: {len(pd.read_csv(path)):,} rows")

print("\nReview any remaining missing YoY growth values.")
print("Original files in data/raw/ were not modified.")
