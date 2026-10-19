
import sqlite3
from pathlib import Path

project_dir = Path(__file__).resolve().parent.parent
db_path = project_dir / "bluestock_mf.db"

if not db_path.exists():
    raise FileNotFoundError(f"Database not found: {db_path}")

connection = sqlite3.connect(db_path)

try:
    print("=" * 60)
    print("EXISTING DATABASE SCHEMA")
    print("=" * 60)

    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    print("\nTABLES:")
    for table in tables:
        print("-", table[0])

    for table_name in ["dim_date", "dim_fund", "fact_nav"]:
        print(f"\nCOLUMNS IN {table_name}:")
        columns = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        for column in columns:
            print(column)

    print("\nFOREIGN KEYS IN fact_nav:")
    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(fact_nav)"
    ).fetchall()

    for foreign_key in foreign_keys:
        print(foreign_key)

    print("\nDATABASE INSPECTION COMPLETED.")

finally:
    connection.close()
