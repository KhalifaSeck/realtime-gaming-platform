"""
Runner Snowflake : execute un fichier .sql ou tout un dossier.

Usage :
    python -m ops.runner sql/04_raw_batch_tables.sql
    python -m ops.runner sql/                        (tous les .sql, ordre alpha)
    python -m ops.runner sql/03_migrate_agg_to_analytics.sql --dry-run
"""
from __future__ import annotations

import argparse
from pathlib import Path

import snowflake.connector
import structlog

from ops.config import get_settings

log = structlog.get_logger()


def _connect() -> snowflake.connector.SnowflakeConnection:
    s = get_settings()
    return snowflake.connector.connect(
        account=f"{s.snowflake_organization_name}-{s.snowflake_account_name}",
        user=s.snowflake_user,
        password=s.snowflake_password,
        role=s.snowflake_role,
        warehouse=s.snowflake_warehouse,
        client_session_keep_alive=False,
    )


def _run_sql_string(conn, sql: str, source: str) -> None:
    log.info("snowflake.script.start", source=source, size_kb=len(sql) // 1024)
    for cursor in conn.execute_string(sql):
        rows = cursor.fetchall()
        if rows:
            # Affiche les 5 premieres lignes de chaque statement (typiquement SHOW/SELECT)
            desc = [d[0] for d in cursor.description] if cursor.description else []
            log.info(
                "snowflake.script.result",
                statement=cursor.query.split("\n")[0][:80] if cursor.query else "",
                cols=desc,
                sample=rows[:5],
                total_rows=len(rows),
            )
    log.info("snowflake.script.done", source=source)


def run_file(path: Path, dry_run: bool = False) -> None:
    sql = path.read_text(encoding="utf-8")
    if dry_run:
        log.info("snowflake.dry_run", file=str(path), size_kb=len(sql) // 1024)
        print(sql)
        return
    conn = _connect()
    try:
        _run_sql_string(conn, sql, source=str(path))
    finally:
        conn.close()


def run_folder(folder: Path, dry_run: bool = False) -> None:
    files = sorted(folder.glob("*.sql"))
    if not files:
        log.warning("snowflake.folder.empty", folder=str(folder))
        return
    log.info("snowflake.folder.start", folder=str(folder), files=[f.name for f in files])
    if dry_run:
        for f in files:
            run_file(f, dry_run=True)
        return
    conn = _connect()
    try:
        for f in files:
            _run_sql_string(conn, f.read_text(encoding="utf-8"), source=str(f))
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Snowflake SQL scripts.")
    parser.add_argument("target", type=Path, help="Path to .sql file OR folder containing .sql files.")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing.")
    args = parser.parse_args()

    if args.target.is_file():
        run_file(args.target, dry_run=args.dry_run)
    elif args.target.is_dir():
        run_folder(args.target, dry_run=args.dry_run)
    else:
        raise SystemExit(f"Not a file or directory: {args.target}")


if __name__ == "__main__":
    main()