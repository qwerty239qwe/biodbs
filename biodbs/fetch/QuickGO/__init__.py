"""QuickGO API client module.

Provides access to the QuickGO REST API for Gene Ontology data.
"""
from biodbs.fetch.QuickGO.quickgo_fetcher import (
    QuickGO_Fetcher,
    QuickGO_APIConfig,
    QuickGONameSpace,
)
from biodbs.fetch.QuickGO import funcs


__all__ = [
    "QuickGO_Fetcher",
    "QuickGO_APIConfig",
    "QuickGONameSpace",
    "funcs",
]
