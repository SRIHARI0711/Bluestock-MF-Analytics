from pathlib import Path
import os
import sqlite3

import pandas as pd
from sqlalchemy import create_engine

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
SCHEMA_FILE = PROJECT_DIR / "sql" / "schema.sql"
DB_FILE = PROJECT_DIR / "bluestock_mf.db"
TEMP_DB_FILE = PROJECT_DIR / "bluestock_mf_build.tmp.db"

DATASETS = {
    "clean_fund_master.csv": "dim_fund",
    "clean_nav_history.csv": "fact_nav",
    "clean_investor_transactions.csv": "fact_transactions",
    "clean_scheme_performance.csv": "fact_performance",
    "clean_aum_by_fund_house.csv": "fact_aum",
    "clean_monthly_sip_inflows.csv": "fact_sip_inflows",
    "clean_category_inflows.csv": "fact_category_inflows",
    "clean_industry_folio_count.csv": "fact_folio_count",
    "clean_portfolio_holdings.csv": "fact_portfolio_holdings",
    "clean_benchmark_indices.csv": "fact_benchmark_indices",
}


def normalize_code(series):
    """Normalize AMFI codes whether pandas reads them as integers or strings."""
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def iso_dates(series):
    """Convert parseable dates to ISO YYYY-MM-DD strings."""
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d")


