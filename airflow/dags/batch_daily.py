"""
RTGaming - Batch Daily
----------------------
1. Ingestion IGDB → ADLS raw/igdb_games/
2. Ingestion SteamSpy → ADLS raw/steamspy_games/
3. Snowflake COPY INTO RAW.* (batch tables)
4. dbt deps + run + test (STAGING + ANALYTICS)
5. Refresh Neo4j Knowledge Graph depuis Snowflake ANALYTICS
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# --------------------------------------------------------------------------
# Chemins DANS le conteneur Astro (les copies /include/ sont montées ici)
# --------------------------------------------------------------------------
INCLUDE_DIR = "/usr/local/airflow/include"
INGESTION_DIR = f"{INCLUDE_DIR}/ingestion"
GRAPH_DIR = f"{INCLUDE_DIR}/graph"
SNOWFLAKE_DIR = f"{INCLUDE_DIR}/snowflake"
DBT_PROJECT_DIR = f"{INCLUDE_DIR}/gaming_dbt"

SNOWFLAKE_COPY_SQL = f"{SNOWFLAKE_DIR}/sql/copy/02_batch.sql"

default_args = {
    "owner": "khalifa",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="batch_daily",
    description="Batch pipeline: IGDB+SteamSpy -> ADLS -> Snowflake -> dbt -> Neo4j",
    default_args=default_args,
    schedule="0 3 * * *",  # tous les jours a 03:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["rtgaming", "batch", "production"],
) as dag:

    # ---------------------------------------------------------------
    # 1) INGESTION (2 taches en parallele)
    # ---------------------------------------------------------------
    ingest_igdb = BashOperator(
        task_id="ingest_igdb",
        bash_command=(
            f"cd {INGESTION_DIR} && "
            f"PYTHONPATH={INGESTION_DIR} python -m src.main --source igdb"
        ),
    )


    ingest_steamspy = BashOperator(
        task_id="ingest_steamspy",
        execution_timeout=timedelta(hours=1),
        bash_command=(
            f"cd {INGESTION_DIR} && "
            f"PYTHONPATH={INGESTION_DIR} python -m src.main "
            f"--source steamspy --pages 20 --enrich-limit 100"
        ),
    )

    # ---------------------------------------------------------------
    # 2) SNOWFLAKE COPY INTO RAW
    # ---------------------------------------------------------------
    snowflake_copy = BashOperator(
        task_id="snowflake_copy_batch",
        bash_command=(
            "cd /usr/local/airflow/include/snowflake && "
            "PYTHONPATH=/usr/local/airflow/include/snowflake "
            "python -m ops.batch_copy "
            "/usr/local/airflow/include/snowflake/sql/copy/02_batch.sql "
            "--date {{ ds }}"
        ),
    )
    # ---------------------------------------------------------------
    # 3) DBT (STAGING + ANALYTICS marts)
    # ---------------------------------------------------------------
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --target dev",
    )

    # ---------------------------------------------------------------
    # 4) REFRESH NEO4J KNOWLEDGE GRAPH
    # ---------------------------------------------------------------
    refresh_neo4j = BashOperator(
        task_id="refresh_neo4j",
        bash_command=(
            f"cd {GRAPH_DIR} && "
            f"PYTHONPATH={GRAPH_DIR} python -m src.main"
        ),
    )

    # ---------------------------------------------------------------
    # DEPENDENCIES
    # ---------------------------------------------------------------
    [ingest_igdb, ingest_steamspy] >> snowflake_copy >> dbt_deps >> dbt_run >> refresh_neo4j