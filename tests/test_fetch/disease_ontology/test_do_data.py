"""Tests for Disease Ontology data models and containers."""

from biodbs.data.DiseaseOntology._data_model import (
    DOBase,
    DOEndpoint,
    OLSEndpoint,
    DiseaseTerm,
    DiseaseTermDetailed,
    SearchResult,
    OntologyInfo,
    XRef,
    DOSearchRequest,
)
from biodbs.data.DiseaseOntology.data import (
    DOFetchedData,
    DOSearchFetchedData,
)


class TestDODataModels:
    """Tests for Disease Ontology Pydantic models."""

    def test_do_base_enum(self):
        """Test DOBase enum values."""
        assert DOBase.DO_API.value == "https://disease-ontology.org/api"
        assert DOBase.OLS_API.value == "https://www.ebi.ac.uk/ols4/api"

    def test_do_endpoint_enum(self):
        """Test DOEndpoint enum values."""
        assert "metadata" in DOEndpoint.METADATA.value

    def test_ols_endpoint_enum(self):
        """Test OLSEndpoint enum values."""
        assert OLSEndpoint.ONTOLOGY_INFO.value == "ontologies/doid"
        assert OLSEndpoint.TERMS.value == "ontologies/doid/terms"
        assert "search" in OLSEndpoint.SEARCH.value

    def test_disease_term_model(self):
        """Test DiseaseTerm model creation."""
        term = DiseaseTerm(
            doid="DOID:162",
            name="cancer",
            definition="A disease of cellular proliferation.",
            synonyms=["malignant neoplasm"],
            xrefs=["MESH:D009369", "UMLS_CUI:C0006826"],
            is_obsolete=False,
        )
        assert term.doid == "DOID:162"
        assert term.name == "cancer"
        assert term.id == "DOID:162"  # Test id property
        assert term.numeric_id == 162  # Test numeric_id property

    def test_disease_term_xref_methods(self):
        """Test DiseaseTerm cross-reference methods."""
        term = DiseaseTerm(
            doid="DOID:162",
            name="cancer",
            xrefs=["MESH:D009369", "UMLS_CUI:C0006826", "ICD10CM:C80.1"],
        )
        assert term.get_xref("MESH") == "D009369"
        assert term.get_xref("UMLS_CUI") == "C0006826"
        assert term.get_xref("ICD10CM") == "C80.1"
        assert term.mesh_id == "D009369"
        assert term.umls_cui == "C0006826"
        assert term.icd10_code == "C80.1"
        assert term.get_xref("NONEXISTENT") is None

    def test_disease_term_detailed_model(self):
        """Test DiseaseTermDetailed model with additional fields."""
        term = DiseaseTermDetailed(
            doid="DOID:162",
            name="cancer",
            iri="http://purl.obolibrary.org/obo/DOID_162",
            short_form="DOID_162",
            ontology_name="doid",
            ontology_prefix="DOID",
            has_children=True,
            is_root=False,
        )
        assert term.iri == "http://purl.obolibrary.org/obo/DOID_162"
        assert term.short_form == "DOID_162"
        assert term.has_children is True

    def test_xref_model(self):
        """Test XRef model."""
        xref = XRef(
            database="MESH",
            id="D009369",
            description="MeSH cross-reference",
        )
        assert xref.full_id == "MESH:D009369"

    def test_search_result_model(self):
        """Test SearchResult model."""
        result = SearchResult(
            iri="http://purl.obolibrary.org/obo/DOID_162",
            obo_id="DOID:162",
            label="cancer",
            description=["A disease of cellular proliferation."],
            synonyms=["malignant neoplasm"],
        )
        assert result.doid == "DOID:162"
        assert result.name == "cancer"
        assert result.definition == "A disease of cellular proliferation."

    def test_ontology_info_model(self):
        """Test OntologyInfo model."""
        info = OntologyInfo(
            ontology_id="doid",
            title="Human Disease Ontology",
            version="2024-01-31",
            number_of_terms=10000,
        )
        assert info.ontology_id == "doid"
        assert info.title == "Human Disease Ontology"

    def test_search_request_model(self):
        """Test DOSearchRequest model."""
        request = DOSearchRequest(
            query="cancer",
            ontology="doid",
            exact=False,
            rows=20,
            start=0,
        )
        params = request.get_params()
        assert params["q"] == "cancer"
        assert params["ontology"] == "doid"
        assert params["rows"] == 20


