import pandas as pd
from sqlalchemy import text
from transforms.db import get_engine


def detect_zscore_anomalies(df: pd.DataFrame, value_col: str, threshold: float = 2.5):
    """Flag rows where value is more than `threshold` std devs from the mean."""
    if len(df) < 3:
        print(
            f"Not enough data points ({len(df)}) for reliable z-score detection — skipping."
        )
        return pd.DataFrame()

    mean = df[value_col].mean()
    std = df[value_col].std()

    if std == 0:
        return pd.DataFrame()

    df = df.copy()
    df["z_score"] = (df[value_col] - mean) / std
    anomalies = df[df["z_score"].abs() > threshold]

    if anomalies.empty:
        return pd.DataFrame()

    return anomalies.assign(
        expected_min=mean - threshold * std,
        expected_max=mean + threshold * std,
        severity=anomalies["z_score"]
        .abs()
        .apply(lambda z: "high" if z > 3.5 else "medium"),
    )


def detect_iqr_anomalies(df: pd.DataFrame, value_col: str):
    """Flag rows outside Q1 - 1.5*IQR / Q3 + 1.5*IQR — more robust to masking than z-score on small samples."""
    if len(df) < 4:
        print(
            f"Not enough data points ({len(df)}) for reliable IQR detection — skipping."
        )
        return pd.DataFrame()

    q1 = df[value_col].quantile(0.25)
    q3 = df[value_col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    df = df.copy()
    anomalies = df[(df[value_col] < lower) | (df[value_col] > upper)]

    if anomalies.empty:
        return pd.DataFrame()

    return anomalies.assign(
        expected_min=lower,
        expected_max=upper,
        severity="medium",
    )


def run_detection():
    engine = get_engine()

    query = text("""
        SELECT d.duration_seconds, d.run_started_at::date AS date, r.repo_name
        FROM warehouse.fact_deployments d
        JOIN warehouse.dim_repo r ON d.repo_key = r.repo_key
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()
        columns = result.keys()

    runs_df = pd.DataFrame(rows, columns=columns)

    if runs_df.empty:
        print("No deployment data found — nothing to analyze.")
        return

    runs_df["duration_seconds"] = runs_df["duration_seconds"].astype(float)

    print(f"Analyzing {len(runs_df)} deployment records...")
    print(runs_df[["repo_name", "date", "duration_seconds"]])

    zscore_anomalies = detect_zscore_anomalies(runs_df, "duration_seconds")
    iqr_anomalies = detect_iqr_anomalies(runs_df, "duration_seconds")

    frames = [f for f in [zscore_anomalies, iqr_anomalies] if not f.empty]

    if not frames:
        print("No CI duration anomalies detected.")
        return

    anomalies = pd.concat(frames).drop_duplicates(
        subset=["date", "repo_name", "duration_seconds"]
    )

    print(f"Found {len(anomalies)} anomalies:")
    print(
        anomalies[
            [
                "repo_name",
                "date",
                "duration_seconds",
                "expected_min",
                "expected_max",
                "severity",
            ]
        ]
    )

    with engine.begin() as conn:
        for _, row in anomalies.iterrows():
            conn.execute(
                text("""
                INSERT INTO warehouse.anomalies
                (metric_name, repo_name, date, value, expected_min, expected_max, severity)
                VALUES ('ci_run_duration_seconds', :repo_name, :date, :value, :emin, :emax, :severity)
            """),
                {
                    "repo_name": row["repo_name"],
                    "date": row["date"],
                    "value": row["duration_seconds"],
                    "emin": float(row["expected_min"]),
                    "emax": float(row["expected_max"]),
                    "severity": row["severity"],
                },
            )

    print(f"Inserted {len(anomalies)} CI duration anomalies into warehouse.anomalies.")


if __name__ == "__main__":
    run_detection()
