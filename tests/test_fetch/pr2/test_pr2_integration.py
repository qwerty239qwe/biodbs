"""Live integration tests for the PR2 fetcher (network required).

Run with:  uv run python -m pytest -m integration tests/test_fetch/pr2
"""

import pytest

from biodbs.fetch.PR2 import PR2_Fetcher

pytestmark = pytest.mark.integration


def test_list_releases_live():
    releases = PR2_Fetcher().list_releases()

    assert len(releases) > 0
    latest = releases[0]
    assert latest.tag  # non-empty tag
    assert len(latest.assets) > 0


def test_list_assets_latest_has_fasta_live():
    assets = PR2_Fetcher().list_assets()

    names = assets.names()
    assert names
    assert any(name.endswith(".gz") for name in names)
