"""Offline tests for KEGG fetched data parsers and storage."""

import pytest

from biodbs.data.KEGG.data import KEGGDataManager, KEGGFetchedData


def test_kegg_tabular_parse_index_filter_dataframe_and_text(tmp_path):
    data = KEGGFetchedData("hsa:7157\tTP53 tumor protein\nhsa:672\tBRCA1\n", "list")

    assert data.format == "tabular"
    assert data[0]["entry_id"] == "hsa:7157"
    assert data["hsa:672"]["description"] == "BRCA1"
    assert [row["entry_id"] for row in data] == ["hsa:7157", "hsa:672"]
    assert data.get_entry("missing") is None
    assert data.show_columns() == ["description", "entry_id"]
    assert data.filter(entry_id=lambda value: value.endswith("7157")).records[0]["description"]
    assert "entry_id" in data.as_dataframe().columns
    assert "entry_id" in data.as_dataframe(engine="polars").columns

    out = tmp_path / "kegg.tsv"
    data.to_text(str(out))
    assert "hsa:7157" in out.read_text()


def test_kegg_tabular_extra_columns_and_type_errors():
    data = KEGGFetchedData("drugA\tdrugB\tsynergy\textra1\textra2\n", "ddi")

    assert data.records[0]["extra"] == ["extra1", "extra2"]
    with pytest.raises(KeyError):
        _ = data["missing"]
    with pytest.raises(TypeError):
        _ = data[object()]


def test_kegg_flat_file_fasta_json_binary_and_dataframe_errors(tmp_path):
    flat = KEGGFetchedData(
        "ENTRY       hsa:7157\nNAME        TP53\nPATHWAY     hsa04115 p53 signaling\n"
        "            hsa04210 Apoptosis\n///\n",
        "get",
    )
    fasta = KEGGFetchedData(">hsa:7157 TP53\nMEEPQ\nSDPSV\n", "get", "aaseq")
    json_data = KEGGFetchedData('{"entry": "hsa:7157"}', "get", "json")
    binary = KEGGFetchedData(b"PNG", "get", "image")
    text = KEGGFetchedData("KEGG database info", "info")

    assert flat.records[0]["ENTRY"] == "hsa:7157"
    assert flat.records[0]["PATHWAY"] == ["hsa04115 p53 signaling", "hsa04210 Apoptosis"]
    assert fasta.records[0]["sequence"] == "MEEPQSDPSV"
    assert json_data.json_data == {"entry": "hsa:7157"}
    assert binary.binary_data == b"PNG"
    assert text.text == "KEGG database info"

    image = tmp_path / "image.png"
    binary.to_binary(str(image))
    assert image.read_bytes() == b"PNG"

    with pytest.raises(ValueError, match="binary data"):
        binary.as_dataframe()
    with pytest.raises(ValueError, match="JSON data"):
        json_data.as_dataframe()
    with pytest.raises(ValueError, match="text data"):
        text.as_dataframe()


def test_kegg_iadd_and_data_manager(tmp_path):
    left = KEGGFetchedData("hsa:1\tone\n", "list")
    right = KEGGFetchedData("hsa:2\ttwo\n", "list")
    left += right
    assert [row["entry_id"] for row in left.records] == ["hsa:1", "hsa:2"]

    with pytest.raises(ValueError, match="different formats"):
        left += KEGGFetchedData("info", "info")

    manager = KEGGDataManager(tmp_path)
    assert manager.save_kegg_data(left, "genes", fmt="csv").exists()
    assert manager.save_kegg_data(left, "genes", fmt="json").exists()
    assert manager.save_kegg_data(left, "genes", fmt="jsonl").exists()
    text = KEGGFetchedData("info", "info")
    assert manager.save_kegg_data(text, "info", fmt="text").read_text() == "info"

    with pytest.raises(ValueError, match="Cannot save format"):
        manager.save_kegg_data(text, "bad", fmt="csv")
