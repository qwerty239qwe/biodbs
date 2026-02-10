"""Tests for biodbs._funcs.analysis.ora — core statistical functions and data classes.

All tests are pure unit tests with no API calls or network access.
"""

import math

import pytest

from biodbs._funcs.analysis.ora import (
    CorrectionMethod,
    GOAspect,
    ORAResult,
    ORATermResult,
    Pathway,
    PathwayDatabase,
    Species,
    TranslationDatabase,
    hypergeometric_test,
    multiple_test_correction,
    ora,
    _normalize_id_type,
)


# =============================================================================
# Species enum
# =============================================================================


class TestSpecies:
    def test_attributes(self):
        assert Species.HUMAN.taxon_id == 9606
        assert Species.HUMAN.kegg_code == "hsa"
        assert Species.MOUSE.common_name == "mouse"

    def test_from_taxon_id(self):
        assert Species.from_taxon_id(9606) is Species.HUMAN
        assert Species.from_taxon_id(10090) is Species.MOUSE

    def test_from_taxon_id_invalid(self):
        with pytest.raises(ValueError, match="Unknown taxon ID"):
            Species.from_taxon_id(99999)

    def test_from_kegg_code(self):
        assert Species.from_kegg_code("hsa") is Species.HUMAN
        assert Species.from_kegg_code("mmu") is Species.MOUSE

    def test_from_kegg_code_invalid(self):
        with pytest.raises(ValueError, match="Unknown KEGG code"):
            Species.from_kegg_code("xxx")

    def test_from_name_common(self):
        assert Species.from_name("human") is Species.HUMAN
        assert Species.from_name("Human") is Species.HUMAN  # case insensitive

    def test_from_name_scientific(self):
        assert Species.from_name("Homo sapiens") is Species.HUMAN

    def test_from_name_kegg_code(self):
        assert Species.from_name("hsa") is Species.HUMAN

    def test_from_name_invalid(self):
        with pytest.raises(ValueError, match="Unknown species"):
            Species.from_name("unicorn")


# =============================================================================
# Pathway dataclass
# =============================================================================


class TestPathway:
    def test_basic(self):
        p = Pathway(
            id="hsa04110",
            name="Cell cycle",
            genes=frozenset(["TP53", "CDK2", "CCNB1"]),
            database="KEGG",
        )
        assert len(p) == 3
        assert "TP53" in p
        assert "BRCA1" not in p

    def test_overlap(self):
        p = Pathway(
            id="p1", name="P", genes=frozenset(["A", "B", "C"]), database="test"
        )
        assert p.overlap({"A", "C", "D"}) == {"A", "C"}

    def test_to_tuple_and_back(self):
        p = Pathway(
            id="p1", name="Path", genes=frozenset(["X", "Y"]), database="test"
        )
        t = p.to_tuple()
        assert t == ("Path", {"X", "Y"})

        p2 = Pathway.from_tuple("p1", t, "test")
        assert p2.name == "Path"
        assert p2.genes == frozenset(["X", "Y"])


# =============================================================================
# ORATermResult
# =============================================================================


