import pandas as pd
from transforms.anomaly_detection import detect_zscore_anomalies, detect_iqr_anomalies


def test_zscore_detects_obvious_outlier():
    df = pd.DataFrame({"duration_seconds": [40, 60, 80, 70, 2700]})
    result = detect_zscore_anomalies(df, "duration_seconds", threshold=1.0)
    assert len(result) >= 1
    assert 2700 in result["duration_seconds"].values


def test_zscore_returns_empty_on_uniform_data():
    df = pd.DataFrame({"duration_seconds": [50, 50, 50, 50]})
    result = detect_zscore_anomalies(df, "duration_seconds")
    assert result.empty


def test_iqr_detects_obvious_outlier():
    df = pd.DataFrame({"duration_seconds": [40, 60, 80, 70, 82, 2700]})
    result = detect_iqr_anomalies(df, "duration_seconds")
    assert len(result) >= 1
    assert 2700 in result["duration_seconds"].values
