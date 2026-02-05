"""Tests for QuickGOModel data validation and URL building."""
import pytest
from pydantic import ValidationError

from biodbs.data.QuickGO._data_model import (
    QuickGOModel,
    GOAspect,
    GOEvidence,
    GORelation,
    AnnotationQualifier,
    GOUsage,
    GeneProductType,
    DownloadFormat,
    OntologySearchModel,
    OntologyTermsModel,
    OntologyAncestorsDescendantsModel,
    AnnotationSearchModel,
    GeneProductSearchModel,
)


# =============================================================================
# Ontology Endpoint Tests
# =============================================================================

class TestOntologyAbout:
    """Tests for ontology/about endpoint."""

    def test_about_endpoint_valid(self):
        model = QuickGOModel(category="ontology", endpoint="about")
        assert model.category == "ontology"
        assert model.endpoint == "about"

    def test_about_endpoint_builds_path(self):
        model = QuickGOModel(category="ontology", endpoint="about")
        assert model.build_path() == "go/about"

    def test_about_with_eco_ontology(self):
        model = QuickGOModel(category="ontology", endpoint="about", ontology="eco")
        assert model.build_path() == "eco/about"


class TestOntologySearch:
    """Tests for ontology/search endpoint."""

    def test_search_requires_query(self):
        with pytest.raises(ValidationError) as exc_info:
            QuickGOModel(category="ontology", endpoint="search")
        assert "query" in str(exc_info.value)

    def test_search_with_query_valid(self):
        model = QuickGOModel(category="ontology", endpoint="search", query="apoptosis")
        assert model.query == "apoptosis"

    def test_search_builds_path(self):
        model = QuickGOModel(category="ontology", endpoint="search", query="apoptosis")
        assert model.build_path() == "go/search"

    def test_search_builds_query_params(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="search",
            query="apoptosis",
            limit=100,
            page=2
        )
        params = model.build_query_params()
        assert params["query"] == "apoptosis"
        assert params["limit"] == 100
        assert params["page"] == 2


class TestOntologyTerms:
    """Tests for ontology/terms endpoints."""

    def test_terms_list_valid(self):
        model = QuickGOModel(category="ontology", endpoint="terms")
        assert model.build_path() == "go/terms"

    def test_terms_by_id_requires_ids(self):
        with pytest.raises(ValidationError) as exc_info:
            QuickGOModel(category="ontology", endpoint="terms/{ids}")
        assert "ids" in str(exc_info.value)

    def test_terms_by_id_single(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}",
            ids="GO:0008150"
        )
        assert model.ids == ["GO:0008150"]
        assert model.build_path() == "go/terms/GO:0008150"

    def test_terms_by_id_multiple(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}",
            ids=["GO:0008150", "GO:0003674"]
        )
        assert model.ids == ["GO:0008150", "GO:0003674"]
        assert model.build_path() == "go/terms/GO:0008150,GO:0003674"

    def test_terms_ancestors(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/ancestors",
            ids=["GO:0008150"],
            relations=[GORelation.is_a, GORelation.part_of]
        )
        assert model.build_path() == "go/terms/GO:0008150/ancestors"
        params = model.build_query_params()
        assert "relations" in params
        assert "is_a" in params["relations"]

    def test_terms_descendants(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/descendants",
            ids=["GO:0008150"]
        )
        assert model.build_path() == "go/terms/GO:0008150/descendants"

    def test_terms_children(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/children",
            ids=["GO:0008150"]
        )
        assert model.build_path() == "go/terms/GO:0008150/children"

    def test_terms_complete(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/complete",
            ids=["GO:0008150"]
        )
        assert model.build_path() == "go/terms/GO:0008150/complete"


