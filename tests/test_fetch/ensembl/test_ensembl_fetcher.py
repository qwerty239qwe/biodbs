"""Integration tests for Ensembl REST API fetcher.

These tests make real API calls to verify URL construction and data parsing.
Run with: uv run pytest tests/test_fetch/ensembl/test_ensembl_fetcher.py -v
Skip slow tests: uv run pytest tests/test_fetch/ensembl/test_ensembl_fetcher.py -v -m "not slow"
"""

import pytest
import pandas as pd

from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher
from biodbs.data.Ensembl.data import EnsemblFetchedData


@pytest.fixture
def fetcher():
    """Create an Ensembl_Fetcher instance."""
    return Ensembl_Fetcher()


# =============================================================================
# Lookup Tests
# =============================================================================

class TestLookup:
    """Tests for lookup operations."""

    @pytest.mark.integration
    def test_lookup_gene(self, fetcher):
        """Test looking up a gene by Ensembl ID."""
        data = fetcher.lookup("ENSG00000141510")  # TP53
        assert isinstance(data, EnsemblFetchedData)
        assert len(data.results) == 1
        assert data.results[0]["display_name"] == "TP53"
        assert data.results[0]["biotype"] == "protein_coding"

    @pytest.mark.integration
    def test_lookup_gene_expanded(self, fetcher):
        """Test looking up a gene with expanded features."""
        data = fetcher.lookup("ENSG00000141510", expand=True)
        assert len(data.results) == 1
        # Expanded lookup should include transcripts
        assert "Transcript" in data.results[0]
        transcripts = data.results[0]["Transcript"]
        assert len(transcripts) > 0

    @pytest.mark.integration
    def test_lookup_transcript(self, fetcher):
        """Test looking up a transcript by Ensembl ID."""
        data = fetcher.lookup("ENST00000269305")
        assert len(data.results) == 1
        assert data.results[0]["object_type"] == "Transcript"

    @pytest.mark.integration
    def test_lookup_symbol(self, fetcher):
        """Test looking up a gene by symbol."""
        data = fetcher.lookup_symbol("human", "TP53")
        assert len(data.results) >= 1
        assert data.results[0]["display_name"] == "TP53"

    @pytest.mark.integration
    def test_lookup_batch(self, fetcher):
        """Test batch lookup of multiple IDs."""
        ids = ["ENSG00000141510", "ENSG00000012048"]  # TP53, BRCA1
        data = fetcher.lookup_batch(ids)
        assert len(data.results) >= 2


# =============================================================================
# Sequence Tests
# =============================================================================

class TestSequence:
    """Tests for sequence retrieval."""

    @pytest.mark.integration
    def test_get_cds_sequence(self, fetcher):
        """Test getting CDS sequence for a transcript."""
        data = fetcher.get_sequence("ENST00000269305", sequence_type="cds")
        assert data.text is not None
        assert len(data.text) > 0
        # CDS should start with ATG (in FASTA format)
        assert "ATG" in data.text

    @pytest.mark.integration
    def test_get_protein_sequence(self, fetcher):
        """Test getting protein sequence."""
        data = fetcher.get_sequence("ENSP00000269305", sequence_type="protein")
        assert data.text is not None
        assert len(data.text) > 0
        # Should be amino acid sequence
        assert ">" in data.text  # FASTA header

    @pytest.mark.integration
    def test_get_genomic_sequence_region(self, fetcher):
        """Test getting genomic sequence for a region."""
        data = fetcher.get_sequence_region("human", "7:140424943-140424963:1")
        assert data.text is not None
        assert len(data.text) > 0

    @pytest.mark.integration
    def test_get_sequence_json_format(self, fetcher):
        """Test getting sequence in JSON format."""
        data = fetcher.get_sequence("ENST00000269305", sequence_type="cds", format="json")
        assert len(data.results) >= 1
        assert "seq" in data.results[0]


# =============================================================================
# Overlap Tests
# =============================================================================

class TestOverlap:
    """Tests for overlap queries."""

    @pytest.mark.integration
    def test_overlap_id_gene(self, fetcher):
        """Test getting genes overlapping an ID."""
        data = fetcher.get_overlap_id("ENSG00000141510", feature="gene")
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_overlap_id_transcript(self, fetcher):
        """Test getting transcripts overlapping an ID."""
        data = fetcher.get_overlap_id("ENSG00000141510", feature="transcript")
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_overlap_region(self, fetcher):
        """Test getting features overlapping a genomic region."""
        data = fetcher.get_overlap_region(
            "human", "7:140424943-140624564",
            feature=["gene", "transcript"]
        )
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_overlap_region_with_biotype(self, fetcher):
        """Test filtering overlapping features by biotype."""
        data = fetcher.get_overlap_region(
            "human", "7:140424943-140624564",
            feature="gene",
            biotype="protein_coding"
        )
        assert len(data.results) >= 0  # May or may not have results


