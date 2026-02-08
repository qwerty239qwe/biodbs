"""Integration tests for Human Protein Atlas Fetcher (require network access)."""

import pytest
from biodbs.fetch.HPA import HPA_Fetcher


@pytest.mark.integration
class TestHPAFetcherSearchDownload:
    """Tests for HPA search_download API."""

    def test_search_download_basic(self):
        """Test basic search_download API call."""
        fetcher = HPA_Fetcher()
        data = fetcher.search_download(
            search="TP53",
            columns=["g", "eg", "gd"]
        )
        assert len(data) > 0
        assert data.results[0].get("Gene") == "TP53"

    def test_search_download_multiple_columns(self):
        """Test search_download with multiple columns."""
        fetcher = HPA_Fetcher()
        data = fetcher.search_download(
            search="BRCA1",
            columns=["g", "gs", "eg", "gd", "pc"]
        )
        assert len(data) > 0
        columns = data.show_columns()
        assert "Gene" in columns
        assert "Ensembl" in columns

    def test_search_download_as_dataframe(self):
        """Test search_download with DataFrame conversion."""
        fetcher = HPA_Fetcher()
        data = fetcher.search_download(
            search="kinase",
            columns=["g", "eg", "pc"]
        )
        df = data.as_dataframe()
        assert len(df) > 0
        assert "Gene" in df.columns

    def test_search_download_tsv_format(self):
        """Test search_download with TSV format."""
        fetcher = HPA_Fetcher()
        data = fetcher.search_download(
            search="TP53",
            columns=["g", "eg"],
            format="tsv"
        )
        assert len(data) > 0


@pytest.mark.integration
class TestHPAFetcherGene:
    """Tests for HPA individual gene fetch."""

    def test_get_gene_by_ensembl_id(self):
        """Test individual gene fetch by Ensembl ID."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_gene("ENSG00000141510")  # TP53
        assert len(data) == 1
        assert data.results[0].get("Gene") == "TP53"

    def test_get_gene_json_format(self):
        """Test gene fetch returns JSON by default."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_gene("ENSG00000012048")  # BRCA1
        assert data.format == "json"
        assert len(data) == 1

    def test_get_gene_has_detailed_data(self):
        """Test gene fetch returns detailed data."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_gene("ENSG00000141510")
        columns = data.show_columns()
        # Should have many columns from detailed entry
        assert len(columns) > 10


@pytest.mark.integration
class TestHPAFetcherConvenienceMethods:
    """Tests for HPA Fetcher convenience methods."""

    def test_get_expression(self):
        """Test expression data fetch."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_expression("BRCA1")
        assert len(data) > 0

    def test_get_subcellular_location(self):
        """Test subcellular location fetch."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_subcellular_location("TP53")
        assert len(data) > 0
        # Check that subcellular location columns are present
        if data.results:
            columns = data.show_columns()
            assert any("Subcellular" in col for col in columns)

    def test_get_pathology(self):
        """Test pathology data fetch."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_pathology("TP53")
        assert len(data) > 0

    def test_get_protein_class(self):
        """Test protein class fetch."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_protein_class("kinase")
        assert len(data) > 0
        # Should find multiple kinases
        assert len(data) > 10

    def test_get_blood_expression(self):
        """Test blood expression fetch."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_blood_expression("TP53")
        assert len(data) > 0

    def test_get_brain_expression(self):
        """Test brain expression fetch."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_brain_expression("TP53")
        assert len(data) > 0

    def test_get_tissue_expression(self):
        """Test tissue expression fetch."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_tissue_expression("BRCA1")
        assert len(data) > 0


@pytest.mark.integration
class TestHPAFetcherUtilities:
    """Tests for HPA Fetcher utility methods."""

    def test_list_columns(self):
        """Test listing available columns."""
        fetcher = HPA_Fetcher()
        columns = fetcher.list_columns()
        assert "g" in columns
        assert "eg" in columns
        assert len(columns) > 10

    def test_list_columns_returns_descriptions(self):
        """Test column listing includes descriptions."""
        fetcher = HPA_Fetcher()
        columns = fetcher.list_columns()
        assert columns["g"] == "Gene"
        assert columns["eg"] == "Ensembl"


@pytest.mark.integration
class TestHPAFetcherBatch:
    """Tests for HPA Fetcher batch operations."""

    def test_get_genes_multiple(self):
        """Test fetching multiple genes."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_genes([
            "ENSG00000141510",  # TP53
            "ENSG00000012048",  # BRCA1
        ])
        assert len(data) == 2

    def test_get_genes_single(self):
        """Test fetching single gene via batch method."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_genes(["ENSG00000141510"])
        assert len(data) == 1

    def test_get_genes_empty(self):
        """Test fetching empty gene list."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_genes([])
        assert len(data) == 0


@pytest.mark.integration
class TestHPAFetcherDataQuality:
    """Tests for HPA data quality and consistency."""

    def test_tp53_gene_name_consistency(self):
        """Test TP53 gene name is consistent across methods."""
        fetcher = HPA_Fetcher()

        # Via search_download
        data1 = fetcher.search_download(search="TP53", columns=["g", "eg"])
        tp53_names = [r["Gene"] for r in data1.results if r.get("Ensembl") == "ENSG00000141510"]

        # Via direct gene fetch
        data2 = fetcher.get_gene("ENSG00000141510")

        assert tp53_names[0] == "TP53"
        assert data2.results[0]["Gene"] == "TP53"

    def test_search_returns_related_genes(self):
        """Test search returns related genes."""
        fetcher = HPA_Fetcher()
        data = fetcher.search_download(search="TP53", columns=["g", "eg"])

        gene_names = data.get_gene_names()
        # Should find TP53 and related genes like TP53INP1, TP53BP1, etc.
        assert "TP53" in gene_names
        assert len(gene_names) > 1

    def test_subcellular_location_has_valid_locations(self):
        """Test subcellular location returns valid location data."""
        fetcher = HPA_Fetcher()
        data = fetcher.get_subcellular_location("TP53")

        if data.results:
            record = data.results[0]
            # Should have location data
            has_location = any(
                "Subcellular" in key or "scl" in key or "scml" in key
                for key in record.keys()
            )
            assert has_location
