"""Offline tests for LPSN convenience functions."""

from biodbs.fetch.LPSN import funcs


class DummyFetcher:
    def fetch(self, ids):
        return ("fetch", ids)

    def advanced_search(self, **params):
        return ("advanced", params)

    def flexible_search(self, search, negate=False, page=0):
        return ("flexible", search, negate, page)

    def search_and_fetch(self, search=None, **params):
        return ("search_fetch", search, params)


def test_convenience_functions_delegate(monkeypatch):
    monkeypatch.setattr(funcs, "_fetcher", DummyFetcher())

    assert funcs.lpsn_fetch([1]) == ("fetch", [1])
    assert funcs.lpsn_advanced_search(category="species") == ("advanced", {"page": 0, "category": "species"})
    assert funcs.lpsn_flexible_search({"category": "species"}, negate=True) == (
        "flexible",
        {"category": "species"},
        True,
        0,
    )
    assert funcs.lpsn_search_and_fetch(category="species") == (
        "search_fetch",
        None,
        {"category": "species"},
    )


def test_public_imports():
    from biodbs import lpsn_fetch as top_level_fetch
    from biodbs.fetch import lpsn_fetch

    assert top_level_fetch is lpsn_fetch