# =============================================================================
# Cross-Reference Tests
# =============================================================================

class TestXrefs:
    """Tests for cross-reference lookups."""

    @pytest.mark.integration
    def test_xrefs_id(self, fetcher):
        """Test getting cross-references for an Ensembl ID."""
        data = fetcher.get_xrefs("ENSG00000141510")
        assert len(data.results) >= 1
        # Should have HGNC, UniProt, etc.
        dbs = {r.get("dbname") for r in data.results}
        assert len(dbs) > 1

    @pytest.mark.integration
    def test_xrefs_id_filtered(self, fetcher):
        """Test getting cross-references filtered by database."""
        data = fetcher.get_xrefs("ENSG00000141510", external_db="HGNC")
        assert len(data.results) >= 1
        for r in data.results:
            assert r.get("dbname") == "HGNC"

    @pytest.mark.integration
    def test_xrefs_symbol(self, fetcher):
        """Test looking up Ensembl IDs by gene symbol."""
        data = fetcher.get_xrefs_symbol("human", "BRCA2")
        assert len(data.results) >= 1
        # Should return Ensembl gene ID
        ids = [r.get("id") for r in data.results]
        assert any(id.startswith("ENSG") for id in ids if id)


# =============================================================================
# Homology Tests
# =============================================================================

class TestHomology:
    """Tests for homology queries."""

    @pytest.mark.integration
    def test_homology_id(self, fetcher):
        """Test getting homologs for a gene."""
        data = fetcher.get_homology("human", "ENSG00000141510")
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_homology_id_target_species(self, fetcher):
        """Test getting homologs filtered by target species."""
        data = fetcher.get_homology(
            "human", "ENSG00000141510",
            target_species="mouse"
        )
        assert len(data.results) >= 1
        # All results should be mouse homologs
        for r in data.results:
            if "target" in r:
                assert "mus_musculus" in r["target"].get("species", "").lower()

    @pytest.mark.integration
    def test_homology_symbol(self, fetcher):
        """Test getting homologs by gene symbol."""
        data = fetcher.get_homology_symbol("human", "TP53")
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_homology_orthologues_only(self, fetcher):
        """Test getting only orthologues."""
        data = fetcher.get_homology(
            "human", "ENSG00000141510",
            homology_type="orthologues"
        )
        assert len(data.results) >= 1
        for r in data.results:
            assert r.get("type") in ["ortholog_one2one", "ortholog_one2many", "ortholog_many2many"]


# =============================================================================
# Variation Tests
# =============================================================================

class TestVariation:
    """Tests for variation queries."""

    @pytest.mark.integration
    def test_get_variation(self, fetcher):
        """Test getting variant information by rsID."""
        data = fetcher.get_variation("human", "rs56116432")
        assert len(data.results) == 1
        assert data.results[0]["name"] == "rs56116432"

    @pytest.mark.integration
    def test_get_variation_with_pops(self, fetcher):
        """Test getting variant with population frequencies."""
        data = fetcher.get_variation("human", "rs56116432", pops=True)
        assert len(data.results) == 1
        assert "populations" in data.results[0]


# =============================================================================
# VEP Tests
# =============================================================================

class TestVEP:
    """Tests for Variant Effect Predictor."""

    @pytest.mark.integration
    def test_vep_hgvs(self, fetcher):
        """Test VEP with HGVS notation."""
        data = fetcher.get_vep_hgvs("human", "ENST00000366667:c.803C>T")
        assert len(data.results) >= 1
        # Should have transcript consequences
        assert "transcript_consequences" in data.results[0]

    @pytest.mark.integration
    def test_vep_id(self, fetcher):
        """Test VEP with variant ID."""
        data = fetcher.get_vep_id("human", "rs56116432")
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_vep_region(self, fetcher):
        """Test VEP with genomic coordinates."""
        data = fetcher.get_vep_region("human", "9:22125503-22125502:1", "C")
        assert len(data.results) >= 1


# =============================================================================
# Mapping Tests
# =============================================================================

class TestMapping:
    """Tests for coordinate mapping."""

    @pytest.mark.integration
    def test_map_assembly(self, fetcher):
        """Test mapping coordinates between assemblies."""
        data = fetcher.map_assembly(
            "human", "GRCh37", "X:1000000..1000100:1", "GRCh38"
        )
        assert len(data.results) >= 1
        # Should have mapped region
        mapping = data.results[0]
        assert "mapped" in mapping


# =============================================================================
# Phenotype Tests
# =============================================================================

