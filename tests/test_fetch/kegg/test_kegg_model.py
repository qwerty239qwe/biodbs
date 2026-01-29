"""Tests for KEGGModel data validation."""
import pytest
from pydantic import ValidationError

from biodbs.data.KEGG._data_model import (
    KEGGModel,
    KEGGOperation,
    KEGGDatabase,
    KEGGOutsideDatabase,
    KEGGOrganism,
    KEGGGetOption,
    KEGGCompoundFindOption,
    KEGGDrugFindOption,
    KEGGBriteOption,
    KEGGLinkRDFOption,
    VALID_DATABASES_BY_OPERATION,
    SEARCH_FIELDS_BY_DATABASE,
)


# =============================================================================
# Enum Tests
# =============================================================================

class TestKEGGOperationEnum:
    """Tests for KEGGOperation enum."""

    def test_all_operations_defined(self):
        operations = [op.value for op in KEGGOperation]
        assert "info" in operations
        assert "list" in operations
        assert "find" in operations
        assert "get" in operations
        assert "conv" in operations
        assert "link" in operations
        assert "ddi" in operations

    def test_operation_count(self):
        assert len(KEGGOperation) == 7


class TestKEGGDatabaseEnum:
    """Tests for KEGGDatabase enum."""

    def test_common_databases_defined(self):
        databases = [db.value for db in KEGGDatabase]
        assert "pathway" in databases
        assert "compound" in databases
        assert "drug" in databases
        assert "disease" in databases
        assert "enzyme" in databases
        assert "reaction" in databases
        assert "ko" in databases
        assert "genome" in databases

    def test_database_count(self):
        assert len(KEGGDatabase) == 16


class TestKEGGOutsideDatabaseEnum:
    """Tests for KEGGOutsideDatabase enum."""

    def test_external_databases_defined(self):
        databases = [db.value for db in KEGGOutsideDatabase]
        assert "pubmed" in databases
        assert "ncbi-geneid" in databases
        assert "ncbi-proteinid" in databases
        assert "uniprot" in databases
        assert "pubchem" in databases
        assert "chebi" in databases


class TestKEGGGetOptionEnum:
    """Tests for KEGGGetOption enum."""

    def test_get_options_defined(self):
        options = [opt.value for opt in KEGGGetOption]
        assert "aaseq" in options
        assert "ntseq" in options
        assert "mol" in options
        assert "kcf" in options
        assert "image" in options
        assert "kgml" in options
        assert "json" in options


# =============================================================================
# INFO Operation Tests
# =============================================================================

class TestInfoOperation:
    """Tests for INFO operation validation."""

    def test_info_with_database(self):
        model = KEGGModel(operation="info", database="pathway")
        assert model.operation == "info"
        assert model.database == "pathway"

    def test_info_with_kegg_database_enum(self):
        model = KEGGModel(operation=KEGGOperation.info, database=KEGGDatabase.compound)
        assert model.operation == "info"
        assert model.database == "compound"

    def test_info_requires_database(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="info")
        assert "database" in str(exc_info.value).lower()

    def test_info_with_organism_code(self):
        model = KEGGModel(operation="info", database="hsa")
        assert model.database == "hsa"

    def test_info_with_all_valid_databases(self):
        valid_dbs = VALID_DATABASES_BY_OPERATION[KEGGOperation.info]
        for db in valid_dbs:
            model = KEGGModel(operation="info", database=db.value)
            assert model.database == db.value


# =============================================================================
# LIST Operation Tests
# =============================================================================

class TestListOperation:
    """Tests for LIST operation validation."""

    def test_list_with_database(self):
        model = KEGGModel(operation="list", database="pathway")
        assert model.operation == "list"
        assert model.database == "pathway"

    def test_list_organism_database(self):
        model = KEGGModel(operation="list", database="organism")
        assert model.database == "organism"

    def test_list_pathway_with_organism(self):
        model = KEGGModel(operation="list", database="pathway", organism="hsa")
        assert model.database == "pathway"
        assert model.organism == "hsa"

    def test_list_brite_with_option(self):
        model = KEGGModel(operation="list", database="brite", brite_option="ko")
        assert model.database == "brite"
        assert model.brite_option == "ko"

    def test_list_requires_database_or_dbentries(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="list")
        assert "database" in str(exc_info.value).lower() or "dbentries" in str(exc_info.value).lower()

    def test_list_with_dbentries(self):
        model = KEGGModel(operation="list", dbentries=["hsa:10458", "hsa:10459"])
        assert model.dbentries == ["hsa:10458", "hsa:10459"]

    def test_list_organism_option_only_for_pathway(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="list", database="compound", organism="hsa")
        assert "pathway" in str(exc_info.value).lower()

    def test_list_with_organism_code_database(self):
        model = KEGGModel(operation="list", database="hsa")
        assert model.database == "hsa"


