import pandas as pd
from sqlalchemy import text
from transforms.db import get_engine
from extractors.config import REPO_OWNER, REPO_NAME

def populate():
    engine = get_engine()
    repo_name = f"{REPO_OWNER}/{REPO_NAME}"

    with engine.begin() as conn:
        # 1. Insert repo into dim_repo (idempotent upsert)
        conn.execute(text("""
            INSERT INTO warehouse.dim_repo (repo_name)
            VALUES (:repo_name)
            ON CONFLICT (repo_name) DO NOTHING
        """), {"repo_name": repo_name})

        repo_key = conn.execute(text(
            "SELECT repo_key FROM warehouse.dim_repo WHERE repo_name = :repo_name"
        ), {"repo_name": repo_name}).scalar()

    # 2. Load staging PRs
    pr_df = pd.read_sql("SELECT * FROM staging.stg_pull_requests", engine)

    with engine.begin() as conn:
        for _, row in pr_df.iterrows():
            # upsert contributor
            conn.execute(text("""
                INSERT INTO warehouse.dim_contributor (username)
                VALUES (:username)
                ON CONFLICT (username) DO NOTHING
            """), {"username": row["author"]})

            author_key = conn.execute(text(
                "SELECT contributor_key FROM warehouse.dim_contributor WHERE username = :username"
            ), {"username": row["author"]}).scalar()

            created_at = pd.to_datetime(row["created_at"])
            merged_at = pd.to_datetime(row["merged_at"]) if pd.notna(row["merged_at"]) else None
            lead_time = (merged_at - created_at).total_seconds() / 3600 if merged_at else None

            conn.execute(text("""
                INSERT INTO warehouse.fact_pull_requests
                (pr_key, repo_key, author_key, pr_number, created_at, merged_at, closed_at,
                 state, is_merged, lead_time_hours, additions, deletions, changed_files)
                VALUES (:pr_key, :repo_key, :author_key, :pr_number, :created_at, :merged_at, :closed_at,
                        :state, :is_merged, :lead_time_hours, :additions, :deletions, :changed_files)
                ON CONFLICT (pr_key) DO UPDATE SET
                    state = EXCLUDED.state,
                    merged_at = EXCLUDED.merged_at,
                    is_merged = EXCLUDED.is_merged,
                    lead_time_hours = EXCLUDED.lead_time_hours
            """), {
                "pr_key": int(row["id"]),
                "repo_key": repo_key,
                "author_key": author_key,
                "pr_number": int(row["number"]),
                "created_at": created_at,
                "merged_at": merged_at,
                "closed_at": pd.to_datetime(row["closed_at"]) if pd.notna(row["closed_at"]) else None,
                "state": row["state"],
                "is_merged": merged_at is not None,
                "lead_time_hours": lead_time,
                "additions": int(row["additions"]) if pd.notna(row["additions"]) else None,
                "deletions": int(row["deletions"]) if pd.notna(row["deletions"]) else None,
                "changed_files": int(row["changed_files"]) if pd.notna(row["changed_files"]) else None,
            })

    print("Warehouse populated.")

if __name__ == "__main__":
    populate()