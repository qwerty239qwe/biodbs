"""Offline tests for SILVA fetcher."""

from pathlib import Path

import pytest

from biodbs.fetch.SILVA.silva_fetcher import SILVA_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, text="", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode()
        self.headers = {}

    def iter_content(self, chunk_size=8192):
        yield self.content


LISTING = """
<html><body>
<a href="../">Parent Directory</a>
<a href="?C=N;O=D">Name</a>
<a href="/absolute/">Absolute</a>
<a href="https://example.org/file.txt">External</a>
<a href="README.txt">README.txt</a>
<a href="QIIME2/">QIIME2/</a>
<a href="DADA2/">DADA2/</a>
</body></html>
"""


def test_list_current_files(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text=LISTING),
    )

    data = SILVA_Fetcher().list_current_files()

    assert data.names() == ["README.txt", "QIIME2", "DADA2"]
    assert data["QIIME2"].is_dir is True


def test_list_current_files_preserves_subdirectory_in_child_urls(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text='<a href="taxonomy.qza">taxonomy.qza</a>'),
    )

    data = SILVA_Fetcher().list_current_files("QIIME2")

    assert data["taxonomy.qza"].url.endswith("/current-release/QIIME2/taxonomy.qza")


def test_list_archive_releases(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="release_138/">release_138</a><a href="misc/">misc</a>'
        ),
    )

    data = SILVA_Fetcher().list_archive_releases()

    assert data.names() == ["release_138"]


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