class TestORATermResult:
    @pytest.fixture
    def term(self):
        return ORATermResult(
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

    def test_odds_ratio(self, term):
        odds = term.odds_ratio
        assert isinstance(odds, float)
        assert odds > 0

    def test_odds_ratio_zero_denominator(self):
        """When all query genes overlap with term, avoid division by zero."""
        t = ORATermResult(
            term_id="t1", term_name="T", p_value=0.01, adjusted_p_value=0.01,
            overlap_count=10, term_size=10, query_size=10,
            background_size=100, fold_enrichment=10.0,
            overlap_genes=[], database="x",
        )
        assert t.odds_ratio == float("inf")

    def test_odds_ratio_no_overlap(self):
        t = ORATermResult(
            term_id="t1", term_name="T", p_value=1.0, adjusted_p_value=1.0,
            overlap_count=0, term_size=10, query_size=10,
            background_size=100, fold_enrichment=0.0,
            overlap_genes=[], database="x",
        )
        assert t.odds_ratio == 0.0

    def test_to_dict(self, term):
        d = term.to_dict()
        assert d["term_id"] == "GO:0006915"
        assert d["overlap_genes"] == "TP53,BAX,BCL2,CASP3,CASP9"
        assert "odds_ratio" in d


# =============================================================================
# ORAResult
# =============================================================================


class TestORAResult:
    @pytest.fixture
    def result(self):
        terms = [
            ORATermResult(
                term_id=f"t{i}", term_name=f"Term {i}",
                p_value=p, adjusted_p_value=ap,
                overlap_count=3, term_size=50, query_size=20,
                background_size=10000, fold_enrichment=3.0,
                overlap_genes=["A", "B", "C"], database="test",
            )
            for i, (p, ap) in enumerate([
                (0.001, 0.01),   # significant
                (0.01, 0.04),    # significant
                (0.05, 0.15),    # not significant
                (0.2, 0.5),      # not significant
            ])
        ]
        return ORAResult(
            results=terms,
            query_genes=["A", "B", "C", "D"],
            mapped_genes=["A", "B", "C"],
            unmapped_genes=["D"],
            background_size=10000,
            database="test",
        )

    def test_len(self, result):
        assert len(result) == 4

    def test_iter(self, result):
        terms = list(result)
        assert len(terms) == 4

    def test_significant_terms_default(self, result):
        sig = result.significant_terms()
        assert len(sig) == 2

    def test_significant_terms_custom_threshold(self, result):
        sig = result.significant_terms(p_threshold=0.2)
        assert len(sig) == 3

    def test_significant_terms_raw_pvalue(self, result):
        sig = result.significant_terms(use_adjusted=False, p_threshold=0.05)
        assert len(sig) == 3  # p=0.001, p=0.01, p=0.05 (uses <=)

    def test_top_terms(self, result):
        top = result.top_terms(n=2)
        assert len(top) == 2
        # Should be sorted by adjusted_p_value
        assert top.results[0].adjusted_p_value <= top.results[1].adjusted_p_value

    def test_as_dataframe(self, result):
        import pandas as pd
        df = result.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4

    def test_as_dataframe_empty(self):
        empty = ORAResult(
            results=[], query_genes=[], mapped_genes=[],
            unmapped_genes=[], background_size=0, database="x",
        )
        df = empty.as_dataframe()
        assert len(df) == 0

    def test_summary(self, result):
        s = result.summary()
        assert "ORA Results Summary" in s
        assert "Query genes: 4" in s
        assert "Mapped genes: 3" in s
        assert "Top 5 terms:" in s


# =============================================================================
# hypergeometric_test
# =============================================================================


class TestHypergeometricTest:
    def test_basic(self):
        """Test a standard enrichment scenario."""
        # k=5 overlap, K=50 term, n=20 query, N=1000 background
        p = hypergeometric_test(5, 50, 20, 1000)
        assert 0 < p < 1

    def test_no_overlap(self):
        """k=0 should give p~1 (no enrichment)."""
        p = hypergeometric_test(0, 50, 20, 1000)
        assert p > 0.9

    def test_perfect_overlap(self):
        """All query genes in term should give very small p."""
        p = hypergeometric_test(10, 100, 10, 10000)
        assert p < 0.05

    def test_trivial_case(self):
        """k=K=n=N → p=1."""
        p = hypergeometric_test(5, 5, 5, 5)
        assert abs(p - 1.0) < 1e-10

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            hypergeometric_test(-1, 10, 10, 100)

    def test_k_exceeds_min_raises(self):
        with pytest.raises(ValueError, match="k cannot exceed"):
            hypergeometric_test(15, 10, 20, 100)

    def test_K_exceeds_N_raises(self):
        with pytest.raises(ValueError, match="cannot exceed N"):
            hypergeometric_test(5, 200, 10, 100)

    def test_known_value(self):
        """Compare against known hypergeometric test value."""
        # Drawing 3+ white balls from urn: 7 white, 13 black, draw 5
        p = hypergeometric_test(3, 7, 5, 20)
        # scipy.stats.hypergeom.sf(2, 20, 7, 5) ≈ 0.2068
        assert abs(p - 0.2068) < 0.01


# =============================================================================
# multiple_test_correction
# =============================================================================


class TestMultipleTestCorrection:
    @pytest.fixture
    def p_values(self):
        return [0.001, 0.01, 0.05, 0.1, 0.5]

    def test_none_method(self, p_values):
        adj = multiple_test_correction(p_values, CorrectionMethod.NONE)
        assert adj == p_values

    def test_bonferroni(self, p_values):
        adj = multiple_test_correction(p_values, CorrectionMethod.BONFERRONI)
        assert adj[0] == 0.005  # 0.001 * 5
        assert adj[-1] == 1.0  # min(0.5 * 5, 1.0) = 1.0

    def test_bh(self, p_values):
        adj = multiple_test_correction(p_values, CorrectionMethod.BH)
        # BH: p[i] * n / rank
        # Adjusted values should be >= original and <= 1
        for orig, adjusted in zip(p_values, adj):
            assert adjusted >= orig
            assert adjusted <= 1.0

    def test_bh_monotonicity(self, p_values):
        """Sorted original p-values should produce sorted adjusted values."""
        adj = multiple_test_correction(p_values, CorrectionMethod.BH)
        sorted_pairs = sorted(zip(p_values, adj))
        adj_sorted = [a for _, a in sorted_pairs]
        assert adj_sorted == sorted(adj_sorted)

    def test_holm(self, p_values):
        adj = multiple_test_correction(p_values, CorrectionMethod.HOLM)
        for orig, adjusted in zip(p_values, adj):
            assert adjusted >= orig
            assert adjusted <= 1.0

    def test_by(self, p_values):
        adj = multiple_test_correction(p_values, CorrectionMethod.BY)
        # BY is more conservative than BH
        adj_bh = multiple_test_correction(p_values, CorrectionMethod.BH)
        for by_val, bh_val in zip(adj, adj_bh):
            assert by_val >= bh_val or abs(by_val - bh_val) < 1e-10

    def test_empty_input(self):
        assert multiple_test_correction([], CorrectionMethod.BH) == []

    def test_single_value(self):
        adj = multiple_test_correction([0.05], CorrectionMethod.BH)
        assert len(adj) == 1
        assert adj[0] == 0.05

    def test_string_method_name(self):
        adj = multiple_test_correction([0.01, 0.05], "bonferroni")
        assert adj[0] == 0.02

    def test_string_aliases(self):
        p = [0.01, 0.05]
        adj_bh = multiple_test_correction(p, "bh")
        adj_fdr = multiple_test_correction(p, "fdr_bh")
        assert adj_bh == adj_fdr

    def test_all_ones(self):
        adj = multiple_test_correction([1.0, 1.0, 1.0], CorrectionMethod.BH)
        assert all(v == 1.0 for v in adj)


# =============================================================================
# _normalize_id_type
# =============================================================================


class TestNormalizeIdType:
    def test_symbol_aliases(self):
        for alias in ["symbol", "gene_symbol", "gene_name", "hgnc_symbol"]:
            assert _normalize_id_type(alias) == "symbol"

    def test_entrez_aliases(self):
        for alias in ["entrez", "entrezgene", "ncbi_gene", "gene_id"]:
            assert _normalize_id_type(alias) == "entrez"

    def test_case_insensitive(self):
        assert _normalize_id_type("SYMBOL") == "symbol"
        assert _normalize_id_type("Ensembl") == "ensembl"

    def test_unknown_passthrough(self):
        assert _normalize_id_type("custom_id") == "custom_id"


# =============================================================================
# ora() — core function with custom gene sets
# =============================================================================


class TestORA:
    @pytest.fixture
    def gene_sets(self):
        return {
            "pathway_a": ("Pathway A", {"G1", "G2", "G3", "G4", "G5"}),
            "pathway_b": ("Pathway B", {"G3", "G4", "G5", "G6", "G7", "G8"}),
            "pathway_c": ("Pathway C", {"G10", "G11", "G12"}),
        }

    def test_basic_enrichment(self, gene_sets):
        genes = ["G1", "G2", "G3", "G4", "G5"]
        result = ora(genes, gene_sets, min_overlap=1)
        assert len(result) > 0
        assert result.database == "custom"
        assert len(result.query_genes) == 5

    def test_custom_background(self, gene_sets):
        genes = ["G1", "G2", "G3"]
        bg = {f"G{i}" for i in range(1, 21)}
        result = ora(genes, gene_sets, background=bg, min_overlap=1)
        assert result.background_size == 20

    def test_no_overlap_returns_empty(self):
        genes = ["X1", "X2"]
        gene_sets = {"p1": ("P", {"Y1", "Y2", "Y3"})}
        result = ora(genes, gene_sets, min_overlap=1)
        # Query genes are in background (added automatically), but no overlap with gene set
        assert len(result.results) == 0

    def test_min_overlap_filter(self, gene_sets):
        genes = ["G3"]  # Only 1 gene overlapping with pathway_a
        result = ora(genes, gene_sets, min_overlap=3)
        assert len(result.results) == 0

    def test_pathway_objects_as_input(self):
        pathways = {
            "p1": Pathway(
                id="p1", name="Path 1",
                genes=frozenset(["A", "B", "C"]),
                database="test",
            )
        }
        result = ora(["A", "B", "C"], pathways, min_overlap=1)
        assert len(result) > 0

    def test_empty_query_genes(self, gene_sets):
        result = ora([], gene_sets)
        assert len(result.results) == 0
        assert result.unmapped_genes == []

    def test_adjusted_p_values_set(self, gene_sets):
        genes = ["G1", "G2", "G3", "G4", "G5"]
        result = ora(genes, gene_sets, min_overlap=1)
        for term in result.results:
            assert term.adjusted_p_value >= term.p_value or abs(
                term.adjusted_p_value - term.p_value
            ) < 1e-10

    def test_results_sorted_by_adjusted_p(self, gene_sets):
        genes = ["G1", "G2", "G3", "G4", "G5"]
        result = ora(genes, gene_sets, min_overlap=1)
        adj_ps = [r.adjusted_p_value for r in result.results]
        assert adj_ps == sorted(adj_ps)

    def test_correction_method_string(self, gene_sets):
        genes = ["G1", "G2", "G3", "G4", "G5"]
        result = ora(genes, gene_sets, min_overlap=1, correction_method="bonferroni")
        assert len(result) > 0

    def test_mapped_unmapped_genes(self):
        gene_sets = {"p1": ("P", {"A", "B", "C"})}
        genes = ["A", "B", "D"]  # D is not in any gene set or background
        result = ora(genes, gene_sets, min_overlap=1)
        # Background = gene_sets union + query_set
        assert "A" in result.mapped_genes
        assert "B" in result.mapped_genes


# =============================================================================
# Enum values
# =============================================================================


class TestEnums:
    def test_pathway_database_values(self):
        assert PathwayDatabase.KEGG.value == "kegg"
        assert PathwayDatabase.GO.value == "go"

    def test_go_aspect_values(self):
        assert GOAspect.BIOLOGICAL_PROCESS.value == "biological_process"
        assert GOAspect.ALL.value == "all"

    def test_correction_method_values(self):
        assert CorrectionMethod.BH.value == "benjamini_hochberg"
        assert CorrectionMethod.BONFERRONI.value == "bonferroni"

    def test_translation_database_values(self):
        assert TranslationDatabase.BIOMART.value == "biomart"
        assert TranslationDatabase.NCBI.value == "ncbi"
