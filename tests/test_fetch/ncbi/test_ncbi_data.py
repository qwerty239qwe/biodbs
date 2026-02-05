"""Tests for NCBI data models and containers."""

import pytest
from biodbs.data.NCBI.data import (
    NCBIGeneFetchedData,
    NCBITaxonomyFetchedData,
    NCBIGenomeFetchedData,
)
from biodbs.data.NCBI._data_model import (
    GeneReport,
    GeneDatasetRequest,
)


class TestGeneReport:
    """Tests for GeneReport model."""

    def test_basic_gene(self):
        """Test basic gene creation."""
        gene = GeneReport(
            geneId=7157,
            symbol="TP53",
            description="tumor protein p53",
            taxId=9606,
            type="protein-coding",
        )
        assert gene.gene_id == 7157
        assert gene.entrez_id == 7157
        assert gene.symbol == "TP53"
        assert gene.gene_type == "protein-coding"

    def test_gene_with_aliases(self):
        """Test gene with synonyms."""
        gene = GeneReport(
            geneId=7157,
            symbol="TP53",
            synonyms=["p53", "TRP53", "LFS1"],
        )
        assert gene.synonyms == ["p53", "TRP53", "LFS1"]

    def test_gene_with_chromosomes(self):
        """Test gene with chromosome info."""
        gene = GeneReport(
            geneId=7157,
            symbol="TP53",
            chromosomes=["17"],
        )
        assert gene.location_str == "17"


class TestGeneDatasetRequest:
    """Tests for GeneDatasetRequest model."""

    def test_basic_request(self):
        """Test basic request model."""
        request = GeneDatasetRequest(
            gene_ids=[7157, 672],
            page_size=50,
        )
        assert len(request.gene_ids) == 2
        assert request.page_size == 50

    def test_get_params(self):
        """Test parameter generation."""
        request = GeneDatasetRequest(
            gene_ids=[7157],
            returned_content="COMPLETE",
            page_size=100,
            query="kinase",
        )
        params = request.get_params()
        assert params["page_size"] == 100
        assert params["returned_content"] == "COMPLETE"
        assert params["query"] == "kinase"


class TestNCBIGeneFetchedData:
    """Tests for NCBIGeneFetchedData container."""

    @pytest.fixture
    def sample_response(self):
        """Sample NCBI gene API response."""
        return {
            "reports": [
                {
                    "gene": {
                        "geneId": 7157,
                        "symbol": "TP53",
                        "description": "tumor protein p53",
                        "taxId": 9606,
                        "taxname": "Homo sapiens",
                        "type": "protein-coding",
                        "chromosomes": ["17"],
                        "synonyms": ["p53", "TRP53"],
                    }
                },
                {
                    "gene": {
                        "geneId": 672,
                        "symbol": "BRCA1",
                        "description": "BRCA1 DNA repair associated",
                        "taxId": 9606,
                        "taxname": "Homo sapiens",
                        "type": "protein-coding",
                        "chromosomes": ["17"],
                    }
                },
            ],
            "total_count": 2,
        }

    def test_init(self, sample_response):
        """Test initialization."""
        data = NCBIGeneFetchedData(
            content=sample_response,
            query_ids=[7157, 672],
        )
        assert len(data) == 2
        assert data.total_count == 2

    def test_get_gene_ids(self, sample_response):
        """Test get_gene_ids method."""
        data = NCBIGeneFetchedData(content=sample_response)
        ids = data.get_gene_ids()
        assert ids == [7157, 672]

    def test_get_gene_symbols(self, sample_response):
        """Test get_gene_symbols method."""
        data = NCBIGeneFetchedData(content=sample_response)
        symbols = data.get_gene_symbols()
        assert symbols == ["TP53", "BRCA1"]

    def test_get_gene(self, sample_response):
        """Test get_gene by ID."""
        data = NCBIGeneFetchedData(content=sample_response)
        gene = data.get_gene(7157)
        assert gene is not None
        assert gene.symbol == "TP53"

    def test_get_gene_by_symbol(self, sample_response):
        """Test get_gene_by_symbol."""
        data = NCBIGeneFetchedData(content=sample_response)
        gene = data.get_gene_by_symbol("tp53")  # Case insensitive
        assert gene is not None
        assert gene.gene_id == 7157

    def test_to_id_mapping(self, sample_response):
        """Test to_id_mapping method."""
        data = NCBIGeneFetchedData(content=sample_response)
        mapping = data.to_id_mapping()
        assert mapping["TP53"] == 7157
        assert mapping["BRCA1"] == 672

    def test_to_symbol_mapping(self, sample_response):
        """Test to_symbol_mapping method."""
        data = NCBIGeneFetchedData(content=sample_response)
        mapping = data.to_symbol_mapping()
        assert mapping[7157] == "TP53"
        assert mapping[672] == "BRCA1"

    def test_as_dict(self, sample_response):
        """Test as_dict method."""
        data = NCBIGeneFetchedData(content=sample_response)
        result = data.as_dict()
        assert len(result) == 2
        assert result[0]["symbol"] == "TP53"
        assert result[0]["gene_id"] == 7157

    def test_as_dataframe(self, sample_response):
        """Test as_dataframe method."""
        data = NCBIGeneFetchedData(content=sample_response)
        df = data.as_dataframe()
        assert len(df) == 2
        assert "symbol" in df.columns
        assert "gene_id" in df.columns

    def test_filter_by_type(self, sample_response):
        """Test filter_by_type method."""
        data = NCBIGeneFetchedData(content=sample_response)
        filtered = data.filter_by_type("protein-coding")
        assert len(filtered) == 2

    def test_summary(self, sample_response):
        """Test summary method."""
        data = NCBIGeneFetchedData(
            content=sample_response,
            query_ids=[7157, 672],
        )
        summary = data.summary()
        assert "NCBI Gene Data Report" in summary
        assert "TP53" in summary

    def test_empty_response(self):
        """Test with empty response."""
        data = NCBIGeneFetchedData(content={})
        assert len(data) == 0
        assert data.genes == []


