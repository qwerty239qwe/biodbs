"""Offline tests for HOMD fetcher."""

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


def test_download_16s_refseq_uses_first_fasta(monkeypatch, tmp_path):
    def fake_list(path=""):
        assert path == "16S_rRNA_refseq"
        return [type("Item", (), {"name": "homd_refseq.fasta"})()]

    fetcher = HOMD_Fetcher()
    monkeypatch.setattr(fetcher, "list_ftp", fake_list)
    monkeypatch.setattr(fetcher, "download_file", lambda path, dest, overwrite=False: dest / path.split("/")[-1])

    assert fetcher.download_16s_refseq(tmp_path) == tmp_path / "homd_refseq.fasta"
