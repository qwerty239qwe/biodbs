"""Offline tests for LPSN data wrappers."""

import pytest

from biodbs.data.LPSN import LPSNEntry, LPSNFetchedData, LPSNSearchData


def test_lpsn_entry_preserves_unknown_fields():
    entry = LPSNEntry.from_dict(
        {
            "id": 520424,
            "full_name": "Bacillus subtilis",
            "category": "species",
            "type_strain_names": "DSM 10",
            "future_field": "kept",
        }
    )

    assert entry.id == 520424
    assert entry.type_strain_names == ["DSM 10"]
    assert entry.raw["future_field"] == "kept"


def test_lpsn_entry_missing_id_is_none():
    entry = LPSNEntry.from_dict({"full_name": "No ID"})

    assert entry.id is None
    assert LPSNFetchedData([{"full_name": "No ID"}]).ids() == []


def test_fetched_data_sequence_and_conversion():
    data = LPSNFetchedData(
        {
            "count": 1,
            "results": [{"id": 1, "full_name": "Bacillus subtilis", "category": "species"}],
        }
    )

    assert len(data) == 1
    assert data[0].full_name == "Bacillus subtilis"
    assert data["1"].id == 1
    assert data["Bacillus subtilis"].id == 1
    assert data.ids() == [1]
    assert data.names() == ["Bacillus subtilis"]
    assert data.as_dict()[0]["category"] == "species"
    assert list(data.as_dataframe().columns) == ["id", "full_name", "category"]


def test_search_data_ids_and_dataframe():
    data = LPSNSearchData({"count": 2, "results": [1, "2"]})

    assert len(data) == 2
    assert data.ids() == [1, 2]
    assert data.as_dict() == [{"id": 1}, {"id": "2"}]
    assert list(data.as_dataframe()["id"]) == [1, "2"]


def test_unsupported_engine_raises():
    with pytest.raises(ValueError):
        LPSNFetchedData([]).as_dataframe(engine="polars")
