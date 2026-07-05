"""Convenience functions for GTDB."""

from pathlib import Path

from biodbs.data.GTDB import GTDBFileListData, GTDBTableData, GTDBTextData
from biodbs.fetch.GTDB.gtdb_fetcher import GTDB_Fetcher

_fetcher: GTDB_Fetcher | None = None


def _get_fetcher() -> GTDB_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = GTDB_Fetcher()
    return _fetcher


def gtdb_list_releases() -> GTDBFileListData:
    """List GTDB releases."""
    return _get_fetcher().list_releases()


def gtdb_list_release_files(release: str = "latest", path: str = "") -> GTDBFileListData:
    """List files for a GTDB release."""
    return _get_fetcher().list_release_files(release, path)


def gtdb_get_version(release: str = "latest") -> GTDBTextData:
    """Fetch GTDB VERSION.txt."""
    return _get_fetcher().get_version(release)


def gtdb_get_release_notes(release: str = "latest") -> GTDBTextData:
    """Fetch GTDB RELEASE_NOTES.txt."""
    return _get_fetcher().get_release_notes(release)


def gtdb_get_file_descriptions(release: str = "latest") -> GTDBTextData:
    """Fetch GTDB FILE_DESCRIPTIONS.txt."""
    return _get_fetcher().get_file_descriptions(release)


def gtdb_get_md5sums(release: str = "latest") -> GTDBTextData:
    """Fetch GTDB MD5SUM.txt."""
    return _get_fetcher().get_md5sums(release)


def gtdb_get_taxonomy(domain: str = "bac120", release: str = "latest") -> GTDBTableData:
    """Fetch GTDB taxonomy table."""
    return _get_fetcher().get_taxonomy(domain, release)


def gtdb_get_metadata(domain: str = "bac120", release: str = "latest") -> GTDBTableData:
    """Fetch GTDB metadata table."""
    return _get_fetcher().get_metadata(domain, release)


def gtdb_get_tree(domain: str = "bac120", release: str = "latest") -> GTDBTextData:
    """Fetch GTDB tree text."""
    return _get_fetcher().get_tree(domain, release)


def gtdb_download_file(path_or_url: str, dest: str | Path, overwrite: bool = False) -> Path:
    """Download a GTDB file."""
    return _get_fetcher().download_file(path_or_url, dest, overwrite)


def gtdb_download_taxonomy(
    domain: str = "bac120",
    dest: str | Path = ".",
    release: str = "latest",
    compressed: bool = True,
    overwrite: bool = False,
) -> Path:
    """Download GTDB taxonomy."""
    return _get_fetcher().download_taxonomy(domain, dest, release, compressed, overwrite)


def gtdb_download_metadata(
    domain: str = "bac120",
    dest: str | Path = ".",
    release: str = "latest",
    overwrite: bool = False,
) -> Path:
    """Download GTDB metadata."""
    return _get_fetcher().download_metadata(domain, dest, release, overwrite)


def gtdb_download_tree(
    domain: str = "bac120",
    dest: str | Path = ".",
    release: str = "latest",
    compressed: bool = True,
    overwrite: bool = False,
) -> Path:
    """Download GTDB tree."""
    return _get_fetcher().download_tree(domain, dest, release, compressed, overwrite)
