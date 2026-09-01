"""
RTGaming - Streaming dbt refresh
--------------------------------
Toutes les 15 min, rafraichit les marts dbt taggees 'streaming'
depuis RAW.STREAM_* (fed par Airflow streaming_copy_to_snowflake).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DBT_PROJECT_DIR = "/usr/local/airflow/include/gaming_dbt"

default_args = {
    "owner": "khalifa",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
    "email_on_failure": False,
}

with DAG(
    dag_id="streaming_dbt_refresh",
    description="Refresh dbt streaming marts every 15 min",
    default_args=default_args,
    schedule="*/15 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["rtgaming", "streaming", "dbt"],
) as dag:

    dbt_run_streaming = BashOperator(
        task_id="dbt_run_streaming",
        execution_timeout=timedelta(minutes=10),
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --target dev --select tag:streaming"
        ),
    )