"""Offline tests for GTDB convenience functions."""

from pathlib import Path

from biodbs.fetch.GTDB import funcs


class DummyFetcher:
    def list_releases(self):
        return "releases"

    def list_release_files(self, release="latest", path=""):
        return ("files", release, path)

    def get_version(self, release="latest"):
        return ("version", release)

    def get_release_notes(self, release="latest"):
        return ("notes", release)

    def get_file_descriptions(self, release="latest"):
        return ("descriptions", release)

    def get_md5sums(self, release="latest"):
        return ("md5", release)

    def get_taxonomy(self, domain="bac120", release="latest"):
        return ("taxonomy", domain, release)

    def get_metadata(self, domain="bac120", release="latest"):
        return ("metadata", domain, release)

    def get_tree(self, domain="bac120", release="latest"):
        return ("tree", domain, release)

    def download_file(self, path_or_url, dest, overwrite=False):
        return ("download", path_or_url, Path(dest), overwrite)

    def download_taxonomy(self, domain="bac120", dest=".", release="latest", compressed=True, overwrite=False):
        return ("download-taxonomy", domain, Path(dest), release, compressed, overwrite)

    def download_metadata(self, domain="bac120", dest=".", release="latest", overwrite=False):
        return ("download-metadata", domain, Path(dest), release, overwrite)

    def download_tree(self, domain="bac120", dest=".", release="latest", compressed=True, overwrite=False):
        return ("download-tree", domain, Path(dest), release, compressed, overwrite)


def test_convenience_functions_delegate(tmp_path, monkeypatch):
    monkeypatch.setattr(funcs, "_fetcher", DummyFetcher())

    assert funcs.gtdb_list_releases() == "releases"
    assert funcs.gtdb_list_release_files("release232", "genomic_files_reps") == (
        "files",
        "release232",
        "genomic_files_reps",
    )
    assert funcs.gtdb_get_version("release232") == ("version", "release232")
    assert funcs.gtdb_get_release_notes() == ("notes", "latest")
    assert funcs.gtdb_get_file_descriptions() == ("descriptions", "latest")
    assert funcs.gtdb_get_md5sums() == ("md5", "latest")
    assert funcs.gtdb_get_taxonomy("ar53") == ("taxonomy", "ar53", "latest")
    assert funcs.gtdb_get_metadata("bac120") == ("metadata", "bac120", "latest")
    assert funcs.gtdb_get_tree("bac120") == ("tree", "bac120", "latest")
    assert funcs.gtdb_download_file("latest/VERSION.txt", tmp_path) == (
        "download",
        "latest/VERSION.txt",
        tmp_path,
        False,
    )
    assert funcs.gtdb_download_taxonomy("bac120", tmp_path) == (
        "download-taxonomy",
        "bac120",
        tmp_path,
        "latest",
        True,
        False,
    )
    assert funcs.gtdb_download_metadata("ar53", tmp_path) == (
        "download-metadata",
        "ar53",
        tmp_path,
        "latest",
        False,
    )
    assert funcs.gtdb_download_tree("bac120", tmp_path) == (
        "download-tree",
        "bac120",
        tmp_path,
        "latest",
        True,
        False,
    )


def test_public_imports():
    from biodbs import gtdb_list_releases as top_level_releases
    from biodbs.fetch import gtdb_list_releases

    assert top_level_releases is gtdb_list_releases
