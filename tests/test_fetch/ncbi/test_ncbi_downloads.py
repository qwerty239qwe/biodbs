"""Offline tests for NCBI static reference downloads."""

from pathlib import Path

from biodbs.fetch.NCBI import NCBI_Fetcher


def test_download_blast_database_uses_ncbi_md5(tmp_path, monkeypatch):
    seen = {}

    def fake_download(url, target, service, **kwargs):
        seen.update(url=url, target=Path(target), service=service, kwargs=kwargs)
        return Path(target)

    monkeypatch.setattr("biodbs.fetch.NCBI.ncbi_fetcher.download_binary", fake_download)

    path = NCBI_Fetcher().download_blast_database("16S_ribosomal_RNA", tmp_path)

    assert path == tmp_path / "16S_ribosomal_RNA.tar.gz"
    assert seen["url"] == "https://ftp.ncbi.nlm.nih.gov/blast/db/16S_ribosomal_RNA.tar.gz"
    assert seen["service"] == "NCBI"
    assert seen["kwargs"]["md5_url"] == f"{seen['url']}.md5"


def test_download_taxdump_uses_new_taxdump_archive(tmp_path, monkeypatch):
    seen = {}

    def fake_download(url, target, service, **kwargs):
        seen.update(url=url, target=Path(target))
        return Path(target)

    monkeypatch.setattr("biodbs.fetch.NCBI.ncbi_fetcher.download_binary", fake_download)

    path = NCBI_Fetcher().download_taxdump(tmp_path)

    assert path.name == "new_taxdump.tar.gz"
    assert seen["url"] == "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz"


def test_download_blast_database_explicit_target(tmp_path, monkeypatch):
    seen = {}

    def fake_download(url, target, service, **kwargs):
        seen["target"] = Path(target)
        return Path(target)

    monkeypatch.setattr("biodbs.fetch.NCBI.ncbi_fetcher.download_binary", fake_download)

    explicit = tmp_path / "my16s.tar.gz"
    NCBI_Fetcher().download_blast_database("16S_ribosomal_RNA", explicit)

    assert seen["target"] == explicit
