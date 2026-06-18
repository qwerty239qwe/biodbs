"""Additional branch tests for PubChem data containers."""

import pytest

from biodbs.data.PubChem.data import PubChemDataManager, PUGRestFetchedData, PUGViewFetchedData


def test_pug_rest_response_shapes_and_helpers(tmp_path):
    assert PUGRestFetchedData({"IdentifierList": {"SID": [1]}}).get_sids() == [1]
    assert PUGRestFetchedData({"IdentifierList": {"AID": [2]}}).results == [{"AID": 2}]
    assert PUGRestFetchedData({"PC_AssayContainer": [{"aid": 1}]}).results == [{"aid": 1}]
    assert PUGRestFetchedData(
        {"Table": {"Columns": {"Column": ["CID", "Name"]}, "Row": [{"Cell": [2244, "aspirin"]}]}}
    ).results == [{"CID": 2244, "Name": "aspirin"}]
    assert PUGRestFetchedData({"Waiting": {}}).results == []
    assert PUGRestFetchedData({"Wrapped": {"CID": 2244}}).results == [{"CID": 2244}]
    assert PUGRestFetchedData({"Wrapped": [{"CID": 2244}]}).results == [{"CID": 2244}]
    assert PUGRestFetchedData(["bad"]).results == []

    compound = PUGRestFetchedData(
        {
            "PC_Compounds": [
                {
                    "id": {"id": {"cid": 2244}},
                    "props": [
                        {"urn": {"label": "Molecular Formula"}, "value": {"sval": "C9H8O4"}},
                        {"urn": {"label": "Molecular Weight"}, "value": {"fval": 180.16}},
                    ],
                    "count": {"heavy_atom": 13},
                    "charge": 0,
                    "nested": {"value": 5},
                }
            ]
        },
        domain="compound",
    )
    assert compound.get_cids() == [2244]
    assert "domain='compound'" in repr(compound)
    assert "Molecular_Formula" in compound.get_properties_df().columns
    assert compound.get_properties_df(engine="polars").height == 1
    assert "nested.value" in compound.show_columns()
    assert compound.format_results(["id.id.cid"]) == [{"id.id.cid": 2244}]
    assert compound.format_results(["missing"], safe_check=False) == [{"missing": None}]
    with pytest.raises(ValueError, match="not valid"):
        compound.format_results(["missing"])
    assert compound.as_dataframe(flatten=True).iloc[0]["nested.value"] == 5
    assert compound.as_dataframe(engine="polars").height == 1
    assert compound.filter(**{"id.id.cid": 2244}).results
    assert compound.filter(**{"id.id.cid": lambda cid: cid == 2244}).results
    assert not compound.filter(**{"id.id.cid": 1}).results

    binary = PUGRestFetchedData(b"SDF")
    with pytest.raises(ValueError, match="binary data"):
        binary.as_dataframe()
    sdf = tmp_path / "compound.sdf"
    png = tmp_path / "compound.png"
    binary.to_sdf(str(sdf))
    binary.to_image(str(png))
    assert sdf.read_bytes() == b"SDF"
    assert png.read_bytes() == b"SDF"

    text = PUGRestFetchedData("mol text")
    text_path = tmp_path / "compound.txt"
    text.to_sdf(str(text_path))
    assert text_path.read_text() == "mol text"


def test_pug_rest_errors_and_data_manager(tmp_path):
    fault = PUGRestFetchedData({"Fault": {"Message": "bad request"}})
    assert fault.has_error()
    assert fault.get_error_message() == "bad request"
    assert not PUGRestFetchedData({}).has_error()

    manager = PubChemDataManager(tmp_path)
    data = PUGRestFetchedData({"IdentifierList": {"CID": [2244]}})
    assert manager.save_rest_data(data, "cids", fmt="csv").exists()
    assert manager.save_rest_data(data, "cids", fmt="json").exists()
    assert manager.save_rest_data(data, "cids", fmt="jsonl").exists()
    assert manager.save_rest_data(PUGRestFetchedData(b"SDF"), "compound", fmt="sdf").exists()
    with pytest.raises(ValueError, match="Cannot save format"):
        manager.save_rest_data(PUGRestFetchedData({}), "empty", fmt="csv")


def test_pug_view_navigation_errors_and_manager(tmp_path):
    content = {
        "Record": {
            "RecordNumber": 2244,
            "Section": [
                {
                    "TOCHeading": "Names and Identifiers",
                    "Section": [
                        {
                            "TOCHeading": "Computed Descriptors",
                            "Information": [{"Name": "IUPAC Name", "Value": {"StringWithMarkup": [{"String": "x"}]}}],
                        }
                    ],
                },
                {"TOCHeading": "Safety", "Information": [{"Name": "Signal"}]},
            ],
        }
    }
    view = PUGViewFetchedData(content, record_type="compound")

    assert view.record_id == 2244
    assert "compound" in repr(view)
    assert view.get_section("Safety")["TOCHeading"] == "Safety"
    assert view.get_section("Missing") is None
    assert view.get_all_headings() == ["Names and Identifiers", "Safety"]
    assert view.get_information("Safety") == [{"Name": "Signal"}]
    assert view.get_subsections("Names and Identifiers")[0]["TOCHeading"] == "Computed Descriptors"
    assert view.find_value("Names and Identifiers", "Computed Descriptors") == [
        {"Name": "IUPAC Name", "Value": {"StringWithMarkup": [{"String": "x"}]}}
    ]
    assert view.find_value("Missing") is None
    assert isinstance(view.as_dict(), dict)
    with pytest.raises(ValueError, match="hierarchical"):
        view.as_dataframe()

    fault = PUGViewFetchedData({"Fault": {"Message": "view bad"}})
    assert fault.has_error()
    assert fault.get_error_message() == "view bad"
    assert PUGViewFetchedData("bad").sections == []

    assert PubChemDataManager(tmp_path).save_view_data(view, "view").exists()
