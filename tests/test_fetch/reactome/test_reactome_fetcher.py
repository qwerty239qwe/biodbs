"""Tests for Reactome fetcher (integration tests)."""

import pytest
from biodbs.fetch.Reactome import Reactome_Fetcher


class TestReactomeFetcherBasic:
    """Basic tests for Reactome fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return Reactome_Fetcher()

    def test_init(self, fetcher):
        """Test fetcher initialization."""
        assert fetcher._species == "Homo sapiens"

    def test_set_species(self, fetcher):
        """Test setting species."""
        fetcher.set_species("Mus musculus")
        assert fetcher._species == "Mus musculus"


class TestReactomeFetcherAPI:
    """API integration tests for Reactome fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return Reactome_Fetcher()

    def test_get_database_version(self, fetcher):
        """Test getting database version."""
        version = fetcher.get_database_version()
        assert version is not None
        assert len(version) > 0
        # Version should be a number
        assert version.isdigit()

    def test_get_species(self, fetcher):
        """Test getting species list."""
        species = fetcher.get_species()
        assert len(species) > 0
        names = species.get_species_names()
        assert "Homo sapiens" in names

    def test_get_species_main(self, fetcher):
        """Test getting main species."""
        species = fetcher.get_species_main()
        assert len(species) > 0
        # Main species should include human
        names = species.get_species_names()
        assert "Homo sapiens" in names

    def test_get_pathways_top(self, fetcher):
        """Test getting top-level pathways."""
        pathways = fetcher.get_pathways_top("Homo sapiens")
        assert len(pathways) > 0
        ids = pathways.get_pathway_ids()
        # All should start with R-HSA
        for pid in ids[:5]:
            assert pid.startswith("R-HSA-")

    def test_analyze_basic(self, fetcher):
        """Test basic analysis."""
        genes = ["TP53", "BRCA1"]
        result = fetcher.analyze(genes, page_size=5)

        assert result.token is not None
        assert len(result.query_identifiers) == 2
        # Should find some pathways
        assert len(result) > 0

    def test_analyze_with_species(self, fetcher):
        """Test analysis with species parameter."""
        genes = ["TP53", "BRCA1"]
        result = fetcher.analyze(
            genes,
            species="Homo sapiens",
            page_size=5,
        )
        assert len(result) > 0

    def test_analyze_single(self, fetcher):
        """Test single identifier analysis."""
        result = fetcher.analyze_single("TP53")
        assert result is not None
        assert len(result) > 0

    def test_analyze_results_content(self, fetcher):
        """Test that analysis results have expected content."""
        genes = ["TP53", "BRCA1", "EGFR"]
        result = fetcher.analyze(genes, page_size=10)

        # Check pathways have required fields
        for pathway in result.pathways[:3]:
            assert pathway.stId is not None
            assert pathway.name is not None
            assert pathway.dbId > 0
            assert pathway.fdr >= 0
            assert pathway.p_value >= 0

    def test_get_not_found_identifiers(self, fetcher):
        """Test getting not-found identifiers."""
        # Use a mix of valid and invalid identifiers
        genes = ["TP53", "INVALID_GENE_XYZ123"]
        result = fetcher.analyze(genes, page_size=5)

        if result.token:
            not_found = fetcher.get_not_found_identifiers(result.token)
            # Should contain the invalid gene
            assert "INVALID_GENE_XYZ123" in not_found

    def test_map_identifiers(self, fetcher):
        """Test identifier mapping."""
        genes = ["TP53", "BRCA1"]
        mapped = fetcher.map_identifiers(genes)

        # Should return a list
        assert isinstance(mapped, list)
        # Should have mapped entities
        assert len(mapped) > 0

    def test_get_pathways_for_entity(self, fetcher):
        """Test getting pathways for an entity."""
        # Use Reactome stable ID for a protein (e.g., TP53)
        # First get a Reactome entity ID
        pathways = fetcher.get_pathways_for_entity("R-HSA-69488")  # A known Reactome entity
        # May return empty if entity doesn't exist
        assert isinstance(pathways.pathways, list)

    def test_query_entry(self, fetcher):
        """Test querying a specific entry."""
        # Query a known pathway
        entry = fetcher.query_entry("R-HSA-69278")
        assert entry is not None
        assert "displayName" in entry


class TestORAReactome:
    """Tests for ora_reactome function."""

    def test_ora_reactome_basic(self):
        """Test basic ora_reactome functionality."""
        from biodbs._funcs.analysis.ora import ora_reactome

        genes = ["TP53", "BRCA1", "EGFR"]
        result = ora_reactome(genes)

        assert len(result) > 0
        assert result.database == "Reactome"
        assert len(result.query_genes) == 3

    def test_ora_reactome_significant(self):
        """Test significant terms from ora_reactome."""
        from biodbs._funcs.analysis.ora import ora_reactome

        genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
        result = ora_reactome(genes)

        # Should have some significant results
        sig = result.significant_terms(p_threshold=0.1)
        # May or may not have significant results depending on genes
        assert isinstance(sig.results, list)

    def test_ora_reactome_dataframe(self):
        """Test converting ora_reactome results to DataFrame."""
        from biodbs._funcs.analysis.ora import ora_reactome

        genes = ["TP53", "BRCA1"]
        result = ora_reactome(genes)

        df = result.as_dataframe()
        assert "term_id" in df.columns
        assert "term_name" in df.columns
        assert "adjusted_p_value" in df.columns

    def test_ora_reactome_parameters(self):
        """Test ora_reactome with parameters."""
        from biodbs._funcs.analysis.ora import ora_reactome

        genes = ["TP53", "BRCA1"]
        result = ora_reactome(
            genes,
            species="Homo sapiens",
            include_disease=False,
        )

        assert result.parameters["species"] == "Homo sapiens"
        assert result.parameters["include_disease"] is False
