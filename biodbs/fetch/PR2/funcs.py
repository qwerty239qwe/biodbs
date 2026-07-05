"""Convenience functions for PR2."""

from pathlib import Path

from biodbs.data.PR2 import PR2AssetListData, PR2ReleaseListData
from biodbs.fetch.PR2.pr2_fetcher import PR2_Fetcher

_fetcher: PR2_Fetcher | None = None


def _get_fetcher() -> PR2_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = PR2_Fetcher()
    return _fetcher


def pr2_list_releases() -> PR2ReleaseListData:
    """List PR2 releases (newest first)."""
    return _get_fetcher().list_releases()


def pr2_list_assets(tag: str | None = None) -> PR2AssetListData:
    """List assets for a PR2 release; the latest release when *tag* is None."""
    return _get_fetcher().list_assets(tag)


def pr2_download_asset(
    name: str, dest: str | Path, tag: str | None = None, overwrite: bool = False
) -> Path:
    """Download a PR2 release asset by name."""
    return _get_fetcher().download_asset(name, dest, tag, overwrite)
