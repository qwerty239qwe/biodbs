"""Integration tests for KEGG_Fetcher.

These tests make real API calls to verify URL construction and data parsing.
Run with: uv run pytest tests/test_kegg_fetcher.py -v
Skip slow tests: uv run pytest tests/test_kegg_fetcher.py -v -m "not slow"
"""

import pytest
import pandas as pd
import polars as pl

from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher


@pytest.fixture
def fetcher():
    """Create a KEGG_Fetcher instance."""
    return KEGG_Fetcher()


# =============================================================================
# INFO Operation Tests
# =============================================================================

class TestInfoOperation:
    """Tests for the info operation."""

    def test_info_kegg_database(self, fetcher):
        """Test getting info for the main KEGG database."""
        data = fetcher.get(operation="info", database="kegg")
        assert data.format == "text"
        assert data.text is not None
        assert "kegg" in data.text.lower()

    def test_info_pathway_database(self, fetcher):
        """Test getting info for the pathway database."""
        data = fetcher.get(operation="info", database="pathway")
        assert data.format == "text"
        assert data.text is not None
        assert "pathway" in data.text.lower()

    def test_info_genes_database(self, fetcher):
        """Test getting info for the genes database."""
        data = fetcher.get(operation="info", database="genes")
        assert data.format == "text"
        assert data.text is not None

    def test_info_compound_database(self, fetcher):
        """Test getting info for the compound database."""
        data = fetcher.get(operation="info", database="compound")
        assert data.format == "text"
        assert data.text is not None
        assert "compound" in data.text.lower()


# =============================================================================
# LIST Operation Tests
# =============================================================================

