import pytest
import pandas as pd

from biodbs._funcs import (
    translate_protein_ids,
    translate_gene_to_uniprot,
    translate_uniprot_to_gene,
    translate_uniprot_to_pdb,
    translate_uniprot_to_ensembl,
    translate_uniprot_to_refseq,
)


# =============================================================================
# Protein ID Translation Tests
# =============================================================================

class TestTranslateProteinIds:
    """Tests for translate_protein_ids function."""

    @pytest.mark.integration
    def test_uniprot_to_geneid(self):
        """Test translating UniProt accessions to NCBI Gene IDs."""
        result = translate_protein_ids(
            ["P04637", "P00533"],  # TP53, EGFR
            from_type="UniProtKB_AC-ID",
            to_type="GeneID",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2
        assert "from" in result.columns
        assert "to" in result.columns

    @pytest.mark.integration
    def test_uniprot_to_ensembl(self):
        """Test translating UniProt accessions to Ensembl IDs."""
        result = translate_protein_ids(
            ["P04637"],  # TP53
            from_type="UniProtKB_AC-ID",
            to_type="Ensembl",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @pytest.mark.integration
    def test_gene_name_to_uniprot(self):
        """Test translating gene names to UniProt accessions."""
        result = translate_protein_ids(
            ["TP53", "EGFR"],
            from_type="Gene_Name",
            to_type="UniProtKB",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2

    @pytest.mark.integration
    def test_return_dict(self):
        """Test returning result as dictionary."""
        result = translate_protein_ids(
            ["P04637"],
            from_type="UniProtKB_AC-ID",
            to_type="GeneID",
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "P04637" in result

    def test_empty_list(self):
        """Test translation with empty list."""
        result = translate_protein_ids(
            [],
            from_type="UniProtKB_AC-ID",
            to_type="GeneID",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


# =============================================================================
# Multiple Target Types Tests
# =============================================================================

class TestTranslateProteinIdsMultipleTargets:
    """Tests for translate_protein_ids with multiple target types."""

    @pytest.mark.integration
    def test_multiple_to_types_dataframe(self):
        """Test translating to multiple ID types, returning DataFrame."""
        result = translate_protein_ids(
            ["P04637", "P00533"],
            from_type="UniProtKB_AC-ID",
            to_type=["GeneID", "Ensembl"],
        )
        assert isinstance(result, pd.DataFrame)
        assert "from" in result.columns
        assert "GeneID" in result.columns
        assert "Ensembl" in result.columns
        assert len(result) == 2

    @pytest.mark.integration
    def test_multiple_to_types_dict(self):
        """Test translating to multiple ID types, returning dict."""
        result = translate_protein_ids(
            ["P04637"],
            from_type="UniProtKB_AC-ID",
            to_type=["GeneID", "Ensembl"],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "P04637" in result
        assert isinstance(result["P04637"], dict)
        assert "GeneID" in result["P04637"]
        assert "Ensembl" in result["P04637"]

    @pytest.mark.integration
    def test_multiple_to_types_three_targets(self):
        """Test translating to three different ID types."""
        result = translate_protein_ids(
            ["P04637"],
            from_type="UniProtKB_AC-ID",
            to_type=["GeneID", "Ensembl", "Gene_Name"],
        )
        assert isinstance(result, pd.DataFrame)
        assert "GeneID" in result.columns
        assert "Ensembl" in result.columns
        assert "Gene_Name" in result.columns


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience translation functions."""

    @pytest.mark.integration
    def test_gene_to_uniprot(self):
        """Test translate_gene_to_uniprot function."""
        result = translate_gene_to_uniprot(
            ["TP53", "BRCA1"],
            organism=9606,
            reviewed_only=True,
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "TP53" in result
        # P04637 is the canonical UniProt accession for TP53
        if result["TP53"] is not None:
            assert result["TP53"].startswith("P") or result["TP53"].startswith("Q")

    @pytest.mark.integration
    def test_uniprot_to_gene(self):
        """Test translate_uniprot_to_gene function."""
        result = translate_uniprot_to_gene(
            ["P04637", "P00533"],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "P04637" in result
        # P04637 should map to TP53
        if result["P04637"] is not None:
            assert "TP53" in result["P04637"].upper()

    @pytest.mark.integration
    def test_uniprot_to_pdb(self):
        """Test translate_uniprot_to_pdb function."""
        result = translate_uniprot_to_pdb(
            ["P04637"],  # TP53 has many PDB structures
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "P04637" in result
        # TP53 should have multiple PDB structures
        pdb_ids = result.get("P04637", [])
        if pdb_ids:
            assert isinstance(pdb_ids, list)
            assert len(pdb_ids) > 0

    @pytest.mark.integration
    def test_uniprot_to_ensembl(self):
        """Test translate_uniprot_to_ensembl function."""
        result = translate_uniprot_to_ensembl(
            ["P04637", "P00533"],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "P04637" in result
        # Should map to Ensembl gene ID starting with ENSG
        if result["P04637"] is not None:
            assert result["P04637"].startswith("ENSG")

    @pytest.mark.integration
    def test_uniprot_to_refseq(self):
        """Test translate_uniprot_to_refseq function."""
        result = translate_uniprot_to_refseq(
            ["P04637"],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "P04637" in result
        # Should return list of RefSeq protein IDs
        refseq_ids = result.get("P04637", [])
        if refseq_ids:
            assert isinstance(refseq_ids, list)

    @pytest.mark.integration
    def test_convenience_return_dataframe(self):
        """Test convenience functions returning DataFrame."""
        result = translate_gene_to_uniprot(
            ["TP53"],
            return_dict=False,
        )
        assert isinstance(result, pd.DataFrame)
        assert "gene_name" in result.columns
        assert "uniprot_accession" in result.columns
