"""Offline tests for the EUKARYOME fetcher."""

import pytest

from biodbs.fetch.EUKARYOME.eukaryome_fetcher import EUKARYOME_Fetcher, MARKERS


class DummyResponse:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content
        self.text = ""
        self.headers = {}

    def iter_content(self, chunk_size=8192):
        yield self.content


def test_build_url_default_version():
    url = EUKARYOME_Fetcher().build_url("SSU")

    assert url.endswith("/General_EUK_SSU_v2.0.zip")


def test_build_url_marker_is_case_insensitive_and_version_configurable():
    url = EUKARYOME_Fetcher().build_url("its", version="1.9")

    assert url.endswith("/General_EUK_ITS_v1.9.zip")


def test_build_url_invalid_marker_raises():
    with pytest.raises(ValueError, match="Unsupported marker"):
        EUKARYOME_Fetcher().build_url("COI")


def test_markers_exposed():
    assert set(MARKERS) == {"SSU", "LSU", "ITS", "longread"}


def test_download(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        return DummyResponse(content=b"zipbytes")

    monkeypatch.setattr(
        "biodbs.fetch.EUKARYOME.eukaryome_fetcher.request_with_retry", fake_request
    )
    fetcher = EUKARYOME_Fetcher()

    path = fetcher.download("SSU", tmp_path)

    assert path == tmp_path / "General_EUK_SSU_v2.0.zip"
    assert path.read_bytes() == b"zipbytes"
    assert calls[0][1] is True
    # cached on disk, no re-download
    assert fetcher.download("SSU", tmp_path) == path
    assert len(calls) == 1
