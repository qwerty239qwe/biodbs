"""Tests for BioMart data classes."""

import pytest
import pandas as pd
from biodbs.data.BioMart.data import (
    BioMartRegistryData,
    BioMartDatasetsData,
    BioMartConfigData,
    BioMartQueryData,
    BioMartDataManager,
    _xml_to_dataframe,
    _tsv_to_dataframe,
)


class TestXmlToDataframe:
    """Tests for _xml_to_dataframe helper function."""

    def test_simple_xml(self):
        """Test parsing simple XML."""
        xml = '<root><item name="a" value="1"/><item name="b" value="2"/></root>'
        df = _xml_to_dataframe(xml, tag="item")
        assert len(df) == 2
        assert "name" in df.columns
        assert "value" in df.columns

    def test_invalid_xml(self):
        """Test parsing invalid XML returns empty DataFrame."""
        df = _xml_to_dataframe("not xml")
        assert df.empty

    def test_empty_xml(self):
        """Test parsing XML with no matching elements."""
        xml = "<root></root>"
        df = _xml_to_dataframe(xml, tag="item")
        assert df.empty

    def test_xml_union_mode(self):
        """Test XML parsing with union mode."""
        xml = '<root><item a="1"/><item a="2" b="3"/></root>'
        df = _xml_to_dataframe(xml, tag="item", how="union")
        assert "a" in df.columns
        assert "b" in df.columns

    def test_xml_intersection_mode(self):
        """Test XML parsing with intersection mode."""
        xml = '<root><item a="1"/><item a="2" b="3"/></root>'
        df = _xml_to_dataframe(xml, tag="item", how="intersection")
        assert "a" in df.columns
        assert "b" not in df.columns


class TestTsvToDataframe:
    """Tests for _tsv_to_dataframe helper function."""

    def test_simple_tsv(self):
        """Test parsing simple TSV."""
        tsv = "col1\tcol2\na\tb\nc\td"
        df = _tsv_to_dataframe(tsv)
        assert len(df) == 2
        assert list(df.columns) == ["col1", "col2"]

    def test_tsv_with_columns(self):
        """Test parsing TSV with provided columns."""
        tsv = "a\tb\nc\td"
        df = _tsv_to_dataframe(tsv, columns=["col1", "col2"])
        assert len(df) == 2
        assert list(df.columns) == ["col1", "col2"]

    def test_empty_tsv(self):
        """Test parsing empty TSV."""
        df = _tsv_to_dataframe("")
        assert df.empty

    def test_tsv_whitespace_only(self):
        """Test parsing TSV with only whitespace."""
        df = _tsv_to_dataframe("   \n   ")
        assert df.empty

    def test_tsv_column_mismatch(self):
        """Test TSV with more columns than specified."""
        tsv = "a\tb\tc\nd\te\tf"
        df = _tsv_to_dataframe(tsv, columns=["col1", "col2"])
        assert len(df.columns) == 3
        assert "col_2" in df.columns


class TestBioMartRegistryData:
    """Tests for BioMartRegistryData."""

    @pytest.fixture
    def sample_registry_xml(self):
        """Sample registry XML."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <MartRegistry>
            <MartURLLocation name="ENSEMBL_MART_ENSEMBL" displayName="Genes" visible="1"/>
            <MartURLLocation name="ENSEMBL_MART_SNP" displayName="Variants" visible="1"/>
        </MartRegistry>
        """

    def test_parse_registry(self, sample_registry_xml):
        """Test parsing registry XML."""
        data = BioMartRegistryData(sample_registry_xml)
        assert len(data) == 2

    def test_marts_property(self, sample_registry_xml):
        """Test marts property."""
        data = BioMartRegistryData(sample_registry_xml)
        marts = data.marts
        assert "ENSEMBL_MART_ENSEMBL" in marts
        assert "ENSEMBL_MART_SNP" in marts

    def test_as_dataframe_pandas(self, sample_registry_xml):
        """Test as_dataframe with pandas."""
        data = BioMartRegistryData(sample_registry_xml)
        df = data.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert "name" in df.columns

    def test_as_dataframe_polars(self, sample_registry_xml):
        """Test as_dataframe with polars."""
        import polars as pl
        data = BioMartRegistryData(sample_registry_xml)
        df = data.as_dataframe(engine="polars")
        assert isinstance(df, pl.DataFrame)

    def test_as_dict(self, sample_registry_xml):
        """Test as_dict method."""
        data = BioMartRegistryData(sample_registry_xml)
        result = data.as_dict()
        assert isinstance(result, list)
        assert len(result) == 2

    def test_empty_registry(self):
        """Test empty registry."""
        data = BioMartRegistryData("<root></root>")
        assert len(data) == 0
        assert data.marts == []


