"""Offline tests for SILVA data wrappers."""

import pytest

from biodbs.data.SILVA import SILVAFile, SILVAFileListData, SILVARelease, SILVAReleaseListData, SILVATextData


def test_file_list_helpers():
    data = SILVAFileListData(
        [
            SILVAFile("README.txt", "https://example/README.txt"),
            SILVAFile("QIIME2", "https://example/QIIME2/", is_dir=True),
        ]
    )

    assert len(data) == 2
    assert data["README.txt"].url.endswith("README.txt")
    assert data.names() == ["README.txt", "QIIME2"]
    assert data.filter("*.txt").names() == ["README.txt"]
    assert list(data.as_dataframe()["name"]) == ["README.txt", "QIIME2"]


def test_release_list_helpers():
    data = SILVAReleaseListData([SILVARelease("release_138", "https://example/release_138/")])

    assert data["release_138"].url.endswith("/")
    assert data.names() == ["release_138"]
    assert data.as_dict()[0]["name"] == "release_138"


def test_text_data():
    data = SILVATextData("SILVA 138", url="https://example/VERSION.txt")

    assert str(data) == "SILVA 138"
    assert data.as_dict()["url"].endswith("VERSION.txt")


def test_unsupported_engine_raises():
    with pytest.raises(ValueError):
        SILVAFileListData([]).as_dataframe(engine="polars")

