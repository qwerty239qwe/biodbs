"""Convenience functions for SILVA."""

from pathlib import Path

from biodbs.data.SILVA import SILVAFileListData, SILVAReleaseListData, SILVATextData
from biodbs.fetch.SILVA.silva_fetcher import SILVA_Fetcher

_fetcher: SILVA_Fetcher | None = None


def _get_fetcher() -> SILVA_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = SILVA_Fetcher()
    return _fetcher


def silva_get_version() -> SILVATextData:
    """Fetch current SILVA VERSION.txt."""
    return _get_fetcher().get_version()


def silva_list_current_files(path: str = "") -> SILVAFileListData:
    """List current SILVA release files."""
    return _get_fetcher().list_current_files(path)


def silva_list_archive_releases() -> SILVAReleaseListData:
    """List archived SILVA releases."""
    return _get_fetcher().list_archive_releases()


def silva_get_readme() -> SILVATextData:
    """Fetch current SILVA README.txt."""
    return _get_fetcher().get_readme()


def silva_get_citation() -> SILVATextData:
    """Fetch current SILVA CITATION.txt."""
    return _get_fetcher().get_citation()


def silva_download_file(
    path: str, dest: str | Path, overwrite: bool = False, *, verify_md5: bool = False
) -> Path:
    """Download a SILVA release file."""
    return _get_fetcher().download_file(path, dest, overwrite, verify_md5=verify_md5)


def silva_download_classifier(
    kind: str, filename: str, dest: str | Path, overwrite: bool = False, verify: bool = True
) -> Path:
    """Download a file from a common SILVA classifier directory (MD5-verified by default)."""
    return _get_fetcher().download_classifier(kind, filename, dest, overwrite, verify)