class TestBioMartDatasetsData:
    """Tests for BioMartDatasetsData."""

    @pytest.fixture
    def sample_datasets_tsv(self):
        """Sample datasets TSV."""
        return """TableSet\thsapiens_gene_ensembl\tHuman genes (GRCh38.p14)\tYES\t\t1\t50000\tdefault\t0
TableSet\tmmusculus_gene_ensembl\tMouse genes (GRCm39)\tYES\t\t1\t45000\tdefault\t0
"""

    def test_parse_datasets(self, sample_datasets_tsv):
        """Test parsing datasets TSV."""
        data = BioMartDatasetsData(sample_datasets_tsv)
        assert len(data) == 2

    def test_datasets_property(self, sample_datasets_tsv):
        """Test datasets property."""
        data = BioMartDatasetsData(sample_datasets_tsv)
        datasets = data.datasets
        assert "hsapiens_gene_ensembl" in datasets
        assert "mmusculus_gene_ensembl" in datasets

    def test_search_contain(self, sample_datasets_tsv):
        """Test search with contain."""
        data = BioMartDatasetsData(sample_datasets_tsv)
        result = data.search(contain="human")
        assert len(result) == 1
        assert result.iloc[0]["dataset"] == "hsapiens_gene_ensembl"

    def test_search_contain_case_sensitive(self, sample_datasets_tsv):
        """Test search with contain case sensitive."""
        data = BioMartDatasetsData(sample_datasets_tsv)
        result = data.search(contain="Human", ignore_case=False)
        assert len(result) == 1

    def test_search_pattern(self, sample_datasets_tsv):
        """Test search with regex pattern."""
        data = BioMartDatasetsData(sample_datasets_tsv)
        result = data.search(pattern=r".*sapiens.*")
        assert len(result) == 1

    def test_as_dataframe(self, sample_datasets_tsv):
        """Test as_dataframe method."""
        data = BioMartDatasetsData(sample_datasets_tsv)
        df = data.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert "dataset" in df.columns
        assert "description" in df.columns

    def test_empty_datasets(self):
        """Test empty datasets."""
        data = BioMartDatasetsData("")
        assert len(data) == 0
        assert data.datasets == []


class TestBioMartConfigData:
    """Tests for BioMartConfigData."""

    @pytest.fixture
    def sample_config_xml(self):
        """Sample configuration XML."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <DatasetConfig>
            <FilterPage>
                <FilterDescription>
                    <Option internalName="ensembl_gene_id" displayName="Gene ID" description="Filter by gene ID"/>
                    <Option internalName="chromosome_name" displayName="Chromosome" description="Filter by chromosome"/>
                </FilterDescription>
            </FilterPage>
            <AttributePage internalName="feature_page" outFormats="TSV">
                <AttributeDescription internalName="ensembl_gene_id" displayName="Gene stable ID"/>
                <AttributeDescription internalName="external_gene_name" displayName="Gene name"/>
            </AttributePage>
        </DatasetConfig>
        """

    def test_parse_config(self, sample_config_xml):
        """Test parsing configuration XML."""
        data = BioMartConfigData(sample_config_xml)
        assert len(data) > 0

    def test_filter_names(self, sample_config_xml):
        """Test filter_names property."""
        data = BioMartConfigData(sample_config_xml)
        filters = data.filter_names
        assert "ensembl_gene_id" in filters
        assert "chromosome_name" in filters

    def test_attribute_names(self, sample_config_xml):
        """Test attribute_names property."""
        data = BioMartConfigData(sample_config_xml)
        attrs = data.attribute_names
        assert "ensembl_gene_id" in attrs
        assert "external_gene_name" in attrs

    def test_get_filters(self, sample_config_xml):
        """Test get_filters method."""
        data = BioMartConfigData(sample_config_xml)
        filters = data.get_filters()
        assert isinstance(filters, pd.DataFrame)
        assert "name" in filters.columns

    def test_get_filters_contain(self, sample_config_xml):
        """Test get_filters with contain filter."""
        data = BioMartConfigData(sample_config_xml)
        filters = data.get_filters(contain="gene")
        assert len(filters) >= 1

    def test_get_attributes(self, sample_config_xml):
        """Test get_attributes method."""
        data = BioMartConfigData(sample_config_xml)
        attrs = data.get_attributes()
        assert isinstance(attrs, pd.DataFrame)
        assert "name" in attrs.columns

    def test_get_attributes_pattern(self, sample_config_xml):
        """Test get_attributes with pattern filter."""
        data = BioMartConfigData(sample_config_xml)
        attrs = data.get_attributes(pattern=r"ensembl.*")
        assert len(attrs) >= 1

    def test_as_dict(self, sample_config_xml):
        """Test as_dict method."""
        data = BioMartConfigData(sample_config_xml)
        result = data.as_dict()
        assert "filters" in result
        assert "attributes" in result

    def test_empty_config(self):
        """Test empty configuration."""
        data = BioMartConfigData("<root></root>")
        assert len(data) == 0
        assert data.filter_names == []
        assert data.attribute_names == []


