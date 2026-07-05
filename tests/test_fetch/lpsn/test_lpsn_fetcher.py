"""Offline tests for LPSN fetcher."""

import pytest

from biodbs.exceptions import APIError
from biodbs.fetch.LPSN.lpsn_fetcher import LPSN_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self.headers = {}

    def json(self):
        return self._payload


def test_fetch_uses_bearer_token_and_chunks(monkeypatch):
    calls = []

    def fake_request(url, params=None, headers=None):
        calls.append((url, params, headers))
        return DummyResponse(payload={"results": [{"id": 1}, {"id": 2}]})

    monkeypatch.setattr("biodbs.fetch.LPSN.lpsn_fetcher.request_with_retry", fake_request)
    fetcher = LPSN_Fetcher(token="abc")

    data = fetcher.fetch(range(101))

    assert len(data) == 4
    assert len(calls) == 2
    assert calls[0][0].endswith("/fetch/" + ";".join(str(i) for i in range(100)))
    assert calls[0][2] == {"Authorization": "Bearer abc"}


def test_token_only_401_raises_expired_message(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.LPSN.lpsn_fetcher.request_with_retry",
        lambda url, params=None, headers=None: DummyResponse(status_code=401),
    )

    with pytest.raises(APIError, match="token expired"):
        LPSN_Fetcher(token="old").fetch(1)


def test_refresh_token_recovers_from_401(monkeypatch):
    calls = []
    posts = []

    def fake_request(url, params=None, headers=None):
        calls.append(headers)
        if len(calls) == 1:
            return DummyResponse(status_code=401)
        return DummyResponse(payload={"results": [{"id": 1}]})

    def fake_post(url, data=None, timeout=30):
        posts.append(data)
        return DummyResponse(payload={"access_token": "new", "refresh_token": "new-ref"})

    monkeypatch.setattr("biodbs.fetch.LPSN.lpsn_fetcher.request_with_retry", fake_request)
    monkeypatch.setattr("biodbs.fetch.LPSN.lpsn_fetcher.requests.post", fake_post)

    data = LPSN_Fetcher(token="old", refresh_token="ref").fetch(1)

    assert data.ids() == [1]
    assert posts[0]["grant_type"] == "refresh_token"
    assert calls[1] == {"Authorization": "Bearer new"}


def test_advanced_search_converts_pythonic_params(monkeypatch):
    seen = {}

    def fake_request(url, params=None, headers=None):
        seen.update(params)
        return DummyResponse(payload={"results": [1]})

    monkeypatch.setattr("biodbs.fetch.LPSN.lpsn_fetcher.request_with_retry", fake_request)

    result = LPSN_Fetcher(token="abc").advanced_search(
        taxon_name="Bacillus",
        validly_published="yes",
        correct_name="yes",
        page=2,
    )

    assert result.ids() == [1]
    assert seen == {
        "taxon-name": "Bacillus",
        "validly-published": "yes",
        "correct-name": "yes",
        "page": 2,
    }


def test_flexible_search_encodes_json_and_negation(monkeypatch):
    seen = {}

    def fake_request(url, params=None, headers=None):
        seen.update(params)
        return DummyResponse(payload={"results": [3]})

    monkeypatch.setattr("biodbs.fetch.LPSN.lpsn_fetcher.request_with_retry", fake_request)

    result = LPSN_Fetcher(token="abc").flexible_search({"category": "species"}, negate=True)

    assert result.ids() == [3]
    assert seen == {"search": '{"category": "species"}', "page": 0, "not": "yes"}


def test_missing_credentials_raise_clear_error(monkeypatch):
    monkeypatch.delenv("BIODBS_LPSN_TOKEN", raising=False)
    monkeypatch.delenv("BIODBS_LPSN_USERNAME", raising=False)
    monkeypatch.delenv("BIODBS_LPSN_PASSWORD", raising=False)

    with pytest.raises(APIError, match="LPSN authentication requires"):
        LPSN_Fetcher().fetch(1)


def test_username_password_login(monkeypatch):
    posted = {}

    def fake_post(url, data=None, timeout=30):
        posted.update(data)
        return DummyResponse(payload={"access_token": "tok", "refresh_token": "ref"})

    def fake_request(url, params=None, headers=None):
        assert headers == {"Authorization": "Bearer tok"}
        return DummyResponse(payload={"results": [{"id": 1}]})

    monkeypatch.setattr("biodbs.fetch.LPSN.lpsn_fetcher.requests.post", fake_post)
    monkeypatch.setattr("biodbs.fetch.LPSN.lpsn_fetcher.request_with_retry", fake_request)

    data = LPSN_Fetcher(username="u", password="p").fetch(1)

    assert len(data) == 1
    assert posted["grant_type"] == "password"
    assert posted["client_id"] == "api.lpsn.public"


def test_search_and_fetch(monkeypatch):
    fetcher = LPSN_Fetcher(token="abc")
    calls = []

    def fake_search(**params):
        calls.append(params)
        next_url = "next" if params["page"] == 0 else None
        return type("R", (), {"next": next_url, "ids": lambda self: [params["page"] + 1]})()

    monkeypatch.setattr(fetcher, "advanced_search", fake_search)
    monkeypatch.setattr(fetcher, "fetch", lambda ids: ids)

    assert fetcher.search_and_fetch(category="species") == [1, 2]
    assert calls == [{"page": 0, "category": "species"}, {"page": 1, "category": "species"}]
