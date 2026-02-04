"""Tests for NCBI fetcher (integration tests)."""

import pytest
from biodbs.fetch.NCBI import NCBI_Fetcher


class TestNCBIFetcherBasic:
    """Basic tests for NCBI fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return NCBI_Fetcher()

    def test_init(self, fetcher):
        """Test fetcher initialization."""
        assert fetcher._api_config is not None

    def test_rate_limit_without_key(self, fetcher):
        """Test rate limit without API key."""
        assert fetcher._api_config.rate_limit == 5


class TestNCBIFetcherGeneAPI:
    """API integration tests for NCBI gene fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return NCBI_Fetcher()

    def test_get_version(self, fetcher):
        """Test getting API version."""
        version = fetcher.get_version()
        assert version is not None
        assert len(version) > 0

    def test_get_genes_by_id(self, fetcher):
        """Test getting genes by NCBI Gene ID."""
        genes = fetcher.get_genes_by_id([7157, 672])
        assert len(genes) == 2
        symbols = genes.get_gene_symbols()
        assert "TP53" in symbols
        assert "BRCA1" in symbols

    def test_get_genes_by_id_single(self, fetcher):
        """Test getting single gene by ID."""
        genes = fetcher.get_genes_by_id([7157])
        assert len(genes) == 1
        assert genes.genes[0].symbol == "TP53"

    def test_get_genes_by_symbol(self, fetcher):
        """Test getting genes by symbol."""
        genes = fetcher.get_genes_by_symbol(["TP53", "BRCA1"], taxon="human")
        assert len(genes) >= 2
        ids = genes.get_gene_ids()
        assert 7157 in ids
        assert 672 in ids

    def test_get_genes_by_symbol_mouse(self, fetcher):
        """Test getting genes by symbol for mouse."""
        genes = fetcher.get_genes_by_symbol(["Trp53", "Brca1"], taxon="mouse")
        assert len(genes) >= 2
        # Mouse TP53 homolog
        symbols = genes.get_gene_symbols()
        assert any("Trp53" in s for s in symbols)

    def test_get_genes_by_taxon(self, fetcher):
        """Test getting genes by taxon with query."""
        genes = fetcher.get_genes_by_taxon("human", query="interleukin", page_size=10)
        assert len(genes) > 0
        # Should return some genes (API may return related genes like chemokines)
        # Just verify we got results back
        assert genes.genes[0].gene_id is not None

    def test_symbol_to_id(self, fetcher):
        """Test symbol to ID conversion."""
        mapping = fetcher.symbol_to_id(["TP53", "BRCA1"], taxon="human")
        assert mapping.get("TP53") == 7157
        assert mapping.get("BRCA1") == 672

    def test_id_to_symbol(self, fetcher):
        """Test ID to symbol conversion."""
        mapping = fetcher.id_to_symbol([7157, 672])
        assert mapping.get(7157) == "TP53"
        assert mapping.get(672) == "BRCA1"

    def test_get_gene_info_mixed(self, fetcher):
        """Test get_gene_info with mixed identifiers."""
        genes = fetcher.get_gene_info([7157, "EGFR"], taxon="human")
        assert len(genes) >= 2

    def test_gene_data_content(self, fetcher):
        """Test that gene data has expected content."""
        genes = fetcher.get_genes_by_id([7157])
        gene = genes.genes[0]
        assert gene.gene_id == 7157
        assert gene.symbol == "TP53"
        assert gene.tax_id == 9606
        assert gene.gene_type is not None

    def test_empty_query(self, fetcher):
        """Test with empty query."""
        genes = fetcher.get_genes_by_id([])
        assert len(genes) == 0


class TestNCBIFetcherTaxonomyAPI:
    """API integration tests for NCBI taxonomy fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return NCBI_Fetcher()

    def test_get_taxonomy(self, fetcher):
        """Test getting taxonomy info."""
        tax = fetcher.get_taxonomy([9606, 10090])
        assert len(tax) == 2

        # Check human
        human = tax.get_taxon(9606)
        assert human is not None
        assert human.organism_name == "Homo sapiens"

        # Check mouse
        mouse = tax.get_taxon(10090)
        assert mouse is not None
        assert mouse.organism_name == "Mus musculus"

    def test_get_taxonomy_by_name(self, fetcher):
        """Test getting taxonomy by name."""
        tax = fetcher.get_taxonomy(["human"])
        assert len(tax) > 0


class TestNCBIFetcherGenomeAPI:
    """API integration tests for NCBI genome fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return NCBI_Fetcher()

    def test_get_genome_by_accession(self, fetcher):
        """Test getting genome by accession."""
        genomes = fetcher.get_genome_by_accession(["GCF_000001405.40"])
        assert len(genomes) == 1
        assert genomes.assemblies[0].accession == "GCF_000001405.40"

    def test_get_genome_by_taxon(self, fetcher):
        """Test getting genome by taxon."""
        genomes = fetcher.get_genome_by_taxon("human", reference_only=True, page_size=5)
        assert len(genomes) > 0


class TestNCBIConvenienceFunctions:
    """Tests for NCBI convenience functions."""

    def test_ncbi_get_gene(self):
        """Test ncbi_get_gene function."""
        from biodbs.fetch.NCBI import ncbi_get_gene

        genes = ncbi_get_gene([7157, 672])
        assert len(genes) == 2
        assert "TP53" in genes.get_gene_symbols()

    def test_ncbi_symbol_to_id(self):
        """Test ncbi_symbol_to_id function."""
        from biodbs.fetch.NCBI import ncbi_symbol_to_id

        mapping = ncbi_symbol_to_id(["TP53", "BRCA1"])
        assert mapping["TP53"] == 7157
        assert mapping["BRCA1"] == 672

    def test_ncbi_id_to_symbol(self):
        """Test ncbi_id_to_symbol function."""
        from biodbs.fetch.NCBI import ncbi_id_to_symbol

        mapping = ncbi_id_to_symbol([7157, 672])
        assert mapping[7157] == "TP53"
        assert mapping[672] == "BRCA1"

    def test_ncbi_get_taxonomy(self):
        """Test ncbi_get_taxonomy function."""
        from biodbs.fetch.NCBI import ncbi_get_taxonomy

        tax = ncbi_get_taxonomy([9606])
        assert len(tax) == 1
        assert tax.taxa[0].organism_name == "Homo sapiens"