class TestBioMartQueryData:
    """Tests for BioMartQueryData."""

    @pytest.fixture
    def sample_query_result(self):
        """Sample query result TSV."""
        return """ensembl_gene_id\texternal_gene_name\tdescription
ENSG00000141510\tTP53\ttumor protein p53
ENSG00000012048\tBRCA1\tBRCA1 DNA repair associated
"""

    def test_parse_query_result(self, sample_query_result):
        """Test parsing query result."""
        data = BioMartQueryData(sample_query_result)
        assert len(data) == 2

    def test_parse_with_columns(self):
        """Test parsing with provided columns."""
        content = "ENSG00000141510\tTP53\nENSG00000012048\tBRCA1"
        data = BioMartQueryData(
            content,
            columns=["gene_id", "gene_name"],
            has_header=False
        )
        assert len(data) == 2
        assert "gene_id" in data.show_columns()

    def test_results_property(self, sample_query_result):
        """Test results property."""
        data = BioMartQueryData(sample_query_result)
        results = data.results
        assert isinstance(results, list)
        assert len(results) == 2

    def test_as_dataframe_pandas(self, sample_query_result):
        """Test as_dataframe with pandas."""
        data = BioMartQueryData(sample_query_result)
        df = data.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert "ensembl_gene_id" in df.columns

    def test_as_dataframe_polars(self, sample_query_result):
        """Test as_dataframe with polars."""
        import polars as pl
        data = BioMartQueryData(sample_query_result)
        df = data.as_dataframe(engine="polars")
        assert isinstance(df, pl.DataFrame)

    def test_as_dict(self, sample_query_result):
        """Test as_dict method."""
        data = BioMartQueryData(sample_query_result)
        result = data.as_dict()
        assert isinstance(result, list)
        assert len(result) == 2

    def test_as_dict_columns(self, sample_query_result):
        """Test as_dict with specific columns."""
        data = BioMartQueryData(sample_query_result)
        result = data.as_dict(columns=["ensembl_gene_id"])
        assert len(result[0].keys()) == 1

    def test_show_columns(self, sample_query_result):
        """Test show_columns method."""
        data = BioMartQueryData(sample_query_result)
        cols = data.show_columns()
        assert "ensembl_gene_id" in cols
        assert "external_gene_name" in cols
        assert "description" in cols

    def test_filter(self, sample_query_result):
        """Test filter method."""
        data = BioMartQueryData(sample_query_result)
        filtered = data.filter(external_gene_name="TP53")
        assert len(filtered) == 1
        assert filtered.as_dataframe().iloc[0]["external_gene_name"] == "TP53"

    def test_filter_callable(self, sample_query_result):
        """Test filter with callable."""
        data = BioMartQueryData(sample_query_result)
        filtered = data.filter(external_gene_name=lambda x: x.startswith("TP"))
        assert len(filtered) == 1

    def test_filter_unknown_column(self, sample_query_result):
        """Test filter with unknown column."""
        data = BioMartQueryData(sample_query_result)
        filtered = data.filter(unknown_col="value")
        assert len(filtered) == 2  # No filtering applied

    def test_drop_duplicates(self):
        """Test drop_duplicates method."""
        content = "col1\tcol2\na\tb\na\tb\nc\td"
        data = BioMartQueryData(content)
        deduplicated = data.drop_duplicates()
        assert len(deduplicated) == 2

    def test_iadd(self, sample_query_result):
        """Test __iadd__ method."""
        data1 = BioMartQueryData(sample_query_result)
        data2 = BioMartQueryData(sample_query_result)
        data1 += data2
        assert len(data1) == 4

    def test_has_error_false(self, sample_query_result):
        """Test has_error returns False for valid data."""
        data = BioMartQueryData(sample_query_result)
        assert data.has_error() is False

    def test_has_error_true(self):
        """Test has_error returns True for error response."""
        data = BioMartQueryData("Query ERROR: some error message")
        assert data.has_error() is True

    def test_get_error_message(self):
        """Test get_error_message method."""
        data = BioMartQueryData("Query ERROR: some error message")
        msg = data.get_error_message()
        assert "Query ERROR" in msg

    def test_get_error_message_none(self, sample_query_result):
        """Test get_error_message returns None for valid data."""
        data = BioMartQueryData(sample_query_result)
        assert data.get_error_message() is None

    def test_empty_content(self):
        """Test empty content."""
        data = BioMartQueryData("")
        assert len(data) == 0
        assert data.results == []

    def test_empty_with_columns(self):
        """Test empty content with columns."""
        data = BioMartQueryData("", columns=["col1", "col2"])
        assert len(data) == 0
        assert list(data.as_dataframe().columns) == ["col1", "col2"]


