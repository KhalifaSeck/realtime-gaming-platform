"""
batch_copy - Execute a Snowflake COPY script with {DATE} substitution.

Usage:
    python -m ops.batch_copy sql/copy/02_batch.sql --date 2026-09-01
    python -m ops.batch_copy sql/copy/02_batch.sql              # defaults to today
"""
from __future__ import annotations

import argparse
from datetime import date
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


def _run_sql(conn, sql: str, source: str) -> None:
    log.info("snowflake.script.start", source=source, size_kb=len(sql) // 1024)
    for cursor in conn.execute_string(sql):
        rows = cursor.fetchall()
        if rows:
            desc = [d[0] for d in cursor.description] if cursor.description else []
            log.info(
                "snowflake.script.result",
                statement=(cursor.query or "").splitlines()[0][:80],
                cols=desc,
                sample=rows[:5],
                total_rows=len(rows),
            )
    log.info("snowflake.script.done", source=source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_path", help="Path to SQL file with {DATE} placeholder")
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Date to substitute for {DATE} in SQL (YYYY-MM-DD). Default: today.",
    )
    args = parser.parse_args()

    sql_path = Path(args.sql_path).resolve()
    raw_sql = sql_path.read_text(encoding="utf-8")
    sql = raw_sql.replace("{DATE}", args.date)

    log.info("batch_copy.substitute", date=args.date, sql_path=str(sql_path))

    with _connect() as conn:
        _run_sql(conn, sql, str(sql_path))


if __name__ == "__main__":
    main()