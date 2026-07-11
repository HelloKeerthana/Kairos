import pandas as pd
from sqlalchemy import text
from transforms.db import get_engine
from extractors.config import REPO_OWNER, REPO_NAME

def populate():
    engine = get_engine()
    repo_name = f"{REPO_OWNER}/{REPO_NAME}"

    with engine.begin() as conn:
        repo_key = conn.execute(text(
            "SELECT repo_key FROM warehouse.dim_repo WHERE repo_name = :repo_name"
        ), {"repo_name": repo_name}).scalar()

    runs_df = pd.read_sql("SELECT * FROM staging.stg_workflow_runs", engine)

    with engine.begin() as conn:
        for _, row in runs_df.iterrows():
            started = pd.to_datetime(row["run_started_at"])
            updated = pd.to_datetime(row["updated_at"])
            duration = (updated - started).total_seconds()
            is_failure = row["conclusion"] not in ("success",)

            conn.execute(text("""
                INSERT INTO warehouse.fact_deployments
                (deployment_key, repo_key, run_started_at, updated_at, status, conclusion, is_failure, duration_seconds)
                VALUES (:key, :repo_key, :started, :updated, :status, :conclusion, :is_failure, :duration)
                ON CONFLICT (deployment_key) DO UPDATE SET
                    status = EXCLUDED.status,
                    conclusion = EXCLUDED.conclusion,
                    is_failure = EXCLUDED.is_failure
            """), {
                "key": int(row["id"]),
                "repo_key": repo_key,
                "started": started,
                "updated": updated,
                "status": row["status"],
                "conclusion": row["conclusion"],
                "is_failure": is_failure,
                "duration": duration,
            })

    print(f"Loaded {len(runs_df)} deployments into warehouse.fact_deployments")

if __name__ == "__main__":
    populate()