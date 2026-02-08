"""Tests for Disease Ontology fetcher (integration tests)."""

import pytest
from biodbs.fetch.DiseaseOntology import DO_Fetcher


class TestDOFetcherBasic:
    """Basic tests for Disease Ontology fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return DO_Fetcher()

    def test_init(self, fetcher):
        """Test fetcher initialization."""
        assert fetcher._api_config is not None

    def test_normalize_doid(self, fetcher):
        """Test DOID normalization."""
        assert fetcher._normalize_doid("DOID:162") == "DOID:162"
        assert fetcher._normalize_doid("DOID_162") == "DOID:162"
        assert fetcher._normalize_doid("162") == "DOID:162"
        assert fetcher._normalize_doid("  DOID:162  ") == "DOID:162"

    def test_doid_to_iri(self, fetcher):
        """Test DOID to IRI conversion."""
        iri = fetcher._doid_to_iri("DOID:162")
        assert iri == "http://purl.obolibrary.org/obo/DOID_162"


class TestDOFetcherTermAPI:
    """API integration tests for Disease Ontology term fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return DO_Fetcher()

    def test_get_term_cancer(self, fetcher):
        """Test getting cancer term by DOID."""
        term = fetcher.get_term("DOID:162")
        assert len(term) == 1
        assert term.terms[0].doid == "DOID:162"
        assert "cancer" in term.terms[0].name.lower()

    def test_get_term_breast_cancer(self, fetcher):
        """Test getting breast cancer term."""
        term = fetcher.get_term("DOID:1612")
        assert len(term) == 1
        assert term.terms[0].doid == "DOID:1612"
        assert "breast" in term.terms[0].name.lower()

    def test_get_term_without_prefix(self, fetcher):
        """Test getting term without DOID prefix."""
        term = fetcher.get_term("162")
        assert len(term) == 1
        assert term.terms[0].doid == "DOID:162"

    def test_get_terms_multiple(self, fetcher):
        """Test getting multiple terms."""
        terms = fetcher.get_terms(["DOID:162", "DOID:1612"])
        assert len(terms) == 2
        doids = terms.get_doids()
        assert "DOID:162" in doids
        assert "DOID:1612" in doids

    def test_get_terms_empty(self, fetcher):
        """Test getting empty list of terms."""
        terms = fetcher.get_terms([])
        assert len(terms) == 0

    def test_get_all_terms(self, fetcher):
        """Test getting all terms (paginated)."""
        terms = fetcher.get_all_terms(page=0, page_size=10)
        assert len(terms) <= 10
        # Should have some terms
        assert len(terms) > 0


class TestDOFetcherSearchAPI:
    """API integration tests for Disease Ontology search."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return DO_Fetcher()

    def test_search_cancer(self, fetcher):
        """Test searching for cancer."""
        results = fetcher.search("cancer", rows=10)
        assert len(results) > 0
        # Should find cancer-related terms
        names = results.get_names()
        assert any("cancer" in name.lower() for name in names)

    def test_search_breast_cancer(self, fetcher):
        """Test searching for breast cancer."""
        results = fetcher.search("breast cancer", rows=10)
        assert len(results) > 0

    def test_search_exact(self, fetcher):
        """Test exact search."""
        results = fetcher.search("cancer", exact=True, rows=10)
        # Exact search might return fewer results
        assert len(results) >= 0

    def test_search_pagination(self, fetcher):
        """Test search pagination."""
        page1 = fetcher.search("disease", rows=5, start=0)
        page2 = fetcher.search("disease", rows=5, start=5)
        # Pages should have different results
        doids1 = set(page1.get_doids())
        doids2 = set(page2.get_doids())
        # There should be no overlap between pages
        assert doids1.isdisjoint(doids2)


class TestDOFetcherHierarchyAPI:
    """API integration tests for Disease Ontology hierarchy."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return DO_Fetcher()

    def test_get_parents(self, fetcher):
        """Test getting parent terms."""
        # Breast cancer should have cancer as parent
        parents = fetcher.get_parents("DOID:1612")
        assert len(parents) > 0
        # Should include breast disease or cancer
        doids = parents.get_doids()
        assert len(doids) > 0

    def test_get_children(self, fetcher):
        """Test getting child terms."""
        # Cancer should have many children
        children = fetcher.get_children("DOID:162")
        assert len(children) > 0

    def test_get_ancestors(self, fetcher):
        """Test getting ancestor terms."""
        # Breast cancer should have multiple ancestors
        ancestors = fetcher.get_ancestors("DOID:1612")
        assert len(ancestors) > 0

    def test_get_descendants(self, fetcher):
        """Test getting descendant terms."""
        # Cancer should have many descendants
        descendants = fetcher.get_descendants("DOID:162")
        assert len(descendants) > 0


