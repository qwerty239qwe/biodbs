"""Offline tests for Reactome fetcher endpoints."""

from biodbs.data.Reactome.data import ReactomeFetchedData, ReactomePathwaysData, ReactomeSpeciesData
from biodbs.fetch.Reactome.reactome_fetcher import Reactome_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


ANALYSIS_PAYLOAD = {
    "summary": {"token": "tok-1"},
    "pathways": [{"stId": "R-HSA-1", "name": "Apoptosis", "entities": {"fdr": 0.01}}],
}


def test_reactome_analysis_post_endpoints(monkeypatch):
    calls = []

    def fake_post(url, data=None, params=None, headers=None):
        calls.append((url, data, params, headers))
        return DummyResponse(json_data=ANALYSIS_PAYLOAD)

    monkeypatch.setattr("biodbs.fetch.Reactome.reactome_fetcher.requests.post", fake_post)

    fetcher = Reactome_Fetcher(species="Mus musculus")
    analysis = fetcher.analyze(["TP53", "BRCA1"], interactors=True, min_entities=1)
    projection = fetcher.analyze_projection(["Trp53"], species="Mus musculus")
    mapped = fetcher.map_identifiers(["TP53"], interactors=True)

    assert isinstance(analysis, ReactomeFetchedData)
    assert analysis.token == "tok-1"
    assert projection.token == "tok-1"
    assert mapped == ANALYSIS_PAYLOAD
    assert calls[0][1] == "TP53\nBRCA1"
    assert calls[0][3] == {"Content-Type": "text/plain"}
    assert calls[2][2] == {"interactors": "true"}


def test_reactome_analysis_get_endpoints(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None):
        calls.append((url, params, headers))
        if "notFound" in url or "notfound" in url:
            return DummyResponse(json_data=[{"id": "BAD1"}, {"other": "ignored"}])
        if "foundEntities" in url or "found" in url:
            return DummyResponse(json_data=[{"id": "TP53"}])
        if "download" in url:
            return DummyResponse(json_data={"all": True})
        return DummyResponse(json_data=ANALYSIS_PAYLOAD)

    monkeypatch.setattr("biodbs.fetch.Reactome.reactome_fetcher.requests.get", fake_get)
    fetcher = Reactome_Fetcher()

    assert fetcher.analyze_single("TP53").token == "tok-1"
    assert fetcher.get_result_by_token("tok-1", species="Homo sapiens").token == "tok-1"
    assert fetcher.get_found_entities("tok-1", "R-HSA-1") == [{"id": "TP53"}]
    assert fetcher.get_not_found_identifiers("tok-1") == ["BAD1", ""]
    assert fetcher.download_results_json("tok-1") == {"all": True}
    assert calls[1][1]["species"] == "Homo sapiens"


def test_reactome_content_get_endpoints(monkeypatch):
    def fake_get(url, params=None, headers=None):
        if "version" in url:
            return DummyResponse(text="90")
        if "species" in url:
            return DummyResponse(json_data=[{"taxId": 9606, "displayName": "Homo sapiens"}])
        if "topLevelPathways" in url or "low/entity" in url:
            return DummyResponse(json_data=[{"stId": "R-HSA-1", "displayName": "Apoptosis"}])
        return DummyResponse(json_data=[{"id": "R-HSA-1", "name": "Apoptosis"}])

    monkeypatch.setattr("biodbs.fetch.Reactome.reactome_fetcher.requests.get", fake_get)
    fetcher = Reactome_Fetcher()

    assert isinstance(fetcher.get_pathways_top(), ReactomePathwaysData)
    assert fetcher.get_events_hierarchy() == [{"id": "R-HSA-1", "name": "Apoptosis"}]
    assert isinstance(fetcher.get_pathways_for_entity("TP53"), ReactomePathwaysData)
    assert isinstance(fetcher.get_species(), ReactomeSpeciesData)
    assert isinstance(fetcher.get_species_main(), ReactomeSpeciesData)
    assert fetcher.get_database_version() == "90"
    assert fetcher.query_entry("R-HSA-1") == [{"id": "R-HSA-1", "name": "Apoptosis"}]
    assert fetcher.get_participants("R-HSA-1") == [{"id": "R-HSA-1", "name": "Apoptosis"}]
    assert fetcher.get_participants_physical_entities("R-HSA-1")
    assert fetcher.get_participants_reference_entities("R-HSA-1")
    assert fetcher.get_event_ancestors("R-HSA-1")
    assert fetcher.get_complex_subunits("R-HSA-1")
    assert fetcher.get_entity_component_of("R-HSA-1")
    assert fetcher.get_entity_other_forms("R-HSA-1")
    assert fetcher.get_diseases()
    assert fetcher.get_diseases_doid()
    assert fetcher.map_to_reactions("P04637")


def test_reactome_pathway_gene_helpers(monkeypatch):
    fetcher = Reactome_Fetcher()
    refs = [
        {"geneName": ["TP53", "MDM2"], "databaseName": "UniProt", "identifier": "P04637"},
        {"geneName": "BRCA1", "databaseName": "ENSEMBL", "identifier": "ENSG1"},
    ]
    monkeypatch.setattr(fetcher, "get_participants_reference_entities", lambda pathway_id: refs)

    assert set(fetcher.get_pathway_genes("R-HSA-1")) == {"TP53", "MDM2", "BRCA1"}
    assert fetcher.get_pathway_genes("R-HSA-1", id_type="uniprot") == ["P04637"]


def test_reactome_all_pathways_with_genes_hierarchy_and_top(monkeypatch):
    fetcher = Reactome_Fetcher()
    hierarchy = [
        {"stId": "R-HSA-1", "name": "One", "children": [{"stId": "R-HSA-2", "name": "Two"}]}
    ]
    monkeypatch.setattr(fetcher, "get_events_hierarchy", lambda species: hierarchy)
    monkeypatch.setattr(fetcher, "get_pathway_genes", lambda pathway_id, id_type: [pathway_id])

    result = fetcher.get_all_pathways_with_genes()
    assert result["R-HSA-1"] == ("One", {"R-HSA-1"})
    assert result["R-HSA-2"] == ("Two", {"R-HSA-2"})

    top = ReactomePathwaysData([{"stId": "R-HSA-3", "displayName": "Three"}])
    monkeypatch.setattr(fetcher, "get_pathways_top", lambda species: top)
    assert fetcher.get_all_pathways_with_genes(include_hierarchy=False)["R-HSA-3"]
