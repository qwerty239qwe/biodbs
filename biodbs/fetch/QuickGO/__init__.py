from .api import QuickGOAPI, DEFAULT_HOST
from biodbs.fetch.QuickGO.fetchers import SearchFetcher, SlimFetcher, ChartFetcher, TermFetcher
from biodbs.fetch.QuickGO.quickgo_fetcher import (
    QuickGO_Fetcher,
    QuickGO_APIConfig,
    QuickGONameSpace,
)


class QuickGODB(SearchFetcher, SlimFetcher, ChartFetcher, TermFetcher):
    def __init__(self, host=DEFAULT_HOST):
        super().__init__(host)


__all__ = [
    "QuickGODB",
    "SearchFetcher",
    "SlimFetcher",
    "ChartFetcher",
    "TermFetcher",
    "DEFAULT_HOST",
    "QuickGO_Fetcher",
    "QuickGO_APIConfig",
    "QuickGONameSpace",
]