def main():
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_FILE}")

    # Read every CSV first; the current database is not touched if an input is missing.
    source = {}
    for filename, table in DATASETS.items():
        path = DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing cleaned CSV: {path}")
        source[table] = pd.read_csv(path)

    # Build in a separate temporary database so the current DB survives failures.
    if TEMP_DB_FILE.exists():
        TEMP_DB_FILE.unlink()

    with sqlite3.connect(TEMP_DB_FILE) as raw_conn:
        raw_conn.execute("PRAGMA foreign_keys = ON")
        raw_conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

    engine = create_engine(f"sqlite:///{TEMP_DB_FILE.as_posix()}")

    try:
        with engine.begin() as conn:
            # 1) Dimension: fund master. SQLite generates fund_key.
            funds = source["dim_fund"].copy()
            funds["amfi_code"] = normalize_code(funds["amfi_code"])
            funds.to_sql("dim_fund", conn, if_exists="append", index=False)

            # Build a complete date dimension from all datasets with date fields.
            date_values = set()
            date_columns = {
                "fact_nav": "date",
                "fact_transactions": "transaction_date",
                "fact_aum": "date",
                "fact_sip_inflows": "month",
                "fact_category_inflows": "month",
                "fact_folio_count": "month",
                "fact_portfolio_holdings": "portfolio_date",
                "fact_benchmark_indices": "date",
            }
            for table, column in date_columns.items():
                df = source[table]
                if column not in df.columns:
                    continue
                parsed = pd.to_datetime(df[column], errors="coerce")
                date_values.update(parsed.dropna().dt.strftime("%Y-%m-%d"))

            dates = pd.DataFrame({"full_date": sorted(date_values)})
            parsed_dates = pd.to_datetime(dates["full_date"])
            dates["year"] = parsed_dates.dt.year
            dates["month"] = parsed_dates.dt.month
            dates["quarter"] = parsed_dates.dt.quarter
            dates["month_name"] = parsed_dates.dt.month_name()
            dates["year_month"] = parsed_dates.dt.strftime("%Y-%m")
            dates.to_sql("dim_date", conn, if_exists="append", index=False)

            fund_keys = pd.read_sql(
                "SELECT fund_key, amfi_code FROM dim_fund", conn
            )
            fund_keys["amfi_code"] = normalize_code(fund_keys["amfi_code"])
            date_keys = pd.read_sql(
                "SELECT date_key, full_date FROM dim_date", conn
            )

            # 2) NAV: map AMFI code and date to surrogate keys.
            nav = source["fact_nav"].copy()
            nav["amfi_code"] = normalize_code(nav["amfi_code"])
            nav["date"] = iso_dates(nav["date"])
            nav = nav.merge(fund_keys, on="amfi_code", how="left", validate="many_to_one")
            nav = nav.merge(
                date_keys, left_on="date", right_on="full_date",
                how="left", validate="many_to_one"
            )
            if nav["fund_key"].isna().any() or nav["date_key"].isna().any():
                raise ValueError("NAV data has an unmatched fund code or date.")
            nav[["fund_key", "date_key", "nav"]].to_sql(
                "fact_nav", conn, if_exists="append", index=False
            )

            # 3) Transactions: map AMFI code and transaction date.
            tx = source["fact_transactions"].copy()
            tx["amfi_code"] = normalize_code(tx["amfi_code"])
            tx["transaction_date"] = iso_dates(tx["transaction_date"])
            tx = tx.merge(fund_keys, on="amfi_code", how="left", validate="many_to_one")
            tx = tx.merge(
                date_keys, left_on="transaction_date", right_on="full_date",
                how="left", validate="many_to_one"
            )
            if tx["fund_key"].isna().any() or tx["date_key"].isna().any():
                raise ValueError("Transactions have an unmatched fund code or date.")
            tx_out = tx[[
                "investor_id", "fund_key", "date_key", "transaction_type",
                "amount_inr", "state", "city", "city_tier", "age_group",
                "gender", "annual_income_lakh", "payment_mode", "kyc_status"
            ]]
            tx_out.to_sql("fact_transactions", conn, if_exists="append", index=False)

            # 4) Performance: one row per fund, mapped to fund_key.
            perf = source["fact_performance"].copy()
            perf["amfi_code"] = normalize_code(perf["amfi_code"])
            perf = perf.merge(fund_keys, on="amfi_code", how="left", validate="one_to_one")
            if perf["fund_key"].isna().any():
                raise ValueError("Performance data has an unmatched fund code.")
            perf_columns = [
                "fund_key", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
                "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
                "aum_crore", "expense_ratio_pct", "morningstar_rating", "risk_grade"
            ]
            perf[perf_columns].to_sql(
                "fact_performance", conn, if_exists="append", index=False
            )

            # 5) Fund-house AUM: map date to date_key.
            aum = source["fact_aum"].copy()
            aum["date"] = iso_dates(aum["date"])
            aum = aum.merge(
                date_keys, left_on="date", right_on="full_date",
                how="left", validate="many_to_one"
            )
            if aum["date_key"].isna().any():
                raise ValueError("AUM data has an unmatched date.")
            aum[[
                "date_key", "fund_house", "aum_lakh_crore",
                "aum_crore", "num_schemes"
            ]].to_sql("fact_aum", conn, if_exists="append", index=False)

            # 6-10) Supplementary datasets retain their source columns.
            sip = source["fact_sip_inflows"].copy()
            sip["month"] = sip["month"].astype(str)
            sip.to_sql("fact_sip_inflows", conn, if_exists="append", index=False)

            category = source["fact_category_inflows"].copy()
            category["month"] = category["month"].astype(str)
            category.to_sql(
                "fact_category_inflows", conn, if_exists="append", index=False
            )

            folios = source["fact_folio_count"].copy()
            folios["month"] = folios["month"].astype(str)
            folios.to_sql("fact_folio_count", conn, if_exists="append", index=False)

            holdings = source["fact_portfolio_holdings"].copy()
            holdings["amfi_code"] = normalize_code(holdings["amfi_code"])
            holdings["portfolio_date"] = iso_dates(holdings["portfolio_date"])
            holdings.to_sql(
                "fact_portfolio_holdings", conn, if_exists="append", index=False
            )

            benchmark = source["fact_benchmark_indices"].copy()
            benchmark["date"] = iso_dates(benchmark["date"])
            benchmark.to_sql(
                "fact_benchmark_indices", conn, if_exists="append", index=False
            )

        # Verify counts and foreign keys on the temporary database.
        with sqlite3.connect(TEMP_DB_FILE) as check_conn:
            check_conn.execute("PRAGMA foreign_keys = ON")
            violations = check_conn.execute("PRAGMA foreign_key_check").fetchall()

            print("\nDATABASE ROW COUNTS")
            count_errors = []
            for table, df in source.items():
                actual = check_conn.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
                expected = len(df)
                print(f"{table}: expected {expected:,}, actual {actual:,}")
                if actual != expected:
                    count_errors.append((table, expected, actual))

            if violations:
                raise RuntimeError(f"Foreign-key violations: {violations}")
            if count_errors:
                raise RuntimeError(f"Row-count mismatches: {count_errors}")

            print("Foreign key violations: []")
            print("All ten dataset row counts match.")

        engine.dispose()
        # Replace the original database only after successful loading and checks.
        os.replace(TEMP_DB_FILE, DB_FILE)
        print(f"\nDatabase successfully rebuilt: {DB_FILE}")

    except Exception:
        engine.dispose()
        if TEMP_DB_FILE.exists():
            TEMP_DB_FILE.unlink()
        raise


if __name__ == "__main__":
    main()
