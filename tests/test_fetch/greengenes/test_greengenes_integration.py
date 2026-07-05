"""Live integration tests for the GreenGenes fetcher (network required)."""

import pytest

from biodbs.fetch.GreenGenes import GreenGenes_Fetcher

pytestmark = pytest.mark.integration


def test_list_releases_live():
    releases = GreenGenes_Fetcher().list_releases()

    names = releases.names()
    assert names
    # The 13_8 release has been stable for years.
    assert any("13_8" in name for name in names)


def test_list_files_of_known_release_live():
    files = GreenGenes_Fetcher().list_files("gg_13_8_otus")

    assert len(files) > 0
