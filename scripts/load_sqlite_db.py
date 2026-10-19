
from pathlib import Path
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, event, text

# --------------------------------------------------
# 1. Paths
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
SCHEMA_FILE = PROJECT_DIR / "sql" / "schema.sql"
DB_FILE = PROJECT_DIR / "bluestock_mf.db"

if not SCHEMA_FILE.exists():
    raise FileNotFoundError(f"Schema not found: {SCHEMA_FILE}")

required_files = [
    "clean_fund_master.csv",
    "clean_nav_history.csv",
    "clean_aum_by_fund_house.csv",
    "clean_investor_transactions.csv",
    "clean_scheme_performance.csv",
]

for filename in required_files:
    if not (DATA_DIR / filename).exists():
        raise FileNotFoundError(f"Missing processed file: {filename}")


# --------------------------------------------------
# 2. Read cleaned CSVs
# --------------------------------------------------
funds = pd.read_csv(DATA_DIR / "clean_fund_master.csv")
nav = pd.read_csv(DATA_DIR / "clean_nav_history.csv")
aum = pd.read_csv(DATA_DIR / "clean_aum_by_fund_house.csv")
transactions = pd.read_csv(
    DATA_DIR / "clean_investor_transactions.csv"
)
performance = pd.read_csv(
    DATA_DIR / "clean_scheme_performance.csv"
)

print("Source row counts:")
for name, df in [
    ("dim_fund source", funds),
    ("fact_nav source", nav),
    ("fact_aum source", aum),
    ("fact_transactions source", transactions),
    ("fact_performance source", performance),
]:
    print(f"{name}: {len(df):,}")


# --------------------------------------------------
# 3. Standardise join keys
# --------------------------------------------------
def normalise_code(series):
    return series.astype("string").str.strip()


for df in [funds, nav, transactions, performance]:
    df["amfi_code"] = normalise_code(df["amfi_code"])

# Fund master must have unique AMFI codes.
if funds["amfi_code"].duplicated().any():
    raise ValueError("Duplicate AMFI codes in fund master.")

fund_keys = set(funds["amfi_code"].dropna())

# Check foreign-key references before loading.
for name, df in [
    ("NAV", nav),
    ("Transactions", transactions),
    ("Performance", performance),
]:
    unknown = set(df["amfi_code"].dropna()) - fund_keys

    if unknown:
        raise ValueError(
            f"{name} contains AMFI codes absent from fund master. "
            f"Examples: {list(unknown)[:10]}"
        )

print("\nAll NAV, transaction and performance fund codes match.")


# --------------------------------------------------
# 4. Build date dimension from actual dates
# --------------------------------------------------
nav["date"] = pd.to_datetime(nav["date"], errors="raise")
transactions["transaction_date"] = pd.to_datetime(
    transactions["transaction_date"], errors="raise"
)
aum["date"] = pd.to_datetime(aum["date"], errors="raise")

all_dates = pd.concat(
    [
        nav["date"],
        transactions["transaction_date"],
        aum["date"],
    ],
    ignore_index=True,
).dropna().drop_duplicates().sort_values()

dates = pd.DataFrame({"full_date": all_dates})

dates["date_key"] = dates["full_date"].dt.strftime("%Y%m%d").astype(int)
dates["year"] = dates["full_date"].dt.year
dates["month"] = dates["full_date"].dt.month
dates["quarter"] = dates["full_date"].dt.quarter
dates["month_name"] = dates["full_date"].dt.strftime("%B")
dates["year_month"] = dates["full_date"].dt.strftime("%Y-%m")
dates["full_date"] = dates["full_date"].dt.strftime("%Y-%m-%d")

print("Unique dates in dim_date:", len(dates))


# --------------------------------------------------
# 5. Create a fresh database from schema.sql
# --------------------------------------------------
# Re-running this script recreates the database.
# Close any SQLite viewer before running it again.
if DB_FILE.exists():
    DB_FILE.unlink()

with sqlite3.connect(DB_FILE) as connection:
    connection.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

engine = create_engine(f"sqlite:///{DB_FILE.as_posix()}")

# Enable SQLite foreign-key enforcement for SQLAlchemy connections.
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# --------------------------------------------------
# 6. Load dim_fund
# --------------------------------------------------
fund_cols = [
    "amfi_code", "fund_house", "scheme_name", "category",
    "sub_category", "plan", "launch_date", "benchmark",
    "expense_ratio_pct", "exit_load_pct", "min_sip_amount",
    "min_lumpsum_amount", "fund_manager", "risk_category",
    "sebi_category_code",
]

dim_fund = funds[fund_cols].copy().reset_index(drop=True)
dim_fund.insert(0, "fund_key", range(1, len(dim_fund) + 1))

# Convert missing optional CSV values into SQL NULLs.
dim_fund = dim_fund.astype(object).where(pd.notna(dim_fund), None)

