"""Tests for Over-Representation Analysis (ORA) module.

Run with: uv run pytest tests/test_analysis/test_ora.py -v
Skip slow tests: uv run pytest tests/test_analysis/test_ora.py -v -m "not slow"
"""

import pytest
import math

from biodbs._funcs.analysis.ora import (
    hypergeometric_test,
    multiple_test_correction,
    ora,
    ora_kegg,
    ora_go,
    ora_enrichr,
    ORAResult,
    ORATermResult,
    CorrectionMethod,
    GOAspect,
)


# =============================================================================
# Hypergeometric Test
# =============================================================================

class TestHypergeometricTest:
    """Tests for hypergeometric_test function."""

    def test_basic_enrichment(self):
        """Test basic enrichment scenario."""
        # 10 genes overlap out of 100 query genes
        # Term has 200 genes out of 20000 background
        p = hypergeometric_test(k=10, K=200, n=100, N=20000)
        assert 0 < p < 1
        # This is significant enrichment
        assert p < 0.001

    def test_no_overlap(self):
        """Test when there's no overlap."""
        p = hypergeometric_test(k=0, K=100, n=50, N=10000)
        # P(X >= 0) should be 1.0
        assert p == 1.0

    def test_perfect_overlap(self):
        """Test when all query genes are in the term."""
        # All 10 query genes are in a term of 10 genes
        p = hypergeometric_test(k=10, K=10, n=10, N=1000)
        assert p < 1e-10  # Very significant

    def test_expected_overlap(self):
        """Test when overlap matches expectation."""
        # Expected overlap: (100/10000) * 500 = 5
        p = hypergeometric_test(k=5, K=100, n=500, N=10000)
        # Should not be very significant when k = expected
        assert p > 0.1

    def test_edge_cases(self):
        """Test edge cases."""
        # Minimum valid case
        p = hypergeometric_test(k=1, K=1, n=1, N=1)
        assert p == 1.0

        # k equals both n and K
        p = hypergeometric_test(k=5, K=5, n=5, N=10)
        assert 0 < p <= 1

    def test_invalid_inputs(self):
        """Test that invalid inputs raise errors."""
        with pytest.raises(ValueError):
            hypergeometric_test(k=-1, K=10, n=10, N=100)

        with pytest.raises(ValueError):
            hypergeometric_test(k=5, K=3, n=10, N=100)  # k > K

        with pytest.raises(ValueError):
            hypergeometric_test(k=5, K=10, n=3, N=100)  # k > n

        with pytest.raises(ValueError):
            hypergeometric_test(k=5, K=200, n=100, N=100)  # K > N

    def test_numerical_stability(self):
        """Test numerical stability with large numbers."""
        # Large but valid case
        p = hypergeometric_test(k=500, K=5000, n=1000, N=100000)
        assert 0 <= p <= 1
        assert not math.isnan(p)
        assert not math.isinf(p)


# =============================================================================
# Multiple Testing Correction
# =============================================================================

