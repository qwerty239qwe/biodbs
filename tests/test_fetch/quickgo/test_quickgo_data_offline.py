"""Offline tests for QuickGO parsed data helpers."""

import pytest

from biodbs.data.QuickGO.data import QuickGODataManager, QuickGOFetchedData


def test_quickgo_json_results_metadata_and_repr():
    data = QuickGOFetchedData(
        {
            "results": [{"id": "GO:0006915", "name": "apoptotic process"}],
            "numberOfHits": 12,
            "pageInfo": {"current": 1, "total": 3},
        },
        endpoint="search",
    )

    assert len(data) == 1
    assert data.get_total_hits() == 12
    assert data.get_page_info()["current"] == 1
    assert "total=12" in repr(data)
    assert "GO:0006915" in repr(data)


def test_quickgo_search_hits_and_list_json_formats():
    hits = QuickGOFetchedData(
        {"searchHits": [{"id": "UniProtKB:P04637"}], "numberOfHits": 1},
        endpoint="search",
    )
    listed = QuickGOFetchedData('[{"id": "GO:1"}, {"id": "GO:2"}]', endpoint="terms")

    assert hits.results == [{"id": "UniProtKB:P04637"}]
    assert hits.metadata["numberOfHits"] == 1
    assert len(listed) == 2


def test_quickgo_tsv_bytes_parses_comments_and_short_rows():
    content = b"Gene\tGO ID\tEvidence\nTP53\tGO:0006915\tIDA\n!ignored\nBRCA1\tGO:1\n"
    data = QuickGOFetchedData(content, endpoint="downloadSearch", download_format="tsv")

    assert data.text.startswith("Gene")
    assert data.results == [
        {"Gene": "TP53", "GO ID": "GO:0006915", "Evidence": "IDA"},
        {"Gene": "BRCA1", "GO ID": "GO:1", "Evidence": None},
    ]


def test_quickgo_gaf_and_gpad_parsers_skip_comments():
    gaf_line = (
        "!gaf-version: 2.2\n"
        "UniProtKB\tP04637\tTP53\t\tGO:0006915\tPMID:1\tIDA\t\tP\tp53\t\t"
        "protein\ttaxon:9606\t20200101\tUniProt\t\t\n"
    )
    gpad_line = (
        "!gpa-version: 2.0\n"
        "UniProtKB:P04637\t\tinvolved_in\tGO:0006915\tPMID:1\tIDA\t\t\t"
        "20200101\tUniProt\t\t\n"
    )

    gaf = QuickGOFetchedData(gaf_line, endpoint="downloadSearch", download_format="gaf")
    gpad = QuickGOFetchedData(gpad_line, endpoint="downloadSearch", download_format="gpad")

    assert gaf.results[0]["db_object_symbol"] == "TP53"
    assert gaf.results[0]["go_id"] == "GO:0006915"
    assert gpad.results[0]["relation"] == "involved_in"
    assert gpad.results[0]["go_id"] == "GO:0006915"


def test_quickgo_dataframe_flatten_filter_and_columns():
    data = QuickGOFetchedData(
        {
            "results": [
                {"id": "GO:1", "nested": {"name": "one"}, "score": 2},
                {"id": "GO:2", "nested": {"name": "two"}, "score": 9},
            ]
        },
        endpoint="search",
    )

    df = data.as_dataframe(columns=["id", "nested"], flatten=True)
    assert "nested.name" in df.columns
    assert data.show_columns() == ["id", "nested", "score"]

    filtered = data.filter(score=lambda value: value > 5)
    assert filtered.results == [{"id": "GO:2", "nested": {"name": "two"}, "score": 9}]
    assert data.filter(missing="x").results == []


def test_quickgo_empty_text_dataframe_error_and_polars_schema():
    text_data = QuickGOFetchedData("plain text response", endpoint="about")
    empty = QuickGOFetchedData({}, endpoint="search")

    with pytest.raises(ValueError, match="text data"):
        text_data.as_dataframe()

    assert list(empty.as_dataframe(columns=["id"]).columns) == ["id"]
    assert empty.as_dataframe(columns=["id"], engine="polars").schema["id"].__class__.__name__


def test_quickgo_iadd_requires_matching_format():
    left = QuickGOFetchedData({"results": [{"id": "GO:1"}]}, endpoint="search")
    right = QuickGOFetchedData({"results": [{"id": "GO:2"}]}, endpoint="search")
    left += right
    assert [row["id"] for row in left.results] == ["GO:1", "GO:2"]

    with pytest.raises(ValueError, match="different formats"):
        left += QuickGOFetchedData("Gene\tGO\nTP53\tGO:1\n", "downloadSearch", "tsv")


def test_quickgo_data_manager_saves_formats(tmp_path):
    manager = QuickGODataManager(tmp_path)
    json_data = QuickGOFetchedData({"results": [{"id": "GO:1"}]}, endpoint="search")
    tsv_data = QuickGOFetchedData(
        "Gene\tGO\nTP53\tGO:0006915\n",
        endpoint="downloadSearch",
        download_format="tsv",
    )

    assert manager.save_quickgo_data(json_data, "terms", fmt="json").exists()
    assert manager.save_quickgo_data(json_data, "terms", fmt="csv").exists()
    assert manager.save_quickgo_data(json_data, "terms", fmt="jsonl").exists()
    assert manager.save_quickgo_data(tsv_data, "annotations", fmt="tsv").read_text() == tsv_data.text

    with pytest.raises(ValueError, match="Cannot save format"):
        manager.save_quickgo_data(json_data, "bad", fmt="gaf")