class TestOntologyChart:
    """Tests for ontology/terms/{ids}/chart endpoint."""

    def test_chart_endpoint(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/chart",
            ids=["GO:0008150"]
        )
        assert model.build_path() == "go/terms/GO:0008150/chart"

    def test_chart_with_options(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/chart",
            ids=["GO:0008150"],
            showKey=True,
            showIds=False,
            fontSize=12
        )
        params = model.build_query_params()
        assert params["showKey"] is True
        assert params["showIds"] is False
        assert params["fontSize"] == 12

    def test_chart_coords(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/chart/coords",
            ids=["GO:0008150"]
        )
        assert model.build_path() == "go/terms/GO:0008150/chart/coords"


class TestOntologyGraph:
    """Tests for ontology/terms/graph endpoint."""

    def test_graph_requires_start_ids(self):
        with pytest.raises(ValidationError) as exc_info:
            QuickGOModel(category="ontology", endpoint="terms/graph")
        assert "startIds" in str(exc_info.value)

    def test_graph_with_start_ids(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/graph",
            startIds=["GO:0008150"]
        )
        params = model.build_query_params()
        assert params["startIds"] == "GO:0008150"

    def test_graph_with_stop_ids(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/graph",
            startIds=["GO:0008150"],
            stopIds=["GO:0003674"]
        )
        params = model.build_query_params()
        assert params["startIds"] == "GO:0008150"
        assert params["stopIds"] == "GO:0003674"


class TestOntologySlim:
    """Tests for ontology/slim endpoint."""

    def test_slim_requires_slims_to_ids(self):
        with pytest.raises(ValidationError) as exc_info:
            QuickGOModel(category="ontology", endpoint="slim")
        assert "slimsToIds" in str(exc_info.value)

    def test_slim_with_slims_to_ids(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="slim",
            slimsToIds=["GO:0008150"]
        )
        params = model.build_query_params()
        assert params["slimsToIds"] == "GO:0008150"

    def test_slim_with_from_ids(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="slim",
            slimsToIds=["GO:0008150"],
            slimsFromIds=["GO:0003674"]
        )
        params = model.build_query_params()
        assert params["slimsToIds"] == "GO:0008150"
        assert params["slimsFromIds"] == "GO:0003674"


# =============================================================================
# Annotation Endpoint Tests
# =============================================================================

class TestAnnotationSearch:
    """Tests for annotation/search endpoint."""

    def test_annotation_search_valid(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915"
        )
        assert model.category == "annotation"
        assert model.build_path() == "search"

    def test_annotation_search_with_taxon(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            taxonId=9606
        )
        params = model.build_query_params()
        assert params["goId"] == "GO:0006915"
        assert params["taxonId"] == 9606

    def test_annotation_search_with_multiple_go_ids(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId=["GO:0006915", "GO:0008150"]
        )
        params = model.build_query_params()
        assert params["goId"] == "GO:0006915,GO:0008150"

    def test_annotation_search_with_evidence(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            goEvidence=[GOEvidence.IDA, GOEvidence.IMP]
        )
        params = model.build_query_params()
        assert "IDA" in params["goEvidence"]
        assert "IMP" in params["goEvidence"]

    def test_annotation_search_with_aspect(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            aspect=GOAspect.biological_process
        )
        params = model.build_query_params()
        assert params["aspect"] == "biological_process"

    def test_annotation_search_with_qualifier(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            qualifier=AnnotationQualifier.enables
        )
        params = model.build_query_params()
        assert params["qualifier"] == "enables"

    def test_annotation_search_with_go_usage(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            goUsage=GOUsage.descendants,
            goUsageRelationships=[GORelation.is_a]
        )
        params = model.build_query_params()
        assert params["goUsage"] == "descendants"
        assert params["goUsageRelationships"] == "is_a"

    def test_annotation_search_with_assigned_by(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            assignedBy=["UniProt", "IntAct"]
        )
        params = model.build_query_params()
        assert params["assignedBy"] == "UniProt,IntAct"


