"""
RTGaming - Streaming COPY (micro-batch alternative to Snowpipe)
---------------------------------------------------------------
Tous les 5 min, execute COPY INTO RAW.STREAM_* depuis
ADLS raw/streaming_events/. Snowflake track les fichiers deja
charges, donc c'est idempotent (skip les parquets connus).

Une fois que le streaming Kafka+Spark sera deploye sur AKS,
les events atteindront Snowflake en moins de 5 min.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

SNOWFLAKE_DIR = "/usr/local/airflow/include/snowflake"
SNOWFLAKE_STREAM_SQL = f"{SNOWFLAKE_DIR}/sql/copy/03_streaming_raw_events.sql"

default_args = {
    "owner": "khalifa",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}

with DAG(
    dag_id="streaming_copy_to_snowflake",
    description="Micro-batch COPY: ADLS streaming_events -> RAW.STREAM_*",
    default_args=default_args,
    schedule="*/5 * * * *",  # toutes les 5 minutes
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["rtgaming", "streaming", "production"],
) as dag:

    stream_copy = BashOperator(
        task_id="stream_copy_all_topics",
        execution_timeout=timedelta(minutes=10),
        bash_command=(
            "cd /usr/local/airflow/include/snowflake && "
            "PYTHONPATH=/usr/local/airflow/include/snowflake "
            "python -m ops.runner "
            "/usr/local/airflow/include/snowflake/sql/copy/03_streaming_raw_events.sql"
        ),
    )