"""Convenience functions for UNITE."""

from pathlib import Path

from biodbs.fetch.UNITE.unite_fetcher import UNITE_Fetcher

_fetcher: UNITE_Fetcher | None = None


def _get_fetcher() -> UNITE_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = UNITE_Fetcher()
    return _fetcher


def unite_resolve_doi(version: str, taxon_group: str = "fungi", singletons: bool = False) -> str:
    """Look up the DOI for a UNITE release."""
    return _get_fetcher().resolve_doi(version, taxon_group, singletons)


def unite_get_download_url(version: str, taxon_group: str = "fungi", singletons: bool = False) -> str:
    """Resolve the newest UNITE archive URL via PlutoF."""
    return _get_fetcher().get_download_url(version, taxon_group, singletons)


def unite_download(
    version: str,
    dest: str | Path,
    taxon_group: str = "fungi",
    singletons: bool = False,
    overwrite: bool = False,
) -> Path:
    """Download a UNITE release archive."""
    return _get_fetcher().download(version, dest, taxon_group, singletons, overwrite)
