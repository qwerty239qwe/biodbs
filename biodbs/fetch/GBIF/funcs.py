"""Convenience functions for GBIF."""

from biodbs.data.GBIF import GBIFMatch, GBIFMatchListData
from biodbs.fetch.GBIF.gbif_fetcher import GBIF_Fetcher

_fetcher: GBIF_Fetcher | None = None


def _get_fetcher() -> GBIF_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = GBIF_Fetcher()
    return _fetcher


def gbif_match_name(name: str, strict: bool = False) -> GBIFMatch:
    """Match one name against the GBIF backbone taxonomy."""
    return _get_fetcher().match_name(name, strict=strict)


def gbif_match_names(names: list[str], strict: bool = False) -> GBIFMatchListData:
    """Match many names against the GBIF backbone taxonomy."""
    return _get_fetcher().match_names(names, strict=strict)
