"""Tests for biodbs.data.FDA.data module."""

import pytest
import pandas as pd
from biodbs.data.FDA.data import FDAFetchedData


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def fda_response():
    return {
        "meta": {"results": {"total": 2}},
        "results": [
            {"patient": {"drug": [{"medicinalproduct": "ASPIRIN"}]}, "serious": 1},
            {"patient": {"drug": [{"medicinalproduct": "IBUPROFEN"}]}, "serious": 0},
        ],
    }


@pytest.fixture
def fda_data(fda_response):
    return FDAFetchedData(fda_response)


# =============================================================================
# Tests
# =============================================================================


class TestInit:
    def test_metadata(self, fda_data):
        assert fda_data.metadata["results"]["total"] == 2

    def test_results(self, fda_data):
        assert len(fda_data.results) == 2

    def test_len(self, fda_data):
        assert len(fda_data) == 2

    def test_repr(self, fda_data):
        r = repr(fda_data)
        assert "FDAFetchedData" in r
        assert "2 results" in r


class TestFlattenDict:
    def test_nested(self, fda_data):
        result = fda_data._flatten_dict({"a": {"b": 1, "c": 2}, "d": 3})
        assert result == {"a.b": 1, "a.c": 2, "d": 3}

    def test_deeply_nested(self, fda_data):
        result = fda_data._flatten_dict({"a": {"b": {"c": 1}}})
        assert result == {"a.b.c": 1}

    def test_flat(self, fda_data):
        result = fda_data._flatten_dict({"x": 1})
        assert result == {"x": 1}


class TestShowValidColumns:
    def test_returns_sorted(self, fda_data):
        cols = fda_data.show_valid_columns()
        assert cols == sorted(cols)

    def test_includes_nested(self, fda_data):
        cols = fda_data.show_valid_columns()
        assert "serious" in cols
        assert "patient.drug.medicinalproduct" in cols


class TestFormatResults:
    def test_select_columns(self, fda_data):
        result = fda_data.format_results(columns=["serious"])
        assert len(result) == 2
        assert result[0] == {"serious": 1}

    def test_nested_column(self, fda_data):
        result = fda_data.format_results(columns=["patient.drug.medicinalproduct"])
        assert len(result) == 2

    def test_invalid_column_raises(self, fda_data):
        with pytest.raises(ValueError, match="not a valid column"):
            fda_data.format_results(columns=["nonexistent"])

    def test_none_columns(self, fda_data):
        result = fda_data.format_results(columns=None)
        assert result == [{}] * 2  # Empty dicts since no columns selected


class TestTrim:
    def test_trim_top_level(self, fda_response):
        data = FDAFetchedData(fda_response)
        result = data.trim(["serious"])
        assert result is data  # Returns self
        assert "serious" not in data.results[0]

    def test_trim_nested(self, fda_response):
        data = FDAFetchedData(fda_response)
        data.trim(["patient.drug"])
        assert "drug" not in data.results[0]["patient"]

    def test_trim_nonexistent_key(self, fda_response):
        data = FDAFetchedData(fda_response)
        # Should not raise
        data.trim(["nonexistent.key"])


class TestAsDataframe:
    def test_flatten(self, fda_data):
        df = fda_data.as_dataframe(flatten=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_with_columns(self, fda_data):
        df = fda_data.as_dataframe(columns=["serious"])
        assert list(df.columns) == ["serious"]

    def test_no_results_raises(self):
        data = FDAFetchedData({"meta": {}, "results": []})
        with pytest.raises(ValueError, match="No results"):
            data.as_dataframe(flatten=True)

    def test_no_columns_no_flatten_raises(self, fda_data):
        with pytest.raises(ValueError, match="deeply nested"):
            fda_data.as_dataframe()


class TestAsDict:
    def test_no_columns(self, fda_data):
        result = fda_data.as_dict()
        assert result is fda_data.results

    def test_with_columns(self, fda_data):
        result = fda_data.as_dict(columns=["serious"])
        assert len(result) == 2
        assert list(result[0].keys()) == ["serious"]


class TestIadd:
    def test_concatenation(self, fda_response):
        data1 = FDAFetchedData(fda_response)
        data2 = FDAFetchedData({
            "meta": {},
            "results": [{"patient": {"drug": [{"medicinalproduct": "TYLENOL"}]}, "serious": 1}],
        })
        data1 += data2
        assert len(data1) == 3
