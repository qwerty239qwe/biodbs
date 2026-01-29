"""Integration tests for QuickGO_Fetcher - tests actual API calls.

These tests make real HTTP requests to the QuickGO API to verify:
1. URL construction is correct
2. Response parsing works
3. Data can be retrieved successfully

Run with: pytest tests/test_quickgo_fetcher.py -v
Skip slow tests: pytest tests/test_quickgo_fetcher.py -v -m "not slow"
"""
import pytest
from biodbs.fetch.QuickGO.quickgo_fetcher import QuickGO_Fetcher
from biodbs.data.QuickGO.data import QuickGOFetchedData


@pytest.fixture
def fetcher():
    """Create a QuickGO_Fetcher instance for testing."""
    return QuickGO_Fetcher()


# =============================================================================
# Ontology Endpoint Tests
# =============================================================================

class TestOntologyAbout:
    """Tests for ontology/about endpoint."""

    def test_about_returns_data(self, fetcher):
        data = fetcher.get(category="ontology", endpoint="about")
        assert isinstance(data, QuickGOFetchedData)
        assert data.results or data.metadata


class TestOntologySearch:
    """Tests for ontology/search endpoint."""

    def test_search_apoptosis(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="search",
            query="apoptosis",
            limit=5
        )
        assert isinstance(data, QuickGOFetchedData)
        assert len(data.results) > 0
        assert len(data.results) <= 5

    def test_search_returns_expected_fields(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="search",
            query="mitochondrion",
            limit=3
        )
        assert len(data.results) > 0
        first_result = data.results[0]
        # Check expected fields exist
        assert "id" in first_result
        assert "name" in first_result
        assert first_result["id"].startswith("GO:")

    def test_search_eco_ontology(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="search",
            ontology="eco",
            query="evidence",
            limit=3
        )
        assert len(data.results) > 0
        first_result = data.results[0]
        assert first_result["id"].startswith("ECO:")


class TestOntologyTerms:
    """Tests for ontology/terms endpoints."""

    def test_get_single_term(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="terms/{ids}",
            ids="GO:0008150"  # biological_process
        )
        assert len(data.results) == 1
        assert data.results[0]["id"] == "GO:0008150"
        assert data.results[0]["name"] == "biological_process"

    def test_get_multiple_terms(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="terms/{ids}",
            ids=["GO:0008150", "GO:0003674", "GO:0005575"]
        )
        assert len(data.results) == 3
        ids = [r["id"] for r in data.results]
        assert "GO:0008150" in ids
        assert "GO:0003674" in ids
        assert "GO:0005575" in ids

    def test_get_term_ancestors(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="terms/{ids}/ancestors",
            ids="GO:0006915"  # apoptotic process
        )
        assert len(data.results) > 0
        # Should have ancestors
        first_result = data.results[0]
        assert "id" in first_result

    def test_get_term_children(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="terms/{ids}/children",
            ids="GO:0008150"  # biological_process - has many children
        )
        assert len(data.results) > 0

    def test_get_term_descendants(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="terms/{ids}/descendants",
            ids="GO:0008150",
            limit=10
        )
        assert len(data.results) > 0


class TestOntologySlim:
    """Tests for ontology/slim endpoint."""

    def test_slim_mapping(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="slim",
            slimsToIds=["GO:0008150", "GO:0003674"],
            slimsFromIds=["GO:0006915"]
        )
        assert isinstance(data, QuickGOFetchedData)
        # May or may not have results depending on mapping


class TestOntologyGraph:
    """Tests for ontology/terms/graph endpoint."""

    def test_graph_with_start_ids(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="terms/graph",
            startIds=["GO:0006915"]
        )
        assert len(data.results) > 0
        # Graph results contain vertices and edges
        first_result = data.results[0]
        assert "vertices" in first_result or "edges" in first_result


# =============================================================================
# Annotation Endpoint Tests
# =============================================================================

class TestAnnotationSearch:
    """Tests for annotation/search endpoint."""

    def test_search_by_go_id(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",  # apoptotic process
            limit=10
        )
        assert isinstance(data, QuickGOFetchedData)
        assert len(data.results) > 0
        assert len(data.results) <= 10

    def test_search_returns_expected_fields(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=5
        )
        assert len(data.results) > 0
        first_result = data.results[0]
        # Check expected annotation fields
        assert "geneProductId" in first_result
        assert "goId" in first_result
        assert "evidenceCode" in first_result

    def test_search_by_go_id_and_taxon(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            taxonId=9606,  # Human
            limit=10
        )
        assert len(data.results) > 0
        # All results should be for human
        for result in data.results:
            assert "9606" in str(result.get("taxonId", ""))

    def test_search_with_evidence_filter(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            goEvidence="IDA",  # Inferred from Direct Assay
            limit=10
        )
        assert len(data.results) > 0

    def test_search_with_aspect_filter(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            aspect="biological_process",
            limit=10
        )
        assert len(data.results) > 0

    def test_search_total_hits_in_metadata(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=5
        )
        total = data.get_total_hits()
        assert total > 0
        assert total >= len(data.results)


class TestAnnotationDownload:
    """Tests for annotation/downloadSearch endpoint."""

    def test_download_tsv_format(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            taxonId=9606,
            downloadFormat="tsv",
            limit=10
        )
        assert isinstance(data, QuickGOFetchedData)
        # TSV format should have text
        assert data.text is not None or len(data.results) > 0

    def test_download_gaf_format(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            taxonId=9606,
            downloadFormat="gaf",
            limit=10
        )
        assert isinstance(data, QuickGOFetchedData)
        # GAF format should have text content
        assert data.text is not None or len(data.results) > 0

    def test_download_gpad_format(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            taxonId=9606,
            downloadFormat="gpad",
            limit=10
        )
        assert isinstance(data, QuickGOFetchedData)


