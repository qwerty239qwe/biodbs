"""Offline tests for the GreenGenes fetcher."""

import pytest

from biodbs.fetch.GreenGenes.greengenes_fetcher import GreenGenes_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, text="", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode()
        self.headers = {}

    def iter_content(self, chunk_size=8192):
        yield self.content


RELEASES = """
<html><body>
<a href="../">Parent Directory</a>
<a href="?C=N;O=D">Name</a>
<a href="gg_13_8_otus/">gg_13_8_otus/</a>
<a href="gg_13_5/">gg_13_5/</a>
<a href="2022.10/">2022.10/</a>
<a href="README.txt">README.txt</a>
</body></html>
"""


def test_list_releases(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GreenGenes.greengenes_fetcher.request_with_retry",
        lambda url: DummyResponse(text=RELEASES),
    )

    data = GreenGenes_Fetcher().list_releases()

    assert data.names() == ["gg_13_8_otus", "gg_13_5", "2022.10"]
    assert data["gg_13_8_otus"].url.endswith("/greengenes_release/gg_13_8_otus/")


def test_list_files_preserves_subdirectory(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GreenGenes.greengenes_fetcher.request_with_retry",
        lambda url: DummyResponse(text='<a href="99_otu_taxonomy.txt">99_otu_taxonomy.txt</a>'),
    )

    data = GreenGenes_Fetcher().list_files("gg_13_8_otus/taxonomy")

    assert data["99_otu_taxonomy.txt"].url.endswith(
        "/greengenes_release/gg_13_8_otus/taxonomy/99_otu_taxonomy.txt"
    )


def test_download_file(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        return DummyResponse(content=b"seq")

    monkeypatch.setattr(
        "biodbs.fetch.GreenGenes.greengenes_fetcher.request_with_retry", fake_request
    )
    fetcher = GreenGenes_Fetcher()

    path = fetcher.download_file("gg_13_8_otus/taxonomy/99_otu_taxonomy.txt", tmp_path)

    assert path == tmp_path / "99_otu_taxonomy.txt"
    assert path.read_bytes() == b"seq"
    assert fetcher.download_file("gg_13_8_otus/taxonomy/99_otu_taxonomy.txt", tmp_path) == path
    assert len([c for c in calls if c[1] is True]) == 1
