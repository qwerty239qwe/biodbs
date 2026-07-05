"""Convenience functions for EUKARYOME."""

from pathlib import Path

from biodbs.fetch.EUKARYOME.eukaryome_fetcher import EUKARYOME_Fetcher

_fetcher: EUKARYOME_Fetcher | None = None


def _get_fetcher() -> EUKARYOME_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = EUKARYOME_Fetcher()
    return _fetcher


def eukaryome_build_url(marker: str, version: str = "2.0") -> str:
    """Build the EUKARYOME download URL for a marker/version."""
    return _get_fetcher().build_url(marker, version)


def eukaryome_download(
    marker: str, dest: str | Path, version: str = "2.0", overwrite: bool = False
) -> Path:
    """Download a EUKARYOME marker archive."""
    return _get_fetcher().download(marker, dest, version, overwrite)
