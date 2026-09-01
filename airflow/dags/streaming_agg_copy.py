"""
RTGaming - Streaming Aggregates COPY
------------------------------------
Toutes les 5 min, execute COPY INTO ANALYTICS.STREAM_*_AGG
depuis ADLS raw/streaming/{topic}/ (aggregates 5-min Spark windows).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "khalifa",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}

with DAG(
    dag_id="streaming_agg_copy_to_snowflake",
    description="Micro-batch COPY: ADLS streaming aggregates -> ANALYTICS.STREAM_*_AGG",
    default_args=default_args,
    schedule="*/5 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["rtgaming", "streaming", "analytics"],
) as dag:

    agg_copy = BashOperator(
        task_id="agg_copy_all_topics",
        execution_timeout=timedelta(minutes=10),
        bash_command=(
            "cd /usr/local/airflow/include/snowflake && "
            "PYTHONPATH=/usr/local/airflow/include/snowflake "
            "python -m ops.runner "
            "/usr/local/airflow/include/snowflake/sql/copy/01_streaming_agg.sql"
        ),
    )