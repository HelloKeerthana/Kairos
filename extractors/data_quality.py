import pandas as pd

class DataQualityError(Exception):
    pass

def check_not_empty(df: pd.DataFrame, name: str):
    if df.empty:
        print(f"[WARNING] {name} is empty — no rows to validate.")
        return
    print(f"[OK] {name}: {len(df)} rows")

def check_required_fields(df: pd.DataFrame, required_cols: list, name: str):
    if df.empty:
        return
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataQualityError(f"{name}: missing required columns {missing}")

    null_counts = df[required_cols].isnull().sum()
    bad_cols = null_counts[null_counts > 0]
    if not bad_cols.empty:
        raise DataQualityError(f"{name}: unexpected nulls in {bad_cols.to_dict()}")
    print(f"[OK] {name}: required fields have no unexpected nulls")

def check_timestamp_order(df: pd.DataFrame, start_col: str, end_col: str, name: str):
    if df.empty or end_col not in df.columns:
        return
    valid = df.dropna(subset=[start_col, end_col])
    if valid.empty:
        return
    bad = valid[pd.to_datetime(valid[start_col]) > pd.to_datetime(valid[end_col])]
    if not bad.empty:
        raise DataQualityError(f"{name}: {len(bad)} rows have {start_col} after {end_col}")
    print(f"[OK] {name}: timestamp order valid")

def validate_pull_requests(df: pd.DataFrame):
    name = "pull_requests"
    check_not_empty(df, name)
    check_required_fields(df, ["id", "number", "created_at", "state"], name)
    check_timestamp_order(df, "created_at", "merged_at", name)

def validate_commits(df: pd.DataFrame):
    name = "commits"
    check_not_empty(df, name)
    check_required_fields(df, ["sha", "author_name", "date"], name)