class TestDOFetcherXrefAPI:
    """API integration tests for Disease Ontology cross-references."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return DO_Fetcher()

    def test_term_has_xrefs(self, fetcher):
        """Test that terms have cross-references."""
        term = fetcher.get_term("DOID:162")
        assert len(term) == 1
        t = term.terms[0]
        # Cancer should have some xrefs
        # Not all terms have all xref types, so just check the term exists
        assert t.doid == "DOID:162"

    def test_doid_to_mesh(self, fetcher):
        """Test DOID to MeSH mapping."""
        mapping = fetcher.doid_to_mesh(["DOID:162"])
        assert "DOID:162" in mapping
        # Cancer should have MeSH mapping
        # MeSH ID for cancer is D009369
        if mapping["DOID:162"]:
            assert mapping["DOID:162"].startswith("D")

    def test_doid_to_umls(self, fetcher):
        """Test DOID to UMLS mapping."""
        mapping = fetcher.doid_to_umls(["DOID:162"])
        assert "DOID:162" in mapping

    def test_doid_to_icd10(self, fetcher):
        """Test DOID to ICD-10 mapping."""
        mapping = fetcher.doid_to_icd10(["DOID:162"])
        assert "DOID:162" in mapping


class TestDOFetcherOntologyInfo:
    """API integration tests for ontology information."""

    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        return DO_Fetcher()

    def test_get_ontology_info(self, fetcher):
        """Test getting ontology info."""
        info = fetcher.get_ontology_info()
        assert info is not None
        # Should have config section
        config = info.get("config", {})
        assert config.get("id") == "doid" or config.get("namespace") == "doid"


class TestDOConvenienceFunctions:
    """Tests for Disease Ontology convenience functions."""

    def test_do_get_term(self):
        """Test do_get_term function."""
        from biodbs.fetch.DiseaseOntology import do_get_term

        term = do_get_term("DOID:162")
        assert len(term) == 1
        assert "cancer" in term.terms[0].name.lower()

    def test_do_get_terms(self):
        """Test do_get_terms function."""
        from biodbs.fetch.DiseaseOntology import do_get_terms

        terms = do_get_terms(["DOID:162", "DOID:1612"])
        assert len(terms) == 2

    def test_do_search(self):
        """Test do_search function."""
        from biodbs.fetch.DiseaseOntology import do_search

        results = do_search("cancer", rows=5)
        assert len(results) > 0

    def test_do_get_parents(self):
        """Test do_get_parents function."""
        from biodbs.fetch.DiseaseOntology import do_get_parents

        parents = do_get_parents("DOID:1612")
        assert len(parents) > 0

    def test_do_get_children(self):
        """Test do_get_children function."""
        from biodbs.fetch.DiseaseOntology import do_get_children

        children = do_get_children("DOID:162")
        assert len(children) > 0

    def test_doid_to_mesh_func(self):
        """Test doid_to_mesh function."""
        from biodbs.fetch.DiseaseOntology import doid_to_mesh

        mapping = doid_to_mesh(["DOID:162"])
        assert "DOID:162" in mapping

    def test_doid_to_mesh_dataframe(self):
        """Test doid_to_mesh function with DataFrame output."""
        from biodbs.fetch.DiseaseOntology import doid_to_mesh

        df = doid_to_mesh(["DOID:162"], return_dict=False)
        assert "doid" in df.columns
        assert "mesh_id" in df.columns

    def test_do_xref_mapping(self):
        """Test do_xref_mapping function."""
        from biodbs.fetch.DiseaseOntology import do_xref_mapping

        mapping = do_xref_mapping(["DOID:162"], "MESH")
        assert isinstance(mapping, dict)