dim_fund.to_sql(
    "dim_fund", engine, if_exists="append", index=False
)

fund_lookup = dict(
    zip(dim_fund["amfi_code"], dim_fund["fund_key"])
)


# --------------------------------------------------
# 7. Load dim_date
# --------------------------------------------------
dates.to_sql(
    "dim_date", engine, if_exists="append", index=False
)

date_lookup = dict(
    zip(dates["full_date"], dates["date_key"])
)


# --------------------------------------------------
# 8. Load fact_nav
# --------------------------------------------------
nav["date_text"] = nav["date"].dt.strftime("%Y-%m-%d")

fact_nav = pd.DataFrame({
    "fund_key": nav["amfi_code"].map(fund_lookup),
    "date_key": nav["date_text"].map(date_lookup),
    "nav": pd.to_numeric(nav["nav"], errors="raise"),
})

if fact_nav[["fund_key", "date_key"]].isna().any().any():
    raise ValueError("Unresolved NAV fund/date keys.")

fact_nav.to_sql(
    "fact_nav", engine, if_exists="append", index=False
)


# --------------------------------------------------
# 9. Load fact_transactions
# --------------------------------------------------
transactions["date_text"] = (
    transactions["transaction_date"].dt.strftime("%Y-%m-%d")
)

transaction_cols = [
    "investor_id", "amfi_code", "date_text",
    "transaction_type", "amount_inr", "state", "city",
    "city_tier", "age_group", "gender", "annual_income_lakh",
    "payment_mode", "kyc_status",
]

fact_transactions = transactions[transaction_cols].copy()

fact_transactions = fact_transactions.rename(columns={
    "date_text": "date_text"
})

fact_transactions.insert(
    0, "date_key",
    fact_transactions["date_text"].map(date_lookup)
)
fact_transactions.insert(
    0, "fund_key",
    fact_transactions["amfi_code"].map(fund_lookup)
)

fact_transactions = fact_transactions.drop(
    columns=["amfi_code", "date_text"]
)

fact_transactions = fact_transactions.rename(columns={
    "date_key": "date_key"
})

fact_transactions = fact_transactions[[
    "investor_id", "fund_key", "date_key",
    "transaction_type", "amount_inr", "state", "city",
    "city_tier", "age_group", "gender", "annual_income_lakh",
    "payment_mode", "kyc_status",
]]

fact_transactions = fact_transactions.astype(object).where(
    pd.notna(fact_transactions), None
)

fact_transactions.to_sql(
    "fact_transactions", engine, if_exists="append", index=False
)


# --------------------------------------------------
# 10. Load fact_performance
# --------------------------------------------------
performance_cols = [
    "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
    "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
    "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
    "aum_crore", "expense_ratio_pct", "morningstar_rating",
    "risk_grade",
]

fact_performance = performance[
    ["amfi_code"] + performance_cols
].copy()

fact_performance.insert(
    0, "fund_key",
    fact_performance["amfi_code"].map(fund_lookup)
)
fact_performance = fact_performance.drop(columns=["amfi_code"])

fact_performance = fact_performance.astype(object).where(
    pd.notna(fact_performance), None
)

fact_performance.to_sql(
    "fact_performance", engine, if_exists="append", index=False
)


# --------------------------------------------------
# 11. Load fact_aum
# --------------------------------------------------
fact_aum = aum.copy()
fact_aum["date_text"] = fact_aum["date"].dt.strftime("%Y-%m-%d")

fact_aum["date_key"] = fact_aum["date_text"].map(date_lookup)

fact_aum = fact_aum[[
    "date_key", "fund_house",
    "aum_lakh_crore", "aum_crore", "num_schemes"
]]

fact_aum = fact_aum.astype(object).where(
    pd.notna(fact_aum), None
)

fact_aum.to_sql(
    "fact_aum", engine, if_exists="append", index=False
)


# --------------------------------------------------
# 12. Verify row counts and foreign keys
# --------------------------------------------------
expected = {
    "dim_fund": len(funds),
    "dim_date": len(dates),
    "fact_nav": len(nav),
    "fact_transactions": len(transactions),
    "fact_performance": len(performance),
    "fact_aum": len(aum),
}

print("\nDatabase verification:")
with engine.connect() as connection:
    for table, expected_count in expected.items():
        actual_count = connection.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        ).scalar_one()

        print(
            f"{table}: {actual_count:,} rows "
            f"(expected {expected_count:,})"
        )

        if actual_count != expected_count:
            raise ValueError(
                f"Row count mismatch for {table}: "
                f"{actual_count} != {expected_count}"
            )

    foreign_key_errors = connection.exec_driver_sql(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if foreign_key_errors:
        raise ValueError(
            f"Foreign-key violations: {foreign_key_errors[:10]}"
        )

    print("Foreign-key check: PASSED")

print("\nDatabase created successfully:")
print(DB_FILE)

engine.dispose()
