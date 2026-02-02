"""Integration tests for translation functions in biodbs._funcs.

These tests make real API calls to verify ID translation functionality.
Run with: uv run pytest tests/test_translate.py -v
Skip slow tests: uv run pytest tests/test_translate.py -v -m "not slow"
"""

import pytest
import pandas as pd

from biodbs._funcs import (
    translate_gene_ids,
    translate_gene_ids_kegg,
    translate_chemical_ids,
    translate_chemical_ids_kegg,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
)


# =============================================================================
# Gene ID Translation Tests (BioMart)
# =============================================================================

class TestTranslateGeneIds:
    """Tests for translate_gene_ids function using BioMart."""

    @pytest.mark.integration
    def test_gene_symbol_to_ensembl(self):
        """Test translating gene symbols to Ensembl IDs."""
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2
        assert "external_gene_name" in result.columns
        assert "ensembl_gene_id" in result.columns
        # Verify TP53 translation
        tp53_rows = result[result["external_gene_name"] == "TP53"]
        assert len(tp53_rows) >= 1
        assert tp53_rows["ensembl_gene_id"].iloc[0].startswith("ENSG")

    @pytest.mark.integration
    def test_ensembl_to_entrez(self):
        """Test translating Ensembl IDs to Entrez Gene IDs."""
        result = translate_gene_ids(
            ["ENSG00000141510"],  # TP53
            from_type="ensembl_gene_id",
            to_type="entrezgene_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1
        assert "ensembl_gene_id" in result.columns
        assert "entrezgene_id" in result.columns

    @pytest.mark.integration
    def test_gene_symbol_to_hgnc(self):
        """Test translating gene symbols to HGNC IDs."""
        result = translate_gene_ids(
            ["TP53"],
            from_type="external_gene_name",
            to_type="hgnc_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @pytest.mark.integration
    def test_return_dict(self):
        """Test returning result as dictionary."""
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "TP53" in result
        assert result["TP53"].startswith("ENSG")

    @pytest.mark.integration
    def test_mouse_species(self):
        """Test translation for mouse genes."""
        result = translate_gene_ids(
            ["Trp53"],  # Mouse TP53 homolog
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
            species="mouse",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1
        # Mouse Ensembl IDs start with ENSMUSG
        if len(result) > 0 and result["ensembl_gene_id"].iloc[0]:
            assert "ENSMUS" in result["ensembl_gene_id"].iloc[0]

    @pytest.mark.integration
    def test_multiple_genes(self):
        """Test translation with multiple genes."""
        genes = ["TP53", "BRCA1", "EGFR", "MYC"]
        result = translate_gene_ids(
            genes,
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= len(genes)


# =============================================================================
# Gene ID Translation Tests (KEGG)
# =============================================================================

class TestTranslateGeneIdsKegg:
    """Tests for translate_gene_ids_kegg function using KEGG."""

    @pytest.mark.integration
    def test_kegg_to_ncbi_geneid(self):
        """Test converting KEGG gene IDs to NCBI Entrez Gene IDs."""
        result = translate_gene_ids_kegg(
            ["hsa:7157", "hsa:672"],  # TP53, BRCA1
            from_db="hsa",
            to_db="ncbi-geneid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "source_id" in result.columns
        assert "target_id" in result.columns
        # Verify target IDs have ncbi-geneid prefix
        for _, row in result.iterrows():
            assert "ncbi-geneid:" in row["target_id"]

    @pytest.mark.integration
    def test_kegg_to_uniprot(self):
        """Test converting KEGG gene IDs to UniProt accessions."""
        result = translate_gene_ids_kegg(
            ["hsa:7157"],  # TP53
            from_db="hsa",
            to_db="uniprot",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @pytest.mark.integration
    @pytest.mark.slow
    def test_entire_organism_conversion(self):
        """Test converting entire organism's genes (slow)."""
        # This fetches all human gene ID conversions - may be slow
        result = translate_gene_ids_kegg(
            [],  # Empty list means convert all
            from_db="hsa",
            to_db="ncbi-geneid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 1000  # Human has many genes


# =============================================================================
# Chemical ID Translation Tests (PubChem)
# =============================================================================

class TestTranslateChemicalIds:
    """Tests for translate_chemical_ids function using PubChem."""

    @pytest.mark.integration
    def test_name_to_cid(self):
        """Test translating compound names to PubChem CIDs."""
        result = translate_chemical_ids(
            ["aspirin", "ibuprofen"],
            from_type="name",
            to_type="cid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "name" in result.columns
        assert "cid" in result.columns
        # Aspirin CID is 2244
        aspirin_row = result[result["name"] == "aspirin"]
        assert len(aspirin_row) == 1
        assert aspirin_row["cid"].iloc[0] == 2244

    @pytest.mark.integration
    def test_cid_to_smiles(self):
        """Test translating PubChem CIDs to SMILES."""
        result = translate_chemical_ids(
            ["2244", "3672"],  # Aspirin, Ibuprofen
            from_type="cid",
            to_type="smiles",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "cid" in result.columns
        assert "smiles" in result.columns
        # SMILES should be non-empty strings
        for _, row in result.iterrows():
            assert row["smiles"] is not None
            assert len(row["smiles"]) > 0

    @pytest.mark.integration
    def test_cid_to_inchikey(self):
        """Test translating PubChem CIDs to InChIKey."""
        result = translate_chemical_ids(
            ["2244"],  # Aspirin
            from_type="cid",
            to_type="inchikey",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result["inchikey"].iloc[0] is not None
        # InChIKey format: 27 characters
        assert len(result["inchikey"].iloc[0]) == 27

    @pytest.mark.integration
    def test_cid_to_formula(self):
        """Test translating PubChem CIDs to molecular formula."""
        result = translate_chemical_ids(
            ["2244"],  # Aspirin: C9H8O4
            from_type="cid",
            to_type="formula",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "C9H8O4" == result["formula"].iloc[0]

    @pytest.mark.integration
    def test_smiles_to_cid(self):
        """Test translating SMILES to PubChem CID."""
        # Aspirin SMILES
        result = translate_chemical_ids(
            ["CC(=O)OC1=CC=CC=C1C(=O)O"],
            from_type="smiles",
            to_type="cid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result["cid"].iloc[0] == 2244

    @pytest.mark.integration
    def test_inchikey_to_cid(self):
        """Test translating InChIKey to PubChem CID."""
        # Aspirin InChIKey
        result = translate_chemical_ids(
            ["BSYNRYMUTXBXSQ-UHFFFAOYSA-N"],
            from_type="inchikey",
            to_type="cid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result["cid"].iloc[0] == 2244

    @pytest.mark.integration
    def test_return_dict(self):
        """Test returning result as dictionary."""
        result = translate_chemical_ids(
            ["aspirin", "ibuprofen"],
            from_type="name",
            to_type="cid",
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "aspirin" in result
        assert result["aspirin"] == 2244

    @pytest.mark.integration
    def test_invalid_name(self):
        """Test handling of invalid compound names."""
        result = translate_chemical_ids(
            ["aspirin", "this_is_not_a_real_compound_12345"],
            from_type="name",
            to_type="cid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        # Invalid compound should have None for cid
        invalid_row = result[result["name"] == "this_is_not_a_real_compound_12345"]
        assert invalid_row["cid"].iloc[0] is None


# =============================================================================
# Chemical ID Translation Tests (KEGG)
# =============================================================================

class TestTranslateChemicalIdsKegg:
    """Tests for translate_chemical_ids_kegg function using KEGG."""

    @pytest.mark.integration
    def test_compound_to_pubchem(self):
        """Test converting KEGG compound IDs to PubChem CIDs."""
        result = translate_chemical_ids_kegg(
            ["cpd:C00022", "cpd:C00031"],  # Pyruvate, Glucose
            from_db="compound",
            to_db="pubchem",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "source_id" in result.columns
        assert "target_id" in result.columns

    @pytest.mark.integration
    def test_drug_to_pubchem(self):
        """Test converting KEGG drug IDs to PubChem CIDs."""
        result = translate_chemical_ids_kegg(
            ["dr:D00217"],  # Aspirin in KEGG Drug
            from_db="drug",
            to_db="pubchem",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @pytest.mark.integration
    def test_compound_to_chebi(self):
        """Test converting KEGG compound IDs to ChEBI IDs."""
        result = translate_chemical_ids_kegg(
            ["cpd:C00022"],  # Pyruvate
            from_db="compound",
            to_db="chebi",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1


# =============================================================================
# ChEMBL to PubChem Translation Tests
# =============================================================================

class TestTranslateChemblToPubchem:
    """Tests for translate_chembl_to_pubchem function."""

    @pytest.mark.integration
    def test_single_chembl_id(self):
        """Test translating a single ChEMBL ID to PubChem CID."""
        result = translate_chembl_to_pubchem(["CHEMBL25"])  # Aspirin
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "chembl_id" in result.columns
        assert "pubchem_cid" in result.columns
        # CHEMBL25 (Aspirin) should map to PubChem CID 2244
        assert result["pubchem_cid"].iloc[0] is not None

    @pytest.mark.integration
    def test_multiple_chembl_ids(self):
        """Test translating multiple ChEMBL IDs."""
        chembl_ids = ["CHEMBL25", "CHEMBL521"]  # Aspirin, Caffeine
        result = translate_chembl_to_pubchem(chembl_ids)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @pytest.mark.integration
    def test_return_dict(self):
        """Test returning result as dictionary."""
        result = translate_chembl_to_pubchem(
            ["CHEMBL25"],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "CHEMBL25" in result

    @pytest.mark.integration
    def test_invalid_chembl_id(self):
        """Test handling of invalid ChEMBL IDs."""
        result = translate_chembl_to_pubchem(
            ["CHEMBL25", "CHEMBL_INVALID_12345"]
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        # Invalid ID should have None for pubchem_cid
        invalid_row = result[result["chembl_id"] == "CHEMBL_INVALID_12345"]
        assert invalid_row["pubchem_cid"].iloc[0] is None


# =============================================================================
# PubChem to ChEMBL Translation Tests
# =============================================================================

class TestTranslatePubchemToChembl:
    """Tests for translate_pubchem_to_chembl function."""

    @pytest.mark.integration
    def test_single_cid(self):
        """Test translating a single PubChem CID to ChEMBL ID."""
        result = translate_pubchem_to_chembl([2244])  # Aspirin
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "pubchem_cid" in result.columns
        assert "chembl_id" in result.columns
        # PubChem CID 2244 (Aspirin) should map to CHEMBL25
        chembl_id = result["chembl_id"].iloc[0]
        if chembl_id is not None:
            assert chembl_id == "CHEMBL25"

    @pytest.mark.integration
    def test_multiple_cids(self):
        """Test translating multiple PubChem CIDs."""
        cids = [2244, 2519]  # Aspirin, Caffeine
        result = translate_pubchem_to_chembl(cids)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @pytest.mark.integration
    def test_return_dict(self):
        """Test returning result as dictionary."""
        result = translate_pubchem_to_chembl(
            [2244],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert 2244 in result

    @pytest.mark.integration
    def test_invalid_cid(self):
        """Test handling of invalid PubChem CIDs."""
        result = translate_pubchem_to_chembl(
            [2244, 999999999999]  # Valid, Invalid
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in translation functions."""

    def test_invalid_from_type_chemical(self):
        """Test that invalid from_type raises ValueError for chemical IDs."""
        with pytest.raises(ValueError, match="Unsupported from_type"):
            translate_chemical_ids(
                ["aspirin"],
                from_type="invalid_type",
                to_type="cid",
            )

    def test_invalid_to_type_chemical(self):
        """Test that invalid to_type raises ValueError for chemical IDs."""
        with pytest.raises(ValueError, match="Unsupported to_type"):
            translate_chemical_ids(
                ["2244"],
                from_type="cid",
                to_type="invalid_type",
            )

    @pytest.mark.integration
    def test_empty_list_gene(self):
        """Test translation with empty list for genes."""
        result = translate_gene_ids(
            [],
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.integration
    def test_empty_list_chemical(self):
        """Test translation with empty list for chemicals."""
        result = translate_chemical_ids(
            [],
            from_type="name",
            to_type="cid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


# =============================================================================
# Round-trip Translation Tests
# =============================================================================

class TestRoundTrip:
    """Tests for round-trip translations (A -> B -> A)."""

    @pytest.mark.integration
    def test_name_cid_name_roundtrip(self):
        """Test name -> CID -> name round-trip."""
        # Name to CID
        result1 = translate_chemical_ids(
            ["aspirin"],
            from_type="name",
            to_type="cid",
        )
        cid = result1["cid"].iloc[0]
        assert cid == 2244

        # CID to name (IUPAC name)
        result2 = translate_chemical_ids(
            [str(cid)],
            from_type="cid",
            to_type="name",
        )
        # IUPAC name for aspirin
        name = result2["name"].iloc[0]
        assert name is not None
        assert "acetyl" in name.lower() or "aspirin" in name.lower()

    @pytest.mark.integration
    def test_chembl_pubchem_roundtrip(self):
        """Test ChEMBL -> PubChem -> ChEMBL round-trip."""
        # ChEMBL to PubChem
        result1 = translate_chembl_to_pubchem(["CHEMBL25"])
        pubchem_cid = result1["pubchem_cid"].iloc[0]

        if pubchem_cid is not None:
            # PubChem to ChEMBL
            result2 = translate_pubchem_to_chembl([pubchem_cid])
            chembl_id = result2["chembl_id"].iloc[0]
            if chembl_id is not None:
                assert chembl_id == "CHEMBL25"