class TestAnnotationDownload:
    """Tests for annotation/downloadSearch endpoint."""

    def test_download_with_tsv_format(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            downloadFormat=DownloadFormat.tsv
        )
        params = model.build_query_params()
        assert params["downloadFormat"] == "tsv"

    def test_download_with_gaf_format(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            downloadFormat=DownloadFormat.gaf
        )
        params = model.build_query_params()
        assert params["downloadFormat"] == "gaf"

    def test_download_with_gpad_format(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            downloadFormat=DownloadFormat.gpad
        )
        params = model.build_query_params()
        assert params["downloadFormat"] == "gpad"

    def test_download_with_selected_fields(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            downloadFormat=DownloadFormat.tsv,
            selectedFields=["geneProductId", "goId", "evidenceCode"]
        )
        params = model.build_query_params()
        assert params["selectedFields"] == "geneProductId,goId,evidenceCode"


class TestAnnotationStats:
    """Tests for annotation/stats endpoint."""

    def test_stats_endpoint(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="stats",
            goId="GO:0006915"
        )
        assert model.build_path() == "stats"


# =============================================================================
# Gene Product Endpoint Tests
# =============================================================================

class TestGeneProductSearch:
    """Tests for geneproduct/search endpoint."""

    def test_geneproduct_search_requires_query(self):
        with pytest.raises(ValidationError) as exc_info:
            QuickGOModel(category="geneproduct", endpoint="search")
        assert "query" in str(exc_info.value)

    def test_geneproduct_search_with_query(self):
        model = QuickGOModel(
            category="geneproduct",
            endpoint="search",
            query="TP53"
        )
        assert model.query == "TP53"
        assert model.build_path() == "search"

    def test_geneproduct_search_with_taxon(self):
        model = QuickGOModel(
            category="geneproduct",
            endpoint="search",
            query="TP53",
            taxonId=9606
        )
        params = model.build_query_params()
        assert params["query"] == "TP53"
        assert params["taxonId"] == 9606

    def test_geneproduct_search_with_type(self):
        model = QuickGOModel(
            category="geneproduct",
            endpoint="search",
            query="TP53",
            geneProductType=GeneProductType.protein
        )
        params = model.build_query_params()
        assert params["geneProductType"] == "protein"


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidation:
    """Tests for model validation."""

    def test_invalid_limit_too_high(self):
        with pytest.raises(ValidationError) as exc_info:
            QuickGOModel(
                category="ontology",
                endpoint="search",
                query="test",
                limit=20000
            )
        assert "limit" in str(exc_info.value)

    def test_invalid_limit_too_low(self):
        with pytest.raises(ValidationError) as exc_info:
            QuickGOModel(
                category="ontology",
                endpoint="search",
                query="test",
                limit=0
            )
        assert "limit" in str(exc_info.value)

    def test_valid_limit(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="search",
            query="test",
            limit=500
        )
        assert model.limit == 500

    def test_ids_converted_to_list(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}",
            ids="GO:0008150"
        )
        assert model.ids == ["GO:0008150"]

    def test_go_id_converted_to_list(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0008150"
        )
        assert model.goId == ["GO:0008150"]


# =============================================================================
# Specialized Model Tests
# =============================================================================

class TestOntologySearchModel:
    """Tests for OntologySearchModel."""

    def test_valid_search(self):
        model = OntologySearchModel(query="apoptosis")
        assert model.query == "apoptosis"

    def test_empty_query_raises_error(self):
        with pytest.raises(ValidationError):
            OntologySearchModel(query="")

    def test_whitespace_query_raises_error(self):
        with pytest.raises(ValidationError):
            OntologySearchModel(query="   ")


class TestOntologyTermsModel:
    """Tests for OntologyTermsModel."""

    def test_valid_go_id(self):
        model = OntologyTermsModel(ids=["GO:0008150"])
        assert model.ids == ["GO:0008150"]

    def test_valid_eco_id(self):
        model = OntologyTermsModel(ids=["ECO:0000001"], ontology="eco")
        assert model.ids == ["ECO:0000001"]

    def test_invalid_id_format(self):
        with pytest.raises(ValidationError) as exc_info:
            OntologyTermsModel(ids=["INVALID:001"])
        assert "Must start with GO: or ECO:" in str(exc_info.value)


