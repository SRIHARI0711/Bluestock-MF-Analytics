
from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "bluestock_mf.db"
CSV_FILE = PROJECT_DIR / "data" / "processed" / "daily_nav_calendar.csv"

EXPECTED_ROWS = 64320
EXPECTED_ACTUAL = 46000
EXPECTED_CARRIED = 18320

if not DB_FILE.exists():
    raise FileNotFoundError(f"Database not found: {DB_FILE}")

if not CSV_FILE.exists():
    raise FileNotFoundError(f"Calendar CSV not found: {CSV_FILE}")

df = pd.read_csv(CSV_FILE)
df["date"] = pd.to_datetime(df["date"], errors="raise").dt.strftime("%Y-%m-%d")
df["nav"] = pd.to_numeric(df["nav"], errors="raise")
df["is_actual_nav"] = df["is_actual_nav"].astype(bool)

if len(df) != EXPECTED_ROWS:
    raise ValueError(f"Expected {EXPECTED_ROWS} CSV rows; found {len(df)}.")

if df.duplicated(["amfi_code", "date"]).any():
    raise ValueError("Duplicate fund/date pairs exist in the CSV.")

if df["nav"].isna().any() or (df["nav"] <= 0).any():
    raise ValueError("CSV contains missing or non-positive NAV values.")

if int(df["is_actual_nav"].sum()) != EXPECTED_ACTUAL:
    raise ValueError("Actual NAV observation count does not match.")

if int((~df["is_actual_nav"]).sum()) != EXPECTED_CARRIED:
    raise ValueError("Carried-forward NAV count does not match.")

connection = sqlite3.connect(DB_FILE)

try:
    connection.execute("PRAGMA foreign_keys = ON")

    # Confirm all fund codes exist before inserting.
    fund_codes = set(
        row[0] for row in connection.execute(
            "SELECT amfi_code FROM dim_fund"
        )
    )

    if not set(df["amfi_code"].astype(str)).issubset(fund_codes):
        raise ValueError("Some calendar fund codes are missing from dim_fund.")

    with connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS fact_nav_daily_calendar (
                calendar_nav_key INTEGER PRIMARY KEY,
                fund_key INTEGER NOT NULL,
                date_key INTEGER NOT NULL,
                nav REAL NOT NULL CHECK (nav > 0),
                is_actual_nav INTEGER NOT NULL
                    CHECK (is_actual_nav IN (0, 1)),
                UNIQUE (fund_key, date_key),
                FOREIGN KEY (fund_key) REFERENCES dim_fund(fund_key),
                FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
            )
        """)

        # Add any calendar dates absent from the existing date dimension.
        dates = pd.to_datetime(df["date"])
        date_records = [
            (
                date.strftime("%Y-%m-%d"),
                date.year,
                date.month,
                (date.month - 1) // 3 + 1,
                date.strftime("%B"),
                date.strftime("%Y-%m"),
            )
            for date in dates.drop_duplicates().sort_values()
        ]

        connection.executemany("""
            INSERT OR IGNORE INTO dim_date
            (full_date, year, month, quarter, month_name, year_month)
            VALUES (?, ?, ?, ?, ?, ?)
        """, date_records)

        # If this table was previously loaded, replace only its contents.
        connection.execute("DELETE FROM fact_nav_daily_calendar")

        fund_key_map = dict(
            connection.execute(
                "SELECT amfi_code, fund_key FROM dim_fund"
            ).fetchall()
        )
        date_key_map = dict(
            connection.execute(
                "SELECT full_date, date_key FROM dim_date"
            ).fetchall()
        )

        records = [
            (
                fund_key_map[str(row.amfi_code)],
                date_key_map[row.date],
                float(row.nav),
                int(row.is_actual_nav),
            )
            for row in df.itertuples(index=False)
        ]

        connection.executemany("""
            INSERT INTO fact_nav_daily_calendar
            (fund_key, date_key, nav, is_actual_nav)
            VALUES (?, ?, ?, ?)
        """, records)

        actual_rows = connection.execute(
            "SELECT COUNT(*) FROM fact_nav_daily_calendar"
        ).fetchone()[0]

        if actual_rows != EXPECTED_ROWS:
            raise ValueError(
                f"Database row count mismatch: {actual_rows}"
            )

        actual_count, carried_count = connection.execute("""
            SELECT
                SUM(is_actual_nav),
                SUM(CASE WHEN is_actual_nav = 0 THEN 1 ELSE 0 END)
            FROM fact_nav_daily_calendar
        """).fetchone()

        if actual_count != EXPECTED_ACTUAL or carried_count != EXPECTED_CARRIED:
            raise ValueError("Database actual/carried-forward counts mismatch.")

        fk_violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if fk_violations:
            raise ValueError(f"Foreign-key violations: {fk_violations[:10]}")

    print("Daily NAV calendar loaded and validated.")
    print("Rows:", actual_rows)
    print("Actual NAV observations:", actual_count)
    print("Carried-forward values:", carried_count)
    print("Foreign-key violations:", fk_violations)

    original_nav_count = connection.execute(
        "SELECT COUNT(*) FROM fact_nav"
    ).fetchone()[0]
    print("Original fact_nav rows preserved:", original_nav_count)

finally:
    connection.close()
