"""Convenience functions for LPSN."""

from typing import Any

from biodbs.data.LPSN.data import LPSNFetchedData, LPSNSearchData
from biodbs.fetch.LPSN.lpsn_fetcher import LPSN_Fetcher

_fetcher: LPSN_Fetcher | None = None


def _get_fetcher() -> LPSN_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = LPSN_Fetcher()
    return _fetcher


def lpsn_fetch(ids) -> LPSNFetchedData:
    """Fetch detailed LPSN records by ID."""
    return _get_fetcher().fetch(ids)


def lpsn_advanced_search(page: int = 0, **params: Any) -> LPSNSearchData:
    """Run LPSN advanced search."""
    return _get_fetcher().advanced_search(page=page, **params)


def lpsn_flexible_search(search: dict[str, Any], negate: bool = False, page: int = 0) -> LPSNSearchData:
    """Run LPSN flexible exact-match search."""
    return _get_fetcher().flexible_search(search, negate=negate, page=page)


def lpsn_search_and_fetch(search: dict[str, Any] | None = None, **params: Any) -> LPSNFetchedData:
    """Search LPSN IDs and fetch full records."""
    return _get_fetcher().search_and_fetch(search=search, **params)

