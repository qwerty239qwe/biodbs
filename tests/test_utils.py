import asyncio
import io
import os
import zipfile
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock, AsyncMock

import pytest

from biodbs.utils import get_rsp, save_image_from_rsp, fetch_and_extract, async_get_resps


# ---------------------------------------------------------------------------
# TestGetRsp
# ---------------------------------------------------------------------------
class TestGetRsp:
    """Tests for the get_rsp helper function."""

    @patch("biodbs.utils.fetch.requests")
    def test_successful_200_response(self, mock_requests):
        """Mock requests.get returns a 200 response object."""
        mock_rsp = Mock()
        mock_rsp.status_code = 200
        mock_requests.get.return_value = mock_rsp

        result = get_rsp("http://example.com/api")

        mock_requests.get.assert_called_once_with("http://example.com/api", params=None)
        assert result is mock_rsp

    @patch("biodbs.utils.fetch.requests")
    def test_safe_check_true_non_200_raises(self, mock_requests):
        """safe_check=True (default) with non-200 status raises AssertionError."""
        mock_rsp = Mock()
        mock_rsp.status_code = 404
        mock_requests.get.return_value = mock_rsp

        with pytest.raises(AssertionError, match="404"):
            get_rsp("http://example.com/api", safe_check=True)

    @patch("biodbs.utils.fetch.requests")
    def test_safe_check_false_non_200_returns_response(self, mock_requests):
        """safe_check=False with non-200 returns the response without assertion."""
        mock_rsp = Mock()
        mock_rsp.status_code = 500
        mock_requests.get.return_value = mock_rsp

        result = get_rsp("http://example.com/api", safe_check=False)

        assert result is mock_rsp
        assert result.status_code == 500

    @patch("biodbs.utils.fetch.requests")
    def test_method_post_calls_requests_post(self, mock_requests):
        """method='post' delegates to requests.post."""
        mock_rsp = Mock()
        mock_rsp.status_code = 200
        mock_requests.post.return_value = mock_rsp

        result = get_rsp("http://example.com/api", method="post")

        mock_requests.post.assert_called_once_with("http://example.com/api", params=None)
        assert result is mock_rsp

    @patch("biodbs.utils.fetch.requests")
    def test_query_params_passed_through(self, mock_requests):
        """Query parameters are forwarded to the underlying request."""
        mock_rsp = Mock()
        mock_rsp.status_code = 200
        mock_requests.get.return_value = mock_rsp
        query = {"gene": "TP53", "format": "json"}

        result = get_rsp("http://example.com/api", params=query)

        mock_requests.get.assert_called_once_with(
            "http://example.com/api", params=query
        )
        assert result is mock_rsp

    @patch("biodbs.utils.fetch.requests")
    def test_kwargs_forwarded(self, mock_requests):
        """Extra keyword arguments (e.g. headers, timeout) are forwarded."""
        mock_rsp = Mock()
        mock_rsp.status_code = 200
        mock_requests.get.return_value = mock_rsp
        headers = {"Authorization": "Bearer token123"}

        result = get_rsp("http://example.com/api", headers=headers, timeout=30)

        mock_requests.get.assert_called_once_with(
            "http://example.com/api", params=None, headers=headers, timeout=30
        )
        assert result is mock_rsp


# ---------------------------------------------------------------------------
# TestSaveImageFromRsp
# ---------------------------------------------------------------------------
class TestSaveImageFromRsp:
    """Tests for save_image_from_rsp."""

    def test_file_written_correctly(self, tmp_path):
        """The response raw content is written to the target file."""
        image_bytes = b"\x89PNG\r\n\x1a\nfake_image_data_1234567890"
        mock_respond = Mock()
        mock_respond.raw = io.BytesIO(image_bytes)

        file_name = str(tmp_path / "output.png")
        save_image_from_rsp(mock_respond, file_name)

        with open(file_name, "rb") as f:
            written = f.read()
        assert written == image_bytes

    def test_decode_content_set_to_true(self, tmp_path):
        """decode_content is set to True on the response raw object."""
        mock_raw = Mock()
        # copyfileobj needs a real read method; use a BytesIO for the read side
        mock_raw.read = io.BytesIO(b"data").read
        mock_respond = Mock()
        mock_respond.raw = mock_raw

        file_name = str(tmp_path / "output.png")
        save_image_from_rsp(mock_respond, file_name)

        # After the call, decode_content should have been set to True
        assert mock_respond.raw.decode_content is True


# ---------------------------------------------------------------------------
# TestFetchAndExtract
# ---------------------------------------------------------------------------
class TestFetchAndExtract:
    """Tests for fetch_and_extract."""

    @staticmethod
    def _make_zip_bytes(file_name: str, file_content: bytes) -> bytes:
        """Create an in-memory zip archive containing a single file."""
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(file_name, file_content)
        return buf.getvalue()

    @patch("biodbs.utils.fetch.requests.get")
    def test_zip_extracted_to_saved_path(self, mock_get, tmp_path):
        """A zip downloaded from the URL is extracted into saved_path."""
        inner_name = "hello.txt"
        inner_content = b"Hello, biodbs!"
        zip_bytes = self._make_zip_bytes(inner_name, inner_content)

        mock_rsp = Mock()
        mock_rsp.content = zip_bytes
        mock_get.return_value = mock_rsp

        saved_path = str(tmp_path / "extracted")
        os.makedirs(saved_path, exist_ok=True)

        fetch_and_extract("http://example.com/data.zip", saved_path)

        mock_get.assert_called_once_with("http://example.com/data.zip", stream=True)

        extracted_file = os.path.join(saved_path, inner_name)
        assert os.path.isfile(extracted_file)
        with open(extracted_file, "rb") as f:
            assert f.read() == inner_content

    @patch("biodbs.utils.fetch.requests.get")
    def test_zip_multiple_files_extracted(self, mock_get, tmp_path):
        """A zip with multiple files is fully extracted."""
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("a.txt", "aaa")
            zf.writestr("subdir/b.txt", "bbb")

        mock_rsp = Mock()
        mock_rsp.content = buf.getvalue()
        mock_get.return_value = mock_rsp

        saved_path = str(tmp_path / "out")
        os.makedirs(saved_path, exist_ok=True)

        fetch_and_extract("http://example.com/multi.zip", saved_path)

        assert os.path.isfile(os.path.join(saved_path, "a.txt"))
        assert os.path.isfile(os.path.join(saved_path, "subdir", "b.txt"))


