"""Offline tests for HOMD fetcher."""

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


def test_download_file_uses_shared_downloader(tmp_path, monkeypatch):
    seen = {}

    def fake_download(url, target, service, **kwargs):
        seen.update(url=url, target=target, service=service, kwargs=kwargs)
        return target

    monkeypatch.setattr("biodbs.fetch.HOMD.homd_fetcher.download_binary", fake_download)

    dest = tmp_path / "refs" / "homd"
    path = HOMD_Fetcher().download_file("ftp/taxa.tsv", dest)

    assert path == dest / "taxa.tsv"
    assert seen == {
        "url": "https://www.homd.org/ftp/taxa.tsv",
        "target": path,
        "service": "HOMD",
        "kwargs": {"overwrite": False},
    }


def test_list_16s_refseq_uses_versioned_source_urls(monkeypatch):
    fetcher = HOMD_Fetcher()
    seen = []
    monkeypatch.setattr(
        fetcher,
        "_list_ftp_url",
        lambda url: seen.append(url) or HOMDFileListData([]),
    )

    fetcher.list_16s_refseq("15.22", "homd")
    fetcher.list_16s_refseq("V5.1", "momd")

    assert seen == [
        "https://www.homd.org/ftp/16S_rRNA_refseq/HOMD_16S_rRNA_RefSeq/V15.22",
        "https://momd.org/ftp/16S_rRNA_refseq/MOMD_16S_rRNA_RefSeq/V5.1",
    ]


def test_16s_refseq_validates_source_and_version():
    with pytest.raises(APIValidationError, match="Unsupported 16S source"):
        HOMD_Fetcher().list_16s_refseq(source="other")
    with pytest.raises(APIValidationError, match="Invalid 16S version"):
        HOMD_Fetcher().list_16s_refseq(version="tomorrow")
    with pytest.raises(APIValidationError, match="Invalid 16S filename"):
        HOMD_Fetcher().download_16s_refseq("refs", filename="../other.fasta")


def test_download_16s_refseq_selects_canonical_files(monkeypatch, tmp_path):
    files = HOMDFileListData(
        [
            HOMDFile("HOMD_16S_rRNA_RefSeq_V15.22.aligned.fasta", "https://x/aligned.fasta"),
            HOMDFile("HOMD_16S_rRNA_RefSeq_V15.22.fasta", "https://x/ref.fasta"),
            HOMDFile(
                "HOMD_16S_rRNA_RefSeq_V15.22.qiime.taxonomy",
                "https://x/ref.qiime.taxonomy",
            ),
        ]
    )
    fetcher = HOMD_Fetcher()
    monkeypatch.setattr(fetcher, "list_16s_refseq", lambda *args: files)
    monkeypatch.setattr(
        fetcher,
        "download_file",
        lambda url, dest, overwrite=False: tmp_path / url.rsplit("/", 1)[-1],
    )

    assert fetcher.download_16s_refseq(tmp_path, version="15.22").name == "ref.fasta"
    assert (
        fetcher.download_16s_taxonomy(tmp_path, version="15.22").name
        == "ref.qiime.taxonomy"
    )


def test_download_16s_refseq_preserves_explicit_filename_directory(monkeypatch, tmp_path):
    fetcher = HOMD_Fetcher()
    seen = {}
    monkeypatch.setattr(
        fetcher,
        "download_file",
        lambda url, dest, overwrite=False: seen.setdefault("url", url) or tmp_path,
    )

    fetcher.download_16s_refseq(
        tmp_path, filename="custom.fasta", version="5.1", source="momd"
    )

    assert seen["url"] == (
        "https://momd.org/ftp/16S_rRNA_refseq/MOMD_16S_rRNA_RefSeq/V5.1/custom.fasta"
    )
