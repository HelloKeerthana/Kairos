from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "kairos",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="kairos_etl_pipeline",
    default_args=default_args,
    description="Extract GitHub data, load to Postgres, transform into warehouse, compute DORA metrics",
    schedule_interval="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["kairos", "etl"],
) as dag:

    # PHASE C/D — Extract
    extract_prs = BashOperator(
        task_id="extract_pull_requests",
        bash_command="cd /opt/airflow && python -m extractors.fetch_pull_requests",
    )

    extract_commits = BashOperator(
        task_id="extract_commits",
        bash_command="cd /opt/airflow && python -m extractors.fetch_commits",
    )

    extract_reviews = BashOperator(
        task_id="extract_reviews",
        bash_command="cd /opt/airflow && python -m extractors.fetch_reviews",
    )

    extract_workflow_runs = BashOperator(
        task_id="extract_workflow_runs",
        bash_command="cd /opt/airflow && python -m extractors.fetch_workflow_runs",
    )

    # PHASE G — Load to staging
    load_staging = BashOperator(
        task_id="load_staging",
        bash_command="cd /opt/airflow && python -m transforms.load_staging",
    )

    # PHASE H — Build/populate warehouse
    build_warehouse = BashOperator(
        task_id="build_warehouse",
        bash_command="cd /opt/airflow && python -m transforms.build_warehouse",
    )

    populate_warehouse = BashOperator(
        task_id="populate_warehouse",
        bash_command="cd /opt/airflow && python -m transforms.populate_warehouse",
    )

    populate_deployments = BashOperator(
        task_id="populate_deployments",
        bash_command="cd /opt/airflow && python -m transforms.populate_deployments",
    )

    # PHASE I — Metrics
    run_metrics = BashOperator(
        task_id="run_metrics",
        bash_command="cd /opt/airflow && python -m transforms.run_metrics",
    )

    # Dependencies: all extracts run in parallel first,
    # reviews depends on PRs already existing (needs pull_requests.parquet)
    extract_prs >> extract_reviews
    [
        extract_prs,
        extract_commits,
        extract_reviews,
        extract_workflow_runs,
    ] >> load_staging
    (
        load_staging
        >> build_warehouse
        >> populate_warehouse
        >> populate_deployments
        >> run_metrics
    )
