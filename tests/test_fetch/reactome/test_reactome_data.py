"""Tests for Reactome data models and containers."""

import pytest
from biodbs.data.Reactome.data import (
    ReactomeFetchedData,
    ReactomePathwaysData,
    ReactomeSpeciesData,
)
from biodbs.data.Reactome._data_model import (
    PathwaySummary,
    EntityStatistics,
    ReactionStatistics,
    SpeciesSummary,
    AnalysisRequestModel,
)


class TestEntityStatistics:
    """Tests for EntityStatistics model."""

    def test_default_values(self):
        """Test default values."""
        stats = EntityStatistics()
        assert stats.curatedFound == 0
        assert stats.curatedTotal == 0
        assert stats.found == 0
        assert stats.total == 0
        assert stats.pValue == 1.0
        assert stats.fdr == 1.0

    def test_with_values(self):
        """Test with custom values."""
        stats = EntityStatistics(
            curatedFound=5,
            curatedTotal=10,
            found=8,
            total=20,
            pValue=0.001,
            fdr=0.01,
        )
        assert stats.curatedFound == 5
        assert stats.found == 8
        assert stats.pValue == 0.001


class TestPathwaySummary:
    """Tests for PathwaySummary model."""

    def test_basic_pathway(self):
        """Test basic pathway creation."""
        pathway = PathwaySummary(
            stId="R-HSA-123456",
            dbId=123456,
            name="Test Pathway",
        )
        assert pathway.stId == "R-HSA-123456"
        assert pathway.name == "Test Pathway"
        assert pathway.p_value == 1.0  # Default
        assert pathway.fdr == 1.0  # Default

    def test_pathway_with_entities(self):
        """Test pathway with entity statistics."""
        entities = EntityStatistics(
            found=5,
            total=20,
            pValue=0.001,
            fdr=0.01,
        )
        pathway = PathwaySummary(
            stId="R-HSA-123456",
            dbId=123456,
            name="Test Pathway",
            entities=entities,
        )
        assert pathway.p_value == 0.001
        assert pathway.fdr == 0.01
        assert pathway.found_entities == 5
        assert pathway.total_entities == 20


class TestAnalysisRequestModel:
    """Tests for AnalysisRequestModel."""

    def test_basic_model(self):
        """Test basic request model."""
        model = AnalysisRequestModel(
            identifiers=["TP53", "BRCA1"],
        )
        assert len(model.identifiers) == 2
        assert model.species is None
        assert model.interactors is False

    def test_get_identifiers_string(self):
        """Test identifiers string generation."""
        model = AnalysisRequestModel(
            identifiers=["TP53", "BRCA1", "EGFR"],
        )
        result = model.get_identifiers_string()
        assert result == "TP53\nBRCA1\nEGFR"

    def test_get_params(self):
        """Test parameters generation."""
        model = AnalysisRequestModel(
            identifiers=["TP53"],
            species="Homo sapiens",
            interactors=True,
            pageSize=50,
        )
        params = model.get_params()
        assert params["species"] == "Homo sapiens"
        assert params["interactors"] == "true"
        assert params["pageSize"] == 50


