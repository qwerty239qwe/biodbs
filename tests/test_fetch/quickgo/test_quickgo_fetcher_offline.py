"""Offline tests for QuickGO fetcher network and pagination behavior."""

import pytest

from biodbs.data.QuickGO.data import QuickGOFetchedData
from biodbs.fetch.QuickGO.quickgo_fetcher import QuickGO_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._json_data


def test_quickgo_get_json_and_download_headers(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None):
        calls.append({"url": url, "params": params, "headers": headers})
        return DummyResponse(
            json_data={"results": [{"id": "GO:0006915"}], "numberOfHits": 1},
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr("biodbs.fetch.QuickGO.quickgo_fetcher.requests.get", fake_get)
    data = QuickGO_Fetcher().get(
        category="ontology", endpoint="search", query="apoptosis", limit=1
    )

    assert data.results == [{"id": "GO:0006915"}]
    assert calls[0]["url"].endswith("/ontology/go/search")
    assert calls[0]["params"]["query"] == "apoptosis"

    def fake_tsv_get(url, params=None, headers=None):
        calls.append({"url": url, "params": params, "headers": headers})
        return DummyResponse(
            text="Gene\tGO\nTP53\tGO:0006915\n",
            headers={"Content-Type": "text/tsv"},
        )

    monkeypatch.setattr("biodbs.fetch.QuickGO.quickgo_fetcher.requests.get", fake_tsv_get)
    tsv = QuickGO_Fetcher().get(
        category="annotation",
        endpoint="downloadSearch",
        goId="GO:0006915",
        downloadFormat="tsv",
    )
    assert tsv.results[0]["Gene"] == "TP53"
    assert calls[-1]["headers"] == {"Accept": "text/tsv"}


def test_quickgo_fetch_page_uses_text_for_non_json(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.QuickGO.quickgo_fetcher.requests.get",
        lambda url, params=None: DummyResponse(
            text="Gene\tGO\nTP53\tGO:0006915\n", headers={"Content-Type": "text/tsv"}
        ),
    )

    data = QuickGO_Fetcher()._fetch_page(
        "https://example.test", {"page": 1}, "downloadSearch", "tsv"
    )
    assert data.results[0]["GO"] == "GO:0006915"


def test_quickgo_get_all_concatenates_pages_and_truncates(monkeypatch):
    fetcher = QuickGO_Fetcher()
    first = QuickGOFetchedData(
        {"results": [{"id": "GO:1"}, {"id": "GO:2"}], "numberOfHits": 5},
        endpoint="search",
    )
    second = QuickGOFetchedData(
        {"results": [{"id": "GO:3"}, {"id": "GO:4"}], "numberOfHits": 5},
        endpoint="search",
    )

    monkeypatch.setattr(fetcher, "_fetch_page", lambda *args, **kwargs: first)
    monkeypatch.setattr(
        fetcher,
        "schedule_process",
        lambda **kwargs: [second],
    )

    data = fetcher.get_all(
        category="ontology",
        endpoint="search",
        query="apoptosis",
        limit_per_page=2,
        max_records=3,
    )

    assert [row["id"] for row in data.results] == ["GO:1", "GO:2", "GO:3"]


def test_quickgo_get_all_empty_and_invalid_modes(monkeypatch):
    fetcher = QuickGO_Fetcher()
    monkeypatch.setattr(
        fetcher,
        "_fetch_page",
        lambda *args, **kwargs: QuickGOFetchedData({"results": []}, endpoint="search"),
    )

    with pytest.raises(ValueError, match="downloadSearch"):
        fetcher.get_all(category="annotation", endpoint="downloadSearch")
    with pytest.raises(ValueError, match="stream_to_storage"):
        fetcher.get_all(category="ontology", endpoint="search", method="stream_to_storage")

    assert fetcher.get_all(category="ontology", endpoint="search", query="x").results == []


def test_quickgo_get_all_streams_to_storage(monkeypatch, tmp_path):
    fetcher = QuickGO_Fetcher(storage_path=tmp_path)
    page = QuickGOFetchedData(
        {"results": [{"id": "GO:1"}], "numberOfHits": 1},
        endpoint="search",
    )
    monkeypatch.setattr(fetcher, "_fetch_page", lambda *args, **kwargs: page)

    path = fetcher.get_all(
        category="ontology",
        endpoint="search",
        method="stream_to_storage",
        query="apoptosis",
    )

    assert path.name == "quickgo_ontology_search.jsonl"
    assert path.exists()