class TestPhenotype:
    """Tests for phenotype queries."""

    @pytest.mark.integration
    def test_phenotype_gene(self, fetcher):
        """Test getting phenotypes for a gene."""
        data = fetcher.get_phenotype_gene("human", "BRCA2")
        # BRCA2 has known phenotypes
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_phenotype_gene_by_ensembl_id(self, fetcher):
        """Test getting phenotypes using Ensembl ID."""
        data = fetcher.get_phenotype_gene("human", "ENSG00000139618")  # BRCA2
        assert len(data.results) >= 1


# =============================================================================
# Ontology Tests
# =============================================================================

class TestOntology:
    """Tests for ontology queries."""

    @pytest.mark.integration
    def test_ontology_term(self, fetcher):
        """Test getting ontology term information."""
        data = fetcher.get_ontology_term("GO:0005667")
        assert len(data.results) == 1
        assert "name" in data.results[0]

    @pytest.mark.integration
    def test_ontology_ancestors(self, fetcher):
        """Test getting ontology term ancestors."""
        data = fetcher.get_ontology_ancestors("GO:0005667")
        assert len(data.results) >= 1

    @pytest.mark.integration
    def test_ontology_descendants(self, fetcher):
        """Test getting ontology term descendants."""
        data = fetcher.get_ontology_descendants("GO:0008150")  # biological_process
        assert len(data.results) >= 1


# =============================================================================
# Gene Tree Tests
# =============================================================================

class TestGeneTree:
    """Tests for gene tree queries."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_genetree_by_id(self, fetcher):
        """Test getting gene tree by ID."""
        data = fetcher.get_genetree("ENSGT00390000003602")
        assert len(data.results) >= 1
        assert "tree" in data.results[0]

    @pytest.mark.integration
    @pytest.mark.slow
    def test_genetree_member(self, fetcher):
        """Test getting gene tree containing a gene."""
        data = fetcher.get_genetree_member("human", "ENSG00000141510")
        assert len(data.results) >= 1


# =============================================================================
# Information Tests
# =============================================================================

class TestInfo:
    """Tests for information queries."""

    @pytest.mark.integration
    def test_assembly_info(self, fetcher):
        """Test getting assembly information."""
        data = fetcher.get_assembly_info("human")
        assert len(data.results) == 1
        info = data.results[0]
        assert info["assembly_name"] == "GRCh38"

    @pytest.mark.integration
    def test_species_info(self, fetcher):
        """Test getting species information."""
        data = fetcher.get_species_info()
        assert len(data.results) >= 1
        # Should have human
        species_names = [r.get("name") for r in data.results]
        assert any("sapiens" in name for name in species_names if name)


# =============================================================================
# Data Conversion Tests
# =============================================================================

class TestDataConversion:
    """Tests for data conversion methods."""

    @pytest.mark.integration
    def test_as_dataframe_pandas(self, fetcher):
        """Test converting results to pandas DataFrame."""
        data = fetcher.get_xrefs("ENSG00000141510")
        df = data.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "dbname" in df.columns

    @pytest.mark.integration
    def test_filter_results(self, fetcher):
        """Test filtering results."""
        data = fetcher.get_xrefs("ENSG00000141510")
        filtered = data.filter(dbname="HGNC")
        assert len(filtered) >= 1
        for r in filtered.results:
            assert r["dbname"] == "HGNC"

    @pytest.mark.integration
    def test_show_columns(self, fetcher):
        """Test showing available columns."""
        data = fetcher.get_xrefs("ENSG00000141510")
        columns = data.show_columns()
        assert "dbname" in columns
        assert "primary_id" in columns

    @pytest.mark.integration
    def test_get_ids(self, fetcher):
        """Test extracting IDs from results."""
        data = fetcher.lookup("ENSG00000141510")
        ids = data.get_ids()
        assert len(ids) >= 1
        assert "ENSG00000141510" in ids


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_lookup_missing_id(self, fetcher):
        """Test that lookup without ID raises ValueError."""
        with pytest.raises(ValueError):
            fetcher.lookup(id=None)

    def test_overlap_missing_feature(self, fetcher):
        """Test that overlap without feature raises ValueError."""
        with pytest.raises(ValueError):
            fetcher.get_overlap_id("ENSG00000141510", feature=None)

    @pytest.mark.integration
    def test_invalid_id_returns_empty(self, fetcher):
        """Test that invalid ID returns empty result."""
        data = fetcher.lookup("INVALID_ID_12345")
        assert len(data.results) == 0

    def test_vep_missing_hgvs(self, fetcher):
        """Test that VEP HGVS without notation raises ValueError."""
        with pytest.raises(ValueError):
            fetcher.get_vep_hgvs("human", hgvs_notation=None)
