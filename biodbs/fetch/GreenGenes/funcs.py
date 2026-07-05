"""Convenience functions for GreenGenes."""

from pathlib import Path

from biodbs.data.GreenGenes import GreenGenesFileListData, GreenGenesReleaseListData
from biodbs.fetch.GreenGenes.greengenes_fetcher import GreenGenes_Fetcher

_fetcher: GreenGenes_Fetcher | None = None


def _get_fetcher() -> GreenGenes_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = GreenGenes_Fetcher()
    return _fetcher


def greengenes_list_releases() -> GreenGenesReleaseListData:
    """List GreenGenes release directories."""
    return _get_fetcher().list_releases()


def greengenes_list_files(path: str = "") -> GreenGenesFileListData:
    """List files/directories under a GreenGenes release path."""
    return _get_fetcher().list_files(path)


def greengenes_download_file(path: str, dest: str | Path, overwrite: bool = False) -> Path:
    """Download a GreenGenes file."""
    return _get_fetcher().download_file(path, dest, overwrite)