class TestOntologyAncestorsDescendantsModel:
    """Tests for OntologyAncestorsDescendantsModel."""

    def test_default_relations(self):
        model = OntologyAncestorsDescendantsModel(ids=["GO:0008150"])
        assert GORelation.is_a in model.relations
        assert GORelation.part_of in model.relations


class TestAnnotationSearchModel:
    """Tests for AnnotationSearchModel."""

    def test_valid_annotation_search(self):
        model = AnnotationSearchModel(goId=["GO:0008150"], taxonId=9606)
        assert model.goId == ["GO:0008150"]
        assert model.taxonId == 9606

    def test_multiple_taxon_ids(self):
        model = AnnotationSearchModel(goId=["GO:0008150"], taxonId=[9606, 10090])
        assert model.taxonId == [9606, 10090]


class TestGeneProductSearchModel:
    """Tests for GeneProductSearchModel."""

    def test_valid_search(self):
        model = GeneProductSearchModel(query="TP53")
        assert model.query == "TP53"

    def test_empty_query_raises_error(self):
        with pytest.raises(ValidationError):
            GeneProductSearchModel(query="")


# =============================================================================
# Build Path Tests
# =============================================================================

class TestBuildPath:
    """Tests for build_path method."""

    def test_ontology_search_path(self):
        model = QuickGOModel(category="ontology", endpoint="search", query="test")
        assert model.build_path() == "go/search"

    def test_ontology_terms_path(self):
        model = QuickGOModel(category="ontology", endpoint="terms")
        assert model.build_path() == "go/terms"

    def test_ontology_terms_by_id_path(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}",
            ids=["GO:0008150", "GO:0003674"]
        )
        assert model.build_path() == "go/terms/GO:0008150,GO:0003674"

    def test_eco_ontology_path(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}",
            ontology="eco",
            ids=["ECO:0000001"]
        )
        assert model.build_path() == "eco/terms/ECO:0000001"

    def test_annotation_search_path(self):
        model = QuickGOModel(category="annotation", endpoint="search", goId="GO:0008150")
        assert model.build_path() == "search"

    def test_geneproduct_search_path(self):
        model = QuickGOModel(category="geneproduct", endpoint="search", query="TP53")
        assert model.build_path() == "search"


# =============================================================================
# Build Query Params Tests
# =============================================================================

class TestBuildQueryParams:
    """Tests for build_query_params method."""

    def test_empty_params(self):
        model = QuickGOModel(category="ontology", endpoint="about")
        params = model.build_query_params()
        assert params == {}

    def test_pagination_params(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="search",
            query="test",
            limit=50,
            page=3
        )
        params = model.build_query_params()
        assert params["limit"] == 50
        assert params["page"] == 3

    def test_list_params_joined(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId=["GO:0008150", "GO:0003674"],
            taxonId=[9606, 10090]
        )
        params = model.build_query_params()
        assert params["goId"] == "GO:0008150,GO:0003674"
        assert params["taxonId"] == "9606,10090"

    def test_enum_params_converted(self):
        model = QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0008150",
            aspect=GOAspect.molecular_function,
            goEvidence=GOEvidence.IDA
        )
        params = model.build_query_params()
        assert params["aspect"] == "molecular_function"
        assert params["goEvidence"] == "IDA"

    def test_relations_joined(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/ancestors",
            ids=["GO:0008150"],
            relations=[GORelation.is_a, GORelation.part_of, GORelation.regulates]
        )
        params = model.build_query_params()
        assert "is_a" in params["relations"]
        assert "part_of" in params["relations"]
        assert "regulates" in params["relations"]

    def test_chart_options(self):
        model = QuickGOModel(
            category="ontology",
            endpoint="terms/{ids}/chart",
            ids=["GO:0008150"],
            showKey=False,
            showIds=True,
            showChildren=True,
            termBoxWidth=200,
            fontSize=10
        )
        params = model.build_query_params()
        assert params["showKey"] is False
        assert params["showIds"] is True
        assert params["showChildren"] is True
        assert params["termBoxWidth"] == 200
        assert params["fontSize"] == 10
