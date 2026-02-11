"""Tests for biodbs.data.EnrichR.data module."""

import pytest
from biodbs.data.EnrichR.data import EnrichRFetchedData, EnrichRLibrariesData


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def dict_results():
    return [
        {
            "rank": 1,
            "term_name": "p53 signaling pathway",
            "p_value": 0.001,
            "z_score": -2.5,
            "combined_score": 15.0,
            "overlapping_genes": ["TP53", "MDM2", "CDKN1A"],
            "adjusted_p_value": 0.01,
        },
        {
            "rank": 2,
            "term_name": "Cell cycle",
            "p_value": 0.01,
            "z_score": -1.8,
            "combined_score": 8.0,
            "overlapping_genes": ["CDK2", "CCNB1"],
            "adjusted_p_value": 0.05,
        },
        {
            "rank": 3,
            "term_name": "Apoptosis",
            "p_value": 0.1,
            "z_score": -0.5,
            "combined_score": 2.0,
            "overlapping_genes": ["BAX"],
            "adjusted_p_value": 0.3,
        },
    ]


@pytest.fixture
def raw_api_results():
    """Raw API row format: [rank, term, p-value, z-score, combined_score, genes, adj_p, old_p, old_adj_p]."""
    return [
        [1, "KEGG pathway A", 0.001, -2.0, 12.0, ["GENE1", "GENE2"], 0.005, 0.002, 0.008],
        [2, "KEGG pathway B", 0.05, -1.0, 4.0, ["GENE3"], 0.1, 0.06, 0.15],
    ]


@pytest.fixture
def enrichr_data(dict_results):
    return EnrichRFetchedData(
        results=dict_results,
        query_genes=["TP53", "MDM2", "CDKN1A", "CDK2", "CCNB1", "BAX"],
        user_list_id=12345,
        library_name="KEGG_2021_Human",
    )


@pytest.fixture
def library_results():
    return [
        {
            "libraryName": "KEGG_2021_Human",
            "numTerms": 320,
            "geneCoverage": 8000,
            "genesPerTerm": 25.0,
            "link": "https://www.kegg.jp",
            "categoryId": 2,
        },
        {
            "libraryName": "GO_Biological_Process_2021",
            "numTerms": 5000,
            "geneCoverage": 15000,
            "genesPerTerm": 30.0,
            "link": "http://geneontology.org",
            "categoryId": 3,
        },
        {
            "libraryName": "KEGG_2019_Mouse",
            "numTerms": 300,
            "geneCoverage": 7500,
            "genesPerTerm": 24.0,
            "link": "https://www.kegg.jp",
            "categoryId": 2,
        },
    ]


# =============================================================================
# Tests: EnrichRFetchedData
# =============================================================================


class TestInit:
    def test_basic(self, enrichr_data):
        assert len(enrichr_data) == 3
        assert enrichr_data.library_name == "KEGG_2021_Human"
        assert enrichr_data.user_list_id == 12345
        assert len(enrichr_data.query_genes) == 6

    def test_defaults(self, dict_results):
        data = EnrichRFetchedData(results=dict_results)
        assert data.query_genes == []
        assert data.user_list_id is None
        assert data.library_name is None

    def test_results_property(self, enrichr_data, dict_results):
        assert enrichr_data.results is dict_results

    def test_repr_with_significant(self, enrichr_data):
        r = repr(enrichr_data)
        assert "EnrichRFetchedData" in r
        assert "3 terms" in r
        assert "significant" in r
        assert "KEGG_2021_Human" in r

    def test_repr_no_significant(self):
        data = EnrichRFetchedData(results=[{
            "term_name": "X", "p_value": 0.5, "adjusted_p_value": 0.9,
            "z_score": 0, "combined_score": 0,
        }])
        r = repr(data)
        assert "EnrichRFetchedData" in r
        assert "significant" not in r


class TestGetEnrichmentTerms:
    def test_dict_format(self, enrichr_data):
        terms = enrichr_data.get_enrichment_terms()
        assert len(terms) == 3
        assert terms[0].term_name == "p53 signaling pathway"
        assert terms[0].overlapping_genes == ["TP53", "MDM2", "CDKN1A"]

    def test_raw_api_format(self, raw_api_results):
        data = EnrichRFetchedData(results=raw_api_results)
        terms = data.get_enrichment_terms()
        assert len(terms) == 2
        assert terms[0].term_name == "KEGG pathway A"
        assert terms[0].p_value == 0.001
        assert terms[0].overlapping_genes == ["GENE1", "GENE2"]

    def test_string_genes(self):
        data = EnrichRFetchedData(results=[{
            "term_name": "Test", "p_value": 0.01,
            "z_score": -1.0, "combined_score": 5.0,
            "overlapping_genes": "GENE1;GENE2;GENE3",
            "adjusted_p_value": 0.05,
        }])
        terms = data.get_enrichment_terms()
        assert terms[0].overlapping_genes == ["GENE1", "GENE2", "GENE3"]

    def test_empty(self):
        data = EnrichRFetchedData(results=[])
        assert data.get_enrichment_terms() == []

    def test_alternate_key_names(self):
        """Test using capitalized key names (alternative format)."""
        data = EnrichRFetchedData(results=[{
            "Term": "Pathway X",
            "P-value": 0.01,
            "Z-score": -1.5,
            "Combined Score": 10.0,
            "Genes": ["A", "B"],
            "Adjusted P-value": 0.05,
        }])
        terms = data.get_enrichment_terms()
        assert terms[0].term_name == "Pathway X"
        assert terms[0].p_value == 0.01


