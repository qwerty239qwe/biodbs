"""Tests for ClinVar_Fetcher and convenience functions — mocked HTTP.

No real network access.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, call

from biodbs.data.ClinVar.data import ClinVarFetchedData
from biodbs.fetch.ClinVar.clinvar_fetcher import ClinVar_Fetcher, _BASE_URL
from tests.test_fetch.clinvar.fixtures import (
    TP53_DOC, BRCA1_DOC, BENIGN_DOC,
    esummary_response, esearch_response, elink_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(json_data=None, status_code=200, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.url = "https://eutils.ncbi.nlm.nih.gov/test"
    resp.headers = {}
    resp.json.return_value = json_data or {}
    return resp


def _patch_request(json_data=None, text="", status_code=200):
    """Context manager: patches request_with_retry + raise_for_status."""
    resp = _mock_response(json_data=json_data, text=text, status_code=status_code)
    rwr = patch("biodbs.fetch.ClinVar.clinvar_fetcher.request_with_retry", return_value=resp)
    rfs = patch("biodbs.fetch.ClinVar.clinvar_fetcher.raise_for_status")
    return rwr, rfs


# =============================================================================
# Rate limit registration
# =============================================================================

class TestRateLimitRegistration:
    def test_without_api_key_registers_3rps(self):
        from biodbs.fetch._rate_limit import get_rate_limiter
        ClinVar_Fetcher(api_key=None)
        limiter = get_rate_limiter()
        assert limiter._rates.get("eutils.ncbi.nlm.nih.gov", 0) == 3

    def test_with_api_key_registers_10rps(self):
        from biodbs.fetch._rate_limit import get_rate_limiter
        ClinVar_Fetcher(api_key="FAKEKEY")
        limiter = get_rate_limiter()
        assert limiter._rates.get("eutils.ncbi.nlm.nih.gov", 0) == 10

    def test_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("NCBI_API_KEY", "ENVKEY")
        fetcher = ClinVar_Fetcher()
        assert fetcher._api_key == "ENVKEY"

    def test_constructor_key_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("NCBI_API_KEY", "ENVKEY")
        fetcher = ClinVar_Fetcher(api_key="ARGKEY")
        assert fetcher._api_key == "ARGKEY"


# =============================================================================
# Base params
# =============================================================================

class TestBaseParams:
    def test_includes_tool_and_email(self):
        fetcher = ClinVar_Fetcher()
        params = fetcher._base_params()
        assert "tool" in params
        assert "email" in params

    def test_api_key_included_when_set(self):
        fetcher = ClinVar_Fetcher(api_key="MYKEY")
        params = fetcher._base_params()
        assert params["api_key"] == "MYKEY"

    def test_api_key_absent_when_not_set(self):
        fetcher = ClinVar_Fetcher(api_key=None)
        params = fetcher._base_params()
        assert "api_key" not in params


# =============================================================================
# esearch — search()
# =============================================================================

class TestSearch:
    def test_returns_uid_list(self):
        rwr, rfs = _patch_request(esearch_response(["12375", "65533"]))
        with rwr, rfs:
            fetcher = ClinVar_Fetcher()
            result = fetcher.search("TP53[gene]")
        assert result == ["12375", "65533"]

    def test_url_uses_esearch_endpoint(self):
        rwr, rfs = _patch_request(esearch_response([]))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().search("BRCA1[gene]")
        url = mock_req.call_args[0][0]
        assert "esearch.fcgi" in url

    def test_params_include_db_clinvar(self):
        rwr, rfs = _patch_request(esearch_response([]))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().search("BRCA1[gene]")
        params = mock_req.call_args[1]["params"]
        assert params["db"] == "clinvar"

    def test_params_include_retmax(self):
        rwr, rfs = _patch_request(esearch_response([]))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().search("BRCA1[gene]", retmax=100)
        params = mock_req.call_args[1]["params"]
        assert params["retmax"] == 100

    def test_params_include_retmode_json(self):
        rwr, rfs = _patch_request(esearch_response([]))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().search("BRCA1[gene]")
        params = mock_req.call_args[1]["params"]
        assert params["retmode"] == "json"

    def test_empty_result(self):
        rwr, rfs = _patch_request(esearch_response([]))
        with rwr, rfs:
            result = ClinVar_Fetcher().search("nonexistent[gene]")
        assert result == []


# =============================================================================
# esearch — count()
# =============================================================================

class TestCount:
    def test_returns_integer(self):
        rwr, rfs = _patch_request(esearch_response([], count=1234))
        with rwr, rfs:
            n = ClinVar_Fetcher().count("TP53[gene]")
        assert n == 1234

    def test_retmax_is_zero(self):
        rwr, rfs = _patch_request(esearch_response([]))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().count("TP53[gene]")
        params = mock_req.call_args[1]["params"]
        assert params["retmax"] == 0


# =============================================================================
# esummary — fetch_summary()
# =============================================================================

class TestFetchSummary:
    def test_returns_clinvar_fetched_data(self):
        rwr, rfs = _patch_request(esummary_response(TP53_DOC))
        with rwr, rfs:
            data = ClinVar_Fetcher().fetch_summary(["12375"])
        assert isinstance(data, ClinVarFetchedData)
        assert len(data) == 1

    def test_ids_joined_in_params(self):
        rwr, rfs = _patch_request(esummary_response(TP53_DOC, BRCA1_DOC))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().fetch_summary(["12375", "65533"])
        params = mock_req.call_args[1]["params"]
        assert "12375" in params["id"]
        assert "65533" in params["id"]

    def test_retmode_json_in_params(self):
        rwr, rfs = _patch_request(esummary_response(TP53_DOC))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().fetch_summary(["12375"])
        params = mock_req.call_args[1]["params"]
        assert params["retmode"] == "json"

    def test_total_count_propagated(self):
        rwr, rfs = _patch_request(esummary_response(TP53_DOC))
        with rwr, rfs:
            data = ClinVar_Fetcher().fetch_summary(["12375"], total_count=99)
        assert data.total_count == 99

    def test_empty_ids_returns_empty(self):
        fetcher = ClinVar_Fetcher()
        data = fetcher.fetch_summary([])
        assert len(data) == 0

    def test_integer_ids_accepted(self):
        rwr, rfs = _patch_request(esummary_response(TP53_DOC))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().fetch_summary([12375])
        params = mock_req.call_args[1]["params"]
        assert "12375" in params["id"]

    def test_url_uses_esummary_endpoint(self):
        rwr, rfs = _patch_request(esummary_response(TP53_DOC))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().fetch_summary(["12375"])
        url = mock_req.call_args[0][0]
        assert "esummary.fcgi" in url


# =============================================================================
# efetch — fetch_vcv() / fetch_rcv()
# =============================================================================

class TestEfetch:
    def test_fetch_vcv_returns_text(self):
        rwr, rfs = _patch_request(text="<ClinVarResult>xml here</ClinVarResult>")
        with rwr, rfs:
            xml = ClinVar_Fetcher().fetch_vcv("VCV000014206")
        assert "<ClinVarResult>" in xml

    def test_fetch_vcv_rettype_param(self):
        rwr, rfs = _patch_request(text="<xml/>")
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().fetch_vcv("VCV000014206")
        params = mock_req.call_args[1]["params"]
        assert params["rettype"] == "vcv"
        assert params["id"] == "VCV000014206"

    def test_fetch_rcv_rettype_param(self):
        rwr, rfs = _patch_request(text="<xml/>")
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().fetch_rcv("RCV000000606")
        params = mock_req.call_args[1]["params"]
        assert params["rettype"] == "clinvarset"
        assert params["id"] == "RCV000000606"

    def test_both_use_efetch_endpoint(self):
        rwr, rfs = _patch_request(text="<xml/>")
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().fetch_vcv("VCV000014206")
        assert "efetch.fcgi" in mock_req.call_args[0][0]


# =============================================================================
# elink — link_to_pubmed()
# =============================================================================

class TestLinkToPubmed:
    def test_returns_pmid_list(self):
        rwr, rfs = _patch_request(elink_response([28492532, 12375682]))
        with rwr, rfs:
            pmids = ClinVar_Fetcher().link_to_pubmed("12375")
        assert set(pmids) == {"28492532", "12375682"}

    def test_empty_when_no_links(self):
        rwr, rfs = _patch_request(elink_response([]))
        with rwr, rfs:
            pmids = ClinVar_Fetcher().link_to_pubmed("12375")
        assert pmids == []

    def test_url_uses_elink_endpoint(self):
        rwr, rfs = _patch_request(elink_response([]))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().link_to_pubmed("12375")
        assert "elink.fcgi" in mock_req.call_args[0][0]

    def test_params_include_pubmed_db(self):
        rwr, rfs = _patch_request(elink_response([]))
        with rwr as mock_req, rfs:
            ClinVar_Fetcher().link_to_pubmed("12375")
        params = mock_req.call_args[1]["params"]
        assert params["db"] == "pubmed"
        assert params["dbfrom"] == "clinvar"


# =============================================================================
# search_gene() — high-level convenience
# =============================================================================

class TestSearchGene:
    def _make_fetcher_mock(self, uids, total, docs):
        fetcher = ClinVar_Fetcher.__new__(ClinVar_Fetcher)
        fetcher._api_key = None
        fetcher.search = MagicMock(return_value=uids)
        fetcher.count = MagicMock(return_value=total)
        fetcher.fetch_summary = MagicMock(
            return_value=ClinVarFetchedData(esummary_response(*docs), total_count=total)
        )
        return fetcher

    def test_builds_gene_query(self):
        fetcher = self._make_fetcher_mock(["12375"], 1, [TP53_DOC])
        fetcher.search_gene("TP53")
        query = fetcher.search.call_args[0][0]
        assert "TP53[gene]" in query

    def test_single_gene_prop_included_by_default(self):
        fetcher = self._make_fetcher_mock([], 0, [])
        fetcher.search_gene("TP53")
        query = fetcher.search.call_args[0][0]
        assert "single_gene[prop]" in query

    def test_single_gene_prop_excluded(self):
        fetcher = self._make_fetcher_mock([], 0, [])
        fetcher.search_gene("TP53", single_gene=False)
        query = fetcher.search.call_args[0][0]
        assert "single_gene[prop]" not in query

    def test_clinical_significance_filter(self):
        fetcher = self._make_fetcher_mock([], 0, [])
        fetcher.search_gene("TP53", clinical_significance="pathogenic")
        query = fetcher.search.call_args[0][0]
        assert "pathogenic[clnsig]" in query

    def test_returns_clinvar_fetched_data(self):
        fetcher = self._make_fetcher_mock(["12375"], 1, [TP53_DOC])
        result = fetcher.search_gene("TP53")
        assert isinstance(result, ClinVarFetchedData)


# =============================================================================
# search_condition() — high-level convenience
# =============================================================================

class TestSearchCondition:
    def _make_fetcher_mock(self, uids, total, docs):
        fetcher = ClinVar_Fetcher.__new__(ClinVar_Fetcher)
        fetcher._api_key = None
        fetcher.search = MagicMock(return_value=uids)
        fetcher.count = MagicMock(return_value=total)
        fetcher.fetch_summary = MagicMock(
            return_value=ClinVarFetchedData(esummary_response(*docs), total_count=total)
        )
        return fetcher

    def test_builds_disease_query(self):
        fetcher = self._make_fetcher_mock([], 0, [])
        fetcher.search_condition("Lynch syndrome")
        query = fetcher.search.call_args[0][0]
        assert '"Lynch syndrome"[dis]' in query

    def test_clinical_significance_appended(self):
        fetcher = self._make_fetcher_mock([], 0, [])
        fetcher.search_condition("Lynch syndrome", clinical_significance="pathogenic")
        query = fetcher.search.call_args[0][0]
        assert "pathogenic[clnsig]" in query


# =============================================================================
# Convenience functions (module-level singleton)
# =============================================================================

class TestConvenienceFunctions:
    """Each function should delegate to the singleton ClinVar_Fetcher."""

    def _patch_singleton(self, method_name, return_value):
        mock_fetcher = MagicMock()
        getattr(mock_fetcher, method_name).return_value = return_value
        return patch("biodbs.fetch.ClinVar.funcs._get_fetcher", return_value=mock_fetcher)

    def test_clinvar_search(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_search
        with self._patch_singleton("search", ["12375"]) as mock_get:
            result = clinvar_search("TP53[gene]", retmax=50)
        mock_get.return_value.search.assert_called_once_with(
            "TP53[gene]", retmax=50, retstart=0
        )
        assert result == ["12375"]

    def test_clinvar_count(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_count
        with self._patch_singleton("count", 999) as mock_get:
            n = clinvar_count("TP53[gene]")
        mock_get.return_value.count.assert_called_once_with("TP53[gene]")
        assert n == 999

    def test_clinvar_fetch_by_id(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_fetch_by_id
        expected = ClinVarFetchedData(esummary_response(TP53_DOC))
        with self._patch_singleton("fetch_summary", expected) as mock_get:
            result = clinvar_fetch_by_id([12375])
        mock_get.return_value.fetch_summary.assert_called_once_with([12375])
        assert result is expected

    def test_clinvar_search_gene(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_search_gene
        expected = ClinVarFetchedData(esummary_response(TP53_DOC))
        with self._patch_singleton("search_gene", expected) as mock_get:
            result = clinvar_search_gene("TP53", retmax=100,
                                         clinical_significance="pathogenic")
        mock_get.return_value.search_gene.assert_called_once_with(
            "TP53", single_gene=True, retmax=100, clinical_significance="pathogenic"
        )

    def test_clinvar_search_condition(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_search_condition
        expected = ClinVarFetchedData(esummary_response(BRCA1_DOC))
        with self._patch_singleton("search_condition", expected) as mock_get:
            clinvar_search_condition("Lynch syndrome", retmax=200)
        mock_get.return_value.search_condition.assert_called_once_with(
            "Lynch syndrome", retmax=200, clinical_significance=None
        )

    def test_clinvar_fetch_vcv(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_fetch_vcv
        with self._patch_singleton("fetch_vcv", "<xml/>") as mock_get:
            xml = clinvar_fetch_vcv("VCV000014206")
        mock_get.return_value.fetch_vcv.assert_called_once_with("VCV000014206")
        assert xml == "<xml/>"

    def test_clinvar_fetch_rcv(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_fetch_rcv
        with self._patch_singleton("fetch_rcv", "<xml/>") as mock_get:
            xml = clinvar_fetch_rcv("RCV000000606")
        mock_get.return_value.fetch_rcv.assert_called_once_with("RCV000000606")

    def test_clinvar_link_pubmed(self):
        from biodbs.fetch.ClinVar.funcs import clinvar_link_pubmed
        with self._patch_singleton("link_to_pubmed", ["111", "222"]) as mock_get:
            pmids = clinvar_link_pubmed(12375)
        mock_get.return_value.link_to_pubmed.assert_called_once_with(12375)
        assert pmids == ["111", "222"]
