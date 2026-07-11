"""Offline tests for SILVA fetcher."""

from pathlib import Path

import pytest

from biodbs.exceptions import APIError
from biodbs.fetch.SILVA.silva_fetcher import SILVA_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, text="", content=b"", content_type=None):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode()
        self.headers = {"content-type": content_type} if content_type else {}

    def iter_content(self, chunk_size=8192):
        yield self.content


# SILVA's CMS links subpages with root-relative hrefs, mixed with global nav.
CURRENT_RELEASE_PAGE = """
<html><body>
<a href="/">Home</a>
<a href="/contact">Contact</a>
<a href="/current-release">Current release</a>
<a href="/current-release/QIIME2">QIIME2</a>
<a href="/current-release/DADA2">DADA2</a>
<a href="/current-release/QIIME2/2025.7">deep link, root should only show QIIME2</a>
<a href="/fileadmin/silva_databases/current/VERSION.txt">VERSION</a>
<a href="https://x.com/ARB_SILVA">external</a>
</body></html>
"""


def test_list_current_files(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text=CURRENT_RELEASE_PAGE),
    )

    data = SILVA_Fetcher().list_current_files()

    # only immediate children under /current-release/, nav/external excluded
    assert data.names() == ["QIIME2", "DADA2"]
    assert data["QIIME2"].is_dir is True


def test_list_current_files_preserves_subdirectory_in_child_urls(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="/current-release/QIIME2/2025.7">2025.7</a>'
        ),
    )

    data = SILVA_Fetcher().list_current_files("QIIME2")

    assert data["2025.7"].url.endswith("/current-release/QIIME2/2025.7")


def test_list_archive_releases(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="/archive/release_138">release_138</a>'
            '<a href="/archive/qiime">qiime</a>'
        ),
    )

    data = SILVA_Fetcher().list_archive_releases()

    assert data.names() == ["release_138"]
    assert data["release_138"].url.endswith("/archive/release_138")


def test_get_text_files(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text="SILVA 138"),
    )

    data = SILVA_Fetcher().get_version()

    assert data.text == "SILVA 138"
    assert data.url.endswith("VERSION.txt")


def test_download_file(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        return DummyResponse(content=b"abc")

    monkeypatch.setattr("biodbs.fetch.SILVA.silva_fetcher.request_with_retry", fake_request)
    fetcher = SILVA_Fetcher()

    path = fetcher.download_file("README.txt", tmp_path)

    assert path == tmp_path / "README.txt"
    assert path.read_bytes() == b"abc"
    assert fetcher.download_file("README.txt", tmp_path) == path
    assert len(calls) == 1
    assert calls[0][1] is True


def test_download_classifier_maps_directory(tmp_path, monkeypatch):
    seen = {}

    def fake_download(path, dest, overwrite=False):
        seen["path"] = path
        return Path(dest) / Path(path).name

    fetcher = SILVA_Fetcher()
    monkeypatch.setattr(fetcher, "download_file", fake_download)

    result = fetcher.download_classifier("qiime2", "taxonomy.qza", tmp_path)

    assert seen["path"] == "QIIME2/taxonomy.qza"
    assert result == tmp_path / "taxonomy.qza"


def test_download_classifier_unknown_kind_raises_value_error(tmp_path):
    fetcher = SILVA_Fetcher()

    with pytest.raises(ValueError, match="Valid kinds"):
        fetcher.download_classifier("qiime", "taxonomy.qza", tmp_path)


def test_download_file_uses_fileadmin_base(tmp_path, monkeypatch):
    seen = {}

    def fake_request(url, stream=False):
        seen["url"] = url
        return DummyResponse(content=b"data", content_type="application/octet-stream")

    monkeypatch.setattr("biodbs.fetch.SILVA.silva_fetcher.request_with_retry", fake_request)

    SILVA_Fetcher().download_file("QIIME2/2025.7/taxonomic-weights/w.qza", tmp_path)

    assert seen["url"] == (
        "https://www.arb-silva.de/fileadmin/silva_databases/current/"
        "QIIME2/2025.7/taxonomic-weights/w.qza"
    )


def test_download_file_rejects_html_page(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url, stream=False: DummyResponse(
            content=b"<!DOCTYPE html><html>...", content_type="text/html; charset=utf-8"
        ),
    )

    with pytest.raises(APIError, match="HTML page"):
        SILVA_Fetcher().download_file("QIIME2/whatever.qza", tmp_path)

    # nothing should have been written
    assert list(tmp_path.iterdir()) == []


def test_download_classifier_builds_fileadmin_classifier_url(tmp_path, monkeypatch):
    seen = {}

    def fake_request(url, stream=False):
        seen["url"] = url
        return DummyResponse(content=b"data", content_type="application/octet-stream")

    monkeypatch.setattr("biodbs.fetch.SILVA.silva_fetcher.request_with_retry", fake_request)

    SILVA_Fetcher().download_classifier(
        "qiime2", "2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza", tmp_path
    )

    assert seen["url"] == (
        "https://www.arb-silva.de/fileadmin/silva_databases/current/"
        "QIIME2/2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza"
    )


def test_download_file_writes_into_fresh_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url, stream=False: DummyResponse(content=b"data", content_type="application/octet-stream"),
    )
    dest = tmp_path / "data" / "silva"  # does not exist yet, no suffix -> a directory

    path = SILVA_Fetcher().download_file("QIIME2/x.qza", dest)

    assert path == dest / "x.qza"
    assert path.read_bytes() == b"data"
    assert dest.is_dir()


def test_download_file_partial_transfer_not_cached(tmp_path, monkeypatch):
    class FailingResponse:
        status_code = 200
        headers = {"content-type": "application/octet-stream"}

        def iter_content(self, chunk_size=8192):
            yield b"partial"
            raise OSError("connection dropped")

    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url, stream=False: FailingResponse(),
    )
    fetcher = SILVA_Fetcher()

    with pytest.raises(OSError):
        fetcher.download_file("QIIME2/x.qza", tmp_path)

    # no valid target and no leftover partial that a later call could reuse
    assert not (tmp_path / "x.qza").exists()
    assert list(tmp_path.glob("*.part")) == []


def test_get_version_uses_fileadmin_base(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text="138.2", content_type="text/plain"),
    )

    data = SILVA_Fetcher().get_version()

    assert data.url == "https://www.arb-silva.de/fileadmin/silva_databases/current/VERSION.txt"