# ---------------------------------------------------------------------------
# TestAsyncGetResps
# ---------------------------------------------------------------------------
class TestAsyncGetResps:
    """Tests for async_get_resps (and indirectly fetch_resp)."""

    @staticmethod
    def _make_mock_session(json_responses):
        """Build an AsyncMock ClientSession whose request() returns the given
        JSON payloads in order.

        Parameters
        ----------
        json_responses : list[dict]
            Each element is the dict that resp.json() should resolve to.

        Returns
        -------
        AsyncMock
            A mock that can be used as ``aiohttp.ClientSession``.
        """
        mock_session = AsyncMock()

        mock_responses = []
        for data in json_responses:
            mock_resp = AsyncMock()
            mock_resp.json.return_value = data
            mock_responses.append(mock_resp)

        mock_session.request.side_effect = mock_responses

        # Support async context manager (async with ... as session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        return mock_session

    @patch("biodbs.utils.fetch.aiohttp.ClientSession")
    def test_single_url_multiple_queries(self, mock_cls):
        """Single URL string with a list of queries fans out to multiple requests."""
        json_responses = [{"result": "r1"}, {"result": "r2"}, {"result": "r3"}]
        mock_session = self._make_mock_session(json_responses)
        mock_cls.return_value = mock_session

        queries = [{"q": "a"}, {"q": "b"}, {"q": "c"}]
        results = asyncio.run(async_get_resps("http://api.example.com", queries=queries))

        assert len(results) == 3
        assert results[0] == {"result": "r1"}
        assert results[1] == {"result": "r2"}
        assert results[2] == {"result": "r3"}

        # Verify each request was made with the correct params
        assert mock_session.request.call_count == 3
        for i, call in enumerate(mock_session.request.call_args_list):
            assert call.kwargs.get("url") == "http://api.example.com"
            assert call.kwargs.get("params") == queries[i]

    @patch("biodbs.utils.fetch.aiohttp.ClientSession")
    def test_multiple_urls(self, mock_cls):
        """A list of URLs dispatches one request per URL with param=None."""
        json_responses = [{"id": 1}, {"id": 2}]
        mock_session = self._make_mock_session(json_responses)
        mock_cls.return_value = mock_session

        urls = ["http://api.example.com/1", "http://api.example.com/2"]
        results = asyncio.run(async_get_resps(urls))

        assert len(results) == 2
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}

        assert mock_session.request.call_count == 2
        for i, call in enumerate(mock_session.request.call_args_list):
            assert call.kwargs.get("url") == urls[i]
            assert call.kwargs.get("params") is None

    @patch("biodbs.utils.fetch.aiohttp.ClientSession")
    def test_invalid_input_raises_value_error(self, mock_cls):
        """Passing a non-list, non-string urls raises ValueError."""
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_cls.return_value = mock_session

        # Provide kwarg_list explicitly so the code doesn't try to iterate
        # over the invalid urls when building the default kwarg_list.
        with pytest.raises(ValueError, match="urls should be a list or a string"):
            asyncio.run(async_get_resps(12345, queries=[{"q": "x"}], kwarg_list=[{}]))

    @patch("biodbs.utils.fetch.aiohttp.ClientSession")
    def test_json_decode_failure_returns_empty_dict(self, mock_cls):
        """When resp.json() raises, fetch_resp should return an empty dict."""
        mock_session = AsyncMock()
        mock_resp = AsyncMock()
        mock_resp.json.side_effect = Exception("Invalid JSON")
        mock_resp.text.return_value = "not json"
        mock_session.request.return_value = mock_resp
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_cls.return_value = mock_session

        results = asyncio.run(
            async_get_resps(["http://api.example.com/bad"])
        )

        assert len(results) == 1
        assert results[0] == {}

    @patch("biodbs.utils.fetch.aiohttp.ClientSession")
    def test_kwarg_list_forwarded(self, mock_cls):
        """Custom kwarg_list entries are forwarded to fetch_resp / session.request."""
        json_responses = [{"ok": True}]
        mock_session = self._make_mock_session(json_responses)
        mock_cls.return_value = mock_session

        kwarg_list = [{"headers": {"X-Custom": "value"}}]
        results = asyncio.run(
            async_get_resps(
                ["http://api.example.com/endpoint"],
                kwarg_list=kwarg_list,
            )
        )

        assert results == [{"ok": True}]
        call_kwargs = mock_session.request.call_args_list[0].kwargs
        assert call_kwargs.get("headers") == {"X-Custom": "value"}
