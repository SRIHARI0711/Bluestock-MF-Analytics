
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "bluestock_mf.db"

with sqlite3.connect(db_path) as conn:
    print("Integrity:", conn.execute("PRAGMA integrity_check").fetchone()[0])

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    print("\nTables:")
    for (name,) in tables:
        print("-", name)

    print("\nRow counts:")
    expected = {
        "dim_fund": 40,
        "fact_nav": 46000,
        "fact_transactions": 32778,
        "fact_performance": 40,
        "fact_aum": 90,
        "fact_sip_inflows": 48,
        "fact_category_inflows": 144,
        "fact_folio_count": 21,
        "fact_portfolio_holdings": 322,
        "fact_benchmark_indices": 8050,
    }

    for table, count in expected.items():
        actual = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]
        status = "PASS" if actual == count else "FAIL"
        print(f"{table}: {actual:,} / {count:,} expected — {status}")

    print("\nForeign key violations:",
          conn.execute("PRAGMA foreign_key_check").fetchall())