class TestNCBITaxonomyFetchedData:
    """Tests for NCBITaxonomyFetchedData container."""

    @pytest.fixture
    def sample_response(self):
        """Sample taxonomy API response (current format)."""
        return {
            "reports": [
                {
                    "taxonomy": {
                        "tax_id": 9606,
                        "rank": "SPECIES",
                        "current_scientific_name": {"name": "Homo sapiens"},
                        "curator_common_name": "human",
                        "group_name": "primates",
                    }
                },
                {
                    "taxonomy": {
                        "tax_id": 10090,
                        "rank": "SPECIES",
                        "current_scientific_name": {"name": "Mus musculus"},
                        "curator_common_name": "house mouse",
                        "group_name": "rodents",
                    }
                },
            ],
            "total_count": 2,
        }

    def test_init(self, sample_response):
        """Test initialization."""
        data = NCBITaxonomyFetchedData(content=sample_response)
        assert len(data) == 2

    def test_get_taxon(self, sample_response):
        """Test get_taxon by ID."""
        data = NCBITaxonomyFetchedData(content=sample_response)
        tax = data.get_taxon(9606)
        assert tax is not None
        assert tax.organism_name == "Homo sapiens"

    def test_get_taxon_by_name(self, sample_response):
        """Test get_taxon_by_name."""
        data = NCBITaxonomyFetchedData(content=sample_response)
        tax = data.get_taxon_by_name("human")
        assert tax is not None
        assert tax.tax_id == 9606

    def test_as_dataframe(self, sample_response):
        """Test as_dataframe method."""
        data = NCBITaxonomyFetchedData(content=sample_response)
        df = data.as_dataframe()
        assert len(df) == 2
        assert "tax_id" in df.columns


class TestNCBIGenomeFetchedData:
    """Tests for NCBIGenomeFetchedData container."""

    @pytest.fixture
    def sample_response(self):
        """Sample genome API response."""
        return {
            "reports": [
                {
                    "accession": "GCF_000001405.40",
                    "organismName": "Homo sapiens",
                    "organismTaxId": 9606,
                    "assemblyInfo": {
                        "assemblyName": "GRCh38.p14",
                        "assemblyLevel": "chromosome",
                    },
                }
            ],
            "total_count": 1,
        }

    def test_init(self, sample_response):
        """Test initialization."""
        data = NCBIGenomeFetchedData(content=sample_response)
        assert len(data) == 1

    def test_get_accessions(self, sample_response):
        """Test get_accessions method."""
        data = NCBIGenomeFetchedData(content=sample_response)
        accs = data.get_accessions()
        assert accs == ["GCF_000001405.40"]

    def test_as_dataframe(self, sample_response):
        """Test as_dataframe method."""
        data = NCBIGenomeFetchedData(content=sample_response)
        df = data.as_dataframe()
        assert len(df) == 1
        assert "accession" in df.columns
