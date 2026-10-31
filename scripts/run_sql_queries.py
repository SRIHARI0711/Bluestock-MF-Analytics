#!/usr/bin/env python3
"""
Execute analytical SQL queries against the Bluestock SQLite database.
Exports results for queries 1 through 10 as individual CSV reports.
"""

from pathlib import Path
import re
import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "bluestock_mf.db"
SQL_FILE = PROJECT_DIR / "sql" / "queries.sql"
OUTPUT_DIR = PROJECT_DIR / "reports" / "sql_results"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    if not SQL_FILE.exists():
        raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")

    sql_text = SQL_FILE.read_text(encoding="utf-8")
    pattern = r"(?im)^\s*--\s*Query\s+(\d+)\s*:\s*.*$"
    parts = re.split(pattern, sql_text)

    queries = []
    for i in range(1, len(parts), 2):
        query_number = int(parts[i])
        query_text = parts[i + 1].strip()

        # Remove comment-only lines
        lines = [
            line for line in query_text.splitlines()
            if not line.strip().startswith("--")
        ]
        query_text = "\n".join(lines).strip()
        query_text = query_text.rstrip().rstrip(";").strip()

        if query_text:
            queries.append((query_number, query_text))

    print(f"Successfully parsed {len(queries)} SQL queries.")

    engine = create_engine(f"sqlite:///{DB_FILE.as_posix()}")
    try:
        with engine.connect() as connection:
            print("\n" + "=" * 65)
            print("BLUESTOCK MUTUAL FUND — ANALYTICAL SQL RESULTS")
            print("=" * 65)

            for number, query in queries:
                print(f"\n{'-' * 65}")
                print(f"QUERY {number}")
                print("-" * 65)

                result_df = pd.read_sql_query(text(query), connection)
                print("Rows returned:", len(result_df))
                print(result_df.head(10).to_string(index=False))

                output_file = OUTPUT_DIR / f"query_{number:02d}_results.csv"
                result_df.to_csv(output_file, index=False)
                print("Saved:", output_file)

        print("\nAll 10 queries executed successfully.")
        print("Results directory:", OUTPUT_DIR)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
