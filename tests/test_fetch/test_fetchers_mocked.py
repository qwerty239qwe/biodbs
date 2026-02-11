"""Tests for fetcher modules with mocked HTTP responses.

Tests cover:
- HTTP 200 success paths for each fetcher
- HTTP error status codes (500, 503, 429, 404) raise appropriate custom exceptions
- Input validation (invalid parameters raise ValueError)
- Special cases (ChEMBL 404 returns empty, KEGG image/json options)
"""

import tempfile

import pytest
from unittest.mock import Mock, patch


from biodbs.exceptions import (
    APIServerError,
    APIRateLimitError,
    APINotFoundError,
    APIValidationError,
    APIError,
)


def _mock_response(
    status_code=200, json_data=None, text="", content=b"", headers=None, url=""
):
    """Create a mock HTTP response."""
    resp = Mock()
    resp.status_code = status_code
    resp.text = text
    resp.content = content
    resp.url = url
    resp.headers = headers or {}
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("No JSON")
    return resp


# =============================================================================
# KEGG Fetcher Tests
# =============================================================================


class TestKEGGFetcherMocked:
    """Test KEGG fetcher with mocked HTTP."""

    @patch("biodbs.utils.fetch.requests")
    def test_get_info_success(self, mock_requests):
        """Test successful info operation returns KEGGFetchedData."""
        mock_requests.get.return_value = _mock_response(
            200, text="kegg db info for pathway..."
        )
        mock_requests.get.return_value.text = "kegg db info for pathway..."

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        result = fetcher.get("info", database="pathway")
        assert result is not None
        assert result.text == "kegg db info for pathway..."

    @patch("biodbs.utils.fetch.requests")
    def test_get_server_error_503(self, mock_requests):
        """Test 503 raises APIServerError."""
        mock_requests.get.return_value = _mock_response(
            503, text="Service Unavailable"
        )

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.get("info", database="pathway")

    @patch("biodbs.utils.fetch.requests")
    def test_get_server_error_500(self, mock_requests):
        """Test 500 raises APIServerError."""
        mock_requests.get.return_value = _mock_response(
            500, text="Internal Server Error"
        )

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.get("info", database="pathway")

    @patch("biodbs.utils.fetch.requests")
    def test_get_rate_limit_error(self, mock_requests):
        """Test 429 raises APIRateLimitError."""
        mock_requests.get.return_value = _mock_response(
            429, text="Too Many Requests"
        )

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(APIRateLimitError):
            fetcher.get("info", database="pathway")

    @patch("biodbs.utils.fetch.requests")
    def test_get_not_found_error(self, mock_requests):
        """Test 404 raises APINotFoundError."""
        mock_requests.get.return_value = _mock_response(404, text="Not Found")

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(APINotFoundError):
            fetcher.get("info", database="pathway")

    @patch("biodbs.utils.fetch.requests")
    def test_get_json_option(self, mock_requests):
        """Test get with json option parses JSON."""
        mock_requests.get.return_value = _mock_response(
            200, json_data={"name": "hsa05200"}
        )

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        result = fetcher.get("get", dbentries=["hsa:7157"], get_option="json")
        assert result is not None

    @patch("biodbs.utils.fetch.requests")
    def test_get_image_option(self, mock_requests):
        """Test get with image option uses response.content (binary)."""
        mock_requests.get.return_value = _mock_response(
            200, content=b"\x89PNG\r\n"
        )

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        result = fetcher.get(
            "get", dbentries=["hsa05200"], get_option="image"
        )
        assert result is not None

    @patch("biodbs.utils.fetch.requests")
    def test_get_text_default(self, mock_requests):
        """Test get without option uses response.text."""
        mock_requests.get.return_value = _mock_response(
            200, text="ENTRY  hsa:7157\nNAME  TP53\n"
        )
        mock_requests.get.return_value.text = "ENTRY  hsa:7157\nNAME  TP53\n"

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        result = fetcher.get("get", dbentries=["hsa:7157"])
        assert result is not None
        assert "TP53" in result.text

    @patch("biodbs.utils.fetch.requests")
    def test_get_list_operation(self, mock_requests):
        """Test list operation."""
        mock_requests.get.return_value = _mock_response(
            200,
            text="hsa:10458\tBCAM\nhsa:7157\tTP53\n",
        )
        mock_requests.get.return_value.text = (
            "hsa:10458\tBCAM\nhsa:7157\tTP53\n"
        )

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        result = fetcher.get("list", database="pathway", organism="hsa")
        assert result is not None

    @patch("biodbs.utils.fetch.requests")
    def test_get_find_operation(self, mock_requests):
        """Test find operation."""
        mock_requests.get.return_value = _mock_response(
            200, text="hsa:7157\tTP53\n"
        )
        mock_requests.get.return_value.text = "hsa:7157\tTP53\n"

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        result = fetcher.get("find", database="genes", query="tp53")
        assert result is not None

    @patch("biodbs.utils.fetch.requests")
    def test_get_client_error_raises_api_error(self, mock_requests):
        """Test non-standard HTTP error (e.g. 403) raises APIError."""
        mock_requests.get.return_value = _mock_response(
            403, text="Forbidden"
        )

        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(APIError):
            fetcher.get("info", database="pathway")


