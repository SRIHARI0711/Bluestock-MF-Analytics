#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Unified End-to-End ETL Pipeline
==================================================================
Runs without manual intervention, implements comprehensive error handling,
standardizes file paths using pathlib.Path, and loads data into SQLite.

Pipeline Stages:
1. Data Ingestion & Raw Data Validation
2. Data Cleaning & Transformation (including calendar reindexing & ffill for NAV)
3. Performance & Quantitative Risk Metrics Computation
4. SQLite Database Schema Migration & Loading (data/db/bluestock_mf.db)
5. Integrity Verification & SQL Query Execution
"""

import sys
import os
import shutil
import sqlite3
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# Setup Paths using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "scripts"))
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "db"
DB_FILE = DB_DIR / "bluestock_mf.db"
ROOT_DB_FILE = BASE_DIR / "bluestock_mf.db"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"
QUERIES_FILE = BASE_DIR / "sql" / "queries.sql"
REPORTS_DIR = BASE_DIR / "reports"
SQL_RESULTS_DIR = REPORTS_DIR / "sql_results"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
SQL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "etl_pipeline.log", mode="w", encoding="utf-8")
    ]
)
logger = logging.getLogger("ETL_Pipeline")


def normalize_code(series):
    """Normalize AMFI codes to clean integer-like strings."""
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def iso_dates(series):
    """Convert dates to standardized ISO YYYY-MM-DD format."""
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")


def stage_1_validate_raw_data():
    """Verify that all expected raw CSV files exist and are non-empty."""
    logger.info("=== STAGE 1: RAW DATA INGESTION & VALIDATION ===")
    required_raw = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "07_scheme_performance.csv",
        "08_investor_transactions.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    missing = []
    for f in required_raw:
        path = RAW_DIR / f
        if not path.exists() or path.stat().st_size == 0:
            missing.append(f)
    if missing:
        raise FileNotFoundError(f"Missing or empty raw data files in {RAW_DIR}: {missing}")
    logger.info("All 10 required raw datasets validated successfully.")


def stage_2_clean_and_transform_data():
    """Clean, standardize, forward-fill missing NAVs across calendar days, and save to processed/."""
    logger.info("=== STAGE 2: DATA CLEANING & TRANSFORMATION ===")

    # 1. Fund Master
    df_funds = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    df_funds["amfi_code"] = normalize_code(df_funds["amfi_code"])
    df_funds["launch_date"] = iso_dates(df_funds["launch_date"])
    df_funds["expense_ratio_pct"] = pd.to_numeric(df_funds.get("expense_ratio_pct"), errors="coerce").fillna(1.25)
    df_funds["exit_load_pct"] = pd.to_numeric(df_funds.get("exit_load_pct"), errors="coerce").fillna(1.0)
    df_funds["min_sip_amount"] = pd.to_numeric(df_funds.get("min_sip_amount"), errors="coerce").fillna(500.0)
    df_funds["min_lumpsum_amount"] = pd.to_numeric(df_funds.get("min_lumpsum_amount"), errors="coerce").fillna(1000.0)
    df_funds.drop_duplicates(subset=["amfi_code"], inplace=True)
    df_funds.to_csv(PROCESSED_DIR / "clean_fund_master.csv", index=False)
    logger.info(f"Processed clean_fund_master.csv: {len(df_funds)} funds")

    # 2. NAV History
    df_nav = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    df_nav["amfi_code"] = normalize_code(df_nav["amfi_code"])
    df_nav["date"] = iso_dates(df_nav["date"])
    df_nav["nav"] = pd.to_numeric(df_nav["nav"], errors="coerce")
    df_nav = df_nav.dropna(subset=["amfi_code", "date", "nav"])
    df_nav = df_nav[df_nav["nav"] > 0]
    df_nav.drop_duplicates(subset=["amfi_code", "date"], keep="last", inplace=True)
    df_nav.sort_values(["amfi_code", "date"], inplace=True)
    df_nav.to_csv(PROCESSED_DIR / "clean_nav_history.csv", index=False)
    logger.info(f"Processed clean_nav_history.csv: {len(df_nav):,} records")

    # 3. Create Daily NAV Calendar (Reindexing & forward-filling across weekends/holidays)
    logger.info("Generating daily NAV calendar with forward-fill for trading breaks...")
    daily_frames = []
    nav_subset = df_nav[["amfi_code", "date", "nav"]].copy()
    nav_subset["dt"] = pd.to_datetime(nav_subset["date"])
    for amfi_code, grp in nav_subset.groupby("amfi_code"):
        grp = grp.sort_values("dt").set_index("dt")
        full_calendar = pd.date_range(start=grp.index.min(), end=grp.index.max(), freq="D")
        actual_dates = full_calendar.isin(grp.index)
        expanded = grp[["nav"]].reindex(full_calendar)
        expanded["nav"] = expanded["nav"].ffill()
        expanded["amfi_code"] = amfi_code
        expanded["is_actual_nav"] = actual_dates
        expanded.index.name = "date"
        daily_frames.append(expanded.reset_index())

    df_daily_calendar = pd.concat(daily_frames, ignore_index=True)
    df_daily_calendar["date"] = df_daily_calendar["date"].dt.strftime("%Y-%m-%d")
    df_daily_calendar.to_csv(PROCESSED_DIR / "daily_nav_calendar.csv", index=False)
    logger.info(f"Processed daily_nav_calendar.csv: {len(df_daily_calendar):,} total daily calendar records")

    # 4. Investor Transactions
    df_tx = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    df_tx["amfi_code"] = normalize_code(df_tx["amfi_code"])
    df_tx["transaction_date"] = iso_dates(df_tx["transaction_date"])
    df_tx["amount_inr"] = pd.to_numeric(df_tx["amount_inr"], errors="coerce")
    df_tx = df_tx.dropna(subset=["investor_id", "amfi_code", "transaction_date", "amount_inr"])
    df_tx.drop_duplicates(inplace=True)
    df_tx.to_csv(PROCESSED_DIR / "clean_investor_transactions.csv", index=False)
    logger.info(f"Processed clean_investor_transactions.csv: {len(df_tx):,} records")

    # 5. Scheme Performance
    df_perf = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    df_perf["amfi_code"] = normalize_code(df_perf["amfi_code"])
    df_perf.drop_duplicates(subset=["amfi_code"], keep="first", inplace=True)
    df_perf.to_csv(PROCESSED_DIR / "clean_scheme_performance.csv", index=False)
    logger.info(f"Processed clean_scheme_performance.csv: {len(df_perf)} schemes")

    # 6. AUM by Fund House
    df_aum = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
    df_aum["date"] = iso_dates(df_aum["date"])
    df_aum["aum_lakh_crore"] = pd.to_numeric(df_aum["aum_lakh_crore"], errors="coerce")
    df_aum["aum_crore"] = df_aum["aum_lakh_crore"] * 100000.0
    df_aum["num_schemes"] = pd.to_numeric(df_aum["num_schemes"], errors="coerce").fillna(0).astype(int)
    df_aum.to_csv(PROCESSED_DIR / "clean_aum_by_fund_house.csv", index=False)
    logger.info(f"Processed clean_aum_by_fund_house.csv: {len(df_aum)} records")

    # 7. Supplementary datasets
    sip = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
    sip.to_csv(PROCESSED_DIR / "clean_monthly_sip_inflows.csv", index=False)

    cat = pd.read_csv(RAW_DIR / "05_category_inflows.csv")
    cat.to_csv(PROCESSED_DIR / "clean_category_inflows.csv", index=False)

    folios = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")
    folios.to_csv(PROCESSED_DIR / "clean_industry_folio_count.csv", index=False)

    holdings = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
    holdings["amfi_code"] = normalize_code(holdings["amfi_code"])
    holdings["portfolio_date"] = iso_dates(holdings["portfolio_date"])
    holdings.to_csv(PROCESSED_DIR / "clean_portfolio_holdings.csv", index=False)

    bench = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")
    bench["date"] = iso_dates(bench["date"])
    bench.to_csv(PROCESSED_DIR / "clean_benchmark_indices.csv", index=False)
    logger.info("All supplementary datasets standardized and saved to processed/.")


def stage_3_compute_metrics():
    """Call the quantitative performance and risk metrics engine."""
    logger.info("=== STAGE 3: COMPUTE QUANTITATIVE METRICS ===")
    from scripts.compute_metrics import compute_metrics
    compute_metrics()
    logger.info("Performance, VaR/CVaR, and Alpha/Beta metrics generated.")


def stage_4_build_sqlite_database():
    """Build SQLite database according to relational schema."""
    logger.info("=== STAGE 4: BUILD SQLITE DATABASE ===")
    from scripts.load_sqlite_db import main as load_db
    load_db()

    # Load daily continuous calendar table if present
    daily_cal_script = BASE_DIR / "scripts" / "load_daily_nav_calendar.py"
    if daily_cal_script.exists():
        try:
            import subprocess
            subprocess.run([sys.executable, str(daily_cal_script)], check=True, capture_output=True)
            logger.info("Daily NAV calendar table successfully loaded.")
        except Exception as err:
            logger.warning(f"Note on load_daily_nav_calendar: {err}")

    # Sync to data/db/bluestock_mf.db
    if ROOT_DB_FILE.exists():
        shutil.copy2(ROOT_DB_FILE, DB_FILE)
        logger.info(f"Database synchronized to {DB_FILE} and {ROOT_DB_FILE}")
    elif DB_FILE.exists():
        shutil.copy2(DB_FILE, ROOT_DB_FILE)
        logger.info(f"Database synchronized to {ROOT_DB_FILE}")


def stage_5_verify_and_run_queries():
    """Verify integrity and execute all analytical queries in sql/queries.sql."""
    logger.info("=== STAGE 5: INTEGRITY CHECKS & SQL QUERY EXECUTION ===")
    from scripts.run_sql_queries import main as run_queries
    run_queries()
    logger.info("All analytical SQL queries executed and saved to reports/sql_results/.")


def main():
    logger.info("Starting Bluestock Mutual Fund Analytics ETL Pipeline...")
    try:
        stage_1_validate_raw_data()
        stage_2_clean_and_transform_data()
        stage_3_compute_metrics()
        stage_4_build_sqlite_database()
        stage_5_verify_and_run_queries()
        logger.info("======================================================================")
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY WITH ZERO MANUAL STEPS!")
        logger.info("======================================================================")
    except Exception as e:
        logger.exception(f"ETL PIPELINE FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
