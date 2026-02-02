
import pytest
import pandas as pd

from biodbs._funcs import (
    translate_gene_ids,
    translate_gene_ids_kegg,
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


@pytest.mark.integration
def test_empty_list_gene():
    """Test translation with empty list for genes."""
    result = translate_gene_ids(
        [],
        from_type="external_gene_name",
        to_type="ensembl_gene_id",
    )
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0