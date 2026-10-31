@echo off
REM Bluestock MF Analytics - Windows Task Scheduler Batch Launcher (Bonus B1)
REM Runs every weekday at 8:00 PM (20:00)
cd /d "%~dp0..\.."
python bonus_challenges\B1_cron_etl_scheduler\cron_scheduler.py --run-now >> reports\cron_scheduler.log 2>&1
