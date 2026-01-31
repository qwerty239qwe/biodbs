"""Integration tests for BioMart fetcher.

These tests require network access to the BioMart API.
Run with: uv run pytest tests/test_fetch/biomart/test_biomart_fetcher.py -m integration
"""

import pytest
from biodbs.fetch.biomart import BioMart_Fetcher
from biodbs.data.BioMart import (
    BioMartHost,
    BioMartMart,
    BioMartDataset,
    BioMartRegistryData,
    BioMartDatasetsData,
    BioMartConfigData,
    BioMartQueryData,
)


@pytest.fixture
def fetcher():
    """Create BioMart fetcher instance."""
    return BioMart_Fetcher()


class TestBioMartFetcherInit:
    """Tests for BioMart fetcher initialization."""

    def test_default_init(self):
        """Test default initialization."""
        fetcher = BioMart_Fetcher()
        assert fetcher.host == "www.ensembl.org"

    def test_custom_host_string(self):
        """Test initialization with custom host string."""
        fetcher = BioMart_Fetcher(host="grch37.ensembl.org")
        assert fetcher.host == "grch37.ensembl.org"

    def test_custom_host_enum(self):
        """Test initialization with host enum."""
        fetcher = BioMart_Fetcher(host=BioMartHost.grch37)
        assert fetcher.host == "grch37.ensembl.org"


@pytest.mark.integration
class TestBioMartFetcherDiscovery:
    """Integration tests for BioMart discovery methods."""

    def test_list_marts(self, fetcher):
        """Test listing available marts."""
        marts = fetcher.list_marts()
        assert isinstance(marts, BioMartRegistryData)
        assert len(marts) > 0
        assert "ENSEMBL_MART_ENSEMBL" in marts.marts

    def test_list_datasets(self, fetcher):
        """Test listing datasets in a mart."""
        datasets = fetcher.list_datasets()
        assert isinstance(datasets, BioMartDatasetsData)
        assert len(datasets) > 0
        assert "hsapiens_gene_ensembl" in datasets.datasets

    def test_list_datasets_search(self, fetcher):
        """Test searching datasets."""
        datasets = fetcher.list_datasets()
        human_datasets = datasets.search(contain="sapiens")
        assert len(human_datasets) >= 1

    def test_get_config(self, fetcher):
        """Test getting dataset configuration."""
        config = fetcher.get_config("hsapiens_gene_ensembl")
        assert isinstance(config, BioMartConfigData)
        assert len(config.filter_names) > 0
        assert len(config.attribute_names) > 0

    def test_get_config_caching(self, fetcher):
        """Test configuration caching."""
        # First call
        config1 = fetcher.get_config("hsapiens_gene_ensembl")
        # Second call should use cache
        config2 = fetcher.get_config("hsapiens_gene_ensembl")
        assert config1 is config2

    def test_list_attributes(self, fetcher):
        """Test listing attributes."""
        attrs = fetcher.list_attributes("hsapiens_gene_ensembl")
        assert len(attrs) > 0
        assert "name" in attrs.columns

    def test_list_attributes_contain(self, fetcher):
        """Test listing attributes with contain filter."""
        attrs = fetcher.list_attributes(
            "hsapiens_gene_ensembl",
            contain="gene"
        )
        assert len(attrs) > 0

    def test_list_filters(self, fetcher):
        """Test listing filters."""
        filters = fetcher.list_filters("hsapiens_gene_ensembl")
        assert len(filters) > 0


@pytest.mark.integration
class TestBioMartFetcherQuery:
    """Integration tests for BioMart query methods."""

    def test_query_basic(self, fetcher):
        """Test basic query."""
        data = fetcher.query(
            dataset="hsapiens_gene_ensembl",
            attributes=["ensembl_gene_id", "external_gene_name"],
            filters={"ensembl_gene_id": ["ENSG00000141510"]}
        )
        assert isinstance(data, BioMartQueryData)
        assert len(data) >= 1
        df = data.as_dataframe()
        assert "ENSG00000141510" in df["ensembl_gene_id"].values

    def test_query_multiple_genes(self, fetcher):
        """Test query with multiple genes."""
        gene_ids = ["ENSG00000141510", "ENSG00000012048"]
        data = fetcher.query(
            dataset="hsapiens_gene_ensembl",
            attributes=["ensembl_gene_id", "external_gene_name"],
            filters={"ensembl_gene_id": gene_ids}
        )
        assert len(data) >= 2

    def test_query_default_attributes(self, fetcher):
        """Test query with default attributes."""
        data = fetcher.query(
            filters={"ensembl_gene_id": ["ENSG00000141510"]}
        )
        assert len(data) >= 1
        cols = data.show_columns()
        assert "ensembl_gene_id" in cols


