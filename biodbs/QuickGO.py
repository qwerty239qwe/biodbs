"""
QuickGO module (deprecated).

This module is kept for backward compatibility. New code should use:
    from biodbs.fetch.QuickGO.quickgo_fetcher import QuickGO_Fetcher
"""
from biodbs.deprecated import (
    QUICKGO_DEFAULT_HOST as DEFAULT_HOST,
    QuickGOKeyWord as KeyWord,
    _get_union_keys_in_dics as get_union_keys_in_dics,
    QuickGOdb,
)

__all__ = ["DEFAULT_HOST", "KeyWord", "get_union_keys_in_dics", "QuickGOdb"]
