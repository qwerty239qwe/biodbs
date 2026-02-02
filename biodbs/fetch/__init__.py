"""Fetch module for biological database APIs.

This module provides fetcher classes and convenience functions for accessing
various biological databases.

Usage:
    # Using fetcher classes
    from biodbs.fetch.pubchem import PubChem_Fetcher
    fetcher = PubChem_Fetcher()
    data = fetcher.get_compound(2244)

    # Using convenience functions
    from biodbs.fetch import funcs
    data = funcs.get_compound(2244)
"""

from biodbs.fetch import _func as funcs

__all__ = ["funcs"]
