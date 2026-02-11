"""Comprehensive tests for ChEMBL data model validation and path/query building."""

import pytest
from pydantic import ValidationError

from biodbs.data.ChEMBL._data_model import (
    ChEMBLModel,
    ChEMBLResource,
    ChEMBLFormat,
    RESOURCE_FILTER_FIELDS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make(**kwargs):
    """Shortcut to build a ChEMBLModel with sensible defaults.

    Supplies ``resource="molecule"`` unless the caller overrides it.
    """
    kwargs.setdefault("resource", ChEMBLResource.molecule)
    return ChEMBLModel(**kwargs)


# ===================================================================
# 1. TestValidateChEMBLId
# ===================================================================

class TestValidateChEMBLId:
    """Tests for the chembl_id field validator."""

    def test_valid_id_uppercase(self):
        """A properly-formatted CHEMBL ID passes validation."""
        model = _make(chembl_id="CHEMBL25")
        assert model.chembl_id == "CHEMBL25"

    def test_lowercase_id_gets_uppercased(self):
        """A lowercase chembl id is automatically uppercased."""
        model = _make(chembl_id="chembl25")
        assert model.chembl_id == "CHEMBL25"

    def test_mixed_case_id_gets_uppercased(self):
        """Mixed-case input like 'Chembl25' is uppercased."""
        model = _make(chembl_id="Chembl25")
        assert model.chembl_id == "CHEMBL25"

    def test_invalid_id_raises(self):
        """An ID that does not start with 'CHEMBL' raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid ChEMBL ID format"):
            _make(chembl_id="XYZ123")

    def test_none_is_allowed(self):
        """chembl_id is optional; None should be accepted."""
        model = _make(chembl_id=None)
        assert model.chembl_id is None

    def test_omitted_defaults_to_none(self):
        """When chembl_id is not provided it defaults to None."""
        model = _make()
        assert model.chembl_id is None


# ===================================================================
# 2. TestValidateLimit
# ===================================================================

class TestValidateLimit:
    """Tests for the limit model validator."""

    def test_valid_limit(self):
        model = _make(limit=100)
        assert model.limit == 100

    def test_limit_zero_raises(self):
        with pytest.raises(ValidationError, match="limit must be between 1 and 1000"):
            _make(limit=0)

    def test_limit_negative_raises(self):
        with pytest.raises(ValidationError, match="limit must be between 1 and 1000"):
            _make(limit=-5)

    def test_limit_1001_raises(self):
        with pytest.raises(ValidationError, match="limit must be between 1 and 1000"):
            _make(limit=1001)

    def test_limit_none_passes(self):
        model = _make(limit=None)
        assert model.limit is None

    def test_limit_lower_boundary(self):
        model = _make(limit=1)
        assert model.limit == 1

    def test_limit_upper_boundary(self):
        model = _make(limit=1000)
        assert model.limit == 1000


# ===================================================================
# 3. TestValidateOffset
# ===================================================================

class TestValidateOffset:
    """Tests for the offset model validator."""

    def test_valid_offset(self):
        model = _make(offset=10)
        assert model.offset == 10

    def test_negative_offset_raises(self):
        with pytest.raises(ValidationError, match="offset must be >= 0"):
            _make(offset=-1)

    def test_offset_zero_passes(self):
        model = _make(offset=0)
        assert model.offset == 0

    def test_offset_none_passes(self):
        model = _make(offset=None)
        assert model.offset is None

    def test_large_offset_passes(self):
        model = _make(offset=999999)
        assert model.offset == 999999


# ===================================================================
# 4. TestValidateOperationMode
# ===================================================================

class TestValidateOperationMode:
    """Only one of chembl_id, search_query, or smiles may be specified."""

    def test_chembl_id_alone_passes(self):
        model = _make(chembl_id="CHEMBL25")
        assert model.chembl_id == "CHEMBL25"

    def test_search_query_alone_passes(self):
        model = _make(search_query="aspirin")
        assert model.search_query == "aspirin"

    def test_smiles_alone_passes(self):
        """smiles alone with a matching resource (similarity) should pass."""
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="c1ccccc1",
            similarity_threshold=70,
        )
        assert model.smiles == "c1ccccc1"

    def test_chembl_id_and_search_query_raises(self):
        with pytest.raises(ValidationError, match="Only one of"):
            _make(chembl_id="CHEMBL25", search_query="aspirin")

    def test_chembl_id_and_smiles_raises(self):
        with pytest.raises(ValidationError, match="Only one of"):
            _make(chembl_id="CHEMBL25", smiles="c1ccccc1")

    def test_search_query_and_smiles_raises(self):
        with pytest.raises(ValidationError, match="Only one of"):
            _make(search_query="aspirin", smiles="c1ccccc1")

    def test_all_three_raises(self):
        with pytest.raises(ValidationError, match="Only one of"):
            _make(chembl_id="CHEMBL25", search_query="aspirin", smiles="c1ccccc1")

    def test_none_of_them_passes(self):
        """No operation mode specified is valid (plain resource listing)."""
        model = _make()
        assert model.chembl_id is None
        assert model.search_query is None
        assert model.smiles is None


# ===================================================================
# 5. TestValidateSimilarityParams
# ===================================================================

class TestValidateSimilarityParams:
    """Tests for similarity resource validation."""

    def test_similarity_with_smiles_passes(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="c1ccccc1",
            similarity_threshold=70,
        )
        assert model.smiles == "c1ccccc1"
        assert model.similarity_threshold == 70

    def test_similarity_without_smiles_raises(self):
        with pytest.raises(ValidationError, match="smiles is required for similarity"):
            ChEMBLModel(resource=ChEMBLResource.similarity)

    def test_threshold_lower_boundary_40_passes(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="c1ccccc1",
            similarity_threshold=40,
        )
        assert model.similarity_threshold == 40

    def test_threshold_upper_boundary_100_passes(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="c1ccccc1",
            similarity_threshold=100,
        )
        assert model.similarity_threshold == 100

    def test_threshold_39_raises(self):
        with pytest.raises(ValidationError, match="similarity_threshold must be between 40 and 100"):
            ChEMBLModel(
                resource=ChEMBLResource.similarity,
                smiles="c1ccccc1",
                similarity_threshold=39,
            )

    def test_threshold_101_raises(self):
        with pytest.raises(ValidationError, match="similarity_threshold must be between 40 and 100"):
            ChEMBLModel(
                resource=ChEMBLResource.similarity,
                smiles="c1ccccc1",
                similarity_threshold=101,
            )

    def test_threshold_none_defaults_allowed(self):
        """When similarity_threshold is None the model is still valid."""
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="c1ccccc1",
        )
        assert model.similarity_threshold is None

    def test_threshold_ignored_for_non_similarity_resource(self):
        """similarity_threshold validation only fires for similarity resource."""
        model = _make(similarity_threshold=200)
        # No error because resource is molecule, not similarity
        assert model.similarity_threshold == 200


# ===================================================================
# 6. TestValidateSubstructureParams
# ===================================================================

class TestValidateSubstructureParams:
    """Tests for substructure resource validation."""

    def test_substructure_with_smiles_passes(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.substructure,
            smiles="c1ccccc1",
        )
        assert model.smiles == "c1ccccc1"

    def test_substructure_without_smiles_raises(self):
        with pytest.raises(ValidationError, match="smiles is required for substructure"):
            ChEMBLModel(resource=ChEMBLResource.substructure)


# ===================================================================
# 7. TestValidateFilters
# ===================================================================

class TestValidateFilters:
    """Tests for filter field validation against RESOURCE_FILTER_FIELDS."""

    def test_valid_filter_for_activity(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.activity,
            filters={"target_chembl_id": "CHEMBL240"},
        )
        assert model.filters == {"target_chembl_id": "CHEMBL240"}

    def test_invalid_filter_field_raises(self):
        with pytest.raises(ValidationError, match="Invalid filter field"):
            ChEMBLModel(
                resource=ChEMBLResource.activity,
                filters={"nonexistent_field": "value"},
            )

    def test_nested_filter_with_double_underscore_passes(self):
        """pchembl_value__gte should be accepted because base field pchembl_value is valid."""
        model = ChEMBLModel(
            resource=ChEMBLResource.activity,
            filters={"pchembl_value__gte": 5},
        )
        assert model.filters == {"pchembl_value__gte": 5}

    def test_nested_filter_invalid_base_raises(self):
        """If the base field (before __) is invalid, it should still raise."""
        with pytest.raises(ValidationError, match="Invalid filter field"):
            ChEMBLModel(
                resource=ChEMBLResource.activity,
                filters={"bad_field__gte": 5},
            )

    def test_no_validation_for_unknown_resource(self):
        """Resources not in RESOURCE_FILTER_FIELDS accept any filter."""
        model = ChEMBLModel(
            resource=ChEMBLResource.status,
            filters={"anything_goes": True},
        )
        assert model.filters == {"anything_goes": True}

    def test_multiple_valid_filters_pass(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.activity,
            filters={
                "target_chembl_id": "CHEMBL240",
                "pchembl_value__gte": 5,
                "standard_type": "IC50",
            },
        )
        assert len(model.filters) == 3

    def test_one_invalid_among_many_raises(self):
        with pytest.raises(ValidationError, match="Invalid filter field"):
            ChEMBLModel(
                resource=ChEMBLResource.activity,
                filters={
                    "target_chembl_id": "CHEMBL240",
                    "not_a_real_field": 42,
                },
            )

    def test_molecule_valid_filter(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.molecule,
            filters={"max_phase": 4},
        )
        assert model.filters == {"max_phase": 4}

    def test_empty_filters_passes(self):
        """An empty dict should not trigger validation issues."""
        model = _make(filters={})
        # Empty dict is falsy, so the validator short-circuits
        assert model.filters == {}

    def test_none_filters_passes(self):
        model = _make(filters=None)
        assert model.filters is None


# ===================================================================
# 8. TestBuildPath
# ===================================================================

class TestBuildPath:
    """Tests for build_path() URL path construction."""

    def test_path_with_chembl_id(self):
        model = _make(chembl_id="CHEMBL25")
        assert model.build_path() == "molecule/CHEMBL25"

    def test_path_with_search_query(self):
        model = _make(search_query="aspirin")
        assert model.build_path() == "molecule/search"

    def test_path_similarity_default_threshold(self):
        """Similarity with no explicit threshold uses 70."""
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="c1ccccc1",
        )
        assert model.build_path() == "similarity/c1ccccc1/70"

    def test_path_similarity_custom_threshold(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="c1ccccc1",
            similarity_threshold=80,
        )
        assert model.build_path() == "similarity/c1ccccc1/80"

    def test_path_substructure(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.substructure,
            smiles="c1ccccc1",
        )
        assert model.build_path() == "substructure/c1ccccc1"

    def test_path_plain_resource(self):
        """No operation mode gives just the resource name."""
        model = _make()
        assert model.build_path() == "molecule"

    def test_path_different_resource(self):
        model = ChEMBLModel(resource=ChEMBLResource.target, chembl_id="CHEMBL240")
        assert model.build_path() == "target/CHEMBL240"

    def test_path_activity_search(self):
        model = ChEMBLModel(resource=ChEMBLResource.activity, search_query="kinase")
        assert model.build_path() == "activity/search"

    def test_path_plain_activity(self):
        model = ChEMBLModel(resource=ChEMBLResource.activity)
        assert model.build_path() == "activity"

    def test_path_similarity_boundary_threshold_40(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="CCO",
            similarity_threshold=40,
        )
        assert model.build_path() == "similarity/CCO/40"

    def test_path_similarity_boundary_threshold_100(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.similarity,
            smiles="CCO",
            similarity_threshold=100,
        )
        assert model.build_path() == "similarity/CCO/100"


# ===================================================================
# 9. TestBuildQueryParams
# ===================================================================

class TestBuildQueryParams:
    """Tests for build_query_params() query-string construction."""

    def test_search_query_adds_q_param(self):
        model = _make(search_query="aspirin")
        params = model.build_query_params()
        assert params["q"] == "aspirin"

    def test_filters_are_added(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.activity,
            filters={"target_chembl_id": "CHEMBL240", "pchembl_value__gte": 5},
        )
        params = model.build_query_params()
        assert params["target_chembl_id"] == "CHEMBL240"
        assert params["pchembl_value__gte"] == 5

    def test_limit_is_added(self):
        model = _make(limit=50)
        params = model.build_query_params()
        assert params["limit"] == 50

    def test_offset_is_added(self):
        model = _make(offset=20)
        params = model.build_query_params()
        assert params["offset"] == 20

    def test_format_defaults_to_json(self):
        model = _make()
        params = model.build_query_params()
        assert params["format"] == "json"

    def test_format_xml(self):
        model = _make(format=ChEMBLFormat.xml)
        params = model.build_query_params()
        assert params["format"] == "xml"

    def test_no_q_when_no_search_query(self):
        model = _make()
        params = model.build_query_params()
        assert "q" not in params

    def test_no_limit_when_none(self):
        model = _make()
        params = model.build_query_params()
        assert "limit" not in params

    def test_no_offset_when_none(self):
        model = _make()
        params = model.build_query_params()
        assert "offset" not in params

    def test_all_params_combined(self):
        model = ChEMBLModel(
            resource=ChEMBLResource.activity,
            search_query="kinase",
            limit=100,
            offset=200,
            format=ChEMBLFormat.xml,
        )
        params = model.build_query_params()
        assert params == {
            "q": "kinase",
            "limit": 100,
            "offset": 200,
            "format": "xml",
        }

    def test_filters_and_search_combined(self):
        """Filters and search query can coexist in query params
        even though operation-mode validation is separate."""
        # Note: search_query + filters is allowed (filters are on the query
        # string, separate from the operation mode).
        model = ChEMBLModel(
            resource=ChEMBLResource.molecule,
            search_query="aspirin",
            filters={"max_phase": 4},
        )
        params = model.build_query_params()
        assert params["q"] == "aspirin"
        assert params["max_phase"] == 4


# ===================================================================
# 10. TestResourceFilterFields (supplementary)
# ===================================================================

class TestResourceFilterFields:
    """Basic sanity checks on the RESOURCE_FILTER_FIELDS mapping."""

    def test_activity_has_target_chembl_id(self):
        assert "target_chembl_id" in RESOURCE_FILTER_FIELDS[ChEMBLResource.activity]

    def test_molecule_has_max_phase(self):
        assert "max_phase" in RESOURCE_FILTER_FIELDS[ChEMBLResource.molecule]

    def test_target_has_organism(self):
        assert "organism" in RESOURCE_FILTER_FIELDS[ChEMBLResource.target]

    def test_status_not_in_mapping(self):
        assert ChEMBLResource.status not in RESOURCE_FILTER_FIELDS

    def test_similarity_not_in_mapping(self):
        assert ChEMBLResource.similarity not in RESOURCE_FILTER_FIELDS


# ===================================================================
# 11. TestEnums (supplementary)
# ===================================================================

class TestEnums:
    """Verify enum members exist and have expected values."""

    def test_chembl_resource_molecule(self):
        assert ChEMBLResource.molecule.value == "molecule"

    def test_chembl_resource_similarity(self):
        assert ChEMBLResource.similarity.value == "similarity"

    def test_chembl_resource_substructure(self):
        assert ChEMBLResource.substructure.value == "substructure"

    def test_chembl_format_json(self):
        assert ChEMBLFormat.json.value == "json"

    def test_chembl_format_xml(self):
        assert ChEMBLFormat.xml.value == "xml"

    def test_invalid_resource_raises(self):
        with pytest.raises(ValidationError):
            ChEMBLModel(resource="not_a_resource")

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError):
            _make(format="csv")
