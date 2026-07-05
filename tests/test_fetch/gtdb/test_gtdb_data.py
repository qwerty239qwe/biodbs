"""Offline tests for GTDB data wrappers."""

import pandas as pd

from biodbs.data.GTDB import GTDBFile, GTDBFileListData, GTDBTableData, GTDBTextData


def test_file_list_data_helpers():
    data = GTDBFileListData(
        [
            GTDBFile("release232", "https://example.org/release232/", is_dir=True),
            GTDBFile("VERSION.txt", "https://example.org/latest/VERSION.txt"),
        ]
    )

    assert len(data) == 2
    assert data["release232"].is_dir is True
    assert data.names() == ["release232", "VERSION.txt"]
    assert data.filter("*.txt").names() == ["VERSION.txt"]
    assert isinstance(data.as_dataframe(), pd.DataFrame)


def test_table_data_parses_tsv():
    data = GTDBTableData("accession\tclassification\nG1\td__Bacteria\n")

    assert len(data) == 1
    assert data[0]["classification"] == "d__Bacteria"
    assert data.as_dataframe()["accession"].iloc[0] == "G1"


def test_table_data_parses_headerless_tsv_with_fieldnames():
    data = GTDBTableData("G1\td__Bacteria\n", fieldnames=["accession", "classification"])

    assert data[0] == {"accession": "G1", "classification": "d__Bacteria"}


def test_text_data():
    data = GTDBTextData("R232\n", url="https://example.org/VERSION.txt")

    assert str(data) == "R232\n"
    assert data.as_dict()["url"].endswith("VERSION.txt")
