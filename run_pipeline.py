#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Master Pipeline Execution Orchestrator
========================================================================
Central automated controller for the Bluestock Mutual Fund Analytics Capstone.
Sequentially executes data ingestion, transformation, quantitative modeling,
database schema population, advanced analytics, and executive deliverable generation.

Usage:
    python run_pipeline.py                 # Runs complete end-to-end pipeline
    python run_pipeline.py --all           # Runs complete end-to-end pipeline
    python run_pipeline.py --etl           # Executes ETL & database loading only
    python run_pipeline.py --analytics     # Computes quantitative metrics & Monte Carlo
    python run_pipeline.py --deliverables  # Generates Final_Report.pdf & Presentation.pptx
    python run_pipeline.py --verify        # Runs database and data sanity verification

Deliverables Managed:
    - Final_Report.pdf (19-page institutional research PDF)
    - Bluestock_MF_Presentation.pptx (12-slide executive deck)
    - bluestock_mf.db (SQLite production relational star schema)
    - reports/ & data/processed/ analytical tables
"""

import sys
import os
import argparse
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Setup project directories
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
DB_FILE = BASE_DIR / "bluestock_mf.db"

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "etl_pipeline.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("MasterPipeline")


def run_script(script_name: str, description: str) -> bool:
    """
    Executes a Python script in a subprocess using the current Python interpreter.
    
    Parameters:
        script_name (str): Relative filename of the script inside scripts/ or root.
        description (str): Human-readable task description.
        
    Returns:
        bool: True if execution succeeded, False otherwise.
    """
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        script_path = BASE_DIR / script_name

    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    logger.info(f"--> [RUNNING] {description} ({script_name})...")
    start_time = datetime.now()

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=True
        )
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[SUCCESS] {description} completed in {duration:.2f}s")
        if result.stdout.strip():
            # Log first 3 lines of output if relevant
            preview = "\n".join(result.stdout.strip().splitlines()[-3:])
            logger.debug(f"Output preview:\n{preview}")
        return True
    except subprocess.CalledProcessError as exc:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"[FAILED] {description} failed after {duration:.2f}s (Exit code {exc.returncode})")
        if exc.stderr:
            logger.error(f"Error output:\n{exc.stderr.strip()[:500]}")
        return False


def run_etl():
    """Executes Stage 1-4: Raw data ingestion, cleaning, metrics, and SQLite loading."""
    logger.info("=" * 75)
    logger.info("STAGE 1 & 2: ETL PIPELINE & DATABASE LOADING")
    logger.info("=" * 75)
    success = run_script("etl_pipeline.py", "End-to-End ETL & Database Schema Migration")
    if not success:
        logger.error("ETL pipeline encountered errors. Please check etl_pipeline.log.")
        return False
    return True


def run_advanced_analytics():
    """Executes Stage 5: Advanced tail-risk modeling, Markowitz Frontier, and Monte Carlo."""
    logger.info("=" * 75)
    logger.info("STAGE 3: ADVANCED QUANTITATIVE ANALYTICS & SIMULATIONS")
    logger.info("=" * 75)
    s1 = run_script("monte_carlo_and_frontier.py", "Markowitz Efficient Frontier & Monte Carlo Simulations")
    s2 = run_script("generate_var_cvar_report.py", "Value at Risk (VaR) & Conditional VaR Analysis")
    return s1 and s2


def run_deliverables():
    """Executes Stage 6: Building Final_Report.pdf and Bluestock_MF_Presentation.pptx."""
    logger.info("=" * 75)
    logger.info("STAGE 4: EXECUTIVE DELIVERABLES GENERATION")
    logger.info("=" * 75)
    s1 = run_script("generate_final_report_pdf.py", "Comprehensive 19-Page PDF Executive Report")
    s2 = run_script("generate_presentation_pptx.py", "12-Slide Executive Presentation Deck (PPTX)")
    return s1 and s2


def run_verification():
    """Executes database integrity and query verification."""
    logger.info("=" * 75)
    logger.info("STAGE 5: SYSTEM INTEGRITY & DATABASE VERIFICATION")
    logger.info("=" * 75)
    return run_script("verify_database.py", "SQLite Database Integrity & 10 Analytical Queries")


def main():
    """Parses CLI arguments and orchestrates the requested pipeline tasks."""
    parser = argparse.ArgumentParser(
        description="Bluestock Mutual Fund Analytics — Master Pipeline Execution Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_pipeline.py --all
    python run_pipeline.py --etl
    python run_pipeline.py --analytics
    python run_pipeline.py --deliverables
    python run_pipeline.py --verify
        """
    )
    parser.add_argument("--all", action="store_true", help="Execute complete end-to-end pipeline (Default)")
    parser.add_argument("--etl", action="store_true", help="Run ETL and load SQLite database only")
    parser.add_argument("--analytics", action="store_true", help="Run quantitative metrics & simulations only")
    parser.add_argument("--deliverables", action="store_true", help="Generate PDF report and presentation deck only")
    parser.add_argument("--verify", action="store_true", help="Run database verification and sample queries only")

    args = parser.parse_args()

    # Default to --all if no specific flags provided
    if not (args.etl or args.analytics or args.deliverables or args.verify):
        args.all = True

    overall_start = datetime.now()
    logger.info("###########################################################################")
    logger.info("     BLUESTOCK MUTUAL FUND ANALYTICS — MASTER PIPELINE ORCHESTRATION       ")
    logger.info(f"     Execution Started: {overall_start.strftime('%Y-%m-%d %H:%M:%S')}      ")
    logger.info("###########################################################################")

    success = True

    if args.all or args.etl:
        if not run_etl():
            success = False

    if args.all or args.analytics:
        if not run_advanced_analytics():
            success = False

    if args.all or args.deliverables:
        if not run_deliverables():
            success = False

    if args.all or args.verify:
        if not run_verification():
            success = False

    total_duration = (datetime.now() - overall_start).total_seconds()
    logger.info("###########################################################################")
    if success:
        logger.info(f"[PIPELINE COMPLETE] All tasks completed successfully in {total_duration:.2f}s!")
        logger.info("Verified Deliverables:")
        logger.info(f"  • Final Report (PDF):        {BASE_DIR / 'Final_Report.pdf'}")
        logger.info(f"  • Presentation (PPTX):       {BASE_DIR / 'Bluestock_MF_Presentation.pptx'}")
        logger.info(f"  • SQLite Database:           {BASE_DIR / 'bluestock_mf.db'}")
        logger.info(f"  • Streamlit Web Dashboard:   {BASE_DIR / 'dashboard' / 'streamlit_app.py'}")
    else:
        logger.warning(f"[PIPELINE WARNING] One or more tasks encountered issues. Total time: {total_duration:.2f}s")
    logger.info("###########################################################################")


if __name__ == "__main__":
    main()
