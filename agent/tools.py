from sqlalchemy import text
from transforms.db import get_engine


def query_metrics_db():
    """Fetch current DORA metrics + anomalies as a dict the agent can reason over."""
    engine = get_engine()

    with engine.connect() as conn:
        lead_time = conn.execute(
            text("SELECT * FROM warehouse.v_dora_lead_time ORDER BY week DESC")
        ).fetchall()
        deploy_freq = conn.execute(
            text(
                "SELECT * FROM warehouse.v_dora_deployment_frequency ORDER BY week DESC"
            )
        ).fetchall()
        failure_rate = conn.execute(
            text(
                "SELECT * FROM warehouse.v_dora_change_failure_rate ORDER BY week DESC"
            )
        ).fetchall()
        anomalies = conn.execute(
            text("SELECT * FROM warehouse.anomalies ORDER BY detected_at DESC")
        ).fetchall()

    return {
        "lead_time": [dict(row._mapping) for row in lead_time],
        "deployment_frequency": [dict(row._mapping) for row in deploy_freq],
        "change_failure_rate": [dict(row._mapping) for row in failure_rate],
        "anomalies": [dict(row._mapping) for row in anomalies],
    }


def get_top_contributors(limit=5):
    """Fetch top contributors by commit count."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT author_name, COUNT(*) AS commit_count
            FROM staging.stg_commits
            GROUP BY author_name
            ORDER BY commit_count DESC
            LIMIT :limit
        """),
            {"limit": limit},
        )
        return [dict(row._mapping) for row in result.fetchall()]
