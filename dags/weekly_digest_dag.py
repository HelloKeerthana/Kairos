from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "kairos",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="kairos_weekly_digest",
    default_args=default_args,
    description="Generate and deliver the AI weekly engineering digest",
    schedule_interval="@weekly",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["kairos", "agent"],
) as dag:

    run_digest = BashOperator(
        task_id="run_weekly_digest",
        bash_command="cd /opt/airflow && python -m agent.run_weekly_digest",
    )
