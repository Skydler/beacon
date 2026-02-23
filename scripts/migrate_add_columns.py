"""One-time migration: add reason and source_name columns to seen_articles table.

Run once against the production database before deploying the frontend:

    uv run python scripts/migrate_add_columns.py
    uv run python scripts/migrate_add_columns.py --db-path /custom/path/seen_articles.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def migrate(db_path: str) -> None:
    path = Path(db_path)
    if not path.exists():
        print(f"Error: database not found at {db_path}")
        sys.exit(1)

    columns_to_add = [
        ("reason", "TEXT"),
        ("source_name", "TEXT"),
    ]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Inspect existing columns
        cursor.execute("PRAGMA table_info(seen_articles)")
        existing = {row[1] for row in cursor.fetchall()}

        for col_name, col_type in columns_to_add:
            if col_name in existing:
                print(f"  Column '{col_name}' already exists — skipping.")
            else:
                cursor.execute(f"ALTER TABLE seen_articles ADD COLUMN {col_name} {col_type}")
                print(f"  Added column '{col_name} {col_type}'.")

        conn.commit()

    print("Migration complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate seen_articles schema")
    parser.add_argument(
        "--db-path",
        default="data/seen_articles.db",
        help="Path to the SQLite database file (default: data/seen_articles.db)",
    )
    args = parser.parse_args()
    migrate(args.db_path)


if __name__ == "__main__":
    main()
