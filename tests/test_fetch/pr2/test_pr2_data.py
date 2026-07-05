"""Tests for PR2 data wrappers."""

import pytest

from biodbs.data.PR2 import PR2Asset, PR2Release, PR2AssetListData, PR2ReleaseListData


def _assets():
    return [
        PR2Asset("pr2_SSU_taxo_long.fasta.gz", "https://x/ssu.gz", 100),
        PR2Asset("pr2_SSU_UTAX.fasta.gz", "https://x/utax.gz", 50),
        PR2Asset("pr2_SSU_taxo.xlsx", "https://x/taxo.xlsx", 10),
    ]


def test_asset_list_names_urls_and_getitem():
    data = PR2AssetListData(_assets())

    assert data.names() == ["pr2_SSU_taxo_long.fasta.gz", "pr2_SSU_UTAX.fasta.gz", "pr2_SSU_taxo.xlsx"]
    assert data.urls()[0] == "https://x/ssu.gz"
    assert data["pr2_SSU_UTAX.fasta.gz"].size == 50
    assert data[0].name == "pr2_SSU_taxo_long.fasta.gz"


def test_asset_list_getitem_missing_raises():
    with pytest.raises(KeyError):
        PR2AssetListData(_assets())["missing"]


def test_asset_list_filter():
    data = PR2AssetListData(_assets()).filter("*.fasta.gz")

    assert data.names() == ["pr2_SSU_taxo_long.fasta.gz", "pr2_SSU_UTAX.fasta.gz"]


def test_asset_list_as_dataframe():
    df = PR2AssetListData(_assets()).as_dataframe()

    assert list(df["name"]) == ["pr2_SSU_taxo_long.fasta.gz", "pr2_SSU_UTAX.fasta.gz", "pr2_SSU_taxo.xlsx"]


def test_release_list_names_are_tags_and_getitem():
    releases = [
        PR2Release("v5.0.0", "https://x/v5", "2023-01-01", _assets()),
        PR2Release("v4.14.0", "https://x/v4", "2021-01-01", []),
    ]
    data = PR2ReleaseListData(releases)

    assert data.names() == ["v5.0.0", "v4.14.0"]
    assert data["v5.0.0"].published == "2023-01-01"
    assert data.as_dict()[0]["assets"] == [a.name for a in _assets()]
