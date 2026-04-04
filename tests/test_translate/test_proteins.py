import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from biodbs._funcs import (
    translate_protein_ids,
    translate_gene_to_uniprot,
    translate_uniprot_to_gene,
    translate_uniprot_to_pdb,
    translate_uniprot_to_ensembl,
    translate_uniprot_to_refseq,
)
from biodbs._funcs.translate.proteins import _translate_protein_multiple_targets


# =============================================================================
# Unit Tests — translate_protein_ids
# =============================================================================

class TestTranslateProteinIdsUnit:
    def test_empty_ids_returns_empty_dict(self):
        result = translate_protein_ids([], "UniProtKB_AC-ID", "GeneID", return_dict=True)
        assert result == {}

    def test_empty_ids_returns_empty_df(self):
        result = translate_protein_ids([], "UniProtKB_AC-ID", "GeneID", return_dict=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch("biodbs._funcs.translate.proteins.gene_to_uniprot")
    def test_gene_name_to_uniprot_kb(self, mock_g2u):
        mock_g2u.return_value = {"TP53": "P04637"}
        result = translate_protein_ids(
            ["TP53"], from_type="Gene_Name", to_type="UniProtKB", return_dict=True
        )
        assert result == {"TP53": "P04637"}

    @patch("biodbs._funcs.translate.proteins.gene_to_uniprot")
    def test_gene_name_to_uniprot_ac(self, mock_g2u):
        mock_g2u.return_value = {"TP53": "P04637"}
        result = translate_protein_ids(
            ["TP53"], from_type="Gene_Name", to_type="UniProtKB_AC-ID", return_dict=True
        )
        assert result == {"TP53": "P04637"}

    @patch("biodbs._funcs.translate.proteins.gene_to_uniprot")
    def test_gene_name_to_uniprot_returns_dataframe(self, mock_g2u):
        mock_g2u.return_value = {"TP53": "P04637"}
        result = translate_protein_ids(
            ["TP53"], from_type="Gene_Name", to_type="UniProtKB", return_dict=False
        )
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["from", "to"]
        assert result["to"].iloc[0] == "P04637"

    @patch("biodbs._funcs.translate.proteins.gene_to_uniprot")
    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_gene_name_to_other_two_step(self, mock_map, mock_g2u):
        mock_g2u.return_value = {"TP53": "P04637"}
        mock_map.return_value = {"P04637": ["7157"]}
        result = translate_protein_ids(
            ["TP53"], from_type="Gene_Name", to_type="GeneID", return_dict=True
        )
        assert result == {"TP53": "7157"}

    @patch("biodbs._funcs.translate.proteins.gene_to_uniprot")
    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_gene_name_to_other_no_mapping_returns_empty(self, mock_map, mock_g2u):
        mock_g2u.return_value = {}   # no match
        mock_map.return_value = {}
        result = translate_protein_ids(
            ["MISSING"], from_type="Gene_Name", to_type="GeneID", return_dict=False
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch("biodbs._funcs.translate.proteins.uniprot_to_gene")
    def test_uniprot_to_gene_name(self, mock_u2g):
        mock_u2g.return_value = {"P04637": "TP53"}
        result = translate_protein_ids(
            ["P04637"], from_type="UniProtKB", to_type="Gene_Name", return_dict=True
        )
        assert result == {"P04637": "TP53"}

    @patch("biodbs._funcs.translate.proteins.uniprot_to_gene")
    def test_uniprot_ac_to_gene_name(self, mock_u2g):
        mock_u2g.return_value = {"P04637": "TP53"}
        result = translate_protein_ids(
            ["P04637"], from_type="UniProtKB_AC-ID", to_type="Gene_Name", return_dict=False
        )
        assert isinstance(result, pd.DataFrame)
        assert result["to"].iloc[0] == "TP53"

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_gene_id_to_uniprot(self, mock_map):
        mock_map.return_value = {"7157": ["P04637"]}
        result = translate_protein_ids(
            ["7157"], from_type="GeneID", to_type="UniProtKB", return_dict=True
        )
        assert result == {"7157": "P04637"}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_gene_id_to_uniprot_ac(self, mock_map):
        mock_map.return_value = {"7157": ["P04637"]}
        result = translate_protein_ids(
            ["7157"], from_type="GeneID", to_type="UniProtKB_AC-ID", return_dict=True
        )
        assert result == {"7157": "P04637"}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_gene_id_to_other_two_step(self, mock_map):
        # First call: GeneID → UniProtKB, second call: UniProtKB → GeneID (different type)
        mock_map.side_effect = [
            {"7157": ["P04637"]},         # GeneID → UniProtKB
            {"P04637": ["ENSG00000141510"]},  # UniProtKB_AC-ID → Ensembl
        ]
        result = translate_protein_ids(
            ["7157"], from_type="GeneID", to_type="Ensembl", return_dict=True
        )
        assert result == {"7157": "ENSG00000141510"}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_general_case_uniprot_ac_to_ensembl(self, mock_map):
        mock_map.return_value = {"P04637": ["ENSG00000141510"]}
        result = translate_protein_ids(
            ["P04637"], from_type="UniProtKB_AC-ID", to_type="Ensembl", return_dict=True
        )
        assert result == {"P04637": "ENSG00000141510"}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_general_case_returns_dataframe_multi_hit(self, mock_map):
        mock_map.return_value = {"P04637": ["1TUP", "2OCJ"]}
        result = translate_protein_ids(
            ["P04637"], from_type="UniProtKB_AC-ID", to_type="PDB", return_dict=False
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # one row per PDB hit

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_general_case_uniprot_ac_id_to_type_remapped(self, mock_map):
        # "UniProtKB_AC-ID" as to_type should be remapped to "UniProtKB"
        mock_map.return_value = {"P04637": ["P04637"]}
        translate_protein_ids(
            ["P04637"], from_type="UniProtKB_AC-ID", to_type="UniProtKB_AC-ID", return_dict=True
        )
        assert mock_map.call_args.kwargs.get("to_db") == "UniProtKB"


# =============================================================================
# Unit Tests — _translate_protein_multiple_targets
# =============================================================================

class TestTranslateProteinMultipleTargetsUnit:
    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_returns_dict_with_nested_targets(self, mock_map):
        mock_map.return_value = {"P04637": ["7157"]}
        result = translate_protein_ids(
            ["P04637"], from_type="UniProtKB_AC-ID",
            to_type=["GeneID", "Ensembl"], return_dict=True,
        )
        assert isinstance(result, dict)
        assert "P04637" in result
        assert isinstance(result["P04637"], dict)

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_returns_dataframe_with_target_columns(self, mock_map):
        mock_map.return_value = {"P04637": ["7157"]}
        result = translate_protein_ids(
            ["P04637"], from_type="UniProtKB_AC-ID",
            to_type=["GeneID", "Ensembl"], return_dict=False,
        )
        assert isinstance(result, pd.DataFrame)
        assert "from" in result.columns
        assert "GeneID" in result.columns
        assert "Ensembl" in result.columns

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_partial_failure_sets_none(self, mock_map):
        mock_map.side_effect = [
            RuntimeError("fail"),
            {"P04637": ["ENSG00000141510"]},
        ]
        result = _translate_protein_multiple_targets(
            ["P04637"], "UniProtKB_AC-ID", ["GeneID", "Ensembl"], 9606, False
        )
        assert isinstance(result, pd.DataFrame)
        assert result["GeneID"].iloc[0] is None


# =============================================================================
# Unit Tests — convenience functions
# =============================================================================

class TestConvenienceFunctionsUnit:
    @patch("biodbs._funcs.translate.proteins.gene_to_uniprot")
    def test_translate_gene_to_uniprot_dict(self, mock_fn):
        mock_fn.return_value = {"TP53": "P04637", "BRCA1": "P38398"}
        result = translate_gene_to_uniprot(["TP53", "BRCA1"])
        assert result == {"TP53": "P04637", "BRCA1": "P38398"}
        mock_fn.assert_called_once()

    @patch("biodbs._funcs.translate.proteins.gene_to_uniprot")
    def test_translate_gene_to_uniprot_dataframe(self, mock_fn):
        mock_fn.return_value = {"TP53": "P04637"}
        result = translate_gene_to_uniprot(["TP53"], return_dict=False)
        assert isinstance(result, pd.DataFrame)
        assert "gene_name" in result.columns
        assert "uniprot_accession" in result.columns

    @patch("biodbs._funcs.translate.proteins.uniprot_to_gene")
    def test_translate_uniprot_to_gene_dict(self, mock_fn):
        mock_fn.return_value = {"P04637": "TP53"}
        result = translate_uniprot_to_gene(["P04637"])
        assert result == {"P04637": "TP53"}

    @patch("biodbs._funcs.translate.proteins.uniprot_to_gene")
    def test_translate_uniprot_to_gene_dataframe(self, mock_fn):
        mock_fn.return_value = {"P04637": "TP53"}
        result = translate_uniprot_to_gene(["P04637"], return_dict=False)
        assert isinstance(result, pd.DataFrame)
        assert "uniprot_accession" in result.columns

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_pdb_dict(self, mock_fn):
        mock_fn.return_value = {"P04637": ["1TUP", "2OCJ"]}
        result = translate_uniprot_to_pdb(["P04637"])
        assert result == {"P04637": ["1TUP", "2OCJ"]}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_pdb_dataframe(self, mock_fn):
        mock_fn.return_value = {"P04637": ["1TUP", "2OCJ"]}
        result = translate_uniprot_to_pdb(["P04637"], return_dict=False)
        assert isinstance(result, pd.DataFrame)
        assert "pdb_id" in result.columns
        assert len(result) == 2

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_pdb_empty_dataframe(self, mock_fn):
        mock_fn.return_value = {"P04637": []}
        result = translate_uniprot_to_pdb(["P04637"], return_dict=False)
        assert len(result) == 1
        assert pd.isna(result["pdb_id"].iloc[0])

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_ensembl_dict(self, mock_fn):
        mock_fn.return_value = {"P04637": ["ENSG00000141510"]}
        result = translate_uniprot_to_ensembl(["P04637"])
        assert result == {"P04637": "ENSG00000141510"}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_ensembl_none_when_empty(self, mock_fn):
        mock_fn.return_value = {"P04637": []}
        result = translate_uniprot_to_ensembl(["P04637"])
        assert result == {"P04637": None}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_ensembl_dataframe(self, mock_fn):
        mock_fn.return_value = {"P04637": ["ENSG00000141510"]}
        result = translate_uniprot_to_ensembl(["P04637"], return_dict=False)
        assert isinstance(result, pd.DataFrame)
        assert "ensembl_id" in result.columns

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_refseq_dict(self, mock_fn):
        mock_fn.return_value = {"P04637": ["NP_000537.3"]}
        result = translate_uniprot_to_refseq(["P04637"])
        assert result == {"P04637": ["NP_000537.3"]}

    @patch("biodbs._funcs.translate.proteins.uniprot_map_ids")
    def test_translate_uniprot_to_refseq_dataframe(self, mock_fn):
        mock_fn.return_value = {"P04637": ["NP_000537.3", "NP_001119584.1"]}
        result = translate_uniprot_to_refseq(["P04637"], return_dict=False)
        assert isinstance(result, pd.DataFrame)
        assert "refseq_id" in result.columns
        assert len(result) == 2


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
