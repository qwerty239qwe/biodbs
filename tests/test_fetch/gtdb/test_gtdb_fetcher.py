"""Offline tests for GTDB fetcher."""

import pytest

from biodbs.fetch.GTDB.gtdb_fetcher import GTDB_Fetcher


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
<a href="/absolute/">Absolute</a>
<a href="latest/">latest/</a>
<a href="release232/">release232/</a>
<a href="misc/">misc/</a>
</body></html>
"""

LATEST = """
<html><body>
<a href="../">Parent Directory</a>
<a href="VERSION.txt">VERSION.txt</a>
<a href="bac120_taxonomy.tsv">bac120_taxonomy.tsv</a>
<a href="bac120_taxonomy.tsv.gz">bac120_taxonomy.tsv.gz</a>
<a href="ar53_metadata.tsv">ar53_metadata.tsv</a>
<a href="bac120_tree.tree">bac120_tree.tree</a>
<a href="bac120_tree.tree.gz">bac120_tree.tree.gz</a>
</body></html>
"""


def test_list_releases_filters_release_dirs(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GTDB.gtdb_fetcher.request_with_retry",
        lambda url: DummyResponse(text=RELEASES),
    )

    data = GTDB_Fetcher().list_releases()

    assert data.names() == ["latest", "release232"]


def test_list_release_files_preserves_subdirectory_urls(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GTDB.gtdb_fetcher.request_with_retry",
        lambda url: DummyResponse(text='<a href="genome.tar.gz">genome.tar.gz</a>'),
    )

    data = GTDB_Fetcher().list_release_files("latest", "genomic_files_reps")

    assert data["genome.tar.gz"].url.endswith("/latest/genomic_files_reps/genome.tar.gz")


def test_get_version(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GTDB.gtdb_fetcher.request_with_retry",
        lambda url: DummyResponse(text="R232\n"),
    )

    data = GTDB_Fetcher().get_version()

    assert data.text == "R232\n"
    assert data.url.endswith("/latest/VERSION.txt")


def test_get_taxonomy_finds_uncompressed_table(monkeypatch):
    def fake_request(url, **kwargs):
        if url.endswith("/latest/"):
            return DummyResponse(text=LATEST)
        return DummyResponse(text="G1\td__Bacteria\nG2\td__Bacteria;p__Bacillota\n")

    monkeypatch.setattr("biodbs.fetch.GTDB.gtdb_fetcher.request_with_retry", fake_request)

    data = GTDB_Fetcher().get_taxonomy("bac120")

    assert data[0] == {"accession": "G1", "classification": "d__Bacteria"}
    assert data[1]["classification"] == "d__Bacteria;p__Bacillota"


def test_download_taxonomy_prefers_compressed(monkeypatch, tmp_path):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        if url.endswith("/latest/"):
            return DummyResponse(text=LATEST)
        return DummyResponse(content=b"abc")

    monkeypatch.setattr("biodbs.fetch.GTDB.gtdb_fetcher.request_with_retry", fake_request)

    path = GTDB_Fetcher().download_taxonomy("bac120", tmp_path)

    assert path == tmp_path / "bac120_taxonomy.tsv.gz"
    assert path.read_bytes() == b"abc"
    assert calls[-1] == ("https://data.gtdb.ecogenomic.org/releases/latest/bac120_taxonomy.tsv.gz", True)


def test_invalid_domain_raises():
    with pytest.raises(ValueError, match="Valid domains"):
        GTDB_Fetcher().get_taxonomy("bad")


def test_download_file_keeps_existing(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        return DummyResponse(content=b"abc")

    monkeypatch.setattr("biodbs.fetch.GTDB.gtdb_fetcher.request_with_retry", fake_request)
    fetcher = GTDB_Fetcher()

    path = fetcher.download_file("latest/VERSION.txt", tmp_path)

    assert path.read_bytes() == b"abc"
    assert fetcher.download_file("latest/VERSION.txt", tmp_path) == path
    assert calls == [("https://data.gtdb.ecogenomic.org/releases/latest/VERSION.txt", True)]
