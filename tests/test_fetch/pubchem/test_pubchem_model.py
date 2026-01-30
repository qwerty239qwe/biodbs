"""Tests for PubChem data models (PUG REST and PUG View)."""

import pytest
from biodbs.data.PubChem._data_model import (
    PUGRestModel, PUGRestDomain, PUGRestNamespace, PUGRestOperation, PUGRestOutput,
    PUGViewModel, PUGViewRecordType, PUGViewOutput, PUGViewHeading,
    PUGREST_DOMAIN_NAMESPACES, PUGREST_DOMAIN_OPERATIONS, COMPOUND_PROPERTIES,
)
from pydantic import ValidationError


# =============================================================================
# PUG REST Model Tests
# =============================================================================

class TestPUGRestModel:
    """Tests for PUGRestModel validation and path building."""

    def test_basic_compound_cid_lookup(self):
        """Test basic compound lookup by CID."""
        model = PUGRestModel(
            domain="compound",
            namespace="cid",
            identifiers=[2244],
            output="JSON"
        )
        assert model.build_path() == "compound/cid/2244/JSON"

    def test_multiple_cids(self):
        """Test multiple CIDs in one request."""
        model = PUGRestModel(
            domain="compound",
            namespace="cid",
            identifiers=[2244, 3672, 5988],
            output="JSON"
        )
        assert model.build_path() == "compound/cid/2244,3672,5988/JSON"

    def test_compound_name_lookup(self):
        """Test compound lookup by name."""
        model = PUGRestModel(
            domain="compound",
            namespace="name",
            identifiers="aspirin",
            output="JSON"
        )
        assert model.build_path() == "compound/name/aspirin/JSON"

    def test_compound_smiles_lookup(self):
        """Test compound lookup by SMILES."""
        model = PUGRestModel(
            domain="compound",
            namespace="smiles",
            identifiers="CC(=O)OC1=CC=CC=C1C(=O)O",
            output="JSON"
        )
        assert "compound/smiles/" in model.build_path()

    def test_compound_inchikey_lookup(self):
        """Test compound lookup by InChIKey."""
        model = PUGRestModel(
            domain="compound",
            namespace="inchikey",
            identifiers="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
            output="JSON"
        )
        assert "compound/inchikey/" in model.build_path()

    def test_compound_formula_lookup(self):
        """Test compound lookup by formula."""
        model = PUGRestModel(
            domain="compound",
            namespace="formula",
            identifiers="C9H8O4",
            output="JSON"
        )
        assert model.build_path() == "compound/formula/C9H8O4/JSON"

    def test_property_operation(self):
        """Test property operation path building."""
        model = PUGRestModel(
            domain="compound",
            namespace="cid",
            identifiers=[2244],
            operation="property",
            properties=["MolecularFormula", "MolecularWeight"],
            output="JSON"
        )
        path = model.build_path()
        assert "property/MolecularFormula,MolecularWeight" in path

    def test_synonyms_operation(self):
        """Test synonyms operation."""
        model = PUGRestModel(
            domain="compound",
            namespace="cid",
            identifiers=[2244],
            operation="synonyms",
            output="JSON"
        )
        assert model.build_path() == "compound/cid/2244/synonyms/JSON"

    def test_sids_operation(self):
        """Test SIDs operation for compound."""
        model = PUGRestModel(
            domain="compound",
            namespace="cid",
            identifiers=[2244],
            operation="sids",
            output="JSON"
        )
        assert model.build_path() == "compound/cid/2244/sids/JSON"

    def test_cids_operation(self):
        """Test CIDs operation."""
        model = PUGRestModel(
            domain="compound",
            namespace="name",
            identifiers="aspirin",
            operation="cids",
            output="JSON"
        )
        assert model.build_path() == "compound/name/aspirin/cids/JSON"

    def test_aids_operation(self):
        """Test AIDs operation for compound."""
        model = PUGRestModel(
            domain="compound",
            namespace="cid",
            identifiers=[2244],
            operation="aids",
            output="JSON"
        )
        assert model.build_path() == "compound/cid/2244/aids/JSON"

    def test_description_operation(self):
        """Test description operation."""
        model = PUGRestModel(
            domain="compound",
            namespace="cid",
            identifiers=[2244],
            operation="description",
            output="JSON"
        )
        assert model.build_path() == "compound/cid/2244/description/JSON"

    def test_substance_lookup(self):
        """Test substance lookup by SID."""
        model = PUGRestModel(
            domain="substance",
            namespace="sid",
            identifiers=[12345],
            output="JSON"
        )
        assert model.build_path() == "substance/sid/12345/JSON"

    def test_assay_lookup(self):
        """Test assay lookup by AID."""
        model = PUGRestModel(
            domain="assay",
            namespace="aid",
            identifiers=[1000],
            output="JSON"
        )
        assert model.build_path() == "assay/aid/1000/JSON"

    def test_gene_lookup(self):
        """Test gene lookup by geneid."""
        model = PUGRestModel(
            domain="gene",
            namespace="geneid",
            identifiers=[7157],
            output="JSON"
        )
        assert model.build_path() == "gene/geneid/7157/JSON"

    def test_protein_lookup(self):
        """Test protein lookup by accession."""
        model = PUGRestModel(
            domain="protein",
            namespace="accession",
            identifiers="P04637",
            output="JSON"
        )
        assert model.build_path() == "protein/accession/P04637/JSON"

    def test_similarity_search(self):
        """Test similarity search path building."""
        model = PUGRestModel(
            domain="compound",
            namespace="fastsimilarity_2d",
            identifiers="CCCC",
            search_type="smiles",
            operation="cids",
            threshold=90,
            output="JSON"
        )
        path = model.build_path()
        assert "fastsimilarity_2d/smiles/CCCC/cids" in path
        params = model.build_query_params()
        assert params["Threshold"] == 90

    def test_substructure_search(self):
        """Test substructure search path building."""
        model = PUGRestModel(
            domain="compound",
            namespace="fastsubstructure",
            identifiers="c1ccccc1",
            search_type="smiles",
            operation="cids",
            output="JSON"
        )
        path = model.build_path()
        assert "fastsubstructure/smiles" in path

    def test_superstructure_search(self):
        """Test superstructure search path building."""
        model = PUGRestModel(
            domain="compound",
            namespace="fastsuperstructure",
            identifiers="c1ccccc1",
            search_type="smiles",
            output="JSON"
        )
        path = model.build_path()
        assert "fastsuperstructure/smiles" in path

    def test_identity_search(self):
        """Test identity search path building."""
        model = PUGRestModel(
            domain="compound",
            namespace="fastidentity",
            identifiers="CC(=O)OC1=CC=CC=C1C(=O)O",
            search_type="smiles",
            output="JSON"
        )
        path = model.build_path()
        assert "fastidentity/smiles" in path

    def test_output_formats(self):
        """Test different output formats."""
        for fmt in ["JSON", "XML", "CSV", "SDF", "PNG"]:
            model = PUGRestModel(
                domain="compound",
                namespace="cid",
                identifiers=[2244],
                output=fmt
            )
            assert model.build_path().endswith(fmt)

    def test_invalid_namespace_for_domain(self):
        """Test invalid namespace raises error."""
        with pytest.raises(ValidationError):
            PUGRestModel(
                domain="substance",
                namespace="smiles",  # smiles not valid for substance
                identifiers="CCCC",
            )

    def test_invalid_operation_for_domain(self):
        """Test invalid operation raises error."""
        with pytest.raises(ValidationError):
            PUGRestModel(
                domain="gene",
                namespace="geneid",
                identifiers=[1234],
                operation="synonyms",  # synonyms not valid for gene
            )

    def test_property_operation_requires_properties(self):
        """Test property operation requires properties list."""
        with pytest.raises(ValidationError):
            PUGRestModel(
                domain="compound",
                namespace="cid",
                identifiers=[2244],
                operation="property",
                # missing properties
            )

    def test_invalid_property(self):
        """Test invalid property name raises error."""
        with pytest.raises(ValidationError):
            PUGRestModel(
                domain="compound",
                namespace="cid",
                identifiers=[2244],
                operation="property",
                properties=["InvalidProperty"],
            )

    def test_similarity_threshold_bounds(self):
        """Test similarity threshold validation."""
        with pytest.raises(ValidationError):
            PUGRestModel(
                domain="compound",
                namespace="fastsimilarity_2d",
                identifiers="CCCC",
                threshold=150,  # Invalid: > 100
            )

    def test_similarity_threshold_negative(self):
        """Test negative threshold raises error."""
        with pytest.raises(ValidationError):
            PUGRestModel(
                domain="compound",
                namespace="fastsimilarity_2d",
                identifiers="CCCC",
                threshold=-10,
            )

    def test_max_records_param(self):
        """Test max_records query parameter."""
        model = PUGRestModel(
            domain="compound",
            namespace="fastsimilarity_2d",
            identifiers="CCCC",
            search_type="smiles",
            max_records=50,
        )
        params = model.build_query_params()
        assert params["MaxRecords"] == 50

    def test_valid_threshold_boundary(self):
        """Test valid threshold at boundaries."""
        model_0 = PUGRestModel(
            domain="compound",
            namespace="fastsimilarity_2d",
            identifiers="CCCC",
            threshold=0,
        )
        assert model_0.threshold == 0

        model_100 = PUGRestModel(
            domain="compound",
            namespace="fastsimilarity_2d",
            identifiers="CCCC",
            threshold=100,
        )
        assert model_100.threshold == 100


