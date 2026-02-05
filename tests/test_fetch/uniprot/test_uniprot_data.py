"""Tests for UniProt data models."""

import pytest
from biodbs.data.uniprot import (
    UniProtEntry,
    UniProtFetchedData,
    UniProtSearchResult,
    Gene,
    GeneName,
    Organism,
    ProteinDescription,
    ProteinName,
    ProteinNameValue,
    Sequence,
)


class TestUniProtEntry:
    """Tests for UniProtEntry model."""

    @pytest.fixture
    def sample_entry_data(self):
        """Sample entry data for testing."""
        return {
            "primaryAccession": "P05067",
            "uniProtkbId": "A4_HUMAN",
            "entryType": "UniProtKB reviewed (Swiss-Prot)",
            "genes": [
                {
                    "geneName": {"value": "APP"},
                    "synonyms": [{"value": "A4"}, {"value": "AD1"}],
                }
            ],
            "organism": {
                "taxonId": 9606,
                "scientificName": "Homo sapiens",
                "commonName": "Human",
            },
            "proteinDescription": {
                "recommendedName": {
                    "fullName": {"value": "Amyloid-beta precursor protein"}
                }
            },
            "sequence": {
                "value": "MLPGLALLLL" * 10,
                "length": 100,
            },
        }

    def test_parse_entry(self, sample_entry_data):
        """Test parsing entry data."""
        entry = UniProtEntry(**sample_entry_data)
        assert entry.primaryAccession == "P05067"
        assert entry.uniProtkbId == "A4_HUMAN"

    def test_entry_properties(self, sample_entry_data):
        """Test entry property accessors."""
        entry = UniProtEntry(**sample_entry_data)
        assert entry.accession == "P05067"
        assert entry.entry_name == "A4_HUMAN"
        assert entry.gene_name == "APP"
        assert entry.protein_name == "Amyloid-beta precursor protein"
        assert entry.organism_name == "Homo sapiens"
        assert entry.tax_id == 9606

    def test_gene_names(self, sample_entry_data):
        """Test getting all gene names."""
        entry = UniProtEntry(**sample_entry_data)
        names = entry.gene_names
        assert "APP" in names
        assert "A4" in names
        assert "AD1" in names

    def test_is_reviewed(self, sample_entry_data):
        """Test is_reviewed property."""
        entry = UniProtEntry(**sample_entry_data)
        assert entry.is_reviewed is True

    def test_sequence_length(self, sample_entry_data):
        """Test sequence length property."""
        entry = UniProtEntry(**sample_entry_data)
        assert entry.sequence_length == 100


