"""Tests for HGNC_Fetcher and convenience functions with mocked HTTP.

No real network access — all HTTP calls are patched.
"""

import pytest
from unittest.mock import MagicMock, patch

from biodbs.data.HGNC._data_model import HGNCEntry
from biodbs.data.HGNC.data import HGNCFetchedData
from biodbs.fetch.HGNC.hgnc_fetcher import HGNC_Fetcher
from biodbs.exceptions import APIServerError, APINotFoundError, APIValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(json_data=None, status_code=200, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.url = "https://rest.genenames.org/test"
    resp.headers = {}
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("No JSON")
    return resp


def _fetch_json(*docs):
    return {"response": {"numFound": len(docs), "docs": list(docs)}}


def _search_json(*hits):
    return {"response": {"numFound": len(hits), "docs": list(hits)}}


TP53_DOC = {
    "hgnc_id": "HGNC:11998",
    "symbol": "TP53",
    "name": "tumor protein p53",
    "ensembl_gene_id": "ENSG00000141510",
    "entrez_id": "7157",
    "uniprot_ids": ["P04637"],
    "refseq_accession": ["NM_000546"],
}

INFO_JSON = {
    "response": {
        "numDoc": 43000,
        "lastModified": "2024-01-01T00:00:00",
        "searchableFields": ["symbol", "hgnc_id"],
        "storedFields": ["symbol", "hgnc_id", "name"],
    }
}


# =============================================================================
# HGNC_Fetcher.info
# =============================================================================


class TestHGNCFetcherInfo:
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_returns_dict(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(INFO_JSON)
        fetcher = HGNC_Fetcher()
        result = fetcher.info()
        assert isinstance(result, dict)
        assert result["response"]["numDoc"] == 43000

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_uses_accept_json_header(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(INFO_JSON)
        HGNC_Fetcher().info()
        _, kwargs = mock_request.call_args
        assert kwargs.get("headers", {}).get("Accept") == "application/json"

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_calls_info_endpoint(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(INFO_JSON)
        HGNC_Fetcher().info()
        url = mock_request.call_args[0][0]
        assert url.endswith("/info")


# =============================================================================
# HGNC_Fetcher.fetch
# =============================================================================


class TestHGNCFetcherFetch:
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_returns_hgnc_fetched_data(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_fetch_json(TP53_DOC))
        data = HGNC_Fetcher().fetch("symbol", "TP53")
        assert isinstance(data, HGNCFetchedData)
        assert data.is_search is False

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_entry_fields(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_fetch_json(TP53_DOC))
        data = HGNC_Fetcher().fetch("symbol", "TP53")
        entry = data[0]
        assert isinstance(entry, HGNCEntry)
        assert entry.symbol == "TP53"
        assert entry.entrez_id == "7157"

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_url_contains_field_and_term(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_fetch_json(TP53_DOC))
        HGNC_Fetcher().fetch("entrez_id", "7157")
        url = mock_request.call_args[0][0]
        assert "/fetch/entrez_id/7157" in url

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_term_is_url_encoded(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_fetch_json())
        HGNC_Fetcher().fetch("hgnc_id", "HGNC:11998")
        url = mock_request.call_args[0][0]
        assert "HGNC%3A11998" in url  # colon encoded

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_empty_result(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_fetch_json())
        data = HGNC_Fetcher().fetch("symbol", "FAKEGENE")
        assert len(data) == 0

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    def test_http_error_raises(self, mock_request):
        from biodbs.exceptions import raise_for_status as _raise
        resp = _mock_response(status_code=500, text="Server error")
        mock_request.return_value = resp
        with pytest.raises(Exception):
            HGNC_Fetcher().fetch("symbol", "TP53")


# =============================================================================
# HGNC_Fetcher.search
# =============================================================================


class TestHGNCFetcherSearch:
    SEARCH_HITS = [
        {"hgnc_id": "HGNC:11998", "symbol": "TP53", "score": 100.0},
        {"hgnc_id": "HGNC:26304", "symbol": "TP53BP1", "score": 90.0},
    ]

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_returns_search_data(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_search_json(*self.SEARCH_HITS))
        data = HGNC_Fetcher().search("symbol", "TP53*")
        assert isinstance(data, HGNCFetchedData)
        assert data.is_search is True

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_field_term_url(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_search_json())
        HGNC_Fetcher().search("symbol", "TP53*")
        url = mock_request.call_args[0][0]
        assert "/search/symbol/TP53" in url

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_free_form_query_url(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_search_json())
        HGNC_Fetcher().search("symbol:TP53*")
        url = mock_request.call_args[0][0]
        assert "/search/symbol" in url

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_wildcard_preserved_in_url(self, mock_raise, mock_request):
        mock_request.return_value = _mock_response(_search_json())
        HGNC_Fetcher().search("symbol", "ZNF*")
        url = mock_request.call_args[0][0]
        assert "*" in url

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_unknown_field_warns(self, mock_raise, mock_request, caplog):
        mock_request.return_value = _mock_response(_search_json())
        import logging
        with caplog.at_level(logging.WARNING, logger="biodbs.fetch.HGNC.hgnc_fetcher"):
            HGNC_Fetcher().search("not_a_real_field", "value")
        assert any("may not be searchable" in r.message for r in caplog.records)

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.request_with_retry")
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.raise_for_status")
    def test_known_field_no_warning(self, mock_raise, mock_request, caplog):
        mock_request.return_value = _mock_response(_search_json())
        import logging
        with caplog.at_level(logging.WARNING, logger="biodbs.fetch.HGNC.hgnc_fetcher"):
            HGNC_Fetcher().search("symbol", "TP53*")
        assert not any("may not be searchable" in r.message for r in caplog.records)


# =============================================================================
# Convenience functions
# =============================================================================


class TestHGNCConvenienceFunctions:
    """Test that each hgnc_fetch_by_* function calls fetch with the right field."""

    def _patch_fetcher(self, method="fetch"):
        patcher = patch(
            "biodbs.fetch.HGNC.funcs._get_fetcher",
            return_value=MagicMock(
                fetch=MagicMock(return_value=HGNCFetchedData(
                    {"response": {"numFound": 1, "docs": [TP53_DOC]}}
                )),
                search=MagicMock(return_value=HGNCFetchedData(
                    {"response": {"numFound": 1, "docs": [
                        {"hgnc_id": "HGNC:11998", "symbol": "TP53", "score": 100}
                    ]}},
                    is_search=True,
                )),
                info=MagicMock(return_value=INFO_JSON),
            ),
        )
        return patcher

    def test_hgnc_fetch_by_symbol(self):
        from biodbs.fetch.HGNC.funcs import hgnc_fetch_by_symbol
        with self._patch_fetcher() as mock_get:
            hgnc_fetch_by_symbol("TP53")
            mock_get.return_value.fetch.assert_called_once_with("symbol", "TP53")

    def test_hgnc_fetch_by_hgnc_id(self):
        from biodbs.fetch.HGNC.funcs import hgnc_fetch_by_hgnc_id
        with self._patch_fetcher() as mock_get:
            hgnc_fetch_by_hgnc_id("HGNC:11998")
            mock_get.return_value.fetch.assert_called_once_with("hgnc_id", "HGNC:11998")

    def test_hgnc_fetch_by_entrez_id(self):
        from biodbs.fetch.HGNC.funcs import hgnc_fetch_by_entrez_id
        with self._patch_fetcher() as mock_get:
            hgnc_fetch_by_entrez_id("7157")
            mock_get.return_value.fetch.assert_called_once_with("entrez_id", "7157")

    def test_hgnc_fetch_by_ensembl_id(self):
        from biodbs.fetch.HGNC.funcs import hgnc_fetch_by_ensembl_id
        with self._patch_fetcher() as mock_get:
            hgnc_fetch_by_ensembl_id("ENSG00000141510")
            mock_get.return_value.fetch.assert_called_once_with(
                "ensembl_gene_id", "ENSG00000141510"
            )

    def test_hgnc_fetch_by_uniprot_id(self):
        from biodbs.fetch.HGNC.funcs import hgnc_fetch_by_uniprot_id
        with self._patch_fetcher() as mock_get:
            hgnc_fetch_by_uniprot_id("P04637")
            mock_get.return_value.fetch.assert_called_once_with("uniprot_ids", "P04637")

    def test_hgnc_fetch_by_refseq(self):
        from biodbs.fetch.HGNC.funcs import hgnc_fetch_by_refseq
        with self._patch_fetcher() as mock_get:
            hgnc_fetch_by_refseq("NM_000546")
            mock_get.return_value.fetch.assert_called_once_with(
                "refseq_accession", "NM_000546"
            )

    def test_hgnc_search_symbol(self):
        from biodbs.fetch.HGNC.funcs import hgnc_search_symbol
        with self._patch_fetcher() as mock_get:
            hgnc_search_symbol("TP53*")
            mock_get.return_value.search.assert_called_once_with("symbol", "TP53*")

    def test_hgnc_info(self):
        from biodbs.fetch.HGNC.funcs import hgnc_info
        with self._patch_fetcher() as mock_get:
            result = hgnc_info()
            mock_get.return_value.info.assert_called_once()
            assert result == INFO_JSON

    def test_hgnc_fetch(self):
        from biodbs.fetch.HGNC.funcs import hgnc_fetch
        with self._patch_fetcher() as mock_get:
            hgnc_fetch("entrez_id", "7157")
            mock_get.return_value.fetch.assert_called_once_with("entrez_id", "7157")

    def test_hgnc_search(self):
        from biodbs.fetch.HGNC.funcs import hgnc_search
        with self._patch_fetcher() as mock_get:
            hgnc_search("symbol", "BRCA*")
            mock_get.return_value.search.assert_called_once_with("symbol", "BRCA*")
