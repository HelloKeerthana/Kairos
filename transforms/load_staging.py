import pandas as pd
from transforms.db import get_engine

def load_table(parquet_path: str, table_name: str, engine):
    df = pd.read_parquet(parquet_path)
    df.to_sql(table_name, engine, schema="staging", if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into staging.{table_name}")

def main():
    engine = get_engine()

    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
        conn.commit()

    load_table("data/raw/pull_requests.parquet", "stg_pull_requests", engine)
    load_table("data/raw/commits.parquet", "stg_commits", engine)
    load_table("data/raw/reviews.parquet", "stg_reviews", engine)
    load_table("data/raw/workflow_runs.parquet", "stg_workflow_runs", engine)

if __name__ == "__main__":
    main()