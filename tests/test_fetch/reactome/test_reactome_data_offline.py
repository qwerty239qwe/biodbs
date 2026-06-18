"""Additional offline branch tests for Reactome data containers."""

import pytest

from biodbs.data.Reactome.data import (
    ReactomeDataManager,
    ReactomeFetchedData,
    ReactomePathwaysData,
    ReactomeSpeciesData,
)


def _analysis_payload():
    return {
        "summary": {"token": "tok-1"},
        "identifiersNotFound": 1,
        "warnings": ["warn"],
        "pathways": [
            {
                "stId": "R-HSA-2",
                "dbId": 2,
                "name": "Later",
                "llp": False,
                "inDisease": True,
                "entities": {"found": 1, "total": 10, "ratio": 0.1, "pValue": 0.2, "fdr": 0.2},
                "reactions": {"found": 2, "total": 20, "ratio": 0.1},
                "species": {"dbId": 1, "taxId": "9606", "name": "Homo sapiens"},
            },
            {
                "stId": "R-HSA-1",
                "dbId": 1,
                "name": "Apoptosis",
                "llp": True,
                "inDisease": False,
                "entities": {"found": 5, "total": 50, "ratio": 0.1, "pValue": 0.001, "fdr": 0.01},
            },
        ],
    }


def test_reactome_analysis_views_and_filters():
    data = ReactomeFetchedData(_analysis_payload(), query_identifiers=["TP53", "BRCA1"])

    assert data.token == "tok-1"
    assert len(data) == 2
    assert "significant" in repr(data)
    assert data.get_pathway_ids() == ["R-HSA-2", "R-HSA-1"]
    assert data.get_pathway_names() == ["Later", "Apoptosis"]
    assert data.get_pathway("R-HSA-1").name == "Apoptosis"
    assert data.get_pathway("missing") is None
    assert data.significant_pathways().get_pathway_ids() == ["R-HSA-1"]
    assert data.top_pathways(1).get_pathway_ids() == ["R-HSA-1"]
    assert data.filter(llp=True).get_pathway_ids() == ["R-HSA-1"]
    assert data.filter(fdr=lambda value: value < 0.05).get_pathway_ids() == ["R-HSA-1"]
    assert "Warnings: 1" in data.summary()

    df = data.as_dataframe()
    assert df.iloc[0]["stId"] == "R-HSA-1"
    assert "species" in data.as_dataframe(engine="polars").columns
    assert data.as_dataframe(columns=["stId"], flatten=True).columns.tolist() == ["stId"]
    assert "reactions_found" in data.show_columns()


def test_reactome_empty_and_iadd():
    empty = ReactomeFetchedData([])
    assert len(empty) == 0
    assert empty.as_dataframe().empty
    assert empty.as_dataframe(engine="polars").is_empty()

    left = ReactomeFetchedData(_analysis_payload())
    right = ReactomeFetchedData({"pathways": [_analysis_payload()["pathways"][0]]})
    left += right
    assert len(left) == 3


def test_reactome_pathways_species_and_manager(tmp_path):
    pathways = ReactomePathwaysData(
        [{"stId": "R-HSA-1", "displayName": "Apoptosis", "nested": {"x": 1}}]
    )
    species = ReactomeSpeciesData(
        [
            {"displayName": "Homo sapiens", "shortName": "human", "taxId": "9606"},
            {"displayName": "Mus musculus", "shortName": "mouse", "taxId": "10090"},
        ]
    )

    assert len(pathways) == 1
    assert "Apoptosis" in repr(pathways)
    assert pathways.as_dict(columns=["stId"]) == [{"stId": "R-HSA-1"}]
    assert "nested.x" in pathways.as_dataframe(flatten=True).columns
    assert pathways.as_dataframe(engine="polars").height == 1
    assert pathways.get_pathway_ids() == ["R-HSA-1"]
    assert pathways.get_pathway_names() == ["Apoptosis"]
    assert ReactomePathwaysData({}).pathways == [{}]
    assert ReactomePathwaysData("bad").pathways == []

    assert len(species) == 2
    assert "Homo sapiens" in repr(species)
    assert species.as_dict(columns=["taxId"]) == [{"taxId": "9606"}, {"taxId": "10090"}]
    assert species.as_dataframe(engine="polars").height == 2
    assert species.get_species_names() == ["Homo sapiens", "Mus musculus"]
    assert species.get_species_by_name("human")["taxId"] == "9606"
    assert species.get_taxon_id("mouse") == "10090"
    assert species.get_taxon_id("rat") is None

    manager = ReactomeDataManager(tmp_path)
    analysis = ReactomeFetchedData(_analysis_payload())
    assert manager.save_analysis_data(analysis, "analysis", fmt="csv").exists()
    assert manager.save_analysis_data(analysis, "analysis", fmt="json").exists()
    assert manager.save_analysis_data(analysis, "analysis", fmt="jsonl").exists()
    with pytest.raises(ValueError, match="Cannot save format"):
        manager.save_analysis_data(ReactomeFetchedData({}), "empty", fmt="csv")
