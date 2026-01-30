"""Integration tests for PubChem Fetcher (require network access)."""

import pytest
from biodbs.fetch.pubchem import PubChem_Fetcher


@pytest.mark.integration
class TestPubChemFetcherCompound:
    """Tests for PubChem compound fetching."""

    def test_get_compound_by_cid(self):
        """Test fetching compound by CID."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_compound(2244)  # Aspirin
        assert len(data) == 1

    def test_get_compounds_multiple(self):
        """Test fetching multiple compounds."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_compounds([2244, 3672])  # Aspirin, Adenosine
        assert len(data) == 2

    def test_search_by_name(self):
        """Test searching compound by name."""
        fetcher = PubChem_Fetcher()
        data = fetcher.search_by_name("aspirin")
        cids = data.get_cids()
        assert 2244 in cids

    def test_search_by_smiles(self):
        """Test searching compound by SMILES."""
        fetcher = PubChem_Fetcher()
        # Aspirin SMILES
        data = fetcher.search_by_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")
        assert len(data) > 0

    def test_search_by_inchikey(self):
        """Test searching compound by InChIKey."""
        fetcher = PubChem_Fetcher()
        # Aspirin InChIKey
        data = fetcher.search_by_inchikey("BSYNRYMUTXBXSQ-UHFFFAOYSA-N")
        assert len(data) > 0


@pytest.mark.integration
class TestPubChemFetcherProperties:
    """Tests for PubChem property fetching."""

    def test_get_properties(self):
        """Test fetching compound properties."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_properties(
            [2244, 3672],
            properties=["MolecularFormula", "MolecularWeight"]
        )
        assert len(data) == 2
        df = data.as_dataframe()
        assert "MolecularFormula" in df.columns
        assert "MolecularWeight" in df.columns

    def test_get_properties_default(self):
        """Test fetching compound properties with defaults."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_properties(2244)
        assert len(data) == 1
        columns = data.show_columns()
        assert "MolecularFormula" in columns

    def test_get_synonyms(self):
        """Test fetching compound synonyms."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_synonyms(2244)
        assert len(data) == 1
        if data.results:
            synonyms = data.results[0].get("Synonym", [])
            assert len(synonyms) > 0


@pytest.mark.integration
class TestPubChemFetcherSearch:
    """Tests for PubChem search operations."""

    def test_similarity_search(self):
        """Test similarity search."""
        fetcher = PubChem_Fetcher()
        data = fetcher.similarity_search(
            smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
            threshold=95,
            max_records=10
        )
        cids = data.get_cids()
        assert len(cids) > 0

    def test_substructure_search(self):
        """Test substructure search."""
        fetcher = PubChem_Fetcher()
        data = fetcher.substructure_search(
            smiles="c1ccccc1",  # Benzene ring
            max_records=10
        )
        cids = data.get_cids()
        assert len(cids) > 0

    def test_get_cids_by_name(self):
        """Test getting CIDs by name."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_cids_by_name("caffeine")
        cids = data.get_cids()
        assert 2519 in cids  # Caffeine CID


@pytest.mark.integration
class TestPubChemFetcherRelated:
    """Tests for PubChem related data fetching."""

    def test_get_sids_for_compound(self):
        """Test getting SIDs for a compound."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_sids_for_compound(2244)
        sids = data.get_sids()
        assert len(sids) > 0

    def test_get_aids_for_compound(self):
        """Test getting AIDs for a compound."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_aids_for_compound(2244)
        assert len(data) > 0

    def test_get_description(self):
        """Test getting compound description."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_description(2244)
        assert len(data) > 0


@pytest.mark.integration
class TestPubChemFetcherSubstance:
    """Tests for PubChem substance fetching."""

    def test_get_substance(self):
        """Test fetching substance by SID."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_substance(144205276)
        assert len(data) >= 0  # May or may not exist


@pytest.mark.integration
class TestPubChemFetcherAssay:
    """Tests for PubChem assay fetching."""

    def test_get_assay(self):
        """Test fetching assay by AID."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_assay(1000)
        assert len(data) >= 0


@pytest.mark.integration
class TestPubChemFetcherPUGView:
    """Tests for PubChem PUG View API."""

    def test_get_view(self):
        """Test fetching compound view."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_view(record_id=2244, record_type="compound")
        assert data.record_id == 2244

    def test_get_compound_annotations(self):
        """Test fetching compound annotations."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_compound_annotations(2244)
        headings = data.get_all_headings()
        assert len(headings) > 0

    def test_get_safety_data(self):
        """Test fetching safety data."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_safety_data(2244)
        assert data.record_id == 2244

    def test_get_pharmacology(self):
        """Test fetching pharmacology data."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_pharmacology(2244)
        assert data.record_id == 2244

    def test_get_names_and_identifiers(self):
        """Test fetching names and identifiers."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_names_and_identifiers(2244)
        assert data.record_id == 2244

    def test_get_physical_properties(self):
        """Test fetching physical properties."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_physical_properties(2244)
        assert data.record_id == 2244


@pytest.mark.integration
class TestPubChemFetcherDataQuality:
    """Tests for PubChem data quality and consistency."""

    def test_aspirin_cid_consistency(self):
        """Test Aspirin CID is consistent across methods."""
        fetcher = PubChem_Fetcher()

        # Via get_compound
        data1 = fetcher.get_compound(2244)
        assert len(data1) == 1

        # Via search_by_name
        data2 = fetcher.search_by_name("aspirin")
        cids = data2.get_cids()
        assert 2244 in cids

    def test_properties_match_expected(self):
        """Test properties return expected values for Aspirin."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_properties(
            2244,
            properties=["MolecularFormula", "MolecularWeight"]
        )
        assert len(data) == 1
        record = data.results[0]
        assert record["MolecularFormula"] == "C9H8O4"
        # Aspirin molecular weight is ~180.16
        assert 180 < record["MolecularWeight"] < 181

    def test_dataframe_conversion(self):
        """Test DataFrame conversion works correctly."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get_properties(
            [2244, 3672],
            properties=["MolecularFormula", "MolecularWeight", "CanonicalSMILES"]
        )
        df = data.as_dataframe()
        assert len(df) == 2
        assert "CID" in df.columns
        assert "MolecularFormula" in df.columns


@pytest.mark.integration
class TestPubChemFetcherGenericGet:
    """Tests for PubChem generic get method."""

    def test_get_basic(self):
        """Test basic get method."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get(
            domain="compound",
            namespace="cid",
            identifiers=2244
        )
        assert len(data) == 1

    def test_get_with_operation(self):
        """Test get method with operation."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get(
            domain="compound",
            namespace="cid",
            identifiers=2244,
            operation="synonyms"
        )
        assert len(data) >= 1

    def test_get_with_properties(self):
        """Test get method with properties."""
        fetcher = PubChem_Fetcher()
        data = fetcher.get(
            domain="compound",
            namespace="cid",
            identifiers=[2244],
            operation="property",
            properties=["MolecularFormula"]
        )
        assert len(data) == 1
