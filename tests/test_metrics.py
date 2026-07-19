import pandas as pd


def calculate_lead_time_hours(created_at: str, merged_at: str) -> float:
    """Extracted logic matching what populate_warehouse.py does inline."""
    created = pd.to_datetime(created_at)
    merged = pd.to_datetime(merged_at)
    return (merged - created).total_seconds() / 3600


def test_lead_time_calculation_basic():
    result = calculate_lead_time_hours("2026-07-04T02:52:01Z", "2026-07-04T02:52:21Z")
    expected = 20 / 3600  # 20 seconds in hours
    assert abs(result - expected) < 0.0001


def test_lead_time_calculation_one_hour():
    result = calculate_lead_time_hours("2026-07-04T10:00:00Z", "2026-07-04T11:00:00Z")
    assert result == 1.0
