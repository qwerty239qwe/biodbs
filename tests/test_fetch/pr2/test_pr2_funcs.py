"""Tests for PR2 convenience functions."""

from biodbs.fetch.PR2 import funcs
from tests.test_fetch.pr2.test_pr2_fetcher import DummyResponse, RELEASES_JSON


def test_pr2_list_releases_delegates(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.PR2.pr2_fetcher.request_with_retry",
        lambda url, stream=False: DummyResponse(json=RELEASES_JSON),
    )

    data = funcs.pr2_list_releases()

    assert data.names() == ["v5.0.0", "v4.14.0"]


def test_pr2_list_assets_delegates(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.PR2.pr2_fetcher.request_with_retry",
        lambda url, stream=False: DummyResponse(json=RELEASES_JSON),
    )

    data = funcs.pr2_list_assets()

    assert data.names()[0] == "pr2_version_5.0.0_SSU_taxo_long.fasta.gz"