# =============================================================================
# Gene Product Endpoint Tests
# =============================================================================

class TestGeneProductSearch:
    """Tests for geneproduct/search endpoint."""

    def test_search_by_symbol(self, fetcher):
        data = fetcher.get(
            category="geneproduct",
            endpoint="search",
            query="TP53"
        )
        assert isinstance(data, QuickGOFetchedData)
        assert len(data.results) > 0

    def test_search_returns_gene_product_fields(self, fetcher):
        data = fetcher.get(
            category="geneproduct",
            endpoint="search",
            query="BRCA1",
            limit=5
        )
        assert len(data.results) > 0
        # Results should be in searchHits format
        first_result = data.results[0]
        # Gene product search returns different structure
        assert isinstance(first_result, dict)

    def test_search_with_taxon_filter(self, fetcher):
        data = fetcher.get(
            category="geneproduct",
            endpoint="search",
            query="TP53",
            taxonId=9606  # Human
        )
        assert len(data.results) > 0


# =============================================================================
# DataFrame Conversion Tests
# =============================================================================

class TestDataFrameConversion:
    """Tests for converting results to DataFrame."""

    def test_annotation_to_pandas_dataframe(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=10
        )
        df = data.as_dataframe(engine="pandas")
        assert len(df) == len(data.results)
        assert "geneProductId" in df.columns

    def test_annotation_to_polars_dataframe(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=10
        )
        df = data.as_dataframe(engine="polars")
        assert len(df) == len(data.results)

    def test_ontology_search_to_dataframe(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="search",
            query="apoptosis",
            limit=5
        )
        df = data.as_dataframe()
        assert len(df) == len(data.results)
        assert "id" in df.columns
        assert "name" in df.columns

    def test_show_columns(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=5
        )
        columns = data.show_columns()
        assert isinstance(columns, list)
        assert len(columns) > 0
        assert "geneProductId" in columns


# =============================================================================
# Filter Tests
# =============================================================================

class TestDataFiltering:
    """Tests for filtering fetched data."""

    def test_filter_by_exact_value(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=50
        )
        # Filter to specific evidence code if present
        evidence_codes = [r.get("evidenceCode") for r in data.results]
        if "IDA" in evidence_codes:
            filtered = data.filter(evidenceCode="IDA")
            assert len(filtered) > 0
            assert all(r["evidenceCode"] == "IDA" for r in filtered.results)

    def test_filter_by_callable(self, fetcher):
        data = fetcher.get(
            category="ontology",
            endpoint="search",
            query="apoptosis",
            limit=20
        )
        # Filter to terms with "apoptosis" in name
        filtered = data.filter(name=lambda x: "apoptosis" in x.lower() if x else False)
        assert len(filtered) <= len(data)
        for r in filtered.results:
            assert "apoptosis" in r["name"].lower()


# =============================================================================
# Pagination Tests (get_all)
# =============================================================================

@pytest.mark.slow
class TestPagination:
    """Tests for get_all pagination - marked slow as they make multiple requests."""

    def test_get_all_annotation_search(self, fetcher):
        data = fetcher.get_all(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            taxonId=9606,
            limit_per_page=50,
            max_records=150
        )
        assert isinstance(data, QuickGOFetchedData)
        # Should have fetched multiple pages
        assert len(data.results) <= 150
        assert len(data.results) > 50  # More than one page

    def test_get_all_respects_max_records(self, fetcher):
        data = fetcher.get_all(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit_per_page=25,
            max_records=75
        )
        assert len(data.results) <= 75

    def test_get_all_ontology_search(self, fetcher):
        data = fetcher.get_all(
            category="ontology",
            endpoint="search",
            query="kinase",
            limit_per_page=50,
            max_records=120
        )
        assert len(data.results) > 0
        assert len(data.results) <= 120


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_go_id_format_raises_error(self, fetcher):
        # API returns 400 for invalid IDs
        with pytest.raises(ConnectionError) as exc_info:
            fetcher.get(
                category="ontology",
                endpoint="terms/{ids}",
                ids="INVALID:0000000"
            )
        assert "400" in str(exc_info.value)
        assert "invalid" in str(exc_info.value).lower()

    def test_missing_required_parameter(self, fetcher):
        with pytest.raises(ValueError):
            fetcher.get(
                category="ontology",
                endpoint="search"
                # Missing required 'query' parameter
            )

    def test_get_all_rejects_download_endpoint(self, fetcher):
        with pytest.raises(ValueError) as exc_info:
            fetcher.get_all(
                category="annotation",
                endpoint="downloadSearch",
                goId="GO:0006915"
            )
        assert "downloadSearch" in str(exc_info.value)


# =============================================================================
# Data Concatenation Tests
# =============================================================================

class TestDataConcatenation:
    """Tests for concatenating fetched data."""

    def test_concatenate_same_format(self, fetcher):
        data1 = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=5
        )
        data2 = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0008150",
            limit=5
        )
        original_len = len(data1.results)
        data1 += data2
        assert len(data1.results) == original_len + len(data2.results)


# =============================================================================
# Metadata Tests
# =============================================================================

class TestMetadata:
    """Tests for response metadata."""

    def test_page_info_present(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=10
        )
        page_info = data.get_page_info()
        # Page info may or may not be present depending on response
        assert isinstance(page_info, dict)

    def test_total_hits(self, fetcher):
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            limit=10
        )
        total = data.get_total_hits()
        assert isinstance(total, int)
        assert total >= len(data.results)
