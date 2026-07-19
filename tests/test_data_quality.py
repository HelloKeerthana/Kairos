import pandas as pd
import pytest
from extractors.data_quality import check_required_fields, DataQualityError


def test_check_required_fields_passes_with_valid_data():
    df = pd.DataFrame({"id": [1, 2], "created_at": ["2026-01-01", "2026-01-02"]})
    check_required_fields(df, ["id", "created_at"], "test_table")  # should not raise


def test_check_required_fields_raises_on_null():
    df = pd.DataFrame({"id": [1, None], "created_at": ["2026-01-01", "2026-01-02"]})
    with pytest.raises(DataQualityError):
        check_required_fields(df, ["id", "created_at"], "test_table")


def test_check_required_fields_raises_on_missing_column():
    df = pd.DataFrame({"id": [1, 2]})
    with pytest.raises(DataQualityError):
        check_required_fields(df, ["id", "created_at"], "test_table")