class TestReactomeFetchedData:
    """Tests for ReactomeFetchedData container."""

    @pytest.fixture
    def sample_response(self):
        """Sample Reactome analysis response."""
        return {
            "summary": {"token": "test_token_123"},
            "pathways": [
                {
                    "stId": "R-HSA-123456",
                    "dbId": 123456,
                    "name": "Cell Cycle",
                    "llp": True,
                    "inDisease": False,
                    "entities": {
                        "found": 5,
                        "total": 100,
                        "pValue": 0.001,
                        "fdr": 0.01,
                        "ratio": 0.05,
                    },
                    "reactions": {
                        "found": 3,
                        "total": 20,
                        "ratio": 0.15,
                    },
                },
                {
                    "stId": "R-HSA-789012",
                    "dbId": 789012,
                    "name": "Apoptosis",
                    "llp": False,
                    "inDisease": True,
                    "entities": {
                        "found": 2,
                        "total": 50,
                        "pValue": 0.1,
                        "fdr": 0.2,
                        "ratio": 0.04,
                    },
                },
            ],
            "identifiersNotFound": 1,
            "speciesSummary": [],
            "resourceSummary": [],
        }

    def test_init(self, sample_response):
        """Test initialization."""
        data = ReactomeFetchedData(
            content=sample_response,
            query_identifiers=["TP53", "BRCA1"],
        )
        assert data.token == "test_token_123"
        assert len(data.pathways) == 2
        assert data.identifiers_not_found == 1

    def test_len(self, sample_response):
        """Test __len__."""
        data = ReactomeFetchedData(content=sample_response)
        assert len(data) == 2

    def test_as_dict(self, sample_response):
        """Test as_dict method."""
        data = ReactomeFetchedData(content=sample_response)
        result = data.as_dict()
        assert len(result) == 2
        assert result[0]["stId"] == "R-HSA-123456"
        assert result[0]["fdr"] == 0.01

    def test_as_dataframe(self, sample_response):
        """Test as_dataframe method."""
        data = ReactomeFetchedData(content=sample_response)
        df = data.as_dataframe()
        assert len(df) == 2
        assert "stId" in df.columns
        assert "fdr" in df.columns

    def test_significant_pathways(self, sample_response):
        """Test significant_pathways filter."""
        data = ReactomeFetchedData(content=sample_response)
        sig = data.significant_pathways(fdr_threshold=0.05)
        assert len(sig) == 1
        assert sig.pathways[0].stId == "R-HSA-123456"

    def test_top_pathways(self, sample_response):
        """Test top_pathways method."""
        data = ReactomeFetchedData(content=sample_response)
        top = data.top_pathways(1)
        assert len(top) == 1
        assert top.pathways[0].stId == "R-HSA-123456"

    def test_filter_llp(self, sample_response):
        """Test filter by lowest level pathway."""
        data = ReactomeFetchedData(content=sample_response)
        filtered = data.filter(llp=True)
        assert len(filtered) == 1
        assert filtered.pathways[0].stId == "R-HSA-123456"

    def test_get_pathway_ids(self, sample_response):
        """Test get_pathway_ids method."""
        data = ReactomeFetchedData(content=sample_response)
        ids = data.get_pathway_ids()
        assert ids == ["R-HSA-123456", "R-HSA-789012"]

    def test_get_pathway_names(self, sample_response):
        """Test get_pathway_names method."""
        data = ReactomeFetchedData(content=sample_response)
        names = data.get_pathway_names()
        assert names == ["Cell Cycle", "Apoptosis"]

    def test_get_pathway(self, sample_response):
        """Test get_pathway by ID."""
        data = ReactomeFetchedData(content=sample_response)
        pathway = data.get_pathway("R-HSA-123456")
        assert pathway is not None
        assert pathway.name == "Cell Cycle"

    def test_summary(self, sample_response):
        """Test summary method."""
        data = ReactomeFetchedData(
            content=sample_response,
            query_identifiers=["TP53", "BRCA1"],
        )
        summary = data.summary()
        assert "Reactome Analysis Results" in summary
        assert "R-HSA-123456" in summary

    def test_empty_response(self):
        """Test with empty response."""
        data = ReactomeFetchedData(content={})
        assert len(data) == 0
        assert data.pathways == []


class TestReactomePathwaysData:
    """Tests for ReactomePathwaysData container."""

    def test_with_list(self):
        """Test with list input."""
        pathways = [
            {"stId": "R-HSA-1", "displayName": "Pathway 1"},
            {"stId": "R-HSA-2", "displayName": "Pathway 2"},
        ]
        data = ReactomePathwaysData(content=pathways)
        assert len(data) == 2
        assert data.get_pathway_ids() == ["R-HSA-1", "R-HSA-2"]

    def test_get_pathway_names(self):
        """Test get_pathway_names method."""
        pathways = [
            {"stId": "R-HSA-1", "displayName": "Pathway 1"},
            {"stId": "R-HSA-2", "name": "Pathway 2"},
        ]
        data = ReactomePathwaysData(content=pathways)
        names = data.get_pathway_names()
        assert "Pathway 1" in names
        assert "Pathway 2" in names

    def test_as_dataframe(self):
        """Test as_dataframe method."""
        pathways = [
            {"stId": "R-HSA-1", "displayName": "Pathway 1"},
        ]
        data = ReactomePathwaysData(content=pathways)
        df = data.as_dataframe()
        assert len(df) == 1


class TestReactomeSpeciesData:
    """Tests for ReactomeSpeciesData container."""

    def test_basic(self):
        """Test basic species data."""
        species = [
            {"dbId": 1, "displayName": "Homo sapiens", "taxId": "9606"},
            {"dbId": 2, "displayName": "Mus musculus", "taxId": "10090"},
        ]
        data = ReactomeSpeciesData(content=species)
        assert len(data) == 2
        assert "Homo sapiens" in data.get_species_names()

    def test_get_species_by_name(self):
        """Test get_species_by_name method."""
        species = [
            {"dbId": 1, "displayName": "Homo sapiens", "taxId": "9606"},
            {"dbId": 2, "displayName": "Mus musculus", "taxId": "10090"},
        ]
        data = ReactomeSpeciesData(content=species)
        human = data.get_species_by_name("homo")
        assert human is not None
        assert human["displayName"] == "Homo sapiens"

    def test_get_taxon_id(self):
        """Test get_taxon_id method."""
        species = [
            {"dbId": 1, "displayName": "Homo sapiens", "taxId": "9606"},
        ]
        data = ReactomeSpeciesData(content=species)
        tax_id = data.get_taxon_id("Homo")
        assert tax_id == "9606"
