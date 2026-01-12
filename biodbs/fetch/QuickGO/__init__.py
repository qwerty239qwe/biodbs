from .api import QuickGOAPI, DEFAULT_HOST
from biodbs.fetch.QuickGO.fetchers import SearchFetcher, SlimFetcher, ChartFetcher, TermFetcher


class QuickGODB(SearchFetcher, SlimFetcher, ChartFetcher, TermFetcher):
    def __init__(self, host=DEFAULT_HOST):
        super().__init__(host)


__all__ = ["QuickGODB", "SearchFetcher", "SlimFetcher", "ChartFetcher", "TermFetcher", "DEFAULT_HOST"]