class TestKEGGFetcherValidation:
    """Test KEGG fetcher input validation."""

    def test_invalid_operation_raises(self):
        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get("invalid_op", database="pathway")

    def test_get_all_invalid_operation(self):
        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get_all("info", dbentries=["hsa:7157"])

    def test_get_all_empty_entries(self):
        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        result = fetcher.get_all("get", dbentries=[])
        assert result is not None
        # Empty entries should return an empty result
        assert result.text == ""

    def test_info_missing_database(self):
        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get("info")

    def test_find_missing_query(self):
        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get("find", database="genes")

    def test_get_missing_dbentries(self):
        from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

        fetcher = KEGG_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get("get")


# =============================================================================
# ChEMBL Fetcher Tests
# =============================================================================


class TestChEMBLFetcherMocked:
    """Test ChEMBL fetcher with mocked HTTP."""

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_molecule_success(self, mock_requests):
        """Test successful molecule lookup."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={
                "molecule_chembl_id": "CHEMBL25",
                "pref_name": "ASPIRIN",
                "max_phase": 4,
            },
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        result = fetcher.get(resource="molecule", chembl_id="CHEMBL25")
        assert result is not None

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_404_returns_empty(self, mock_requests):
        """Test 404 returns empty result, not exception."""
        mock_requests.get.return_value = _mock_response(404, text="Not Found")

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        result = fetcher.get(resource="molecule", chembl_id="CHEMBL99999999")
        assert len(result.results) == 0

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_server_error_500(self, mock_requests):
        """Test 500 raises APIServerError."""
        mock_requests.get.return_value = _mock_response(
            500, text="Internal Server Error"
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.get(resource="molecule", chembl_id="CHEMBL25")

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_server_error_502(self, mock_requests):
        """Test 502 raises APIServerError."""
        mock_requests.get.return_value = _mock_response(
            502, text="Bad Gateway"
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.get(resource="molecule", chembl_id="CHEMBL25")

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_rate_limit_error(self, mock_requests):
        """Test 429 raises APIRateLimitError."""
        mock_requests.get.return_value = _mock_response(
            429, text="Too Many Requests"
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(APIRateLimitError):
            fetcher.get(resource="molecule", chembl_id="CHEMBL25")

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_search(self, mock_requests):
        """Test search returns results."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={
                "molecules": [
                    {"molecule_chembl_id": "CHEMBL25", "pref_name": "ASPIRIN"}
                ]
            },
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        result = fetcher.get(
            resource="molecule", search_query="aspirin", limit=5
        )
        assert result is not None

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_with_filters(self, mock_requests):
        """Test filtered query."""
        mock_requests.get.return_value = _mock_response(
            200, json_data={"activities": []}
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        result = fetcher.get(
            resource="activity",
            filters={"target_chembl_id": "CHEMBL240"},
            limit=10,
        )
        assert result is not None

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_fetch_page_success(self, mock_requests):
        """Test _fetch_page returns ChEMBLFetchedData on 200."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={
                "molecules": [
                    {"molecule_chembl_id": "CHEMBL25", "pref_name": "ASPIRIN"}
                ]
            },
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        result = fetcher._fetch_page(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            {"limit": 1},
            "molecule",
        )
        assert result is not None

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_fetch_page_error(self, mock_requests):
        """Test _fetch_page raises on non-200."""
        mock_requests.get.return_value = _mock_response(
            502, text="Bad Gateway"
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(APIServerError):
            fetcher._fetch_page(
                "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
                {},
                "molecule",
            )

    @patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests")
    def test_get_validation_error(self, mock_requests):
        """Test 400 raises APIValidationError."""
        mock_requests.get.return_value = _mock_response(
            400, text="Bad Request: invalid query"
        )

        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(APIValidationError):
            fetcher._fetch_page(
                "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
                {},
                "molecule",
            )


class TestChEMBLFetcherValidation:
    """Test ChEMBL fetcher input validation."""

    def test_invalid_resource_raises(self):
        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get(resource="invalid_resource")

    def test_invalid_chembl_id_raises(self):
        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get(resource="molecule", chembl_id="NOT_VALID")

    def test_chembl_id_must_start_with_chembl(self):
        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get(resource="molecule", chembl_id="12345")

    def test_limit_out_of_range(self):
        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get(resource="molecule", limit=2000)

    def test_negative_offset(self):
        from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

        fetcher = ChEMBL_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get(resource="molecule", offset=-1)


# =============================================================================
# FDA Fetcher Tests
# =============================================================================


class TestFDAFetcherMocked:
    """Test FDA fetcher with mocked HTTP."""

    @pytest.fixture(autouse=True)
    def _tmp_storage(self, tmp_path):
        self._storage_path = str(tmp_path)

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_get_success(self, mock_requests):
        """Test successful drug event query."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={
                "meta": {"results": {"total": 1}},
                "results": [{"receivedate": "20200101"}],
            },
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        result = fetcher.get(
            category="drug",
            endpoint="event",
            search={"patient.drug.medicinalproduct": "aspirin"},
            limit=1,
        )
        assert result is not None
        assert len(result.results) == 1

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_get_server_error_503(self, mock_requests):
        """Test 503 raises APIServerError."""
        mock_requests.get.return_value = _mock_response(
            503, text="Service Unavailable"
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(APIServerError):
            fetcher.get(
                category="drug",
                endpoint="event",
                search={"patient.drug.medicinalproduct": "aspirin"},
                limit=1,
            )

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_get_server_error_500(self, mock_requests):
        """Test 500 raises APIServerError."""
        mock_requests.get.return_value = _mock_response(
            500, text="Internal Server Error"
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(APIServerError):
            fetcher.get(
                category="drug",
                endpoint="event",
                search={"patient.drug.medicinalproduct": "aspirin"},
                limit=1,
            )

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_get_rate_limit(self, mock_requests):
        """Test 429 raises APIRateLimitError with retry_after."""
        mock_requests.get.return_value = _mock_response(
            429,
            text="Too Many Requests",
            headers={"Retry-After": "60"},
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(APIRateLimitError) as exc_info:
            fetcher.get(
                category="drug",
                endpoint="event",
                search={"patient.drug.medicinalproduct": "aspirin"},
                limit=1,
            )
        assert exc_info.value.retry_after == 60.0

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_get_not_found(self, mock_requests):
        """Test 404 raises APINotFoundError."""
        mock_requests.get.return_value = _mock_response(
            404, text="Not Found"
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(APINotFoundError):
            fetcher.get(
                category="drug",
                endpoint="event",
                search={"patient.drug.medicinalproduct": "aspirin"},
                limit=1,
            )

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_fetch_page_success(self, mock_requests):
        """Test _fetch_page returns FDAFetchedData on 200."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={
                "meta": {"results": {"total": 1}},
                "results": [{"id": 1}],
            },
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        result = fetcher._fetch_page(
            "https://api.fda.gov/drug/event.json", limit=1
        )
        assert result is not None

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_fetch_page_error(self, mock_requests):
        """Test _fetch_page raises on non-200."""
        mock_requests.get.return_value = _mock_response(500, text="Error")

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(APIServerError):
            fetcher._fetch_page(
                "https://api.fda.gov/drug/event.json", limit=1
            )

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_get_multiple_results(self, mock_requests):
        """Test response with multiple results."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={
                "meta": {"results": {"total": 3}},
                "results": [
                    {"receivedate": "20200101"},
                    {"receivedate": "20200201"},
                    {"receivedate": "20200301"},
                ],
            },
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        result = fetcher.get(
            category="drug",
            endpoint="event",
            search={"patient.drug.medicinalproduct": "aspirin"},
            limit=3,
        )
        assert len(result.results) == 3

    @patch("biodbs.fetch.FDA.fda_fetcher.requests")
    def test_get_client_error_raises_api_error(self, mock_requests):
        """Test non-standard client error raises APIError."""
        mock_requests.get.return_value = _mock_response(
            403, text="Forbidden"
        )

        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(APIError):
            fetcher.get(
                category="drug",
                endpoint="event",
                search={"patient.drug.medicinalproduct": "aspirin"},
                limit=1,
            )


class TestFDAFetcherValidation:
    """Test FDA fetcher input validation."""

    @pytest.fixture(autouse=True)
    def _tmp_storage(self, tmp_path):
        self._storage_path = str(tmp_path)

    def test_invalid_category_raises(self):
        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(ValueError):
            fetcher.get(
                category="invalid",
                endpoint="event",
                search={"patient.drug.medicinalproduct": "aspirin"},
            )

    def test_invalid_endpoint_raises(self):
        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(ValueError):
            fetcher.get(
                category="drug",
                endpoint="nonexistent",
                search={"patient.drug.medicinalproduct": "aspirin"},
            )

    def test_get_all_batch_size_too_large(self):
        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(ValueError):
            fetcher.get_all(
                category="drug", endpoint="event", batch_size=1001
            )

    def test_get_all_invalid_method(self):
        from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

        fetcher = FDA_Fetcher(storage_path=self._storage_path)
        with pytest.raises(ValueError):
            fetcher.get_all(
                category="drug",
                endpoint="event",
                method="invalid",
                search={"patient.drug.medicinalproduct": "aspirin"},
            )


# =============================================================================
# Ensembl Fetcher Tests
# =============================================================================


class TestEnsemblFetcherMocked:
    """Test Ensembl fetcher with mocked HTTP."""

    @patch("biodbs.fetch.ensembl.ensembl_fetcher.requests")
    def test_get_lookup_success(self, mock_requests):
        """Test successful gene lookup."""
        mock_resp = _mock_response(
            200,
            json_data={
                "id": "ENSG00000141510",
                "display_name": "TP53",
                "biotype": "protein_coding",
            },
        )
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp

        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher

        fetcher = Ensembl_Fetcher()
        result = fetcher.get(
            endpoint="lookup/id", id="ENSG00000141510"
        )
        assert result is not None

    @patch("biodbs.fetch.ensembl.ensembl_fetcher.requests")
    def test_get_404_returns_empty(self, mock_requests):
        """Test 404 returns empty result for Ensembl."""
        mock_resp = _mock_response(404, text="Not Found")
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp

        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher

        fetcher = Ensembl_Fetcher()
        result = fetcher.get(
            endpoint="lookup/id", id="ENSG00000000000"
        )
        assert result is not None
        # 404 returns EnsemblFetchedData({}) which wraps empty dict as single result
        assert result.results == [{}]

    @patch("biodbs.fetch.ensembl.ensembl_fetcher.requests")
    def test_get_400_raises_validation_error(self, mock_requests):
        """Test 400 raises APIValidationError for Ensembl."""
        mock_resp = _mock_response(
            400, text="Bad Request: invalid identifier"
        )
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp

        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher

        fetcher = Ensembl_Fetcher()
        with pytest.raises(APIValidationError):
            fetcher.get(endpoint="lookup/id", id="ENSG00000141510")

    @patch("biodbs.fetch.ensembl.ensembl_fetcher.requests")
    def test_get_server_error(self, mock_requests):
        """Test 500 raises APIServerError."""
        mock_resp = _mock_response(500, text="Internal Server Error")
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp

        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher

        fetcher = Ensembl_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.get(endpoint="lookup/id", id="ENSG00000141510")

    @patch("biodbs.fetch.ensembl.ensembl_fetcher.requests")
    def test_get_rate_limit_error(self, mock_requests):
        """Test 429 raises APIRateLimitError."""
        mock_resp = _mock_response(429, text="Too Many Requests")
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp

        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher

        fetcher = Ensembl_Fetcher()
        with pytest.raises(APIRateLimitError):
            fetcher.get(endpoint="lookup/id", id="ENSG00000141510")

    @patch("biodbs.fetch.ensembl.ensembl_fetcher.requests")
    def test_get_fasta_content_type(self, mock_requests):
        """Test fasta content type returns text-based result."""
        mock_resp = _mock_response(
            200, text=">ENST00000269305\nATGGAGGAGCCGCAGTCAG"
        )
        mock_resp.text = ">ENST00000269305\nATGGAGGAGCCGCAGTCAG"
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp

        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher

        fetcher = Ensembl_Fetcher()
        result = fetcher.get(
            endpoint="sequence/id",
            id="ENST00000269305",
            content_type="fasta",
        )
        assert result is not None


class TestEnsemblFetcherValidation:
    """Test Ensembl fetcher input validation."""

    def test_invalid_endpoint_raises(self):
        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher

        fetcher = Ensembl_Fetcher()
        with pytest.raises(ValueError):
            fetcher.get(endpoint="invalid/endpoint", id="ENSG00000141510")


# =============================================================================
# EnrichR Fetcher Tests
# =============================================================================


class TestEnrichRFetcherMocked:
    """Test EnrichR fetcher with mocked HTTP."""

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_enrich_success(self, mock_requests):
        """Test successful enrichment analysis (two-step: addList + enrich)."""
        # First call: addList POST
        add_list_resp = _mock_response(
            200,
            json_data={"userListId": 12345, "shortId": "abc"},
        )
        # Second call: enrich GET
        enrich_resp = _mock_response(
            200,
            json_data={
                "KEGG_2021_Human": [
                    [1, "Pathways in cancer", 0.001, 5, 100, [], 0.01, 0.005, ["TP53", "BRCA1"]],
                ]
            },
        )

        mock_requests.post.return_value = add_list_resp
        mock_requests.get.return_value = enrich_resp

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        result = fetcher.enrich(
            genes=["TP53", "BRCA1", "EGFR"],
            library="KEGG_2021_Human",
        )
        assert result is not None

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_add_list_failure(self, mock_requests):
        """Test addList POST failure raises error."""
        mock_requests.post.return_value = _mock_response(
            500, text="Internal Server Error"
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.enrich(
                genes=["TP53", "BRCA1"],
                library="KEGG_2021_Human",
            )

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_enrich_rate_limit(self, mock_requests):
        """Test rate limit during addList."""
        mock_requests.post.return_value = _mock_response(
            429, text="Too Many Requests"
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        with pytest.raises(APIRateLimitError):
            fetcher.enrich(
                genes=["TP53", "BRCA1"],
                library="KEGG_2021_Human",
            )

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_get_libraries_success(self, mock_requests):
        """Test getting available libraries."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={
                "statistics": [
                    {"libraryName": "KEGG_2021_Human", "numTerms": 320},
                    {"libraryName": "GO_Biological_Process_2023", "numTerms": 15000},
                ]
            },
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        result = fetcher.get_libraries()
        assert result is not None

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_get_libraries_server_error(self, mock_requests):
        """Test libraries endpoint server error."""
        mock_requests.get.return_value = _mock_response(
            503, text="Service Unavailable"
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.get_libraries()

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_enrich_step2_failure(self, mock_requests):
        """Test enrich GET failure after successful addList."""
        # addList succeeds
        mock_requests.post.return_value = _mock_response(
            200,
            json_data={"userListId": 12345, "shortId": "abc"},
        )
        # enrich fails
        mock_requests.get.return_value = _mock_response(
            500, text="Internal Server Error"
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        with pytest.raises(APIServerError):
            fetcher.enrich(
                genes=["TP53", "BRCA1"],
                library="KEGG_2021_Human",
            )

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_view_gene_list_success(self, mock_requests):
        """Test viewing a previously submitted gene list."""
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={"genes": ["TP53", "BRCA1", "EGFR"]},
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        result = fetcher.view_gene_list(user_list_id=12345)
        assert result == ["TP53", "BRCA1", "EGFR"]

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_view_gene_list_error(self, mock_requests):
        """Test view gene list error."""
        mock_requests.get.return_value = _mock_response(
            404, text="Not Found"
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        with pytest.raises(APINotFoundError):
            fetcher.view_gene_list(user_list_id=99999)

    @patch("biodbs.fetch.EnrichR.enrichr_fetcher.requests")
    def test_enrich_multiple_libraries(self, mock_requests):
        """Test enrichment against multiple libraries."""
        # addList POST
        mock_requests.post.return_value = _mock_response(
            200,
            json_data={"userListId": 12345, "shortId": "abc"},
        )
        # enrich GET (called for each library)
        mock_requests.get.return_value = _mock_response(
            200,
            json_data={},
        )

        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher()
        result = fetcher.enrich_multiple(
            genes=["TP53", "BRCA1"],
            libraries=["KEGG_2021_Human", "GO_Biological_Process_2023"],
        )
        assert isinstance(result, dict)
        assert len(result) == 2

    def test_set_organism(self):
        """Test changing organism updates base URL."""
        from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

        fetcher = EnrichR_Fetcher(organism="human")
        fetcher.set_organism("fly")
        assert fetcher._organism == "fly"


# =============================================================================
# Cross-cutting error handling tests
# =============================================================================


class TestRaiseForStatus:
    """Test the raise_for_status helper directly."""

    def test_200_no_exception(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(200, text="OK")
        raise_for_status(resp, "TestService")  # Should not raise

    def test_429_rate_limit(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(
            429, text="Slow down", headers={"Retry-After": "30"}
        )
        with pytest.raises(APIRateLimitError) as exc_info:
            raise_for_status(resp, "TestService")
        assert exc_info.value.retry_after == 30.0

    def test_429_no_retry_after(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(429, text="Slow down")
        with pytest.raises(APIRateLimitError) as exc_info:
            raise_for_status(resp, "TestService")
        assert exc_info.value.retry_after is None

    def test_404_not_found(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(404, text="Not Found")
        with pytest.raises(APINotFoundError):
            raise_for_status(resp, "TestService")

    def test_400_validation(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(400, text="Bad Request")
        with pytest.raises(APIValidationError):
            raise_for_status(resp, "TestService")

    def test_500_server_error(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(500, text="Server Error")
        with pytest.raises(APIServerError):
            raise_for_status(resp, "TestService")

    def test_503_server_error(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(503, text="Service Unavailable")
        with pytest.raises(APIServerError):
            raise_for_status(resp, "TestService")

    def test_401_other_error(self):
        from biodbs.exceptions import raise_for_status

        resp = _mock_response(401, text="Unauthorized")
        with pytest.raises(APIError) as exc_info:
            raise_for_status(resp, "TestService")
        assert exc_info.value.status_code == 401

    def test_long_response_truncated(self):
        from biodbs.exceptions import raise_for_status

        long_text = "x" * 1000
        resp = _mock_response(500, text=long_text)
        with pytest.raises(APIServerError):
            raise_for_status(resp, "TestService")