class TestGetEnrichmentResult:
    def test_returns_result(self, enrichr_data):
        result = enrichr_data.get_enrichment_result()
        assert result.library_name == "KEGG_2021_Human"
        assert len(result.terms) == 3

    def test_unknown_library(self, dict_results):
        data = EnrichRFetchedData(results=dict_results)
        result = data.get_enrichment_result()
        assert result.library_name == "unknown"


class TestSignificantTerms:
    def test_default_threshold(self, enrichr_data):
        sig = enrichr_data.significant_terms()
        assert len(sig) == 1  # Only adj_p < 0.05 → p53 pathway (0.01)

    def test_custom_threshold(self, enrichr_data):
        sig = enrichr_data.significant_terms(p_threshold=0.1)
        assert len(sig) == 2  # adj_p < 0.1 → p53 (0.01) + Cell cycle (0.05)

    def test_use_raw_pvalue(self, enrichr_data):
        sig = enrichr_data.significant_terms(use_adjusted=False)
        assert len(sig) == 2  # p < 0.05 → p53 (0.001) + Cell cycle (0.01)

    def test_preserves_metadata(self, enrichr_data):
        sig = enrichr_data.significant_terms()
        assert sig.library_name == "KEGG_2021_Human"
        assert sig.query_genes == enrichr_data.query_genes


class TestTopTerms:
    def test_top_n(self, enrichr_data):
        top = enrichr_data.top_terms(n=2)
        assert len(top) == 2
        # Sorted by combined_score descending: 15.0, 8.0
        terms = top.get_enrichment_terms()
        assert terms[0].combined_score >= terms[1].combined_score

    def test_top_more_than_available(self, enrichr_data):
        top = enrichr_data.top_terms(n=100)
        assert len(top) == 3

    def test_preserves_metadata(self, enrichr_data):
        top = enrichr_data.top_terms(n=1)
        assert top.library_name == "KEGG_2021_Human"


class TestGetTermNames:
    def test_names(self, enrichr_data):
        names = enrichr_data.get_term_names()
        assert names == ["p53 signaling pathway", "Cell cycle", "Apoptosis"]

    def test_empty(self):
        data = EnrichRFetchedData(results=[])
        assert data.get_term_names() == []


class TestGetGenesForTerm:
    def test_existing_term(self, enrichr_data):
        genes = enrichr_data.get_genes_for_term("p53 signaling pathway")
        assert genes == ["TP53", "MDM2", "CDKN1A"]

    def test_nonexistent_term(self, enrichr_data):
        genes = enrichr_data.get_genes_for_term("Nonexistent pathway")
        assert genes == []


# =============================================================================
# Tests: EnrichRLibrariesData
# =============================================================================


class TestLibrariesInit:
    def test_basic(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        assert len(libs) == 3

    def test_repr(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        r = repr(libs)
        assert "EnrichRLibrariesData" in r
        assert "3 libraries" in r

    def test_results_property(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        assert libs.results is library_results


class TestGetLibraries:
    def test_parses(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        parsed = libs.get_libraries()
        assert len(parsed) == 3
        assert parsed[0].libraryName == "KEGG_2021_Human"
        assert parsed[0].numTerms == 320

    def test_empty(self):
        libs = EnrichRLibrariesData(results=[])
        assert libs.get_libraries() == []


class TestGetLibraryNames:
    def test_names(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        names = libs.get_library_names()
        assert "KEGG_2021_Human" in names
        assert "GO_Biological_Process_2021" in names


class TestFilterByCategory:
    def test_filter(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        filtered = libs.filter_by_category(2)  # PATHWAYS
        assert len(filtered) == 2
        names = filtered.get_library_names()
        assert "KEGG_2021_Human" in names
        assert "KEGG_2019_Mouse" in names

    def test_no_match(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        filtered = libs.filter_by_category(99)
        assert len(filtered) == 0


class TestSearch:
    def test_case_insensitive(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        found = libs.search("kegg")
        assert len(found) == 2

    def test_partial_match(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        found = libs.search("Biological")
        assert len(found) == 1
        assert found.get_library_names() == ["GO_Biological_Process_2021"]

    def test_no_match(self, library_results):
        libs = EnrichRLibrariesData(results=library_results)
        found = libs.search("nonexistent_library")
        assert len(found) == 0