class TestMultipleTestCorrection:
    """Tests for multiple_test_correction function."""

    def test_bonferroni(self):
        """Test Bonferroni correction."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        adjusted = multiple_test_correction(p_values, "bonferroni")

        assert len(adjusted) == len(p_values)
        # Bonferroni multiplies by n
        assert adjusted[0] == pytest.approx(0.05)  # 0.01 * 5
        assert adjusted[1] == pytest.approx(0.10)
        # Should be capped at 1.0
        assert all(p <= 1.0 for p in adjusted)

    def test_benjamini_hochberg(self):
        """Test Benjamini-Hochberg FDR correction."""
        p_values = [0.001, 0.01, 0.05, 0.1, 0.5]
        adjusted = multiple_test_correction(p_values, "bh")

        assert len(adjusted) == len(p_values)
        # Order should be preserved
        for i in range(len(p_values) - 1):
            assert adjusted[i] <= adjusted[i + 1]
        # Adjusted >= raw
        for i, p in enumerate(p_values):
            assert adjusted[i] >= p

    def test_holm(self):
        """Test Holm-Bonferroni correction."""
        p_values = [0.01, 0.02, 0.03]
        adjusted = multiple_test_correction(p_values, "holm")

        assert len(adjusted) == len(p_values)
        # Holm is less conservative than Bonferroni
        bonferroni = multiple_test_correction(p_values, "bonferroni")
        for h, b in zip(adjusted, bonferroni):
            assert h <= b

    def test_no_correction(self):
        """Test no correction."""
        p_values = [0.01, 0.05, 0.1]
        adjusted = multiple_test_correction(p_values, "none")

        assert adjusted == p_values

    def test_empty_input(self):
        """Test with empty input."""
        adjusted = multiple_test_correction([], "bh")
        assert adjusted == []

    def test_single_value(self):
        """Test with single p-value."""
        adjusted = multiple_test_correction([0.05], "bh")
        assert len(adjusted) == 1
        assert adjusted[0] == pytest.approx(0.05)

    def test_enum_method(self):
        """Test using CorrectionMethod enum."""
        p_values = [0.01, 0.05]
        adjusted = multiple_test_correction(p_values, CorrectionMethod.BH)
        assert len(adjusted) == 2


# =============================================================================
# ORA with Custom Gene Sets
# =============================================================================

class TestORA:
    """Tests for core ORA function."""

    @pytest.fixture
    def sample_gene_sets(self):
        """Create sample gene sets for testing."""
        return {
            "pathway1": ("Pathway One", {"GENE1", "GENE2", "GENE3", "GENE4", "GENE5"}),
            "pathway2": ("Pathway Two", {"GENE3", "GENE4", "GENE5", "GENE6", "GENE7"}),
            "pathway3": ("Pathway Three", {"GENE8", "GENE9", "GENE10"}),
        }

    def test_basic_ora(self, sample_gene_sets):
        """Test basic ORA analysis."""
        query_genes = ["GENE1", "GENE2", "GENE3", "GENE4"]

        result = ora(query_genes, sample_gene_sets)

        assert isinstance(result, ORAResult)
        assert len(result.query_genes) == 4
        assert result.database == "custom"

    def test_enriched_pathway(self, sample_gene_sets):
        """Test that enriched pathway is detected."""
        # Genes mostly from pathway1
        query_genes = ["GENE1", "GENE2", "GENE3", "GENE4"]

        result = ora(query_genes, sample_gene_sets, min_overlap=2)

        # pathway1 should be enriched
        pathway1_result = [r for r in result.results if r.term_id == "pathway1"]
        assert len(pathway1_result) == 1
        assert pathway1_result[0].overlap_count == 4

    def test_no_overlap(self, sample_gene_sets):
        """Test when query genes don't overlap with any pathway."""
        query_genes = ["GENEX", "GENEY", "GENEZ"]

        result = ora(query_genes, sample_gene_sets)

        assert len(result.results) == 0

    def test_min_overlap_filter(self, sample_gene_sets):
        """Test min_overlap parameter."""
        query_genes = ["GENE1", "GENE2"]  # 2 overlaps with pathway1

        result_low = ora(query_genes, sample_gene_sets, min_overlap=2)
        result_high = ora(query_genes, sample_gene_sets, min_overlap=3)

        assert len(result_low.results) >= len(result_high.results)

    def test_custom_background(self, sample_gene_sets):
        """Test with custom background."""
        query_genes = ["GENE1", "GENE2"]
        background = {"GENE1", "GENE2", "GENE3", "GENE4", "GENE5"}  # Only 5 genes

        result = ora(query_genes, sample_gene_sets, background=background)

        assert result.background_size == 5

    def test_result_dataframe(self, sample_gene_sets):
        """Test converting results to DataFrame."""
        query_genes = ["GENE1", "GENE2", "GENE3"]

        result = ora(query_genes, sample_gene_sets, min_overlap=1)
        df = result.as_dataframe()

        assert len(df) == len(result.results)
        assert "term_id" in df.columns
        assert "p_value" in df.columns
        assert "adjusted_p_value" in df.columns

    def test_significant_terms(self, sample_gene_sets):
        """Test filtering significant terms."""
        query_genes = ["GENE1", "GENE2", "GENE3", "GENE4"]

        result = ora(query_genes, sample_gene_sets, min_overlap=1)
        significant = result.significant_terms(p_threshold=0.5)

        assert len(significant.results) <= len(result.results)

    def test_top_terms(self, sample_gene_sets):
        """Test getting top terms."""
        query_genes = ["GENE1", "GENE2", "GENE3", "GENE4", "GENE5"]

        result = ora(query_genes, sample_gene_sets, min_overlap=1)
        top = result.top_terms(n=2)

        assert len(top.results) <= 2

    def test_result_summary(self, sample_gene_sets):
        """Test result summary."""
        query_genes = ["GENE1", "GENE2", "GENE3"]

        result = ora(query_genes, sample_gene_sets, min_overlap=1)
        summary = result.summary()

        assert "Query genes" in summary
        assert "custom" in summary


