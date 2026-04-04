import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call

from biodbs._funcs import (
    translate_chemical_ids,
    translate_chemical_ids_kegg,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl
)


# =============================================================================
# Helpers
# =============================================================================

def _mock_pubchem_search(cids: list) -> MagicMock:
    m = MagicMock()
    m.get_cids.return_value = cids
    return m


def _mock_pubchem_props(result_dict: dict) -> MagicMock:
    m = MagicMock()
    m.results = [result_dict] if result_dict else []
    return m


def _mock_kegg_data(rows: list) -> MagicMock:
    m = MagicMock()
    m.as_dataframe.return_value = pd.DataFrame(rows)
    return m


# =============================================================================
# Unit Tests — translate_chemical_ids
# =============================================================================

class TestTranslateChemicalIdsUnit:
    """Unit tests for translate_chemical_ids — all network calls mocked."""

    def test_cid_to_smiles(self):
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            mock_props.return_value = _mock_pubchem_props({"CanonicalSMILES": "CC(=O)Oc1ccccc1C(=O)O"})
            result = translate_chemical_ids(["2244"], from_type="cid", to_type="smiles")
        assert isinstance(result, pd.DataFrame)
        assert result["smiles"].iloc[0] == "CC(=O)Oc1ccccc1C(=O)O"

    def test_cid_to_inchikey(self):
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            mock_props.return_value = _mock_pubchem_props({"InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"})
            result = translate_chemical_ids(["2244"], from_type="cid", to_type="inchikey")
        assert result["inchikey"].iloc[0] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"

    def test_cid_to_formula(self):
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            mock_props.return_value = _mock_pubchem_props({"MolecularFormula": "C9H8O4"})
            result = translate_chemical_ids(["2244"], from_type="cid", to_type="formula")
        assert result["formula"].iloc[0] == "C9H8O4"

    def test_cid_to_cid_no_props_call(self):
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            result = translate_chemical_ids(["2244"], from_type="cid", to_type="cid")
        mock_props.assert_not_called()
        assert result["cid"].iloc[0] == 2244

    def test_name_to_cid_mocked(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search:
            mock_search.return_value = _mock_pubchem_search([2244])
            result = translate_chemical_ids(["aspirin"], from_type="name", to_type="cid")
        assert result["cid"].iloc[0] == 2244

    def test_smiles_to_cid_mocked(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_smiles") as mock_search:
            mock_search.return_value = _mock_pubchem_search([2244])
            result = translate_chemical_ids(
                ["CC(=O)Oc1ccccc1C(=O)O"], from_type="smiles", to_type="cid"
            )
        assert result["cid"].iloc[0] == 2244

    def test_inchikey_to_cid_mocked(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_inchikey") as mock_search:
            mock_search.return_value = _mock_pubchem_search([2244])
            result = translate_chemical_ids(
                ["BSYNRYMUTXBXSQ-UHFFFAOYSA-N"], from_type="inchikey", to_type="cid"
            )
        assert result["cid"].iloc[0] == 2244

    def test_no_cid_found_produces_none(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search:
            mock_search.return_value = _mock_pubchem_search([])  # no results
            result = translate_chemical_ids(["nonexistent"], from_type="name", to_type="cid")
        assert pd.isna(result["cid"].iloc[0])

    def test_exception_produces_none(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search:
            mock_search.side_effect = RuntimeError("network fail")
            result = translate_chemical_ids(["aspirin"], from_type="name", to_type="smiles")
        assert pd.isna(result["smiles"].iloc[0])

    def test_return_dict(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search:
            mock_search.return_value = _mock_pubchem_search([2244])
            result = translate_chemical_ids(
                ["aspirin"], from_type="name", to_type="cid", return_dict=True
            )
        assert isinstance(result, dict)
        assert result["aspirin"] == 2244

    def test_empty_list_returns_empty_df(self):
        result = translate_chemical_ids([], from_type="name", to_type="cid")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_name_prop_uses_iupac_key(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search, \
             patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            mock_search.return_value = _mock_pubchem_search([2244])
            mock_props.return_value = _mock_pubchem_props({"IUPACName": "2-acetyloxybenzoic acid"})
            result = translate_chemical_ids(["aspirin"], from_type="name", to_type="name")
        assert result["name"].iloc[0] == "2-acetyloxybenzoic acid"


# =============================================================================
# Unit Tests — translate_chemical_ids (multiple targets)
# =============================================================================

class TestTranslateChemicalIdsMultipleTargetsUnit:
    def test_multiple_to_types_dataframe(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search, \
             patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            mock_search.return_value = _mock_pubchem_search([2244])
            mock_props.return_value = _mock_pubchem_props({
                "CanonicalSMILES": "CC(=O)Oc1ccccc1C(=O)O",
                "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
            })
            result = translate_chemical_ids(
                ["aspirin"], from_type="name", to_type=["cid", "smiles", "inchikey"]
            )
        assert isinstance(result, pd.DataFrame)
        assert "cid" in result.columns
        assert "smiles" in result.columns
        assert "inchikey" in result.columns

    def test_multiple_to_types_dict(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search, \
             patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            mock_search.return_value = _mock_pubchem_search([2244])
            mock_props.return_value = _mock_pubchem_props({"CanonicalSMILES": "CC(=O)Oc1ccccc1C(=O)O"})
            result = translate_chemical_ids(
                ["aspirin"], from_type="name", to_type=["cid", "smiles"], return_dict=True
            )
        assert isinstance(result, dict)
        assert "aspirin" in result
        assert isinstance(result["aspirin"], dict)
        assert result["aspirin"]["cid"] == 2244

    def test_only_cid_in_targets(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search, \
             patch("biodbs._funcs.translate.chem.pubchem_get_properties") as mock_props:
            mock_search.return_value = _mock_pubchem_search([2244])
            result = translate_chemical_ids(["aspirin"], from_type="name", to_type=["cid"])
        mock_props.assert_not_called()
        assert result["cid"].iloc[0] == 2244

    def test_invalid_to_type_in_list_raises(self):
        with pytest.raises(ValueError, match="Unsupported to_type"):
            translate_chemical_ids(["aspirin"], from_type="name", to_type=["cid", "invalid_type"])

    def test_no_cid_found_sets_all_none(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search:
            mock_search.return_value = _mock_pubchem_search([])
            result = translate_chemical_ids(
                ["nonexistent"], from_type="name", to_type=["cid", "smiles"]
            )
        assert pd.isna(result["cid"].iloc[0])
        assert pd.isna(result["smiles"].iloc[0])

    def test_exception_sets_all_none(self):
        with patch("biodbs._funcs.translate.chem.pubchem_search_by_name") as mock_search:
            mock_search.side_effect = RuntimeError("fail")
            result = translate_chemical_ids(
                ["aspirin"], from_type="name", to_type=["cid", "smiles"]
            )
        assert pd.isna(result["cid"].iloc[0])
        assert pd.isna(result["smiles"].iloc[0])


# =============================================================================
# Unit Tests — translate_chembl_to_pubchem
# =============================================================================

class TestTranslateChemblToPubchemUnit:
    def test_via_cross_references(self):
        mol_data = MagicMock()
        mol_data.results = [{
            "cross_references": [{"xref_src": "PubChem", "xref_id": "2244"}],
            "molecule_structures": None,
        }]
        with patch("biodbs._funcs.translate.chem.chembl_get_molecule", return_value=mol_data):
            result = translate_chembl_to_pubchem(["CHEMBL25"])
        assert result["pubchem_cid"].iloc[0] == "2244"

    def test_via_inchikey_fallback(self):
        mol_data = MagicMock()
        mol_data.results = [{
            "cross_references": [],
            "molecule_structures": {"standard_inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"},
        }]
        search_data = MagicMock()
        search_data.get_cids.return_value = [2244]
        with patch("biodbs._funcs.translate.chem.chembl_get_molecule", return_value=mol_data), \
             patch("biodbs._funcs.translate.chem.pubchem_search_by_inchikey", return_value=search_data):
            result = translate_chembl_to_pubchem(["CHEMBL25"])
        assert result["pubchem_cid"].iloc[0] == 2244

    def test_no_results_produces_none(self):
        mol_data = MagicMock()
        mol_data.results = []
        with patch("biodbs._funcs.translate.chem.chembl_get_molecule", return_value=mol_data):
            result = translate_chembl_to_pubchem(["CHEMBL_INVALID"])
        assert pd.isna(result["pubchem_cid"].iloc[0])

    def test_exception_produces_none(self):
        with patch("biodbs._funcs.translate.chem.chembl_get_molecule", side_effect=RuntimeError("fail")):
            result = translate_chembl_to_pubchem(["CHEMBL25"])
        assert pd.isna(result["pubchem_cid"].iloc[0])

    def test_return_dict(self):
        mol_data = MagicMock()
        mol_data.results = [{"cross_references": [{"xref_src": "PubChem", "xref_id": "2244"}],
                              "molecule_structures": None}]
        with patch("biodbs._funcs.translate.chem.chembl_get_molecule", return_value=mol_data):
            result = translate_chembl_to_pubchem(["CHEMBL25"], return_dict=True)
        assert isinstance(result, dict)
        assert "CHEMBL25" in result

    def test_null_molecule_structures(self):
        mol_data = MagicMock()
        mol_data.results = [{"cross_references": [], "molecule_structures": None}]
        with patch("biodbs._funcs.translate.chem.chembl_get_molecule", return_value=mol_data):
            result = translate_chembl_to_pubchem(["CHEMBL25"])
        assert pd.isna(result["pubchem_cid"].iloc[0])


# =============================================================================
# Unit Tests — translate_pubchem_to_chembl
# =============================================================================

class TestTranslatePubchemToChemblUnit:
    def test_found(self):
        prop_data = MagicMock()
        prop_data.results = [{"InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"}]
        search_data = MagicMock()
        search_data.results = [{"molecule_chembl_id": "CHEMBL25"}]
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties", return_value=prop_data), \
             patch("biodbs._funcs.translate.chem.chembl_search_molecules", return_value=search_data):
            result = translate_pubchem_to_chembl([2244])
        assert result["chembl_id"].iloc[0] == "CHEMBL25"

    def test_no_inchikey_produces_none(self):
        prop_data = MagicMock()
        prop_data.results = [{}]  # no InChIKey key
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties", return_value=prop_data):
            result = translate_pubchem_to_chembl([2244])
        assert pd.isna(result["chembl_id"].iloc[0])

    def test_no_prop_results_produces_none(self):
        prop_data = MagicMock()
        prop_data.results = []
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties", return_value=prop_data):
            result = translate_pubchem_to_chembl([2244])
        assert pd.isna(result["chembl_id"].iloc[0])

    def test_no_chembl_search_results_produces_none(self):
        prop_data = MagicMock()
        prop_data.results = [{"InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"}]
        search_data = MagicMock()
        search_data.results = []
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties", return_value=prop_data), \
             patch("biodbs._funcs.translate.chem.chembl_search_molecules", return_value=search_data):
            result = translate_pubchem_to_chembl([2244])
        assert pd.isna(result["chembl_id"].iloc[0])

    def test_exception_produces_none(self):
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties", side_effect=RuntimeError("fail")):
            result = translate_pubchem_to_chembl([2244])
        assert pd.isna(result["chembl_id"].iloc[0])

    def test_return_dict(self):
        prop_data = MagicMock()
        prop_data.results = [{"InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"}]
        search_data = MagicMock()
        search_data.results = [{"molecule_chembl_id": "CHEMBL25"}]
        with patch("biodbs._funcs.translate.chem.pubchem_get_properties", return_value=prop_data), \
             patch("biodbs._funcs.translate.chem.chembl_search_molecules", return_value=search_data):
            result = translate_pubchem_to_chembl([2244], return_dict=True)
        assert isinstance(result, dict)
        assert result[2244] == "CHEMBL25"


# =============================================================================
# Unit Tests — translate_chemical_ids_kegg
# =============================================================================

class TestTranslateChemicalIdsKeggUnit:
    @patch("biodbs._funcs.translate.chem.kegg_conv")
    def test_with_ids(self, mock_conv):
        mock_conv.return_value = _mock_kegg_data([
            {"source_id": "cpd:C00022", "target_id": "pubchem:3324"}
        ])
        result = translate_chemical_ids_kegg(["cpd:C00022"], from_db="compound", to_db="pubchem")
        assert isinstance(result, pd.DataFrame)
        mock_conv.assert_called_once_with(target_db="pubchem", source=["cpd:C00022"])

    @patch("biodbs._funcs.translate.chem.kegg_conv")
    def test_empty_ids_uses_from_db(self, mock_conv):
        mock_conv.return_value = _mock_kegg_data([])
        translate_chemical_ids_kegg([], from_db="compound", to_db="pubchem")
        mock_conv.assert_called_once_with(target_db="pubchem", source="compound")



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
        if aspirin_row["cid"].iloc[0] is None:
            pytest.skip("PubChem returned no CID for aspirin (service degraded)")
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
        # At least one SMILES should be retrieved successfully
        valid_smiles = result[pd.notna(result["smiles"])]
        assert len(valid_smiles) >= 1
        # Valid SMILES should be non-empty strings
        for _, row in valid_smiles.iterrows():
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
        # API may fail in CI, skip if no result
        formula = result["formula"].iloc[0]
        if pd.isna(formula):
            pytest.skip("PubChem API returned no data")
        assert formula == "C9H8O4"

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
        # API may fail in CI, skip if no result
        cid = result["cid"].iloc[0]
        if pd.isna(cid):
            pytest.skip("PubChem API returned no data")
        assert cid == 2244

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
        # API may fail in CI, skip if no result
        cid = result["cid"].iloc[0]
        if pd.isna(cid):
            pytest.skip("PubChem API returned no data")
        assert cid == 2244

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
        # API may fail in CI, skip if no result
        if pd.isna(result["aspirin"]):
            pytest.skip("PubChem API returned no data")
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
        # Invalid compound should have None/NaN for cid
        invalid_row = result[result["name"] == "this_is_not_a_real_compound_12345"]
        assert pd.isna(invalid_row["cid"].iloc[0])


# =============================================================================
# Multiple Target Types Tests
# =============================================================================

class TestTranslateChemicalIdsMultipleTargets:
    """Tests for translate_chemical_ids with multiple target types."""

    @pytest.mark.integration
    def test_multiple_to_types_dataframe(self):
        """Test translating to multiple ID types, returning DataFrame."""
        result = translate_chemical_ids(
            ["aspirin"],
            from_type="name",
            to_type=["cid", "smiles", "inchikey"],
        )
        assert isinstance(result, pd.DataFrame)
        assert "name" in result.columns
        assert "cid" in result.columns
        assert "smiles" in result.columns
        assert "inchikey" in result.columns
        assert len(result) == 1
        # Check that aspirin has valid CID
        if result["cid"].iloc[0] is None:
            pytest.skip("PubChem returned no CID for aspirin (service degraded)")
        assert result["cid"].iloc[0] == 2244

    @pytest.mark.integration
    def test_multiple_to_types_dict(self):
        """Test translating to multiple ID types, returning dict."""
        result = translate_chemical_ids(
            ["aspirin"],
            from_type="name",
            to_type=["cid", "smiles"],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "aspirin" in result
        assert isinstance(result["aspirin"], dict)
        assert "cid" in result["aspirin"]
        assert "smiles" in result["aspirin"]
        if result["aspirin"]["cid"] is None:
            pytest.skip("PubChem returned no CID for aspirin (service degraded)")
        assert result["aspirin"]["cid"] == 2244

    @pytest.mark.integration
    def test_multiple_to_types_all_properties(self):
        """Test translating to all supported target types."""
        result = translate_chemical_ids(
            ["aspirin"],
            from_type="name",
            to_type=["cid", "smiles", "inchikey", "inchi", "formula"],
        )
        assert isinstance(result, pd.DataFrame)
        assert "cid" in result.columns
        assert "smiles" in result.columns
        assert "inchikey" in result.columns
        assert "inchi" in result.columns
        assert "formula" in result.columns

    @pytest.mark.integration
    def test_multiple_to_types_cid_input(self):
        """Test translating from CID to multiple target types."""
        result = translate_chemical_ids(
            ["2244"],  # Aspirin CID
            from_type="cid",
            to_type=["smiles", "inchikey", "formula"],
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "smiles" in result.columns
        assert "inchikey" in result.columns
        assert "formula" in result.columns

    @pytest.mark.integration
    def test_multiple_compounds_multiple_targets(self):
        """Test translating multiple compounds to multiple target types."""
        result = translate_chemical_ids(
            ["aspirin", "caffeine"],
            from_type="name",
            to_type=["cid", "smiles"],
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        # Verify both compounds have CIDs
        aspirin_row = result[result["name"] == "aspirin"]
        if aspirin_row["cid"].iloc[0] is None:
            pytest.skip("PubChem returned no CID for aspirin (service degraded)")
        assert aspirin_row["cid"].iloc[0] == 2244


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
        try:
            result = translate_chembl_to_pubchem(["CHEMBL25"])  # Aspirin
        except ConnectionError as e:
            pytest.skip(f"ChEMBL API unavailable: {e}")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "chembl_id" in result.columns
        assert "pubchem_cid" in result.columns
        # CHEMBL25 (Aspirin) should map to PubChem CID 2244
        # May be None if ChEMBL doesn't have cross-reference (fallback to InChIKey lookup)
        if result["pubchem_cid"].iloc[0] is None:
            pytest.skip("ChEMBL API returned no cross-reference for CHEMBL25")

    @pytest.mark.integration
    def test_multiple_chembl_ids(self):
        """Test translating multiple ChEMBL IDs."""
        chembl_ids = ["CHEMBL25", "CHEMBL521"]  # Aspirin, Caffeine
        try:
            result = translate_chembl_to_pubchem(chembl_ids)
        except ConnectionError as e:
            pytest.skip(f"ChEMBL API unavailable: {e}")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @pytest.mark.integration
    def test_return_dict(self):
        """Test returning result as dictionary."""
        try:
            result = translate_chembl_to_pubchem(
                ["CHEMBL25"],
                return_dict=True,
            )
        except ConnectionError as e:
            pytest.skip(f"ChEMBL API unavailable: {e}")
        assert isinstance(result, dict)
        assert "CHEMBL25" in result

    @pytest.mark.integration
    def test_invalid_chembl_id(self):
        """Test handling of invalid ChEMBL IDs."""
        try:
            result = translate_chembl_to_pubchem(
                ["CHEMBL25", "CHEMBL_INVALID_12345"]
            )
        except ConnectionError as e:
            pytest.skip(f"ChEMBL API unavailable: {e}")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        # Invalid ID should have None/NaN for pubchem_cid
        invalid_row = result[result["chembl_id"] == "CHEMBL_INVALID_12345"]
        assert pd.isna(invalid_row["pubchem_cid"].iloc[0])


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
        if cid is None:
            pytest.skip("PubChem returned no CID for aspirin (service degraded)")
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