class TestDOFetchedData:
    """Tests for DOFetchedData container."""

    def test_empty_data(self):
        """Test DOFetchedData with empty data."""
        data = DOFetchedData([], query_ids=[])
        assert len(data) == 0
        assert data.total_count == 0
        assert data.terms == []

    def test_single_term_dict(self):
        """Test DOFetchedData with single term dict."""
        content = {
            "id": "DOID:162",
            "name": "cancer",
            "definition": "A disease of cellular proliferation.",
        }
        data = DOFetchedData(content, query_ids=["DOID:162"])
        assert len(data) == 1
        assert data.terms[0].doid == "DOID:162"
        assert data.terms[0].name == "cancer"

    def test_term_list(self):
        """Test DOFetchedData with list of terms."""
        content = [
            {"id": "DOID:162", "name": "cancer"},
            {"id": "DOID:1612", "name": "breast cancer"},
        ]
        data = DOFetchedData(content, query_ids=["DOID:162", "DOID:1612"])
        assert len(data) == 2
        assert data.get_doids() == ["DOID:162", "DOID:1612"]
        assert data.get_names() == ["cancer", "breast cancer"]

    def test_ols_embedded_response(self):
        """Test DOFetchedData with OLS _embedded response."""
        content = {
            "_embedded": {
                "terms": [
                    {
                        "obo_id": "DOID:162",
                        "label": "cancer",
                        "description": ["A disease of cellular proliferation."],
                        "is_obsolete": False,
                        "has_children": True,
                    }
                ]
            }
        }
        data = DOFetchedData(content, query_ids=["DOID:162"])
        assert len(data) == 1
        assert data.terms[0].doid == "DOID:162"
        assert data.terms[0].name == "cancer"
        assert data.terms[0].has_children is True

    def test_get_term_by_id(self):
        """Test get_term method."""
        content = [
            {"id": "DOID:162", "name": "cancer"},
            {"id": "DOID:1612", "name": "breast cancer"},
        ]
        data = DOFetchedData(content)

        term = data.get_term("DOID:162")
        assert term is not None
        assert term.name == "cancer"

        # Test without prefix
        term = data.get_term("162")
        assert term is not None
        assert term.name == "cancer"

    def test_get_term_by_name(self):
        """Test get_term_by_name method."""
        content = [
            {"id": "DOID:162", "name": "cancer"},
            {"id": "DOID:1612", "name": "breast cancer"},
        ]
        data = DOFetchedData(content)

        term = data.get_term_by_name("breast")
        assert term is not None
        assert term.doid == "DOID:1612"

    def test_as_dict(self):
        """Test as_dict method."""
        content = [
            {
                "id": "DOID:162",
                "name": "cancer",
                "xrefs": ["MESH:D009369"],
            }
        ]
        data = DOFetchedData(content)
        result = data.as_dict()
        assert len(result) == 1
        assert result[0]["doid"] == "DOID:162"
        assert result[0]["name"] == "cancer"
        assert result[0]["mesh_id"] == "D009369"

    def test_as_dict_with_columns(self):
        """Test as_dict with column filter."""
        content = [{"id": "DOID:162", "name": "cancer"}]
        data = DOFetchedData(content)
        result = data.as_dict(columns=["doid", "name"])
        assert "doid" in result[0]
        assert "name" in result[0]
        assert "definition" not in result[0]

    def test_as_dataframe_pandas(self):
        """Test as_dataframe with pandas."""
        content = [
            {"id": "DOID:162", "name": "cancer"},
            {"id": "DOID:1612", "name": "breast cancer"},
        ]
        data = DOFetchedData(content)
        df = data.as_dataframe(engine="pandas")
        assert len(df) == 2
        assert "doid" in df.columns
        assert "name" in df.columns

    def test_as_dataframe_polars(self):
        """Test as_dataframe with polars."""
        content = [{"id": "DOID:162", "name": "cancer"}]
        data = DOFetchedData(content)
        df = data.as_dataframe(engine="polars")
        assert len(df) == 1
        assert "doid" in df.columns

    def test_filter_by_xref_db(self):
        """Test filter_by_xref_db method."""
        content = [
            {"id": "DOID:162", "name": "cancer", "xrefs": ["MESH:D009369"]},
            {"id": "DOID:1612", "name": "breast cancer"},
        ]
        data = DOFetchedData(content)
        filtered = data.filter_by_xref_db("MESH")
        assert len(filtered) == 1
        assert filtered.terms[0].doid == "DOID:162"

    def test_to_xref_mapping(self):
        """Test to_xref_mapping method."""
        content = [
            {"id": "DOID:162", "name": "cancer", "xrefs": ["MESH:D009369"]},
            {"id": "DOID:1612", "name": "breast cancer", "xrefs": ["MESH:D001943"]},
        ]
        data = DOFetchedData(content)
        mapping = data.to_xref_mapping("MESH")
        assert mapping["DOID:162"] == "D009369"
        assert mapping["DOID:1612"] == "D001943"

    def test_concatenation(self):
        """Test += operator for concatenation."""
        data1 = DOFetchedData([{"id": "DOID:162", "name": "cancer"}])
        data2 = DOFetchedData([{"id": "DOID:1612", "name": "breast cancer"}])
        data1 += data2
        assert len(data1) == 2

    def test_show_columns(self):
        """Test show_columns method."""
        data = DOFetchedData([])
        columns = data.show_columns()
        assert "doid" in columns
        assert "name" in columns
        assert "mesh_id" in columns

    def test_summary(self):
        """Test summary method."""
        content = [{"id": "DOID:162", "name": "cancer"}]
        data = DOFetchedData(content, query_ids=["DOID:162"])
        summary = data.summary()
        assert "Disease Ontology Results" in summary
        assert "Terms found: 1" in summary


