"""Offline tests for the PR2 fetcher."""

import pytest

from biodbs.fetch.PR2.pr2_fetcher import PR2_Fetcher


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


RELEASES_JSON = [
    {
        "tag_name": "v5.0.0",
        "html_url": "https://github.com/pr2database/pr2database/releases/tag/v5.0.0",
        "published_at": "2023-01-01T00:00:00Z",
        "assets": [
            {
                "name": "pr2_version_5.0.0_SSU_taxo_long.fasta.gz",
                "browser_download_url": "https://example.org/ssu.fasta.gz",
                "size": 100,
            },
            {
                "name": "pr2_version_5.0.0_SSU_UTAX.fasta.gz",
                "browser_download_url": "https://example.org/utax.fasta.gz",
                "size": 50,
            },
        ],
    },
    {
        "tag_name": "v4.14.0",
        "html_url": "https://github.com/pr2database/pr2database/releases/tag/v4.14.0",
        "published_at": "2021-01-01T00:00:00Z",
        "assets": [
            {
                "name": "pr2_version_4.14.0_SSU_taxo_long.fasta.gz",
                "browser_download_url": "https://example.org/old.fasta.gz",
                "size": 90,
            }
        ],
    },
]


def _patch_releases(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.PR2.pr2_fetcher.request_with_retry",
        lambda url, stream=False: DummyResponse(json=RELEASES_JSON),
    )


def test_list_releases(monkeypatch):
    _patch_releases(monkeypatch)

    data = PR2_Fetcher().list_releases()

    assert data.names() == ["v5.0.0", "v4.14.0"]
    assert len(data["v5.0.0"].assets) == 2
    assert data["v5.0.0"].url.endswith("/tag/v5.0.0")


def test_list_assets_defaults_to_latest(monkeypatch):
    _patch_releases(monkeypatch)

    data = PR2_Fetcher().list_assets()

    assert data.names() == [
        "pr2_version_5.0.0_SSU_taxo_long.fasta.gz",
        "pr2_version_5.0.0_SSU_UTAX.fasta.gz",
    ]


def test_list_assets_by_tag(monkeypatch):
    _patch_releases(monkeypatch)

    data = PR2_Fetcher().list_assets(tag="v4.14.0")

    assert data.names() == ["pr2_version_4.14.0_SSU_taxo_long.fasta.gz"]


def test_list_assets_unknown_tag_raises(monkeypatch):
    _patch_releases(monkeypatch)

    with pytest.raises(ValueError, match="Unknown PR2 release tag"):
        PR2_Fetcher().list_assets(tag="v9.9.9")


def test_download_asset(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        if url.endswith("/releases"):
            return DummyResponse(json=RELEASES_JSON)
        return DummyResponse(content=b"seqdata")

    monkeypatch.setattr("biodbs.fetch.PR2.pr2_fetcher.request_with_retry", fake_request)
    fetcher = PR2_Fetcher()

    path = fetcher.download_asset("pr2_version_5.0.0_SSU_UTAX.fasta.gz", tmp_path)

    assert path == tmp_path / "pr2_version_5.0.0_SSU_UTAX.fasta.gz"
    assert path.read_bytes() == b"seqdata"
    # second call is served from disk, no new download
    assert fetcher.download_asset("pr2_version_5.0.0_SSU_UTAX.fasta.gz", tmp_path) == path
    stream_calls = [c for c in calls if c[1] is True]
    assert len(stream_calls) == 1
    assert stream_calls[0][0] == "https://example.org/utax.fasta.gz"


def test_download_asset_unknown_name_raises(tmp_path, monkeypatch):
    _patch_releases(monkeypatch)

    with pytest.raises(ValueError, match="Unknown PR2 asset"):
        PR2_Fetcher().download_asset("nope.fasta.gz", tmp_path)