# =============================================================================
# FIND Operation Tests
# =============================================================================

class TestFindOperation:
    """Tests for FIND operation validation."""

    def test_find_basic(self):
        model = KEGGModel(operation="find", database="genes", query="shiga toxin")
        assert model.operation == "find"
        assert model.database == "genes"
        assert model.query == "shiga toxin"

    def test_find_compound_with_formula(self):
        model = KEGGModel(
            operation="find",
            database="compound",
            query="C7H10O5",
            find_option="formula"
        )
        assert model.database == "compound"
        assert model.query == "C7H10O5"
        assert model.find_option == "formula"

    def test_find_compound_with_exact_mass(self):
        model = KEGGModel(
            operation="find",
            database="compound",
            query="174.05",
            find_option="exact_mass"
        )
        assert model.find_option == "exact_mass"

    def test_find_compound_with_mol_weight(self):
        model = KEGGModel(
            operation="find",
            database="compound",
            query="300-500",
            find_option="mol_weight"
        )
        assert model.find_option == "mol_weight"

    def test_find_drug_with_formula(self):
        model = KEGGModel(
            operation="find",
            database="drug",
            query="C9H8O4",
            find_option="formula"
        )
        assert model.database == "drug"
        assert model.find_option == "formula"

    def test_find_requires_database(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="find", query="test")
        assert "database" in str(exc_info.value).lower()

    def test_find_requires_query(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="find", database="genes")
        assert "query" in str(exc_info.value).lower()

    def test_find_invalid_compound_option(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(
                operation="find",
                database="compound",
                query="test",
                find_option="invalid_option"
            )
        assert "find_option" in str(exc_info.value).lower()

    def test_find_pathway(self):
        model = KEGGModel(operation="find", database="pathway", query="cancer")
        assert model.database == "pathway"

    def test_find_disease(self):
        model = KEGGModel(operation="find", database="disease", query="diabetes")
        assert model.database == "disease"


# =============================================================================
# GET Operation Tests
# =============================================================================

class TestGetOperation:
    """Tests for GET operation validation."""

    def test_get_single_entry(self):
        model = KEGGModel(operation="get", dbentries=["hsa:10458"])
        assert model.operation == "get"
        assert model.dbentries == ["hsa:10458"]

    def test_get_multiple_entries(self):
        model = KEGGModel(operation="get", dbentries=["hsa:10458", "ece:Z5100"])
        assert len(model.dbentries) == 2

    def test_get_with_aaseq_option(self):
        model = KEGGModel(operation="get", dbentries=["hsa:10458"], get_option="aaseq")
        assert model.get_option == "aaseq"

    def test_get_with_ntseq_option(self):
        model = KEGGModel(operation="get", dbentries=["hsa:10458"], get_option="ntseq")
        assert model.get_option == "ntseq"

    def test_get_with_image_option(self):
        model = KEGGModel(operation="get", dbentries=["C00002"], get_option="image")
        assert model.get_option == "image"

    def test_get_with_kgml_option(self):
        model = KEGGModel(operation="get", dbentries=["hsa00010"], get_option="kgml")
        assert model.get_option == "kgml"

    def test_get_with_json_option(self):
        model = KEGGModel(operation="get", dbentries=["hsa00010"], get_option="json")
        assert model.get_option == "json"

    def test_get_requires_dbentries(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="get")
        assert "dbentries" in str(exc_info.value).lower()

    def test_get_image_limited_to_one_entry(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(
                operation="get",
                dbentries=["C00001", "C00002"],
                get_option="image"
            )
        assert "1 entry" in str(exc_info.value).lower()

    def test_get_kgml_limited_to_one_entry(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(
                operation="get",
                dbentries=["hsa00010", "hsa00020"],
                get_option="kgml"
            )
        assert "1 entry" in str(exc_info.value).lower()

    def test_get_max_entries_limit(self):
        # Default max is 10
        entries = [f"hsa:{10458 + i}" for i in range(15)]
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="get", dbentries=entries)
        assert "10" in str(exc_info.value) or "entries" in str(exc_info.value).lower()

    def test_get_at_max_entries(self):
        entries = [f"hsa:{10458 + i}" for i in range(10)]
        model = KEGGModel(operation="get", dbentries=entries)
        assert len(model.dbentries) == 10

    def test_get_compound_entry(self):
        model = KEGGModel(operation="get", dbentries=["C00001"])
        assert model.dbentries == ["C00001"]

    def test_get_pathway_entry(self):
        model = KEGGModel(operation="get", dbentries=["hsa00010"])
        assert model.dbentries == ["hsa00010"]

    def test_get_drug_entry(self):
        model = KEGGModel(operation="get", dbentries=["D00001"])
        assert model.dbentries == ["D00001"]


# =============================================================================
# CONV Operation Tests
# =============================================================================

class TestConvOperation:
    """Tests for CONV operation validation."""

    def test_conv_database_to_database(self):
        model = KEGGModel(
            operation="conv",
            target_db="eco",
            source_db="ncbi-geneid"
        )
        assert model.operation == "conv"
        assert model.target_db == "eco"
        assert model.source_db == "ncbi-geneid"

    def test_conv_with_dbentries(self):
        model = KEGGModel(
            operation="conv",
            target_db="ncbi-proteinid",
            dbentries=["hsa:10458"]
        )
        assert model.target_db == "ncbi-proteinid"
        assert model.dbentries == ["hsa:10458"]

    def test_conv_kegg_to_external(self):
        model = KEGGModel(
            operation="conv",
            target_db="uniprot",
            source_db="hsa"
        )
        assert model.target_db == "uniprot"
        assert model.source_db == "hsa"

    def test_conv_external_to_kegg(self):
        model = KEGGModel(
            operation="conv",
            target_db="hsa",
            source_db="uniprot"
        )
        assert model.target_db == "hsa"

    def test_conv_compound_to_pubchem(self):
        model = KEGGModel(
            operation="conv",
            target_db="pubchem",
            source_db="compound"
        )
        assert model.target_db == "pubchem"
        assert model.source_db == "compound"

    def test_conv_requires_target_db(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="conv", source_db="hsa")
        assert "target_db" in str(exc_info.value).lower()

    def test_conv_requires_source_or_entries(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="conv", target_db="eco")
        assert "source_db" in str(exc_info.value).lower() or "dbentries" in str(exc_info.value).lower()

    def test_conv_cannot_have_both_source_and_entries(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(
                operation="conv",
                target_db="eco",
                source_db="hsa",
                dbentries=["hsa:10458"]
            )
        assert "cannot have both" in str(exc_info.value).lower()


# =============================================================================
# LINK Operation Tests
# =============================================================================

class TestLinkOperation:
    """Tests for LINK operation validation."""

    def test_link_database_to_database(self):
        model = KEGGModel(
            operation="link",
            target_db="pathway",
            source_db="hsa"
        )
        assert model.operation == "link"
        assert model.target_db == "pathway"
        assert model.source_db == "hsa"

    def test_link_with_dbentries(self):
        model = KEGGModel(
            operation="link",
            target_db="pathway",
            dbentries=["hsa:10458"]
        )
        assert model.target_db == "pathway"
        assert model.dbentries == ["hsa:10458"]

    def test_link_compound_to_reaction(self):
        model = KEGGModel(
            operation="link",
            target_db="reaction",
            source_db="compound"
        )
        assert model.target_db == "reaction"

    def test_link_enzyme_to_compound(self):
        model = KEGGModel(
            operation="link",
            target_db="compound",
            source_db="enzyme"
        )
        assert model.source_db == "enzyme"

    def test_link_with_rdf_option(self):
        model = KEGGModel(
            operation="link",
            target_db="pathway",
            source_db="hsa",
            rdf_option="turtle"
        )
        assert model.rdf_option == "turtle"

    def test_link_requires_target_db(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="link", source_db="hsa")
        assert "target_db" in str(exc_info.value).lower()

    def test_link_requires_source_or_entries(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="link", target_db="pathway")
        assert "source_db" in str(exc_info.value).lower() or "dbentries" in str(exc_info.value).lower()

    def test_link_cannot_have_both_source_and_entries(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(
                operation="link",
                target_db="pathway",
                source_db="hsa",
                dbentries=["hsa:10458"]
            )
        assert "cannot have both" in str(exc_info.value).lower()


# =============================================================================
# DDI Operation Tests
# =============================================================================

class TestDdiOperation:
    """Tests for DDI (Drug-Drug Interaction) operation validation."""

    def test_ddi_with_drug_entries(self):
        model = KEGGModel(operation="ddi", dbentries=["D00564", "D00100"])
        assert model.operation == "ddi"
        assert model.dbentries == ["D00564", "D00100"]

    def test_ddi_with_single_drug(self):
        model = KEGGModel(operation="ddi", dbentries=["D00564"])
        assert model.dbentries == ["D00564"]

    def test_ddi_with_ndc_entries(self):
        model = KEGGModel(operation="ddi", dbentries=["ndc:12345-678-90"])
        assert "ndc:" in model.dbentries[0]

    def test_ddi_with_yj_entries(self):
        model = KEGGModel(operation="ddi", dbentries=["yj:1234567"])
        assert "yj:" in model.dbentries[0]

    def test_ddi_requires_dbentries(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="ddi")
        assert "dbentries" in str(exc_info.value).lower()

    def test_ddi_invalid_entry_format(self):
        with pytest.raises(ValidationError) as exc_info:
            KEGGModel(operation="ddi", dbentries=["C00001"])  # Compound, not drug
        assert "drug" in str(exc_info.value).lower() or "D" in str(exc_info.value)

    def test_ddi_mixed_valid_entries(self):
        model = KEGGModel(operation="ddi", dbentries=["D00564", "ndc:12345-678-90"])
        assert len(model.dbentries) == 2


# =============================================================================
# Database Validation Tests
# =============================================================================

class TestDatabaseValidation:
    """Tests for database validation."""

    def test_valid_organism_code_3_letters(self):
        model = KEGGModel(operation="info", database="hsa")
        assert model.database == "hsa"

    def test_valid_organism_code_4_letters(self):
        model = KEGGModel(operation="info", database="ecok")
        assert model.database == "ecok"

    def test_valid_t_number_organism(self):
        model = KEGGModel(operation="info", database="T00001")
        assert model.database == "T00001"

    def test_special_databases(self):
        # These special database names should be valid
        for db in ["vg", "ag", "genes", "ligand", "kegg"]:
            model = KEGGModel(operation="info", database=db)
            assert model.database == db


# =============================================================================
# Entry Format Tests
# =============================================================================

class TestEntryFormatValidation:
    """Tests for database entry format validation."""

    def test_gene_entry_format(self):
        model = KEGGModel(operation="get", dbentries=["hsa:10458"])
        assert model.dbentries == ["hsa:10458"]

    def test_compound_entry_format(self):
        model = KEGGModel(operation="get", dbentries=["C00001"])
        assert model.dbentries == ["C00001"]

    def test_drug_entry_format(self):
        model = KEGGModel(operation="get", dbentries=["D00001"])
        assert model.dbentries == ["D00001"]

    def test_pathway_entry_format(self):
        model = KEGGModel(operation="get", dbentries=["hsa00010"])
        assert model.dbentries == ["hsa00010"]

    def test_ko_entry_format(self):
        model = KEGGModel(operation="get", dbentries=["K00001"])
        assert model.dbentries == ["K00001"]

    def test_reaction_entry_format(self):
        model = KEGGModel(operation="get", dbentries=["R00001"])
        assert model.dbentries == ["R00001"]

    def test_enzyme_entry_format(self):
        model = KEGGModel(operation="get", dbentries=["ec:1.1.1.1"])
        assert model.dbentries == ["ec:1.1.1.1"]

    def test_external_db_entry_format(self):
        model = KEGGModel(
            operation="conv",
            target_db="hsa",
            dbentries=["ncbi-geneid:948364"]
        )
        assert model.dbentries == ["ncbi-geneid:948364"]

    def test_mixed_entry_formats(self):
        model = KEGGModel(
            operation="get",
            dbentries=["hsa:10458", "ece:Z5100", "K00001"]
        )
        assert len(model.dbentries) == 3


# =============================================================================
# Search Field Mapping Tests
# =============================================================================

class TestSearchFieldMapping:
    """Tests for search field mappings."""

    def test_pathway_search_fields_exist(self):
        from biodbs.data.KEGG._data_model import KEGGPathwaySearchField
        fields = [f.value for f in KEGGPathwaySearchField]
        assert "entry" in fields
        assert "definition" in fields
        assert "pathway" in fields

    def test_compound_search_fields_exist(self):
        from biodbs.data.KEGG._data_model import KEGGCompoundSearchField
        fields = [f.value for f in KEGGCompoundSearchField]
        assert "formula" in fields
        assert "mass" in fields
        assert "pathway" in fields

    def test_drug_search_fields_exist(self):
        from biodbs.data.KEGG._data_model import KEGGDrugSearchField
        fields = [f.value for f in KEGGDrugSearchField]
        assert "formula" in fields
        assert "target" in fields
        assert "disease" in fields

    def test_all_databases_have_search_fields(self):
        for db in SEARCH_FIELDS_BY_DATABASE:
            assert db in KEGGDatabase
            assert SEARCH_FIELDS_BY_DATABASE[db] is not None


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dbentries_list(self):
        with pytest.raises(ValidationError):
            KEGGModel(operation="get", dbentries=[])

    def test_operation_case_sensitivity(self):
        # Operation should accept lowercase
        model = KEGGModel(operation="info", database="pathway")
        assert model.operation == "info"

    def test_database_case_sensitivity(self):
        # Database should accept lowercase
        model = KEGGModel(operation="info", database="pathway")
        assert model.database == "pathway"

    def test_enum_values_used_correctly(self):
        model = KEGGModel(
            operation=KEGGOperation.get,
            dbentries=["C00001"],
            get_option=KEGGGetOption.mol
        )
        assert model.operation == "get"
        assert model.get_option == "mol"

    def test_custom_max_entries(self):
        entries = [f"hsa:{10458 + i}" for i in range(20)]
        model = KEGGModel(operation="get", dbentries=entries, max_entries=25)
        assert len(model.dbentries) == 20


# =============================================================================
# Integration-Style Validation Tests
# =============================================================================

class TestCommonUseCases:
    """Tests for common KEGG API use cases."""

    def test_get_human_gene_info(self):
        """Get information about human gene."""
        model = KEGGModel(operation="get", dbentries=["hsa:7157"])  # TP53
        assert model.dbentries == ["hsa:7157"]

    def test_find_cancer_pathways(self):
        """Search for cancer-related pathways."""
        model = KEGGModel(operation="find", database="pathway", query="cancer")
        assert model.query == "cancer"

    def test_list_human_pathways(self):
        """List all human pathways."""
        model = KEGGModel(operation="list", database="pathway", organism="hsa")
        assert model.organism == "hsa"

    def test_convert_gene_to_uniprot(self):
        """Convert KEGG gene ID to UniProt."""
        model = KEGGModel(
            operation="conv",
            target_db="uniprot",
            dbentries=["hsa:7157"]
        )
        assert model.target_db == "uniprot"

    def test_link_gene_to_pathway(self):
        """Find pathways containing a gene."""
        model = KEGGModel(
            operation="link",
            target_db="pathway",
            dbentries=["hsa:7157"]
        )
        assert model.target_db == "pathway"

    def test_check_drug_interactions(self):
        """Check drug-drug interactions."""
        model = KEGGModel(
            operation="ddi",
            dbentries=["D00001", "D00002"]
        )
        assert model.operation == "ddi"

    def test_get_compound_structure(self):
        """Get compound structure in MOL format."""
        model = KEGGModel(
            operation="get",
            dbentries=["C00002"],  # ATP
            get_option="mol"
        )
        assert model.get_option == "mol"

    def test_get_pathway_image(self):
        """Get pathway image."""
        model = KEGGModel(
            operation="get",
            dbentries=["hsa00010"],  # Glycolysis
            get_option="image"
        )
        assert model.get_option == "image"

    def test_get_gene_sequence(self):
        """Get gene amino acid sequence."""
        model = KEGGModel(
            operation="get",
            dbentries=["hsa:7157"],
            get_option="aaseq"
        )
        assert model.get_option == "aaseq"

    def test_find_compound_by_formula(self):
        """Find compounds by molecular formula."""
        model = KEGGModel(
            operation="find",
            database="compound",
            query="C6H12O6",
            find_option="formula"
        )
        assert model.find_option == "formula"
