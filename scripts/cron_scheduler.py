#!/usr/bin/env python3
"""
Bonus Challenge B1: Scheduled NAV Auto-Fetcher & Incremental ETL
================================================================
Schedules automated fetching of latest NAV data from mfapi.in every weekday at 8:00 PM (20:00 IST).
Updates historical NAV records, generates audit logs, and triggers incremental pipeline refresh.

Usage:
  python scripts/cron_scheduler.py             # Runs daemon scheduler (active polling loop)
  python scripts/cron_scheduler.py --run-now   # Immediately executes scheduled job once for verification

Crontab (Linux/macOS):
  0 20 * * 1-5 /usr/bin/python3 /path/to/Bluestock-MF-Analytics/scripts/cron_scheduler.py --run-now >> /path/to/cron.log 2>&1

Windows Task Scheduler:
  Trigger: Weekly on Mon, Tue, Wed, Thu, Fri at 8:00 PM
  Action: Start Program -> python.exe -> Arguments: scripts/cron_scheduler.py --run-now
"""

import sys
import os
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
import schedule

# Path setup using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "scripts"))

from scripts.live_nav_fetch import main as fetch_live_nav
from scripts.compute_metrics import compute_metrics

LOG_DIR = BASE_DIR / "reports"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "cron_scheduler.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CRON-B1] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("CronScheduler")


def scheduled_nav_etl_job():
    """Daily weekday 8:00 PM job: fetch NAV from mfapi.in and recompute performance metrics."""
    now = datetime.now()
    logger.info("=" * 70)
    logger.info(f"Triggering Weekday Scheduled NAV Fetch & Metrics Update: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Target Source: https://api.mfapi.in/mf/")

    try:
        # Step 1: Ingest live NAVs
        logger.info("Step 1/2: Fetching live NAV feeds...")
        fetch_live_nav()
        logger.info("Live NAV ingestion completed successfully.")

        # Step 2: Compute performance & risk metrics
        logger.info("Step 2/2: Updating fund performance scorecards & risk metrics...")
        compute_metrics()
        logger.info("Metrics calculation completed successfully.")

        logger.info(f"CRON JOB FINISHED: NAV and metrics successfully updated at {datetime.now().strftime('%H:%M:%S')}")
        logger.info("=" * 70)
    except Exception as e:
        logger.exception(f"CRON JOB EXECUTION FAILED: {e}")


def run_scheduler_daemon():
    """Runs the continuous scheduler loop for weekdays at 20:00 (8:00 PM)."""
    logger.info("Initializing Cron Scheduler Daemon for Bluestock MF Analytics...")
    logger.info("Configuring schedule: Monday through Friday at 20:00 (8:00 PM IST)...")

    schedule.every().monday.at("20:00").do(scheduled_nav_etl_job)
    schedule.every().tuesday.at("20:00").do(scheduled_nav_etl_job)
    schedule.every().wednesday.at("20:00").do(scheduled_nav_etl_job)
    schedule.every().thursday.at("20:00").do(scheduled_nav_etl_job)
    schedule.every().friday.at("20:00").do(scheduled_nav_etl_job)

    logger.info("Scheduler active. Waiting for next scheduled trigger time (Ctrl+C to stop)...")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")


def main():
    parser = argparse.ArgumentParser(description="Bluestock MF Cron Scheduler (Bonus B1)")
    parser.add_argument("--run-now", action="store_true", help="Immediately execute the scheduled job once and exit")
    args = parser.parse_args()

    if args.run_now:
        logger.info("Executing immediate manual test run of scheduled NAV ETL job...")
        scheduled_nav_etl_job()
    else:
        run_scheduler_daemon()


if __name__ == "__main__":
    main()
