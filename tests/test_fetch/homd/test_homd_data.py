"""Offline tests for HOMD data wrappers."""

import pandas as pd

from biodbs.data.HOMD import HOMDFile, HOMDFileListData, HOMDTableData, HOMDTextData


def test_file_list_data_helpers():
    data = HOMDFileListData(
        [
            HOMDFile("taxa.tsv", "https://example.org/taxa.tsv"),
            HOMDFile("genomes/", "https://example.org/genomes/", is_dir=True),
        ]
    )

    assert len(data) == 2
    assert data["taxa.tsv"].url.endswith("taxa.tsv")
    assert data.names() == ["taxa.tsv", "genomes/"]
    assert data.filter("*.tsv").names() == ["taxa.tsv"]
    assert isinstance(data.as_dataframe(), pd.DataFrame)


def test_table_data_parses_tsv():
    data = HOMDTableData("id\tname\n1\tStreptococcus\n")

    assert len(data) == 1
    assert data[0]["name"] == "Streptococcus"
    assert data.as_dataframe()["id"].iloc[0] == "1"


def test_text_data():
    data = HOMDTextData(">seq\nACGT\n", url="https://example.org/seq.fa")

    assert str(data).startswith(">seq")
    assert data.as_dict()["url"].endswith("seq.fa")