# =============================================================================
# PUG View Model Tests
# =============================================================================

class TestPUGViewModel:
    """Tests for PUGViewModel validation and path building."""

    def test_compound_view(self):
        """Test compound view path."""
        model = PUGViewModel(
            record_type="compound",
            record_id=2244,
            output="JSON"
        )
        assert model.build_path() == "data/compound/2244/JSON"

    def test_substance_view(self):
        """Test substance view path."""
        model = PUGViewModel(
            record_type="substance",
            record_id=12345,
            output="JSON"
        )
        assert model.build_path() == "data/substance/12345/JSON"

    def test_assay_view(self):
        """Test assay view path."""
        model = PUGViewModel(
            record_type="assay",
            record_id=1000,
            output="JSON"
        )
        assert model.build_path() == "data/assay/1000/JSON"

    def test_gene_view(self):
        """Test gene view path."""
        model = PUGViewModel(
            record_type="gene",
            record_id=7157,
            output="JSON"
        )
        assert model.build_path() == "data/gene/7157/JSON"

    def test_protein_view(self):
        """Test protein view path."""
        model = PUGViewModel(
            record_type="protein",
            record_id="P04637",
            output="JSON"
        )
        assert model.build_path() == "data/protein/P04637/JSON"

    def test_heading_filter(self):
        """Test heading query parameter."""
        model = PUGViewModel(
            record_type="compound",
            record_id=2244,
            heading="Safety and Hazards",
            output="JSON"
        )
        params = model.build_query_params()
        assert params["heading"] == "Safety and Hazards"

    def test_xml_output(self):
        """Test XML output format."""
        model = PUGViewModel(
            record_type="compound",
            record_id=2244,
            output="XML"
        )
        assert model.build_path() == "data/compound/2244/XML"

    def test_no_heading(self):
        """Test no heading filter returns empty params."""
        model = PUGViewModel(
            record_type="compound",
            record_id=2244,
            output="JSON"
        )
        params = model.build_query_params()
        assert "heading" not in params

    def test_default_output_is_json(self):
        """Test default output format is JSON."""
        model = PUGViewModel(
            record_type="compound",
            record_id=2244,
        )
        assert model.output == PUGViewOutput.JSON