class TestListOperation:
    """Tests for the list operation."""

    def test_list_organism(self, fetcher):
        """Test listing organisms."""
        data = fetcher.get(operation="list", database="organism")
        assert data.format == "tabular"
        assert len(data.records) > 0
        assert "entry_id" in data.records[0]
        assert "description" in data.records[0]

    def test_list_pathway_with_organism(self, fetcher):
        """Test listing pathways for a specific organism (human)."""
        data = fetcher.get(operation="list", database="pathway", organism="hsa")
        assert data.format == "tabular"
        assert len(data.records) > 0
        # All pathways should be for human
        for record in data.records[:5]:
            assert record["entry_id"].startswith("path:hsa") or "hsa" in record["entry_id"]

    def test_list_module(self, fetcher):
        """Test listing modules."""
        data = fetcher.get(operation="list", database="module")
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_list_with_dbentries(self, fetcher):
        """Test listing specific entries."""
        data = fetcher.get(
            operation="list",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        assert data.format == "tabular"
        assert len(data.records) == 2

    def test_list_brite_hierarchy(self, fetcher):
        """Test listing BRITE hierarchies."""
        # brite_option only accepts specific org codes like "ko" for KEGG Orthology
        data = fetcher.get(operation="list", database="brite", brite_option="ko")
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_list_as_dataframe_pandas(self, fetcher):
        """Test converting list results to pandas DataFrame."""
        data = fetcher.get(operation="list", database="organism")
        df = data.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "entry_id" in df.columns
        assert "description" in df.columns

    def test_list_as_dataframe_polars(self, fetcher):
        """Test converting list results to polars DataFrame."""
        data = fetcher.get(operation="list", database="organism")
        df = data.as_dataframe(engine="polars")
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0
        assert "entry_id" in df.columns
        assert "description" in df.columns


# =============================================================================
# FIND Operation Tests
# =============================================================================

class TestFindOperation:
    """Tests for the find operation."""

    def test_find_genes_by_keyword(self, fetcher):
        """Test finding genes by keyword."""
        data = fetcher.get(operation="find", database="genes", query="shiga+toxin")
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_find_compound_by_name(self, fetcher):
        """Test finding compounds by name."""
        data = fetcher.get(operation="find", database="compound", query="aspirin")
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_find_compound_by_formula(self, fetcher):
        """Test finding compounds by molecular formula."""
        data = fetcher.get(
            operation="find",
            database="compound",
            query="C10H13N5O4",
            find_option="formula"
        )
        assert data.format == "tabular"
        # Should find adenosine and related compounds
        assert len(data.records) >= 1

    def test_find_compound_by_exact_mass(self, fetcher):
        """Test finding compounds by exact mass."""
        data = fetcher.get(
            operation="find",
            database="compound",
            query="174.05",
            find_option="exact_mass"
        )
        assert data.format == "tabular"
        assert len(data.records) >= 0  # May or may not find matches

    def test_find_compound_by_mol_weight(self, fetcher):
        """Test finding compounds by molecular weight range."""
        data = fetcher.get(
            operation="find",
            database="compound",
            query="300-350",
            find_option="mol_weight"
        )
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_find_drug_by_name(self, fetcher):
        """Test finding drugs by name."""
        data = fetcher.get(operation="find", database="drug", query="ibuprofen")
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_find_pathway_by_keyword(self, fetcher):
        """Test finding pathways by keyword."""
        data = fetcher.get(operation="find", database="pathway", query="apoptosis")
        assert data.format == "tabular"
        assert len(data.records) > 0


# =============================================================================
# GET Operation Tests
# =============================================================================

class TestGetOperation:
    """Tests for the get operation."""

    def test_get_gene_flat_file(self, fetcher):
        """Test getting gene entry in flat file format."""
        data = fetcher.get(operation="get", dbentries=["hsa:10458"])
        assert data.format == "flat_file"
        assert len(data.records) == 1
        # ENTRY field should contain the gene ID
        assert "ENTRY" in data.records[0]

    def test_get_multiple_genes(self, fetcher):
        """Test getting multiple gene entries."""
        data = fetcher.get(
            operation="get",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        assert data.format == "flat_file"
        assert len(data.records) == 2

    def test_get_gene_amino_acid_sequence(self, fetcher):
        """Test getting gene amino acid sequence (FASTA)."""
        data = fetcher.get(
            operation="get",
            dbentries=["hsa:10458"],
            get_option="aaseq"
        )
        assert data.format == "fasta"
        assert len(data.records) == 1
        assert "sequence" in data.records[0]
        assert len(data.records[0]["sequence"]) > 0

    def test_get_gene_nucleotide_sequence(self, fetcher):
        """Test getting gene nucleotide sequence (FASTA)."""
        data = fetcher.get(
            operation="get",
            dbentries=["hsa:10458"],
            get_option="ntseq"
        )
        assert data.format == "fasta"
        assert len(data.records) == 1
        assert "sequence" in data.records[0]
        # Nucleotide sequence should contain only ATCG
        seq = data.records[0]["sequence"].upper()
        assert all(c in "ATCGN" for c in seq)

    def test_get_pathway_entry(self, fetcher):
        """Test getting pathway entry."""
        data = fetcher.get(operation="get", dbentries=["path:hsa00010"])
        assert data.format == "flat_file"
        assert len(data.records) == 1
        assert "NAME" in data.records[0] or "ENTRY" in data.records[0]

    def test_get_compound_entry(self, fetcher):
        """Test getting compound entry."""
        data = fetcher.get(operation="get", dbentries=["cpd:C00001"])
        assert data.format == "flat_file"
        assert len(data.records) == 1
        # C00001 is water
        record = data.records[0]
        assert "NAME" in record or "ENTRY" in record

    def test_get_compound_mol_file(self, fetcher):
        """Test getting compound MOL file."""
        data = fetcher.get(
            operation="get",
            dbentries=["cpd:C00001"],
            get_option="mol"
        )
        assert data.format == "text"
        assert data.text is not None
        # MOL files have specific format
        assert "M  END" in data.text or len(data.text) > 0

    def test_get_drug_entry(self, fetcher):
        """Test getting drug entry."""
        data = fetcher.get(operation="get", dbentries=["dr:D00001"])
        assert data.format == "flat_file"
        assert len(data.records) == 1

    @pytest.mark.slow
    def test_get_compound_image(self, fetcher):
        """Test getting compound image (GIF)."""
        data = fetcher.get(
            operation="get",
            dbentries=["cpd:C00001"],
            get_option="image"
        )
        assert data.format == "binary"
        assert data.binary_data is not None
        # Compound images are GIF format (starts with "GIF8")
        assert data.binary_data[:4] == b'GIF8'

    @pytest.mark.slow
    def test_get_pathway_image(self, fetcher):
        """Test getting pathway image (PNG)."""
        data = fetcher.get(
            operation="get",
            dbentries=["path:hsa00010"],
            get_option="image"
        )
        assert data.format == "binary"
        assert data.binary_data is not None

    def test_get_entry_helper(self, fetcher):
        """Test the get_entry helper method."""
        data = fetcher.get(
            operation="get",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        # get_entry matches by checking if ENTRY starts with the ID
        # ENTRY field format is like "10458            CDS       hsa"
        entry = data.get_entry("10458")
        assert entry is not None
        assert "ENTRY" in entry


# =============================================================================
# CONV Operation Tests
# =============================================================================

class TestConvOperation:
    """Tests for the conv (ID conversion) operation."""

    def test_conv_ncbi_geneid_to_kegg(self, fetcher):
        """Test converting NCBI Gene IDs to KEGG IDs."""
        data = fetcher.get(
            operation="conv",
            target_db="hsa",
            source_db="ncbi-geneid"
        )
        assert data.format == "tabular"
        assert len(data.records) > 0
        assert "source_id" in data.records[0]
        assert "target_id" in data.records[0]

    def test_conv_specific_entries(self, fetcher):
        """Test converting specific entries."""
        data = fetcher.get(
            operation="conv",
            target_db="ncbi-geneid",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        assert data.format == "tabular"
        assert len(data.records) == 2

    def test_conv_uniprot_to_kegg(self, fetcher):
        """Test converting UniProt IDs to KEGG."""
        data = fetcher.get(
            operation="conv",
            target_db="hsa",
            source_db="uniprot"
        )
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_conv_as_dataframe(self, fetcher):
        """Test converting conv results to DataFrame."""
        data = fetcher.get(
            operation="conv",
            target_db="ncbi-geneid",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        df = data.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert "source_id" in df.columns
        assert "target_id" in df.columns


# =============================================================================
# LINK Operation Tests
# =============================================================================

class TestLinkOperation:
    """Tests for the link operation."""

    def test_link_pathway_to_genes(self, fetcher):
        """Test linking pathways to genes for human."""
        data = fetcher.get(
            operation="link",
            target_db="hsa",
            source_db="pathway"
        )
        assert data.format == "tabular"
        assert len(data.records) > 0
        assert "source_id" in data.records[0]
        assert "target_id" in data.records[0]

    def test_link_specific_genes(self, fetcher):
        """Test getting pathway links for specific genes."""
        data = fetcher.get(
            operation="link",
            target_db="pathway",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        assert data.format == "tabular"
        assert len(data.records) > 0

    def test_link_compound_to_pathway(self, fetcher):
        """Test linking compounds to pathways."""
        data = fetcher.get(
            operation="link",
            target_db="pathway",
            dbentries=["cpd:C00001", "cpd:C00002"]
        )
        assert data.format == "tabular"
        # Water and ATP are in many pathways
        assert len(data.records) > 0

    def test_link_disease_to_genes(self, fetcher):
        """Test linking diseases to genes."""
        data = fetcher.get(
            operation="link",
            target_db="hsa",
            source_db="disease"
        )
        assert data.format == "tabular"
        assert len(data.records) > 0


# =============================================================================
# DDI Operation Tests
# =============================================================================

class TestDDIOperation:
    """Tests for the ddi (drug-drug interaction) operation."""

    @pytest.mark.xfail(reason="DDI API may require specific drug formats or subscription")
    def test_ddi_single_drug(self, fetcher):
        """Test getting drug-drug interactions for a single drug."""
        # Note: DDI operation may not be available for all drugs or require specific format
        data = fetcher.get(
            operation="ddi",
            dbentries=["D00001"]
        )
        assert data.format == "tabular"
        # D00001 (water for injection) may not have DDI, so just check format
        assert "drug1" in data.show_columns() or len(data.records) == 0

    @pytest.mark.xfail(reason="DDI API may require specific drug formats or subscription")
    def test_ddi_drug_pair(self, fetcher):
        """Test checking interaction between two drugs."""
        # Aspirin and Warfarin - known interaction, but API access may be restricted
        data = fetcher.get(
            operation="ddi",
            dbentries=["D00564", "D00175"]
        )
        assert data.format == "tabular"
        # Known drug interaction pair
        if len(data.records) > 0:
            assert "drug1" in data.records[0]
            assert "drug2" in data.records[0]


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_operation(self, fetcher):
        """Test that invalid operation raises ValueError."""
        with pytest.raises(ValueError, match="operation"):
            fetcher.get(operation="invalid_op", database="kegg")

    def test_missing_required_param(self, fetcher):
        """Test that missing required parameter raises ValueError."""
        with pytest.raises(ValueError):
            fetcher.get(operation="find")  # Missing database and query

    def test_invalid_database_for_operation(self, fetcher):
        """Test that invalid database for operation raises error."""
        with pytest.raises(ValueError):
            fetcher.get(operation="info", database="invalid_db")

    def test_get_without_dbentries(self, fetcher):
        """Test that get operation without dbentries raises ValueError."""
        with pytest.raises(ValueError):
            fetcher.get(operation="get")

    def test_conv_without_target_db(self, fetcher):
        """Test that conv operation without target_db raises ValueError."""
        with pytest.raises(ValueError):
            fetcher.get(operation="conv", source_db="hsa")

    def test_invalid_entry_returns_error(self, fetcher):
        """Test that invalid entry ID raises an error.

        Note: The get_rsp utility asserts on 404 status, so we expect AssertionError.
        """
        with pytest.raises((ConnectionError, AssertionError)):
            fetcher.get(operation="get", dbentries=["invalid:entry123"])


# =============================================================================
# KEGGFetchedData Methods Tests
# =============================================================================

class TestKEGGFetchedData:
    """Tests for KEGGFetchedData methods."""

    def test_filter_by_exact_match(self, fetcher):
        """Test filtering records by exact match."""
        data = fetcher.get(
            operation="list",
            dbentries=["hsa:10458", "hsa:7157", "hsa:672"]
        )
        filtered = data.filter(entry_id="hsa:10458")
        assert len(filtered.records) == 1
        assert filtered.records[0]["entry_id"] == "hsa:10458"

    def test_filter_by_callable(self, fetcher):
        """Test filtering records with a callable."""
        data = fetcher.get(
            operation="conv",
            target_db="ncbi-geneid",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        # Filter source IDs that contain "7157"
        filtered = data.filter(source_id=lambda x: "7157" in x)
        assert len(filtered.records) >= 1
        for record in filtered.records:
            assert "7157" in record["source_id"]

    def test_show_columns(self, fetcher):
        """Test showing available columns."""
        data = fetcher.get(operation="list", database="organism")
        columns = data.show_columns()
        assert "entry_id" in columns
        assert "description" in columns

    def test_len(self, fetcher):
        """Test __len__ returns record count."""
        data = fetcher.get(
            operation="list",
            dbentries=["hsa:10458", "hsa:7157"]
        )
        assert len(data) == 2

    def test_as_dict_with_columns(self, fetcher):
        """Test as_dict with column selection."""
        data = fetcher.get(
            operation="conv",
            target_db="ncbi-geneid",
            dbentries=["hsa:10458"]
        )
        records = data.as_dict(columns=["target_id"])
        assert len(records) == 1
        assert "target_id" in records[0]
        assert "source_id" not in records[0]


# =============================================================================
# get_all Batch Tests
# =============================================================================

@pytest.mark.slow
class TestGetAllBatch:
    """Tests for get_all batching functionality."""

    def test_get_all_multiple_entries(self, fetcher):
        """Test get_all with multiple entries."""
        entries = ["hsa:10458", "hsa:7157", "hsa:672", "hsa:5290"]
        data = fetcher.get_all(
            operation="get",
            dbentries=entries,
            batch_size=2
        )
        assert len(data.records) == 4

    def test_get_all_conv_entries(self, fetcher):
        """Test get_all for conv operation."""
        entries = ["hsa:10458", "hsa:7157", "hsa:672"]
        data = fetcher.get_all(
            operation="conv",
            dbentries=entries,
            target_db="ncbi-geneid",
            batch_size=2
        )
        assert len(data.records) == 3

    def test_get_all_link_entries(self, fetcher):
        """Test get_all for link operation."""
        entries = ["hsa:10458", "hsa:7157"]
        data = fetcher.get_all(
            operation="link",
            dbentries=entries,
            target_db="pathway",
            batch_size=1
        )
        assert len(data.records) > 0

    def test_get_all_empty_entries(self, fetcher):
        """Test get_all with empty entries list."""
        data = fetcher.get_all(
            operation="get",
            dbentries=[]
        )
        assert len(data.records) == 0

    def test_get_all_invalid_operation(self, fetcher):
        """Test get_all rejects invalid operations."""
        with pytest.raises(ValueError, match="get_all only supports"):
            fetcher.get_all(
                operation="list",  # list doesn't use batching
                dbentries=["hsa:10458"]
            )

    def test_get_all_concatenates_results(self, fetcher):
        """Test that get_all properly concatenates batch results."""
        entries = ["hsa:10458", "hsa:7157", "hsa:672"]
        data = fetcher.get_all(
            operation="get",
            dbentries=entries,
            batch_size=1,  # Force separate requests
            method="concat"
        )
        # All entries should be in the final result
        entry_ids = [r.get("ENTRY", "").split()[0] for r in data.records]
        for entry in entries:
            gene_id = entry.split(":")[1]  # Extract just the number
            assert any(gene_id in eid for eid in entry_ids)


# =============================================================================
# Integration Tests - Common Use Cases
# =============================================================================

class TestCommonUseCases:
    """Tests for common biological use cases."""

    def test_find_cancer_genes(self, fetcher):
        """Find genes associated with cancer."""
        data = fetcher.get(
            operation="find",
            database="genes",
            query="cancer"
        )
        assert len(data.records) > 0
        df = data.as_dataframe()
        assert len(df) > 0

    def test_get_p53_gene_info(self, fetcher):
        """Get detailed information for TP53 (p53) gene."""
        data = fetcher.get(
            operation="get",
            dbentries=["hsa:7157"]  # TP53
        )
        assert len(data.records) == 1
        record = data.records[0]
        # TP53 entry should have gene name
        assert "NAME" in record or "DEFINITION" in record

    def test_convert_gene_ids(self, fetcher):
        """Convert KEGG gene IDs to NCBI Gene IDs."""
        data = fetcher.get(
            operation="conv",
            target_db="ncbi-geneid",
            dbentries=["hsa:7157", "hsa:672"]  # TP53, BRCA1
        )
        assert len(data.records) == 2
        # Check conversion was successful
        for record in data.records:
            assert record["target_id"].startswith("ncbi-geneid:")

    def test_find_pathways_for_gene(self, fetcher):
        """Find pathways that include a specific gene."""
        data = fetcher.get(
            operation="link",
            target_db="pathway",
            dbentries=["hsa:7157"]  # TP53
        )
        assert len(data.records) > 0
        # TP53 is in many pathways
        assert len(data.records) >= 5

    def test_list_human_pathways(self, fetcher):
        """List all human metabolic pathways."""
        data = fetcher.get(
            operation="list",
            database="pathway",
            organism="hsa"
        )
        assert len(data.records) > 100  # Human has many pathways
        df = data.as_dataframe()
        assert len(df) > 100

    def test_find_drug_by_target(self, fetcher):
        """Find drugs and their targets."""
        data = fetcher.get(
            operation="link",
            target_db="drug",
            dbentries=["hsa:7157"]  # TP53 - some drugs target p53
        )
        # May or may not have drugs targeting TP53 directly
        assert data.format == "tabular"

    def test_get_sequence_for_analysis(self, fetcher):
        """Get protein sequence for bioinformatics analysis."""
        data = fetcher.get(
            operation="get",
            dbentries=["hsa:7157"],  # TP53
            get_option="aaseq"
        )
        assert len(data.records) == 1
        seq = data.records[0]["sequence"]
        # TP53 protein is about 393 amino acids
        assert len(seq) > 300
        # Should be valid amino acid sequence
        valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
        assert all(aa in valid_aa for aa in seq)