class TestBioMartDataManager:
    """Tests for BioMartDataManager."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temp directory for tests."""
        return tmp_path

    @pytest.fixture
    def manager(self, temp_dir):
        """Create BioMartDataManager instance."""
        return BioMartDataManager(storage_path=temp_dir)

    @pytest.fixture
    def sample_query_data(self):
        """Create sample query data."""
        content = """ensembl_gene_id\texternal_gene_name
ENSG00000141510\tTP53
ENSG00000012048\tBRCA1"""
        return BioMartQueryData(content)

    @pytest.fixture
    def sample_config_data(self):
        """Create sample config data."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <DatasetConfig>
            <FilterPage>
                <FilterDescription>
                    <Option internalName="ensembl_gene_id" displayName="Gene ID"/>
                </FilterDescription>
            </FilterPage>
            <AttributePage internalName="feature_page">
                <AttributeDescription internalName="ensembl_gene_id" displayName="Gene ID"/>
            </AttributePage>
        </DatasetConfig>
        """
        return BioMartConfigData(xml)

    def test_init(self, temp_dir):
        """Test manager initialization."""
        manager = BioMartDataManager(storage_path=temp_dir)
        assert manager is not None

    def test_save_query_data_csv(self, manager, sample_query_data):
        """Test saving query data as CSV."""
        path = manager.save_query_data(sample_query_data, "test_genes", fmt="csv")
        assert path.exists()
        assert path.suffix == ".csv"

    def test_save_query_data_json(self, manager, sample_query_data):
        """Test saving query data as JSON."""
        path = manager.save_query_data(sample_query_data, "test_genes", fmt="json")
        assert path.exists()
        assert path.suffix == ".json"

    def test_save_query_data_tsv(self, manager, sample_query_data):
        """Test saving query data as TSV."""
        path = manager.save_query_data(sample_query_data, "test_genes", fmt="tsv")
        assert path.exists()
        assert path.suffix == ".tsv"

    def test_save_query_data_parquet(self, manager, sample_query_data):
        """Test saving query data as Parquet."""
        pytest.importorskip("pyarrow")
        path = manager.save_query_data(sample_query_data, "test_genes", fmt="parquet")
        assert path.exists()
        assert path.suffix == ".parquet"

    def test_save_query_data_empty_error(self, manager):
        """Test saving empty query data raises error."""
        empty_data = BioMartQueryData("")
        with pytest.raises(ValueError, match="Cannot save empty data"):
            manager.save_query_data(empty_data, "test")

    def test_save_query_data_invalid_format(self, manager, sample_query_data):
        """Test saving with invalid format raises error."""
        with pytest.raises(ValueError, match="Unknown format"):
            manager.save_query_data(sample_query_data, "test", fmt="invalid")

    def test_save_config_data(self, manager, sample_config_data):
        """Test saving config data."""
        paths = manager.save_config_data(sample_config_data, "hsapiens")
        assert "filters" in paths
        assert "attributes" in paths
        assert paths["filters"].exists()
        assert paths["attributes"].exists()
