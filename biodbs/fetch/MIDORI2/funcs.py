"""Convenience functions for MIDORI2."""

from pathlib import Path

from biodbs.fetch.MIDORI2.midori2_fetcher import MIDORI2_Fetcher

_fetcher: MIDORI2_Fetcher | None = None


def _get_fetcher() -> MIDORI2_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = MIDORI2_Fetcher()
    return _fetcher


def midori2_build_url(
    gene: str, version: str, kind: str = "fasta", unique: bool = True, species: bool = False
) -> str:
    """Build a MIDORI2 download URL."""
    return _get_fetcher().build_url(gene, version, kind=kind, unique=unique, species=species)


def midori2_download(
    gene: str,
    dest: str | Path,
    version: str,
    kind: str = "fasta",
    unique: bool = True,
    species: bool = False,
    overwrite: bool = False,
) -> Path:
    """Download a MIDORI2 reference file."""
    return _get_fetcher().download(
        gene, dest, version, kind=kind, unique=unique, species=species, overwrite=overwrite
    )
