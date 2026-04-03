"""Tests for HGNCFetchedData.

Pure unit tests — no network access.
"""

import pytest
import pandas as pd

from biodbs.data.HGNC._data_model import HGNCEntry
from biodbs.data.HGNC.data import HGNCFetchedData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_response(*entries: dict, num_found: int = None) -> dict:
    """Build a /fetch-style API response dict."""
    docs = list(entries)
    return {"response": {"numFound": num_found or len(docs), "docs": docs}}


def _search_response(*hits: dict, num_found: int = None) -> dict:
    """Build a /search-style API response dict (lightweight dicts)."""
    docs = list(hits)
    return {"response": {"numFound": num_found or len(docs), "docs": docs}}


TP53 = {
    "hgnc_id": "HGNC:11998",
    "symbol": "TP53",
    "name": "tumor protein p53",
    "ensembl_gene_id": "ENSG00000141510",
    "entrez_id": "7157",
    "uniprot_ids": ["P04637"],
    "refseq_accession": ["NM_000546"],
}

BRCA1 = {
    "hgnc_id": "HGNC:1100",
    "symbol": "BRCA1",
    "name": "BRCA1 DNA repair associated",
    "ensembl_gene_id": "ENSG00000012048",
    "entrez_id": "672",
    "uniprot_ids": ["P38398"],
}


# =============================================================================
# Construction — fetch response (is_search=False)
# =============================================================================


class TestHGNCFetchedDataFetch:
    def test_results_are_hgnc_entries(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        assert all(isinstance(r, HGNCEntry) for r in data.results)

    def test_num_found(self):
        data = HGNCFetchedData(_fetch_response(TP53, num_found=42))
        assert data.num_found == 42

    def test_is_search_false(self):
        data = HGNCFetchedData(_fetch_response(TP53))
        assert data.is_search is False

    def test_len(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        assert len(data) == 2

    def test_iter(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        entries = list(data)
        assert len(entries) == 2
        assert all(isinstance(e, HGNCEntry) for e in entries)

    def test_getitem_int(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        assert data[0].symbol == "TP53"
        assert data[1].symbol == "BRCA1"

    def test_getitem_slice(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        sliced = data[0:1]
        assert len(sliced) == 1

    def test_getitem_by_hgnc_id(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        entry = data["HGNC:11998"]
        assert entry.symbol == "TP53"

    def test_getitem_by_symbol(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        entry = data["brca1"]  # case-insensitive
        assert entry.hgnc_id == "HGNC:1100"

    def test_getitem_missing_raises_key_error(self):
        data = HGNCFetchedData(_fetch_response(TP53))
        with pytest.raises(KeyError):
            _ = data["NONEXISTENT"]

    def test_getitem_wrong_type_raises(self):
        data = HGNCFetchedData(_fetch_response(TP53))
        with pytest.raises(TypeError):
            _ = data[3.14]

    def test_empty_response(self):
        data = HGNCFetchedData({"response": {"numFound": 0, "docs": []}})
        assert len(data) == 0
        assert list(data) == []

    def test_repr_fetch(self):
        data = HGNCFetchedData(_fetch_response(TP53))
        r = repr(data)
        assert "gene entries" in r
        assert "1" in r

    def test_symbols(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        assert set(data.symbols()) == {"TP53", "BRCA1"}

    def test_hgnc_ids(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        assert set(data.hgnc_ids()) == {"HGNC:11998", "HGNC:1100"}

    def test_as_dict(self):
        data = HGNCFetchedData(_fetch_response(TP53))
        dicts = data.as_dict()
        assert isinstance(dicts, list)
        assert dicts[0]["hgnc_id"] == "HGNC:11998"

    def test_as_dataframe(self):
        data = HGNCFetchedData(_fetch_response(TP53, BRCA1))
        df = data.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "hgnc_id" in df.columns
        assert "symbol" in df.columns

    def test_as_dataframe_unsupported_engine(self):
        data = HGNCFetchedData(_fetch_response(TP53))
        with pytest.raises(ValueError, match="Unsupported engine"):
            data.as_dataframe(engine="polars")


# =============================================================================
# Construction — search response (is_search=True)
# =============================================================================


class TestHGNCFetchedDataSearch:
    HITS = [
        {"hgnc_id": "HGNC:11998", "symbol": "TP53", "score": 100.0},
        {"hgnc_id": "HGNC:1100",  "symbol": "BRCA1", "score": 95.0},
    ]

    def _make(self):
        return HGNCFetchedData(_search_response(*self.HITS), is_search=True)

    def test_is_search_true(self):
        assert self._make().is_search is True

    def test_results_are_dicts(self):
        data = self._make()
        assert all(isinstance(r, dict) for r in data.results)

    def test_len(self):
        assert len(self._make()) == 2

    def test_getitem_by_symbol_search(self):
        data = self._make()
        hit = data["TP53"]
        assert hit["hgnc_id"] == "HGNC:11998"

    def test_getitem_missing_search_raises(self):
        data = self._make()
        with pytest.raises(KeyError):
            _ = data["UNKNOWN"]

    def test_symbols_search(self):
        assert set(self._make().symbols()) == {"TP53", "BRCA1"}

    def test_hgnc_ids_search(self):
        assert set(self._make().hgnc_ids()) == {"HGNC:11998", "HGNC:1100"}

    def test_as_dict_search(self):
        dicts = self._make().as_dict()
        assert isinstance(dicts, list)
        assert dicts[0]["symbol"] == "TP53"

    def test_as_dataframe_search(self):
        df = self._make().as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert "symbol" in df.columns

    def test_repr_search(self):
        r = repr(self._make())
        assert "search hits" in r