# =============================================================================
# Domain/Namespace/Operation Mapping Tests
# =============================================================================

class TestDomainMappings:
    """Tests for domain-namespace-operation mappings."""

    def test_compound_has_expected_namespaces(self):
        """Test compound domain has expected namespaces."""
        compound_ns = PUGREST_DOMAIN_NAMESPACES[PUGRestDomain.compound]
        assert PUGRestNamespace.cid in compound_ns
        assert PUGRestNamespace.name in compound_ns
        assert PUGRestNamespace.smiles in compound_ns
        assert PUGRestNamespace.inchikey in compound_ns

    def test_substance_has_expected_namespaces(self):
        """Test substance domain has expected namespaces."""
        substance_ns = PUGREST_DOMAIN_NAMESPACES[PUGRestDomain.substance]
        assert PUGRestNamespace.sid in substance_ns
        assert PUGRestNamespace.name in substance_ns

    def test_assay_has_expected_namespaces(self):
        """Test assay domain has expected namespaces."""
        assay_ns = PUGREST_DOMAIN_NAMESPACES[PUGRestDomain.assay]
        assert PUGRestNamespace.aid in assay_ns

    def test_compound_has_expected_operations(self):
        """Test compound domain has expected operations."""
        compound_ops = PUGREST_DOMAIN_OPERATIONS[PUGRestDomain.compound]
        assert PUGRestOperation.property in compound_ops
        assert PUGRestOperation.synonyms in compound_ops
        assert PUGRestOperation.cids in compound_ops
        assert PUGRestOperation.sids in compound_ops

    def test_compound_properties_list(self):
        """Test compound properties list contains expected properties."""
        assert "MolecularFormula" in COMPOUND_PROPERTIES
        assert "MolecularWeight" in COMPOUND_PROPERTIES
        assert "CanonicalSMILES" in COMPOUND_PROPERTIES
        assert "InChI" in COMPOUND_PROPERTIES
        assert "XLogP" in COMPOUND_PROPERTIES