class TestUniProtFetchedData:
    """Tests for UniProtFetchedData container."""

    @pytest.fixture
    def sample_search_response(self):
        """Sample search response data."""
        return {
            "results": [
                {
                    "primaryAccession": "P05067",
                    "uniProtkbId": "A4_HUMAN",
                    "genes": [{"geneName": {"value": "APP"}}],
                    "organism": {"taxonId": 9606, "scientificName": "Homo sapiens"},
                    "proteinDescription": {
                        "recommendedName": {"fullName": {"value": "Amyloid-beta precursor protein"}}
                    },
                },
                {
                    "primaryAccession": "P04637",
                    "uniProtkbId": "P53_HUMAN",
                    "genes": [{"geneName": {"value": "TP53"}}],
                    "organism": {"taxonId": 9606, "scientificName": "Homo sapiens"},
                    "proteinDescription": {
                        "recommendedName": {"fullName": {"value": "Cellular tumor antigen p53"}}
                    },
                },
            ]
        }

    def test_parse_search_response(self, sample_search_response):
        """Test parsing search response."""
        data = UniProtFetchedData(sample_search_response)
        assert len(data) == 2
        assert data.total_count == 2

    def test_get_accessions(self, sample_search_response):
        """Test getting accessions."""
        data = UniProtFetchedData(sample_search_response)
        accessions = data.get_accessions()
        assert "P05067" in accessions
        assert "P04637" in accessions

    def test_get_gene_names(self, sample_search_response):
        """Test getting gene names."""
        data = UniProtFetchedData(sample_search_response)
        genes = data.get_gene_names()
        assert "APP" in genes
        assert "TP53" in genes

    def test_get_entry(self, sample_search_response):
        """Test getting entry by accession."""
        data = UniProtFetchedData(sample_search_response)
        entry = data.get_entry("P05067")
        assert entry is not None
        assert entry.gene_name == "APP"

    def test_get_entry_by_gene(self, sample_search_response):
        """Test getting entry by gene name."""
        data = UniProtFetchedData(sample_search_response)
        entry = data.get_entry_by_gene("TP53")
        assert entry is not None
        assert entry.primaryAccession == "P04637"

    def test_filter_reviewed(self, sample_search_response):
        """Test filtering to reviewed entries."""
        data = UniProtFetchedData(sample_search_response)
        # Patch entries to have reviewed status
        for e in data.entries:
            e.entryType = "UniProtKB reviewed (Swiss-Prot)"
        filtered = data.filter_reviewed()
        assert len(filtered) == 2

    def test_filter_by_organism(self, sample_search_response):
        """Test filtering by organism."""
        data = UniProtFetchedData(sample_search_response)
        filtered = data.filter_by_organism(9606)
        assert len(filtered) == 2
        filtered_empty = data.filter_by_organism(10090)  # Mouse
        assert len(filtered_empty) == 0

    def test_to_gene_mapping(self, sample_search_response):
        """Test accession to gene mapping."""
        data = UniProtFetchedData(sample_search_response)
        mapping = data.to_gene_mapping()
        assert mapping["P05067"] == "APP"
        assert mapping["P04637"] == "TP53"

    def test_to_accession_mapping(self, sample_search_response):
        """Test gene to accession mapping."""
        data = UniProtFetchedData(sample_search_response)
        mapping = data.to_accession_mapping()
        assert mapping["APP"] == "P05067"
        assert mapping["TP53"] == "P04637"

    def test_as_dict(self, sample_search_response):
        """Test converting to list of dicts."""
        data = UniProtFetchedData(sample_search_response)
        records = data.as_dict()
        assert len(records) == 2
        assert records[0]["accession"] == "P05067"
        assert records[0]["gene_name"] == "APP"

    def test_as_dataframe(self, sample_search_response):
        """Test converting to DataFrame."""
        data = UniProtFetchedData(sample_search_response)
        df = data.as_dataframe()
        assert len(df) == 2
        assert "accession" in df.columns
        assert "gene_name" in df.columns

    def test_empty_response(self):
        """Test handling empty response."""
        data = UniProtFetchedData({"results": []})
        assert len(data) == 0

    def test_single_entry_response(self):
        """Test parsing single entry response."""
        entry_data = {
            "primaryAccession": "P05067",
            "genes": [{"geneName": {"value": "APP"}}],
            "organism": {"taxonId": 9606, "scientificName": "Homo sapiens"},
        }
        data = UniProtFetchedData(entry_data)
        assert len(data) == 1
        assert data.entries[0].primaryAccession == "P05067"


class TestUniProtSearchResult:
    """Tests for UniProtSearchResult."""

    def test_search_result_with_cursor(self):
        """Test search result with pagination cursor."""
        content = {"results": []}
        result = UniProtSearchResult(content, query="test", next_cursor="abc123")
        assert result.query == "test"
        assert result.next_cursor == "abc123"
        assert result.has_next is True

    def test_search_result_without_cursor(self):
        """Test search result without cursor."""
        content = {"results": []}
        result = UniProtSearchResult(content, query="test")
        assert result.has_next is False


class TestGeneModel:
    """Tests for Gene model."""

    def test_gene_primary_name(self):
        """Test getting primary gene name."""
        gene = Gene(
            geneName=GeneName(value="TP53"),
            synonyms=[GeneName(value="P53")],
        )
        assert gene.primary_name == "TP53"

    def test_gene_all_names(self):
        """Test getting all gene names."""
        gene = Gene(
            geneName=GeneName(value="TP53"),
            synonyms=[GeneName(value="P53"), GeneName(value="LFS1")],
        )
        names = gene.all_names
        assert "TP53" in names
        assert "P53" in names
        assert "LFS1" in names


class TestOrganismModel:
    """Tests for Organism model."""

    def test_organism(self):
        """Test organism model."""
        organism = Organism(
            taxonId=9606,
            scientificName="Homo sapiens",
            commonName="Human",
        )
        assert organism.taxonId == 9606
        assert organism.scientificName == "Homo sapiens"


class TestProteinDescriptionModel:
    """Tests for ProteinDescription model."""

    def test_full_name(self):
        """Test getting full protein name."""
        desc = ProteinDescription(
            recommendedName=ProteinName(
                fullName=ProteinNameValue(value="Cellular tumor antigen p53")
            )
        )
        assert desc.full_name == "Cellular tumor antigen p53"

    def test_full_name_from_submission(self):
        """Test getting name from submission names."""
        desc = ProteinDescription(
            submissionNames=[
                ProteinName(fullName=ProteinNameValue(value="Submitted protein"))
            ]
        )
        assert desc.full_name == "Submitted protein"


class TestSequenceModel:
    """Tests for Sequence model."""

    def test_sequence(self):
        """Test sequence model."""
        seq = Sequence(
            value="MEEPQSDPSV" * 10,
            length=100,
            molWeight=11000,
        )
        assert seq.length == 100
        assert seq.molWeight == 11000
        assert seq.value.startswith("MEEP")
