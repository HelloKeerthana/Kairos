from sqlalchemy import text
from transforms.db import get_engine

DDL = """
CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_repo (
    repo_key SERIAL PRIMARY KEY,
    repo_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_contributor (
    contributor_key SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_pull_requests (
    pr_key BIGINT PRIMARY KEY,
    repo_key INT REFERENCES warehouse.dim_repo(repo_key),
    author_key INT REFERENCES warehouse.dim_contributor(contributor_key),
    pr_number INT,
    created_at TIMESTAMP,
    merged_at TIMESTAMP,
    closed_at TIMESTAMP,
    state TEXT,
    is_merged BOOLEAN,
    lead_time_hours NUMERIC,
    additions INT,
    deletions INT,
    changed_files INT
);

CREATE TABLE IF NOT EXISTS warehouse.fact_deployments (
    deployment_key BIGINT PRIMARY KEY,
    repo_key INT REFERENCES warehouse.dim_repo(repo_key),
    run_started_at TIMESTAMP,
    updated_at TIMESTAMP,
    status TEXT,
    conclusion TEXT,
    is_failure BOOLEAN,
    duration_seconds NUMERIC
);

CREATE TABLE IF NOT EXISTS warehouse.anomalies (
    id SERIAL PRIMARY KEY,
    metric_name TEXT,
    repo_name TEXT,
    date DATE,
    value NUMERIC,
    expected_min NUMERIC,
    expected_max NUMERIC,
    severity TEXT,
    detected_at TIMESTAMP DEFAULT NOW()
);
"""


def main():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text(DDL))

    print("Warehouse schema created.")


if __name__ == "__main__":
    main()