# =============================================================================
# ORA Term Result
# =============================================================================

class TestORATermResult:
    """Tests for ORATermResult dataclass."""

    def test_term_result_creation(self):
        """Test creating an ORATermResult."""
        result = ORATermResult(
            term_id="GO:0006915",
            term_name="apoptotic process",
            p_value=0.001,
            adjusted_p_value=0.01,
            overlap_count=5,
            term_size=100,
            query_size=50,
            background_size=20000,
            fold_enrichment=2.0,
            overlap_genes=["TP53", "BAX", "BCL2", "CASP3", "CASP9"],
            database="GO",
        )

        assert result.term_id == "GO:0006915"
        assert result.overlap_count == 5
        assert len(result.overlap_genes) == 5

    def test_odds_ratio(self):
        """Test odds ratio calculation."""
        result = ORATermResult(
            term_id="test",
            term_name="Test",
            p_value=0.01,
            adjusted_p_value=0.05,
            overlap_count=10,
            term_size=100,
            query_size=50,
            background_size=1000,
            fold_enrichment=2.0,
            overlap_genes=[],
            database="test",
        )

        odds = result.odds_ratio
        assert odds > 0
        assert not math.isnan(odds)

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ORATermResult(
            term_id="test",
            term_name="Test Pathway",
            p_value=0.01,
            adjusted_p_value=0.05,
            overlap_count=5,
            term_size=50,
            query_size=100,
            background_size=10000,
            fold_enrichment=2.5,
            overlap_genes=["A", "B", "C"],
            database="test",
        )

        d = result.to_dict()

        assert d["term_id"] == "test"
        assert d["overlap_genes"] == "A,B,C"
        assert "odds_ratio" in d


# =============================================================================
# KEGG ORA (Integration Tests)
# =============================================================================

class TestORAKegg:
    """Integration tests for KEGG ORA."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_kegg_ora_entrez(self):
        """Test KEGG ORA with Entrez IDs."""
        # TP53-related genes (Entrez IDs)
        genes = ["7157", "672", "675", "7158", "891"]  # TP53, BRCA1, BRCA2, TP73, CCNB1

        result = ora_kegg(genes, organism="hsa", id_type="entrez", use_cache=True)

        assert isinstance(result, ORAResult)
        assert result.database == "KEGG"
        assert len(result.query_genes) == 5

    @pytest.mark.integration
    @pytest.mark.slow
    def test_kegg_ora_symbols(self):
        """Test KEGG ORA with gene symbols."""
        genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]

        result = ora_kegg(genes, organism="hsa", id_type="symbol", use_cache=True)

        assert isinstance(result, ORAResult)
        # Some genes may not be mapped
        assert len(result.mapped_genes) >= 0

    @pytest.mark.integration
    def test_kegg_ora_empty_result(self):
        """Test KEGG ORA with non-existent genes."""
        genes = ["NOTAREALGENE1", "NOTAREALGENE2"]

        result = ora_kegg(genes, organism="hsa", id_type="symbol", use_cache=True)

        assert isinstance(result, ORAResult)
        assert len(result.results) == 0


# =============================================================================
# GO ORA (Integration Tests)
# =============================================================================

class TestORAGo:
    """Integration tests for GO ORA."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_go_ora_uniprot(self):
        """Test GO ORA with UniProt IDs."""
        # Human proteins
        proteins = ["P04637", "P38398", "O15350"]  # TP53, BRCA1, TP73

        result = ora_go(
            proteins,
            taxon_id=9606,
            id_type="uniprot",
            aspect=GOAspect.BIOLOGICAL_PROCESS,
            use_cache=True,
        )

        assert isinstance(result, ORAResult)
        assert "GO" in result.database

    @pytest.mark.integration
    @pytest.mark.slow
    def test_go_ora_aspect_filter(self):
        """Test GO ORA with different aspects."""
        proteins = ["P04637", "P38398"]

        result_bp = ora_go(proteins, aspect="biological_process", use_cache=True)
        result_mf = ora_go(proteins, aspect="molecular_function", use_cache=True)

        # Database name includes aspect when terms are found, or just "GO" if empty
        assert "GO" in result_bp.database
        assert "GO" in result_mf.database
        # Aspect is always stored in parameters
        assert result_bp.parameters.get("aspect") == "biological_process"
        assert result_mf.parameters.get("aspect") == "molecular_function"


