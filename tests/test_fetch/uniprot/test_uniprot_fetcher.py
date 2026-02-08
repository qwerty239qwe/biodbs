"""Tests for UniProt fetcher (integration tests)."""

import pytest
from biodbs.fetch.uniprot import UniProt_Fetcher


class TestUniProtFetcherBasic:
    """Basic tests for UniProt fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return UniProt_Fetcher()

    def test_init(self, fetcher):
        """Test fetcher initialization."""
        assert fetcher._api_config is not None

    def test_rate_limit(self, fetcher):
        """Test rate limit configuration."""
        assert fetcher._api_config.RATE_LIMIT == 10


class TestUniProtFetcherEntryAPI:
    """API integration tests for UniProt entry retrieval."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return UniProt_Fetcher()

    def test_get_entry(self, fetcher):
        """Test getting entry by accession."""
        result = fetcher.get_entry("P05067")
        assert len(result) == 1
        entry = result.entries[0]
        assert entry.primaryAccession == "P05067"
        assert entry.gene_name == "APP"

    def test_get_entry_content(self, fetcher):
        """Test that entry data has expected content."""
        result = fetcher.get_entry("P04637")
        entry = result.entries[0]
        assert entry.primaryAccession == "P04637"
        assert entry.gene_name == "TP53"
        assert entry.organism_name == "Homo sapiens"
        assert entry.tax_id == 9606
        assert entry.sequence_length > 0

    def test_get_entries(self, fetcher):
        """Test getting multiple entries."""
        result = fetcher.get_entries(["P05067", "P04637", "P00533"])
        assert len(result) == 3
        accessions = result.get_accessions()
        assert "P05067" in accessions
        assert "P04637" in accessions
        assert "P00533" in accessions

    def test_get_entries_empty(self, fetcher):
        """Test with empty list."""
        result = fetcher.get_entries([])
        assert len(result) == 0


class TestUniProtFetcherSearchAPI:
    """API integration tests for UniProt search."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return UniProt_Fetcher()

    def test_search(self, fetcher):
        """Test basic search."""
        result = fetcher.search("gene:TP53 AND organism_id:9606 AND reviewed:true", size=5)
        assert len(result) > 0
        assert any(e.gene_name == "TP53" for e in result.entries)

    def test_search_by_gene(self, fetcher):
        """Test search by gene name."""
        result = fetcher.search_by_gene("BRCA1", organism=9606, reviewed_only=True)
        assert len(result) >= 1
        assert result.entries[0].gene_name == "BRCA1"
        assert result.entries[0].tax_id == 9606

    def test_search_by_organism(self, fetcher):
        """Test search by organism."""
        result = fetcher.search_by_organism(9606, reviewed_only=True, size=5)
        assert len(result) > 0
        assert all(e.tax_id == 9606 for e in result.entries)

    def test_search_by_keyword(self, fetcher):
        """Test search by keyword."""
        result = fetcher.search_by_keyword("kinase", organism=9606, reviewed_only=True, size=5)
        assert len(result) > 0


class TestUniProtFetcherIDMappingAPI:
    """API integration tests for UniProt ID mapping."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return UniProt_Fetcher()

    def test_map_ids_to_gene_id(self, fetcher):
        """Test ID mapping to NCBI Gene ID."""
        mapping = fetcher.map_ids(["P05067", "P04637"], from_db="UniProtKB_AC-ID", to_db="GeneID")
        assert "P05067" in mapping
        assert "P04637" in mapping
        assert "351" in mapping["P05067"]  # APP gene ID
        assert "7157" in mapping["P04637"]  # TP53 gene ID

    def test_map_ids_empty(self, fetcher):
        """Test ID mapping with empty list."""
        mapping = fetcher.map_ids([], from_db="UniProtKB_AC-ID", to_db="GeneID")
        assert mapping == {}


class TestUniProtFetcherConvenienceMethods:
    """Tests for UniProt fetcher convenience methods."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return UniProt_Fetcher()

    def test_gene_to_uniprot(self, fetcher):
        """Test gene to UniProt mapping."""
        mapping = fetcher.gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
        assert mapping["TP53"] == "P04637"
        assert mapping["BRCA1"] == "P38398"
        assert mapping["EGFR"] == "P00533"

    def test_uniprot_to_gene(self, fetcher):
        """Test UniProt to gene mapping."""
        mapping = fetcher.uniprot_to_gene(["P04637", "P38398", "P00533"])
        assert mapping["P04637"] == "TP53"
        assert mapping["P38398"] == "BRCA1"
        assert mapping["P00533"] == "EGFR"

    def test_get_sequences(self, fetcher):
        """Test getting sequences."""
        seqs = fetcher.get_sequences(["P04637"])
        assert "P04637" in seqs
        assert len(seqs["P04637"]) > 0
        # TP53 sequence starts with MEEP...
        assert seqs["P04637"].startswith("MEEP")


class TestUniProtConvenienceFunctions:
    """Tests for UniProt convenience functions."""

    def test_uniprot_get_entry(self):
        """Test uniprot_get_entry function."""
        from biodbs.fetch.uniprot import uniprot_get_entry

        result = uniprot_get_entry("P05067")
        assert len(result) == 1
        assert result.entries[0].gene_name == "APP"

    def test_uniprot_get_entries(self):
        """Test uniprot_get_entries function."""
        from biodbs.fetch.uniprot import uniprot_get_entries

        result = uniprot_get_entries(["P05067", "P04637"])
        assert len(result) == 2

    def test_uniprot_search(self):
        """Test uniprot_search function."""
        from biodbs.fetch.uniprot import uniprot_search

        result = uniprot_search("gene:TP53", reviewed_only=True, size=3)
        assert len(result) > 0

    def test_uniprot_search_by_gene(self):
        """Test uniprot_search_by_gene function."""
        from biodbs.fetch.uniprot import uniprot_search_by_gene

        result = uniprot_search_by_gene("BRCA1")
        assert len(result) >= 1
        assert result.entries[0].gene_name == "BRCA1"

    def test_gene_to_uniprot(self):
        """Test gene_to_uniprot function."""
        from biodbs.fetch.uniprot import gene_to_uniprot

        mapping = gene_to_uniprot(["TP53", "EGFR"])
        assert mapping["TP53"] == "P04637"
        assert mapping["EGFR"] == "P00533"

    def test_uniprot_to_gene(self):
        """Test uniprot_to_gene function."""
        from biodbs.fetch.uniprot import uniprot_to_gene

        mapping = uniprot_to_gene(["P04637", "P00533"])
        assert mapping["P04637"] == "TP53"
        assert mapping["P00533"] == "EGFR"

    def test_uniprot_get_sequences(self):
        """Test uniprot_get_sequences function."""
        from biodbs.fetch.uniprot import uniprot_get_sequences

        seqs = uniprot_get_sequences(["P04637"])
        assert "P04637" in seqs
        assert len(seqs["P04637"]) > 0

    def test_uniprot_map_ids(self):
        """Test uniprot_map_ids function."""
        from biodbs.fetch.uniprot import uniprot_map_ids

        mapping = uniprot_map_ids(["P04637"], "UniProtKB_AC-ID", "GeneID")
        assert "P04637" in mapping
        assert "7157" in mapping["P04637"]
