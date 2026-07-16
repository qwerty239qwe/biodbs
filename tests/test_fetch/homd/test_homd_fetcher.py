"""Offline tests for HOMD fetcher."""

from pathlib import Path

import pytest

from biodbs.data.HOMD import HOMDFile, HOMDFileListData
from biodbs.exceptions import APIValidationError
from biodbs.fetch.HOMD.homd_fetcher import HOMD_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, text="", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode()
        self.headers = {}

    def iter_content(self, chunk_size=8192):
        yield self.content


FTP_LISTING = """
<html><body>
<a href="../">Parent Directory</a>
<a href="?C=N;O=D">Name</a>
<a href="/absolute/">Absolute</a>
<a href="mailto:help@example.org">Mail</a>
<a href="genomes/">genomes/</a>
<a href="taxa.tsv">taxa.tsv</a>
</body></html>
"""


DOWNLOADS = """
<html><body>
<h3>Taxonomy</h3>
<a href="/ftp/taxa.tsv">Taxon Table</a>
<a href="/ftp/hierarchy.tsv">Taxonomic Hierarchy</a>
<h3>Genomes</h3>
<a href="/ftp/genome_metadata.tsv">Genome Metadata</a>
<h3>Mobile Elements</h3>
<a href="/ftp/crispr.tsv">CRISPR Table</a>
</body></html>
"""


def test_list_ftp_skips_autoindex_junk(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.HOMD.homd_fetcher.request_with_retry",
        lambda url: DummyResponse(text=FTP_LISTING),
    )

    data = HOMD_Fetcher().list_ftp()

    assert data.names() == ["genomes", "taxa.tsv"]
    assert data["genomes"].is_dir is True


def test_list_ftp_preserves_subdirectory_in_child_urls(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.HOMD.homd_fetcher.request_with_retry",
        lambda url: DummyResponse(text='<a href="genome.tsv">genome.tsv</a>'),
    )

    data = HOMD_Fetcher().list_ftp("genomes")

    assert data["genome.tsv"].url.endswith("/ftp/genomes/genome.tsv")


def test_list_downloads_parses_links(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.HOMD.homd_fetcher.request_with_retry",
        lambda url: DummyResponse(text=DOWNLOADS),
    )

    data = HOMD_Fetcher().list_downloads()

    assert "Taxon Table" in data.names()
    assert data["Taxon Table"].url.endswith("/ftp/taxa.tsv")


def test_get_table_by_keyword(monkeypatch):
    def fake_request(url, **kwargs):
        if url.endswith("/download/download/all"):
            return DummyResponse(text=DOWNLOADS)
        return DummyResponse(text="id\tname\n1\tHMT-001\n")

    monkeypatch.setattr("biodbs.fetch.HOMD.homd_fetcher.request_with_retry", fake_request)

    data = HOMD_Fetcher().get_taxon_table()

    assert data[0]["name"] == "HMT-001"


def test_download_file_streams_and_keeps_existing(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        return DummyResponse(content=b"abc")

    monkeypatch.setattr("biodbs.fetch.HOMD.homd_fetcher.request_with_retry", fake_request)
    fetcher = HOMD_Fetcher()

    path = fetcher.download_file("ftp/taxa.tsv", tmp_path)

    assert path == tmp_path / "taxa.tsv"
    assert path.read_bytes() == b"abc"
    assert fetcher.download_file("ftp/taxa.tsv", tmp_path) == path
    assert calls == [("https://www.homd.org/ftp/taxa.tsv", True)]


def test_list_16s_refseq_descends_to_selected_version(monkeypatch):
    fetcher = HOMD_Fetcher()
    seen = []
    monkeypatch.setattr(fetcher, "list_ftp", lambda path: seen.append(path) or HOMDFileListData([]))

    fetcher.list_16s_refseq(version="15.22")

    assert seen == ["https://www.homd.org/ftp/16S_rRNA_refseq/HOMD_16S_rRNA_RefSeq/V15.22"]


def test_list_16s_refseq_supports_momd(monkeypatch):
    fetcher = HOMD_Fetcher()
    seen = []
    monkeypatch.setattr(fetcher, "list_ftp", lambda path: seen.append(path) or HOMDFileListData([]))

    fetcher.list_16s_refseq(version="5.1", source="momd")

    assert seen == ["https://www.momd.org/ftp/16S_rRNA_refseq/MOMD_16S_rRNA_RefSeq/V5.1"]
    # the shared instance host must be left unchanged
    assert fetcher.ftp_url == "https://www.homd.org/ftp/"


def test_refseq_dir_url_current_and_bad_source():
    tag, url = HOMD_Fetcher()._refseq_dir_url("current", "homd")
    assert tag == "HOMD"
    assert url == "https://www.homd.org/ftp/16S_rRNA_refseq/HOMD_16S_rRNA_RefSeq/current"

    with pytest.raises(APIValidationError):
        HOMD_Fetcher()._refseq_dir_url("current", "bogus")


def test_download_16s_selects_unaligned_fasta_and_taxonomy(monkeypatch, tmp_path):
    files = HOMDFileListData(
        [
            HOMDFile("HOMD_16S_rRNA_RefSeq_V16.03.aligned.fasta", "https://x/aligned.fasta"),
            HOMDFile("HOMD_16S_rRNA_RefSeq_V16.03.p9.fasta", "https://x/p9.fasta"),
            HOMDFile("HOMD_16S_rRNA_RefSeq_V16.03.fasta", "https://x/ref.fasta"),
            HOMDFile("HOMD_16S_rRNA_RefSeq_V16.03.mothur.taxonomy", "https://x/mothur.taxonomy"),
            HOMDFile("HOMD_16S_rRNA_RefSeq_V16.03.qiime.taxonomy", "https://x/ref.qiime.taxonomy"),
        ]
    )
    fetcher = HOMD_Fetcher()
    monkeypatch.setattr(fetcher, "list_16s_refseq", lambda **kwargs: files)
    monkeypatch.setattr(fetcher, "download_file", lambda url, dest, overwrite=False: Path(dest) / Path(url).name)

    assert fetcher.download_16s_refseq(tmp_path).name == "ref.fasta"
    assert fetcher.download_16s_taxonomy(tmp_path).name == "ref.qiime.taxonomy"


def test_download_16s_refseq_with_explicit_filename(monkeypatch, tmp_path):
    fetcher = HOMD_Fetcher()
    seen = {}

    def fake_download(url, dest, overwrite=False):
        seen["url"] = url
        return Path(dest)

    monkeypatch.setattr(fetcher, "download_file", fake_download)

    fetcher.download_16s_refseq(tmp_path, filename="custom.fasta", version="15.22")

    assert seen["url"] == (
        "https://www.homd.org/ftp/16S_rRNA_refseq/HOMD_16S_rRNA_RefSeq/V15.22/custom.fasta"
    )
