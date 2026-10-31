# ⏰ Bonus Challenge B1 — Weekday 8:00 PM Automated Cron Scheduler (+10 Marks)

## 📌 Overview
This module automates mutual fund NAV ingestion and performance metrics calculation on an automated schedule:
- **Frequency:** Every weekday (Monday through Friday) at **20:00 (8:00 PM IST)**.
- **Source Endpoint:** Public AMFI / mfapi.in REST API (`https://api.mfapi.in/mf/{amfi_code}`).
- **Actions:** Fetches closing daily NAVs, appends them to historical tables, recalculates fund risk & performance scorecards, and logs results to `reports/cron_scheduler.log`.

---

## 🚀 Execution & Usage

### 1. Manual Verification / Test Run
To immediately run the ETL cycle once and verify:
```bash
python bonus_challenges/B1_cron_etl_scheduler/cron_scheduler.py --run-now
```

### 2. Standalone Continuous Daemon
To leave the scheduler running as an active background loop:
```bash
python bonus_challenges/B1_cron_etl_scheduler/cron_scheduler.py
```

### 3. Windows Task Scheduler Setup
- **Action:** Start a Program
- **Program/Script:** `cmd.exe`
- **Arguments:** `/c bonus_challenges\B1_cron_etl_scheduler\run_scheduled_fetch.bat`
- **Trigger:** Daily at 8:00 PM, recur every weekday (Mon-Fri).

### 4. Linux / macOS Crontab
Add the following line to `crontab -e`:
```bash
0 20 * * 1-5 cd /path/to/Bluestock-MF-Analytics && python3 bonus_challenges/B1_cron_etl_scheduler/cron_scheduler.py --run-now >> reports/cron_scheduler.log 2>&1
```

---

## 📂 Output Logs
Execution results, timestamps, HTTP status codes, and recalculation status are appended to:
- [`reports/cron_scheduler.log`](file:///reports/cron_scheduler.log)