class TestDOSearchFetchedData:
    """Tests for DOSearchFetchedData container."""

    def test_empty_search(self):
        """Test DOSearchFetchedData with empty results."""
        content = {"response": {"docs": [], "numFound": 0, "start": 0}}
        data = DOSearchFetchedData(content, query="test")
        assert len(data) == 0
        assert data.total_count == 0

    def test_search_results(self):
        """Test DOSearchFetchedData with results."""
        content = {
            "response": {
                "docs": [
                    {
                        "iri": "http://purl.obolibrary.org/obo/DOID_162",
                        "obo_id": "DOID:162",
                        "label": "cancer",
                        "description": ["A disease of cellular proliferation."],
                    },
                    {
                        "iri": "http://purl.obolibrary.org/obo/DOID_1612",
                        "obo_id": "DOID:1612",
                        "label": "breast cancer",
                    },
                ],
                "numFound": 100,
                "start": 0,
            }
        }
        data = DOSearchFetchedData(content, query="cancer")
        assert len(data) == 2
        assert data.total_count == 100
        assert data.query == "cancer"
        assert data.get_doids() == ["DOID:162", "DOID:1612"]
        assert data.get_names() == ["cancer", "breast cancer"]

    def test_as_dict(self):
        """Test as_dict method."""
        content = {
            "response": {
                "docs": [
                    {
                        "iri": "http://purl.obolibrary.org/obo/DOID_162",
                        "obo_id": "DOID:162",
                        "label": "cancer",
                        "description": ["A disease."],
                    }
                ],
                "numFound": 1,
            }
        }
        data = DOSearchFetchedData(content, query="cancer")
        result = data.as_dict()
        assert len(result) == 1
        assert result[0]["doid"] == "DOID:162"

    def test_as_dataframe(self):
        """Test as_dataframe method."""
        content = {
            "response": {
                "docs": [
                    {
                        "iri": "http://purl.obolibrary.org/obo/DOID_162",
                        "obo_id": "DOID:162",
                        "label": "cancer",
                    }
                ],
                "numFound": 1,
            }
        }
        data = DOSearchFetchedData(content, query="cancer")
        df = data.as_dataframe(engine="pandas")
        assert len(df) == 1
        assert "doid" in df.columns
