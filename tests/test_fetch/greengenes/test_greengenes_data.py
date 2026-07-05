"""Tests for GreenGenes data wrappers."""

import pytest

from biodbs.data.GreenGenes import (
    GreenGenesFile,
    GreenGenesRelease,
    GreenGenesFileListData,
    GreenGenesReleaseListData,
)


def test_file_list_names_urls_getitem_filter():
    files = [
        GreenGenesFile("99_otus.fasta", "https://x/99_otus.fasta"),
        GreenGenesFile("97_otus.fasta", "https://x/97_otus.fasta"),
        GreenGenesFile("taxonomy", "https://x/taxonomy/", is_dir=True),
    ]
    data = GreenGenesFileListData(files)

    assert data.names() == ["99_otus.fasta", "97_otus.fasta", "taxonomy"]
    assert data.urls()[0] == "https://x/99_otus.fasta"
    assert data["taxonomy"].is_dir is True
    assert data.filter("*.fasta").names() == ["99_otus.fasta", "97_otus.fasta"]


def test_file_list_getitem_missing_raises():
    with pytest.raises(KeyError):
        GreenGenesFileListData([])["missing"]


def test_release_list_names_and_dataframe():
    releases = [
        GreenGenesRelease("gg_13_8_otus", "https://x/gg_13_8_otus/"),
        GreenGenesRelease("2022.10", "https://x/2022.10/"),
    ]
    data = GreenGenesReleaseListData(releases)

    assert data.names() == ["gg_13_8_otus", "2022.10"]
    assert list(data.as_dataframe()["name"]) == ["gg_13_8_otus", "2022.10"]