@pytest.mark.integration
class TestBioMartFetcherConvenience:
    """Integration tests for BioMart convenience methods."""

    def test_get_genes(self, fetcher):
        """Test get_genes method."""
        data = fetcher.get_genes(
            ids=["ENSG00000141510", "ENSG00000012048"],
            attributes=["ensembl_gene_id", "external_gene_name", "description"]
        )
        assert len(data) >= 2
        df = data.as_dataframe()
        gene_names = df["external_gene_name"].tolist()
        assert "TP53" in gene_names or "BRCA1" in gene_names

    def test_get_genes_by_name(self, fetcher):
        """Test get_genes_by_name method."""
        data = fetcher.get_genes_by_name(
            names=["TP53", "BRCA1"],
            attributes=["ensembl_gene_id", "external_gene_name"]
        )
        assert len(data) >= 2

    def test_get_genes_by_chromosome(self, fetcher):
        """Test get_genes_by_chromosome method."""
        data = fetcher.get_genes_by_chromosome(
            chromosome="17",
            start=7661779,
            end=7687550,
            attributes=["ensembl_gene_id", "external_gene_name", "start_position"]
        )
        assert len(data) >= 1
        # TP53 is on chromosome 17 in this region
        df = data.as_dataframe()
        assert "TP53" in df["external_gene_name"].values

    def test_get_transcripts(self, fetcher):
        """Test get_transcripts method."""
        data = fetcher.get_transcripts(
            gene_ids=["ENSG00000141510"],
        )
        assert len(data) >= 1
        df = data.as_dataframe()
        assert "ensembl_transcript_id" in df.columns

    def test_get_go_annotations(self, fetcher):
        """Test get_go_annotations method."""
        data = fetcher.get_go_annotations(
            gene_ids=["ENSG00000141510"]
        )
        assert len(data) >= 1
        df = data.as_dataframe()
        assert "go_id" in df.columns

    def test_get_homologs(self, fetcher):
        """Test get_homologs method."""
        data = fetcher.get_homologs(
            gene_ids=["ENSG00000141510"],
            target_species="mmusculus"
        )
        assert len(data) >= 1
        df = data.as_dataframe()
        assert "mmusculus_homolog_ensembl_gene" in df.columns

    def test_convert_ids(self, fetcher):
        """Test convert_ids method."""
        data = fetcher.convert_ids(
            ids=["ENSG00000141510", "ENSG00000012048"],
            from_type="ensembl_gene_id",
            to_type="external_gene_name"
        )
        assert len(data) >= 2
        df = data.as_dataframe()
        assert "ensembl_gene_id" in df.columns
        assert "external_gene_name" in df.columns


@pytest.mark.integration
@pytest.mark.slow
class TestBioMartFetcherBatch:
    """Integration tests for BioMart batch queries."""

    def test_batch_query_small(self, fetcher):
        """Test batch query with small list."""
        gene_ids = [f"ENSG{str(i).zfill(11)}" for i in range(141500, 141510)]
        # Most of these won't exist, but we're testing the batching
        data = fetcher.batch_query(
            filter_name="ensembl_gene_id",
            filter_values=gene_ids,
            attributes=["ensembl_gene_id", "external_gene_name"],
            batch_size=5,
            show_progress=False
        )
        # Just verify it runs without error
        assert isinstance(data, BioMartQueryData)

    def test_get_genes_auto_batch(self, fetcher):
        """Test get_genes with automatic batching."""
        # Create a list of gene IDs that exceeds batch size
        gene_ids = ["ENSG00000141510", "ENSG00000012048"]
        data = fetcher.get_genes(
            ids=gene_ids,
            batch_size=1  # Force batching
        )
        assert len(data) >= 2


@pytest.mark.integration
class TestBioMartFetcherDataFrame:
    """Integration tests for DataFrame output."""

    def test_pandas_output(self, fetcher):
        """Test pandas DataFrame output."""
        import pandas as pd
        data = fetcher.get_genes(
            ids=["ENSG00000141510"],
            attributes=["ensembl_gene_id", "external_gene_name"]
        )
        df = data.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1

    def test_polars_output(self, fetcher):
        """Test polars DataFrame output."""
        import polars as pl
        data = fetcher.get_genes(
            ids=["ENSG00000141510"],
            attributes=["ensembl_gene_id", "external_gene_name"]
        )
        df = data.as_dataframe(engine="polars")
        assert isinstance(df, pl.DataFrame)
        assert len(df) >= 1


@pytest.mark.integration
class TestBioMartFetcherArchive:
    """Integration tests for BioMart archive hosts."""

    def test_grch37_host(self):
        """Test GRCh37 archive host."""
        fetcher = BioMart_Fetcher(host=BioMartHost.grch37)
        marts = fetcher.list_marts()
        assert len(marts) > 0
