"""Create or replace the gold.benchmark_reference view in DuckDB.

Run once after any change to the view definition:

    .venv/bin/python -m app.scripts.create_benchmark_view
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from app.query.catalogs import REPO_ROOT

VIEW_SQL_PATH = REPO_ROOT / "etl" / "gold" / "benchmark_reference_view.sql"


def create_view(db_path: str | None = None) -> None:
    load_dotenv()
    resolved = db_path or os.getenv("DB_CONNECTION")
    if not resolved:
        raise ValueError("DB_CONNECTION is not configured")

    path = Path(resolved)
    if not path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {resolved}")

    sql = VIEW_SQL_PATH.read_text(encoding="utf-8")

    con = duckdb.connect(str(path), read_only=False)
    try:
        # The repo-local bootstrap may materialize benchmark_reference as a table
        # before we later switch back to the canonical view definition.
        existing = con.execute(
            """
            SELECT table_type
            FROM information_schema.tables
            WHERE table_schema = 'gold'
              AND table_name = 'benchmark_reference'
            """
        ).fetchone()
        if existing is not None:
            if existing[0] == "VIEW":
                con.execute("DROP VIEW gold.benchmark_reference")
            else:
                con.execute("DROP TABLE gold.benchmark_reference")
        con.execute(sql)
        print(f"Created gold.benchmark_reference view in {resolved}")
        row = con.execute(
            "SELECT COUNT(*) FROM gold.benchmark_reference"
        ).fetchone()
        print(f"View row count: {row[0]:,}")
    finally:
        con.close()


if __name__ == "__main__":
    create_view()
