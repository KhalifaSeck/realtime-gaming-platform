from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="hello_rtgaming",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["test", "rtgaming"],
) as dag:
    BashOperator(
        task_id="say_hello",
        bash_command="echo 'Hello from RTGaming Airflow on AKS!'",
    )