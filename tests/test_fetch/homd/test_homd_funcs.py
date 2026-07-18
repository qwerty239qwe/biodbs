"""Offline tests for HOMD convenience functions."""

from pathlib import Path

from biodbs.fetch.HOMD import funcs


class DummyFetcher:
    def list_ftp(self, path=""):
        return ("ftp", path)

    def list_downloads(self):
        return "downloads"

    def download_file(self, path_or_url, dest, overwrite=False):
        return ("download", path_or_url, Path(dest), overwrite)

    def get_table(self, path_or_url, delimiter="\t"):
        return ("table", path_or_url, delimiter)

    def get_text(self, path_or_url):
        return ("text", path_or_url)

    def get_taxon_table(self):
        return "taxa"

    def get_taxonomic_hierarchy(self):
        return "hierarchy"

    def get_hmt_lineage(self):
        return "lineage"

    def get_genome_metadata(self):
        return "genomes"

    def get_gtdb_taxonomy(self):
        return "gtdb"

    def get_phage_table(self):
        return "phage"

    def get_crispr_table(self):
        return "crispr"

    def list_16s_refseq(self, version="current", source="homd"):
        return ("16s", version, source)

    def download_16s_refseq(self, dest, filename="", overwrite=False, *, version="current", source="homd"):
        return ("16s-download", Path(dest), filename, overwrite, version, source)

    def download_16s_taxonomy(self, dest, overwrite=False, *, version="current", source="homd"):
        return ("16s-taxonomy", Path(dest), overwrite, version, source)


def test_convenience_functions_delegate(tmp_path, monkeypatch):
    monkeypatch.setattr(funcs, "_fetcher", DummyFetcher())

    assert funcs.homd_list_ftp("genomes") == ("ftp", "genomes")
    assert funcs.homd_list_downloads() == "downloads"
    assert funcs.homd_download_file("ftp/taxa.tsv", tmp_path) == (
        "download",
        "ftp/taxa.tsv",
        tmp_path,
        False,
    )
    assert funcs.homd_get_table("ftp/taxa.tsv") == ("table", "ftp/taxa.tsv", "\t")
    assert funcs.homd_get_text("ftp/readme.txt") == ("text", "ftp/readme.txt")
    assert funcs.homd_get_taxon_table() == "taxa"
    assert funcs.homd_get_taxonomic_hierarchy() == "hierarchy"
    assert funcs.homd_get_hmt_lineage() == "lineage"
    assert funcs.homd_get_genome_metadata() == "genomes"
    assert funcs.homd_get_gtdb_taxonomy() == "gtdb"
    assert funcs.homd_get_phage_table() == "phage"
    assert funcs.homd_get_crispr_table() == "crispr"
    assert funcs.homd_list_16s_refseq() == ("16s", "current", "homd")
    assert funcs.homd_download_16s_refseq(tmp_path) == (
        "16s-download",
        tmp_path,
        "",
        False,
        "current",
        "homd",
    )
    assert funcs.homd_download_16s_taxonomy(tmp_path, version="15.22", source="momd") == (
        "16s-taxonomy",
        tmp_path,
        False,
        "15.22",
        "momd",
    )


def test_public_imports():
    from biodbs import homd_list_ftp as top_level_list
    from biodbs.fetch import homd_list_ftp

    assert top_level_list is homd_list_ftp
