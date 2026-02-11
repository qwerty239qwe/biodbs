"""Tests for biodbs.exceptions module."""

import pytest
from unittest.mock import Mock

from biodbs.exceptions import (
    BiodBSError,
    APIError,
    APIServerError,
    APIRateLimitError,
    APINotFoundError,
    APITimeoutError,
    APIValidationError,
    IDTranslationError,
    raise_for_status,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy and inheritance."""

    def test_biodbs_error_is_exception(self):
        assert issubclass(BiodBSError, Exception)

    def test_api_error_is_biodbs_error(self):
        assert issubclass(APIError, BiodBSError)

    def test_api_server_error_is_api_error(self):
        assert issubclass(APIServerError, APIError)

    def test_api_rate_limit_error_is_api_error(self):
        assert issubclass(APIRateLimitError, APIError)

    def test_api_not_found_error_is_api_error(self):
        assert issubclass(APINotFoundError, APIError)

    def test_api_timeout_error_is_api_error(self):
        assert issubclass(APITimeoutError, APIError)

    def test_api_validation_error_is_api_error(self):
        assert issubclass(APIValidationError, APIError)

    def test_id_translation_error_is_biodbs_error(self):
        assert issubclass(IDTranslationError, BiodBSError)

    def test_id_translation_error_not_api_error(self):
        assert not issubclass(IDTranslationError, APIError)

    def test_catch_api_error_catches_server_error(self):
        with pytest.raises(APIError):
            raise APIServerError("ChEMBL", 503)

    def test_catch_biodbs_catches_all(self):
        with pytest.raises(BiodBSError):
            raise APIServerError("ChEMBL", 503)
        with pytest.raises(BiodBSError):
            raise IDTranslationError("failed")


class TestAPIError:
    """Test APIError base class."""

    def test_basic_creation(self):
        e = APIError("test message", service="Test")
        assert str(e) == "test message"
        assert e.service == "Test"
        assert e.status_code is None
        assert e.url == ""

    def test_with_all_fields(self):
        e = APIError(
            "error",
            service="ChEMBL",
            status_code=403,
            url="https://example.com",
        )
        assert e.service == "ChEMBL"
        assert e.status_code == 403
        assert e.url == "https://example.com"


class TestAPIServerError:
    """Test APIServerError."""

    def test_message_format(self):
        e = APIServerError("ChEMBL", 503)
        msg = str(e)
        assert "ChEMBL" in msg
        assert "503" in msg
        assert "server-side issue" in msg
        assert "try again later" in msg

    def test_attributes(self):
        e = APIServerError("KEGG", 500, url="https://rest.kegg.jp/get/hsa:7157")
        assert e.service == "KEGG"
        assert e.status_code == 500
        assert "kegg.jp" in e.url

    def test_with_response_text(self):
        e = APIServerError("Ensembl", 502, response_text="Bad Gateway")
        assert e.response_text == "Bad Gateway"

    def test_url_in_message(self):
        e = APIServerError("KEGG", 503, url="https://rest.kegg.jp")
        assert "https://rest.kegg.jp" in str(e)


class TestAPIRateLimitError:
    """Test APIRateLimitError."""

    def test_message_without_retry(self):
        e = APIRateLimitError("EnrichR")
        assert "Rate limit exceeded" in str(e)
        assert "EnrichR" in str(e)
        assert e.retry_after is None
        assert e.status_code == 429

    def test_message_with_retry_after(self):
        e = APIRateLimitError("NCBI", retry_after=30.0)
        assert "30" in str(e)
        assert e.retry_after == 30.0

    def test_url_in_message(self):
        e = APIRateLimitError("FDA", url="https://api.fda.gov")
        assert "fda.gov" in str(e)


class TestAPINotFoundError:
    """Test APINotFoundError."""

    def test_basic(self):
        e = APINotFoundError("PubChem")
        assert "not found" in str(e).lower()
        assert "PubChem" in str(e)
        assert e.status_code == 404

    def test_with_detail(self):
        e = APINotFoundError("ChEMBL", detail="CHEMBL99999999 does not exist")
        assert "CHEMBL99999999" in str(e)


class TestAPITimeoutError:
    """Test APITimeoutError."""

    def test_basic(self):
        e = APITimeoutError("Ensembl")
        assert "timed out" in str(e).lower()
        assert "Ensembl" in str(e)
        assert e.status_code is None

    def test_with_timeout_value(self):
        e = APITimeoutError("BioMart", timeout=120.0)
        assert "120" in str(e)
        assert e.timeout == 120.0


class TestAPIValidationError:
    """Test APIValidationError."""

    def test_basic(self):
        e = APIValidationError("Ensembl")
        assert "Invalid request" in str(e)
        assert e.status_code == 400

    def test_with_detail(self):
        e = APIValidationError("Ensembl", detail="Missing required parameter: species")
        assert "Missing required parameter" in str(e)


class TestIDTranslationError:
    """Test IDTranslationError."""

    def test_basic(self):
        e = IDTranslationError("Could not translate IDs")
        assert str(e) == "Could not translate IDs"

    def test_with_attributes(self):
        e = IDTranslationError(
            "Failed to translate 3 IDs",
            source_db="Ensembl",
            target_db="NCBI",
            failed_ids=["ENSG001", "ENSG002", "ENSG003"],
        )
        assert e.source_db == "Ensembl"
        assert e.target_db == "NCBI"
        assert len(e.failed_ids) == 3

    def test_defaults(self):
        e = IDTranslationError("error")
        assert e.source_db == ""
        assert e.target_db == ""
        assert e.failed_ids == []


class TestRaiseForStatus:
    """Test raise_for_status helper function."""

    def _mock_response(self, status_code, text="", headers=None, url=""):
        resp = Mock()
        resp.status_code = status_code
        resp.text = text
        resp.url = url
        resp.headers = headers or {}
        return resp

    def test_200_does_not_raise(self):
        resp = self._mock_response(200)
        raise_for_status(resp, "Test")  # Should not raise

    def test_201_does_not_raise(self):
        resp = self._mock_response(201)
        raise_for_status(resp, "Test")

    def test_429_raises_rate_limit(self):
        resp = self._mock_response(429, text="Too many requests")
        with pytest.raises(APIRateLimitError) as exc_info:
            raise_for_status(resp, "KEGG")
        assert exc_info.value.service == "KEGG"

    def test_429_with_retry_after_header(self):
        resp = self._mock_response(
            429, headers={"Retry-After": "60"}
        )
        with pytest.raises(APIRateLimitError) as exc_info:
            raise_for_status(resp, "Test")
        assert exc_info.value.retry_after == 60.0

    def test_429_with_invalid_retry_after(self):
        resp = self._mock_response(
            429, headers={"Retry-After": "not-a-number"}
        )
        with pytest.raises(APIRateLimitError) as exc_info:
            raise_for_status(resp, "Test")
        assert exc_info.value.retry_after is None

    def test_404_raises_not_found(self):
        resp = self._mock_response(404, text="Not Found")
        with pytest.raises(APINotFoundError) as exc_info:
            raise_for_status(resp, "ChEMBL")
        assert exc_info.value.status_code == 404

    def test_400_raises_validation(self):
        resp = self._mock_response(400, text="Bad Request")
        with pytest.raises(APIValidationError):
            raise_for_status(resp, "Ensembl")

    def test_500_raises_server_error(self):
        resp = self._mock_response(500, text="Internal Server Error")
        with pytest.raises(APIServerError) as exc_info:
            raise_for_status(resp, "Reactome")
        assert exc_info.value.status_code == 500

    def test_502_raises_server_error(self):
        resp = self._mock_response(502, text="Bad Gateway")
        with pytest.raises(APIServerError):
            raise_for_status(resp, "BioMart")

    def test_503_raises_server_error(self):
        resp = self._mock_response(503, text="Service Unavailable")
        with pytest.raises(APIServerError) as exc_info:
            raise_for_status(resp, "ChEMBL")
        assert exc_info.value.status_code == 503

    def test_other_client_error_raises_api_error(self):
        resp = self._mock_response(403, text="Forbidden")
        with pytest.raises(APIError) as exc_info:
            raise_for_status(resp, "FDA")
        assert exc_info.value.status_code == 403

    def test_url_from_response(self):
        resp = self._mock_response(500, url="https://api.example.com/test")
        with pytest.raises(APIServerError) as exc_info:
            raise_for_status(resp, "Test")
        assert exc_info.value.url == "https://api.example.com/test"

    def test_url_override(self):
        resp = self._mock_response(500, url="https://wrong.com")
        with pytest.raises(APIServerError) as exc_info:
            raise_for_status(resp, "Test", url="https://correct.com")
        assert exc_info.value.url == "https://correct.com"

    def test_long_response_text_truncated(self):
        long_text = "x" * 1000
        resp = self._mock_response(500, text=long_text)
        with pytest.raises(APIServerError) as exc_info:
            raise_for_status(resp, "Test")
        assert len(exc_info.value.response_text) <= 503  # 500 + "..."


class TestExceptionsImportFromTop:
    """Test that exceptions are importable from biodbs top level."""

    def test_import_from_biodbs(self):
        from biodbs import (
            BiodBSError,
            APIError,
            APIServerError,
            APIRateLimitError,
            APINotFoundError,
            APITimeoutError,
            APIValidationError,
            IDTranslationError,
        )
        assert BiodBSError is not None
        assert issubclass(APIServerError, APIError)
