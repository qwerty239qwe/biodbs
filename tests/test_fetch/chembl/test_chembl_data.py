"""Tests for biodbs.data.ChEMBL.data module."""

import pytest
import pandas as pd
from biodbs.data.ChEMBL.data import ChEMBLFetchedData


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def paginated_response():
    return {
        "page_meta": {"limit": 20, "offset": 0, "total_count": 2, "next": None},
        "molecules": [
            {"molecule_chembl_id": "CHEMBL25", "pref_name": "ASPIRIN"},
            {"molecule_chembl_id": "CHEMBL1642", "pref_name": "IBUPROFEN"},
        ],
    }


@pytest.fixture
def single_entry_response():
    return {"molecule_chembl_id": "CHEMBL25", "pref_name": "ASPIRIN", "max_phase": 4}


@pytest.fixture
def list_response():
    return [
        {"molecule_chembl_id": "CHEMBL25"},
        {"molecule_chembl_id": "CHEMBL1642"},
    ]


# =============================================================================
# Tests
# =============================================================================


class TestExtractResults:
    def test_paginated_response(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        assert len(data.results) == 2
        assert data.results[0]["molecule_chembl_id"] == "CHEMBL25"

    def test_single_entry(self, single_entry_response):
        data = ChEMBLFetchedData(single_entry_response)
        assert len(data.results) == 1
        assert data.results[0]["molecule_chembl_id"] == "CHEMBL25"

    def test_list_response(self, list_response):
        data = ChEMBLFetchedData(list_response)
        assert len(data.results) == 2

    def test_empty_dict(self):
        data = ChEMBLFetchedData({})
        assert data.results == []

    def test_non_dict_non_list(self):
        data = ChEMBLFetchedData("invalid")
        assert data.results == []

    def test_metadata(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        assert data.metadata["total_count"] == 2
        assert data.get_total_count() == 2


class TestFlattenDict:
    def test_nested(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        result = data._flatten_dict({"a": {"b": 1, "c": {"d": 2}}, "e": 3})
        assert result == {"a.b": 1, "a.c.d": 2, "e": 3}

    def test_flat(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        result = data._flatten_dict({"x": 1, "y": 2})
        assert result == {"x": 1, "y": 2}


class TestFormatResults:
    def test_select_columns(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        result = data.format_results(columns=["molecule_chembl_id"])
        assert len(result) == 2
        assert list(result[0].keys()) == ["molecule_chembl_id"]

    def test_invalid_column_raises(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        with pytest.raises(ValueError, match="not valid"):
            data.format_results(columns=["nonexistent_col"])

    def test_safe_check_disabled(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        result = data.format_results(columns=["nonexistent"], safe_check=False)
        assert len(result) == 2
        assert result[0]["nonexistent"] is None


class TestFilter:
    def test_filter_exact(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        filtered = data.filter(molecule_chembl_id="CHEMBL25")
        assert len(filtered) == 1
        assert filtered.results[0]["pref_name"] == "ASPIRIN"

    def test_filter_callable(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        filtered = data.filter(pref_name=lambda x: x is not None and x.startswith("A"))
        assert len(filtered) == 1

    def test_filter_no_match(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        filtered = data.filter(molecule_chembl_id="NONEXISTENT")
        assert len(filtered) == 0


class TestAsDataframe:
    def test_pandas(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        df = data.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_empty(self):
        data = ChEMBLFetchedData({})
        df = data.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_flatten(self):
        content = {
            "page_meta": {"limit": 1, "total_count": 1},
            "molecules": [{"props": {"a": 1, "b": 2}, "name": "x"}],
        }
        data = ChEMBLFetchedData(content)
        df = data.as_dataframe(flatten=True)
        assert "props.a" in df.columns

    def test_with_columns(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        df = data.as_dataframe(columns=["molecule_chembl_id"])
        assert list(df.columns) == ["molecule_chembl_id"]


class TestGetChemblIds:
    def test_molecule_ids(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        ids = data.get_chembl_ids()
        assert ids == ["CHEMBL25", "CHEMBL1642"]

    def test_target_ids(self):
        content = [{"target_chembl_id": "CHEMBL2096904"}]
        data = ChEMBLFetchedData(content)
        ids = data.get_chembl_ids()
        assert ids == ["CHEMBL2096904"]

    def test_no_ids(self):
        content = [{"some_field": "value"}]
        data = ChEMBLFetchedData(content)
        ids = data.get_chembl_ids()
        assert ids == []


class TestMisc:
    def test_iadd(self, paginated_response, list_response):
        data1 = ChEMBLFetchedData(paginated_response)
        data2 = ChEMBLFetchedData(list_response)
        data1 += data2
        assert len(data1) == 4

    def test_len(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        assert len(data) == 2

    def test_repr(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response, resource="molecule")
        r = repr(data)
        assert "ChEMBLFetchedData" in r
        assert "2 results" in r

    def test_show_columns(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        cols = data.show_columns()
        assert "molecule_chembl_id" in cols
        assert "pref_name" in cols

    def test_as_dict_no_columns(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        result = data.as_dict()
        assert result is data.results

    def test_as_dict_with_columns(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        result = data.as_dict(columns=["molecule_chembl_id"])
        assert len(result) == 2
        assert list(result[0].keys()) == ["molecule_chembl_id"]

    def test_get_next_offset(self):
        content = {
            "page_meta": {"next": "/api/data?offset=20&limit=20", "total_count": 100},
            "molecules": [{"molecule_chembl_id": "CHEMBL25"}],
        }
        data = ChEMBLFetchedData(content)
        assert data.get_next_offset() == 20

    def test_get_next_offset_none(self, paginated_response):
        data = ChEMBLFetchedData(paginated_response)
        assert data.get_next_offset() is None
