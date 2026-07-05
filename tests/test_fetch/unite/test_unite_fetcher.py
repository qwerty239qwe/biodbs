"""Offline tests for the UNITE fetcher."""

import pytest

from biodbs.fetch.UNITE.unite_fetcher import UNITE_Fetcher, UNITE_DOIS

MEDIA_URL = "https://files.plutof.ut.ee/public/orig/AB/CD/sh_qiime_release_19.02.2025.tgz"
DOI_JSON = {"data": [{"attributes": {"media": [
    {"url": "https://old/older.tgz"},
    {"url": MEDIA_URL},
]}}]}


class DummyResponse:
    def __init__(self, status_code=200, json=None, content=b""):
        self.status_code = status_code
        self._json = json
        self.content = content
        self.text = ""
        self.headers = {}

    def json(self):
        return self._json

    def iter_content(self, chunk_size=8192):
        yield self.content


def test_resolve_doi_known_combo():
    doi = UNITE_Fetcher().resolve_doi("2025-02-19", "fungi", singletons=False)

    assert doi == "10.15156/BIO/3301241"


def test_resolve_doi_unknown_version_raises():
    with pytest.raises(ValueError, match="version"):
        UNITE_Fetcher().resolve_doi("1999-01-01", "fungi")


def test_resolve_doi_unknown_taxon_group_raises():
    with pytest.raises(ValueError, match="taxon_group"):
        UNITE_Fetcher().resolve_doi("2025-02-19", "plants")


def test_get_download_url_returns_newest_media(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.UNITE.unite_fetcher.request_with_retry",
        lambda url, stream=False: DummyResponse(json=DOI_JSON),
    )

    url = UNITE_Fetcher().get_download_url("2025-02-19", "fungi")

    assert url == MEDIA_URL


def test_download(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        if url.startswith("https://api.plutof.ut.ee"):
            return DummyResponse(json=DOI_JSON)
        return DummyResponse(content=b"tgzbytes")

    monkeypatch.setattr("biodbs.fetch.UNITE.unite_fetcher.request_with_retry", fake_request)
    fetcher = UNITE_Fetcher()

    path = fetcher.download("2025-02-19", tmp_path, "fungi")

    assert path == tmp_path / "sh_qiime_release_19.02.2025.tgz"
    assert path.read_bytes() == b"tgzbytes"
    stream_calls = [c for c in calls if c[1] is True]
    assert len(stream_calls) == 1
    assert stream_calls[0][0] == MEDIA_URL


def test_doi_table_covers_expected_versions():
    assert "2025-02-19" in UNITE_DOIS
    assert set(UNITE_DOIS["2025-02-19"]) == {"fungi", "eukaryotes"}
