#!/usr/bin/env python3
"""Apply SQL migration files to a PostgreSQL database.

This small helper is intended for CI/test runs where a DATABASE_URL is available.
It executes SQL files in order and exits non‑zero on failure.

Usage:
  DATABASE_URL=postgres://... python scripts/apply_migrations.py --files infra/postgres/init-auth.sql infra/postgres/init-orders.sql

The script uses `psycopg` (psycopg3). If it's not installed the script will print an instruction.
"""
from __future__ import annotations

import argparse
import os
import sys


def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def apply_file(conn, path: str) -> None:
    print(f"Applying SQL: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        sql = fh.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply SQL files to a PostgreSQL DB")
    parser.add_argument("--database-url", help="Postgres DSN (or set DATABASE_URL env)")
    parser.add_argument("--files", nargs="+", help="SQL files to apply", required=True)
    args = parser.parse_args(argv)

    database_url = args.database_url or os.getenv("DATABASE_URL")
    if not database_url:
        fail("DATABASE_URL must be provided via --database-url or the DATABASE_URL env var", 2)

    try:
        import psycopg
    except Exception:
        fail("psycopg (psycopg3) is required. Install with: pip install 'psycopg[binary]'")

    try:
        conn = psycopg.connect(database_url)
    except Exception as exc:  # pragma: no cover - environment dependent
        fail(f"Failed to connect to database: {exc}", 3)

    try:
        for p in args.files:
            if not os.path.exists(p):
                fail(f"SQL file not found: {p}", 4)
            apply_file(conn, p)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    print("Migrations applied successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