# =============================================================================
# EnrichR ORA (Integration Tests)
# =============================================================================

class TestORAEnrichr:
    """Integration tests for EnrichR ORA."""

    @pytest.mark.integration
    def test_enrichr_kegg(self):
        """Test EnrichR ORA with KEGG library."""
        genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]

        try:
            result = ora_enrichr(genes, gene_set_library="KEGG_2021_Human")

            assert isinstance(result, ORAResult)
            assert "EnrichR" in result.database
            assert len(result.query_genes) == 5
        except ConnectionError:
            pytest.skip("EnrichR API not available")

    @pytest.mark.integration
    def test_enrichr_go(self):
        """Test EnrichR ORA with GO library."""
        genes = ["TP53", "MDM2", "CDKN1A", "BAX", "BCL2"]

        try:
            result = ora_enrichr(genes, gene_set_library="GO_Biological_Process_2021")

            assert isinstance(result, ORAResult)
        except ConnectionError:
            pytest.skip("EnrichR API not available")


# =============================================================================
# Cache Tests
# =============================================================================

class TestCache:
    """Tests for pathway caching."""

    def test_cache_operations(self, tmp_path):
        """Test cache read/write operations."""
        from biodbs._funcs.analysis._cache import (
            cache_pathways,
            get_cached_pathways,
            clear_cache,
            get_cache_info,
        )

        cache_dir = str(tmp_path)

        # Test data
        pathways = {
            "path1": ("Pathway 1", frozenset(["A", "B", "C"])),
            "path2": ("Pathway 2", frozenset(["D", "E", "F"])),
        }

        # Write to cache
        success = cache_pathways("test_key", pathways, cache_dir=cache_dir)
        assert success

        # Read from cache
        cached = get_cached_pathways("test_key", cache_dir=cache_dir)
        assert cached is not None
        assert "path1" in cached
        assert "path2" in cached

        # Check cache info
        info = get_cache_info(cache_dir=cache_dir)
        assert info["db_exists"]
        assert len(info["entries"]) == 1

        # Clear cache
        success = clear_cache("test_key", cache_dir=cache_dir)
        assert success

        # Verify cleared
        cached = get_cached_pathways("test_key", cache_dir=cache_dir)
        assert cached is None

    def test_cache_expiry(self, tmp_path):
        """Test cache expiration."""
        from biodbs._funcs.analysis._cache import (
            cache_pathways,
            get_cached_pathways,
        )

        cache_dir = str(tmp_path)
        pathways = {"path1": ("Pathway 1", frozenset(["A"]))}

        # Cache with very short expiry
        cache_pathways("test_key", pathways, cache_dir=cache_dir, expiry=0.001)

        # Wait for expiry
        import time
        time.sleep(0.01)

        # Should be expired
        cached = get_cached_pathways("test_key", cache_dir=cache_dir)
        assert cached is None
