"""Offline tests for SILVA convenience functions."""

from pathlib import Path

from biodbs.fetch.SILVA import funcs


class DummyFetcher:
    def get_version(self):
        return "version"

    def list_current_files(self, path=""):
        return ("current", path)

    def list_archive_releases(self):
        return "archive"

    def get_readme(self):
        return "readme"

    def get_citation(self):
        return "citation"

    def download_file(self, path, dest, overwrite=False):
        return ("download", path, Path(dest), overwrite)

    def download_classifier(self, kind, filename, dest, overwrite=False, verify=True):
        return ("classifier", kind, filename, Path(dest), overwrite, verify)


def test_convenience_functions_delegate(tmp_path, monkeypatch):
    monkeypatch.setattr(funcs, "_fetcher", DummyFetcher())

    assert funcs.silva_get_version() == "version"
    assert funcs.silva_list_current_files("QIIME2") == ("current", "QIIME2")
    assert funcs.silva_list_archive_releases() == "archive"
    assert funcs.silva_get_readme() == "readme"
    assert funcs.silva_get_citation() == "citation"
    assert funcs.silva_download_file("README.txt", tmp_path) == (
        "download",
        "README.txt",
        tmp_path,
        False,
    )
    assert funcs.silva_download_classifier("qiime2", "taxonomy.qza", tmp_path) == (
        "classifier",
        "qiime2",
        "taxonomy.qza",
        tmp_path,
        False,
        True,
    )


def test_public_imports():
    from biodbs import silva_get_version as top_level_version
    from biodbs.fetch import silva_get_version

    assert top_level_version is silva_get_version
