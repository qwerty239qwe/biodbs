"""Tests for BioMart data models."""

import pytest
from pydantic import ValidationError
from biodbs.data.BioMart._data_model import (
    BioMartHost,
    BioMartMart,
    BioMartDataset,
    BioMartQueryType,
    BioMartServerModel,
    BioMartMartModel,
    BioMartConfigModel,
    BioMartQueryModel,
    BioMartBatchQueryModel,
    COMMON_GENE_ATTRIBUTES,
    COMMON_SEQUENCE_ATTRIBUTES,
    COMMON_FILTERS,
    DEFAULT_QUERY_ATTRIBUTES,
)


class TestBioMartEnums:
    """Tests for BioMart enums."""

    def test_host_enum_values(self):
        """Test BioMartHost enum has expected values."""
        assert BioMartHost.main.value == "www.ensembl.org"
        assert BioMartHost.grch37.value == "grch37.ensembl.org"
        assert BioMartHost.plants.value == "plants.ensembl.org"
        # Test archive versions
        assert BioMartHost.ensembl_115.value == "sep2025.archive.ensembl.org"
        assert BioMartHost.ensembl_100.value == "apr2020.archive.ensembl.org"
        assert BioMartHost.ensembl_75.value == "feb2014.archive.ensembl.org"

    def test_mart_enum_values(self):
        """Test BioMartMart enum has expected values."""
        assert BioMartMart.ensembl.value == "ENSEMBL_MART_ENSEMBL"
        assert BioMartMart.mouse.value == "ENSEMBL_MART_MOUSE"
        assert BioMartMart.snp.value == "ENSEMBL_MART_SNP"

    def test_dataset_enum_values(self):
        """Test BioMartDataset enum has expected values."""
        assert BioMartDataset.hsapiens_gene.value == "hsapiens_gene_ensembl"
        assert BioMartDataset.mmusculus_gene.value == "mmusculus_gene_ensembl"

    def test_query_type_enum_values(self):
        """Test BioMartQueryType enum has expected values."""
        assert BioMartQueryType.registry.value == "registry"
        assert BioMartQueryType.datasets.value == "datasets"
        assert BioMartQueryType.configuration.value == "configuration"


class TestConstants:
    """Tests for BioMart constants."""

    def test_common_gene_attributes(self):
        """Test COMMON_GENE_ATTRIBUTES list."""
        assert "ensembl_gene_id" in COMMON_GENE_ATTRIBUTES
        assert "external_gene_name" in COMMON_GENE_ATTRIBUTES
        assert "chromosome_name" in COMMON_GENE_ATTRIBUTES

    def test_common_sequence_attributes(self):
        """Test COMMON_SEQUENCE_ATTRIBUTES list."""
        assert "ensembl_gene_id" in COMMON_SEQUENCE_ATTRIBUTES
        assert "cdna" in COMMON_SEQUENCE_ATTRIBUTES
        assert "peptide" in COMMON_SEQUENCE_ATTRIBUTES

    def test_common_filters(self):
        """Test COMMON_FILTERS list."""
        assert "ensembl_gene_id" in COMMON_FILTERS
        assert "chromosome_name" in COMMON_FILTERS

    def test_default_query_attributes(self):
        """Test DEFAULT_QUERY_ATTRIBUTES list."""
        assert "ensembl_gene_id" in DEFAULT_QUERY_ATTRIBUTES
        assert "external_gene_name" in DEFAULT_QUERY_ATTRIBUTES


class TestBioMartServerModel:
    """Tests for BioMartServerModel."""

    def test_default_host(self):
        """Test default host value."""
        model = BioMartServerModel()
        assert model.host == BioMartHost.main

    def test_custom_host_enum(self):
        """Test custom host with enum."""
        model = BioMartServerModel(host=BioMartHost.grch37)
        assert model.host == BioMartHost.grch37

    def test_custom_host_string(self):
        """Test custom host with string."""
        model = BioMartServerModel(host="www.ensembl.org")
        assert model.host == "www.ensembl.org"

    def test_build_url(self):
        """Test URL building."""
        model = BioMartServerModel(host=BioMartHost.main)
        url = model.build_url()
        assert url == "http://www.ensembl.org/biomart/martservice"

    def test_build_query_params(self):
        """Test query params building."""
        model = BioMartServerModel()
        params = model.build_query_params()
        assert params == {"type": "registry"}


class TestBioMartMartModel:
    """Tests for BioMartMartModel."""

    def test_default_values(self):
        """Test default values."""
        model = BioMartMartModel()
        assert model.host == BioMartHost.main
        assert model.mart == BioMartMart.ensembl

    def test_custom_mart_enum(self):
        """Test custom mart with enum."""
        model = BioMartMartModel(mart=BioMartMart.mouse)
        assert model.mart == BioMartMart.mouse

    def test_custom_mart_string(self):
        """Test custom mart with string."""
        model = BioMartMartModel(mart="ENSEMBL_MART_ENSEMBL")
        assert model.mart == "ENSEMBL_MART_ENSEMBL"

    def test_build_url(self):
        """Test URL building."""
        model = BioMartMartModel()
        url = model.build_url()
        assert "biomart/martservice" in url

    def test_build_query_params(self):
        """Test query params building."""
        model = BioMartMartModel(mart=BioMartMart.ensembl)
        params = model.build_query_params()
        assert params["type"] == "datasets"
        assert params["mart"] == "ENSEMBL_MART_ENSEMBL"


class TestBioMartConfigModel:
    """Tests for BioMartConfigModel."""

    def test_default_values(self):
        """Test default values."""
        model = BioMartConfigModel()
        assert model.host == BioMartHost.main
        assert model.dataset == BioMartDataset.hsapiens_gene

    def test_custom_dataset_enum(self):
        """Test custom dataset with enum."""
        model = BioMartConfigModel(dataset=BioMartDataset.mmusculus_gene)
        assert model.dataset == BioMartDataset.mmusculus_gene

    def test_custom_dataset_string(self):
        """Test custom dataset with string."""
        model = BioMartConfigModel(dataset="custom_dataset")
        assert model.dataset == "custom_dataset"

    def test_build_query_params(self):
        """Test query params building."""
        model = BioMartConfigModel(dataset="hsapiens_gene_ensembl")
        params = model.build_query_params()
        assert params["type"] == "configuration"
        assert params["dataset"] == "hsapiens_gene_ensembl"


class TestBioMartQueryModel:
    """Tests for BioMartQueryModel."""

    def test_required_attributes(self):
        """Test that attributes are required."""
        with pytest.raises(ValidationError):
            BioMartQueryModel()

    def test_empty_attributes_invalid(self):
        """Test that empty attributes list is invalid."""
        with pytest.raises(ValidationError):
            BioMartQueryModel(attributes=[])

    def test_valid_query(self):
        """Test valid query model."""
        model = BioMartQueryModel(
            attributes=["ensembl_gene_id", "external_gene_name"]
        )
        assert model.dataset == BioMartDataset.hsapiens_gene
        assert len(model.attributes) == 2
        assert model.unique_rows is True
        assert model.header is True

    def test_with_filters(self):
        """Test query with filters."""
        model = BioMartQueryModel(
            attributes=["ensembl_gene_id"],
            filters={"chromosome_name": "17"}
        )
        assert model.filters == {"chromosome_name": "17"}

    def test_with_list_filter(self):
        """Test query with list filter."""
        model = BioMartQueryModel(
            attributes=["ensembl_gene_id"],
            filters={"ensembl_gene_id": ["ENSG00000141510", "ENSG00000012048"]}
        )
        assert len(model.filters["ensembl_gene_id"]) == 2

    def test_build_xml_query(self):
        """Test XML query building."""
        model = BioMartQueryModel(
            dataset="hsapiens_gene_ensembl",
            attributes=["ensembl_gene_id", "external_gene_name"],
            filters={"chromosome_name": "17"}
        )
        xml = model.build_xml_query()
        assert "<Query" in xml
        assert "<Dataset" in xml
        assert 'name="hsapiens_gene_ensembl"' in xml
        assert "<Filter" in xml
        assert "<Attribute" in xml
        assert 'name="ensembl_gene_id"' in xml
        assert 'name="external_gene_name"' in xml
        assert 'name="chromosome_name"' in xml

    def test_build_xml_query_list_filter(self):
        """Test XML query with list filter."""
        model = BioMartQueryModel(
            attributes=["ensembl_gene_id"],
            filters={"ensembl_gene_id": ["ENSG1", "ENSG2"]}
        )
        xml = model.build_xml_query()
        assert 'value="ENSG1,ENSG2"' in xml

    def test_build_xml_query_unique_rows(self):
        """Test XML query with uniqueRows setting."""
        model = BioMartQueryModel(
            attributes=["ensembl_gene_id"],
            unique_rows=False
        )
        xml = model.build_xml_query()
        assert 'uniqueRows="0"' in xml

    def test_build_xml_query_no_header(self):
        """Test XML query with header=False."""
        model = BioMartQueryModel(
            attributes=["ensembl_gene_id"],
            header=False
        )
        xml = model.build_xml_query()
        assert 'header="0"' in xml

    def test_build_query_params(self):
        """Test query params includes XML."""
        model = BioMartQueryModel(
            attributes=["ensembl_gene_id"]
        )
        params = model.build_query_params()
        assert "query" in params
        assert "<Query" in params["query"]


class TestBioMartBatchQueryModel:
    """Tests for BioMartBatchQueryModel."""

    def test_required_filter_values(self):
        """Test that filter_values are required."""
        with pytest.raises(ValidationError):
            BioMartBatchQueryModel(
                attributes=["ensembl_gene_id"],
                filter_name="ensembl_gene_id",
            )

    def test_empty_filter_values_invalid(self):
        """Test that empty filter_values is invalid."""
        with pytest.raises(ValidationError):
            BioMartBatchQueryModel(
                attributes=["ensembl_gene_id"],
                filter_name="ensembl_gene_id",
                filter_values=[]
            )

    def test_valid_batch_model(self):
        """Test valid batch model."""
        model = BioMartBatchQueryModel(
            attributes=["ensembl_gene_id"],
            filter_name="ensembl_gene_id",
            filter_values=["ENSG1", "ENSG2", "ENSG3"],
            batch_size=2
        )
        assert model.batch_size == 2
        assert len(model.filter_values) == 3

    def test_get_batches(self):
        """Test batch splitting."""
        model = BioMartBatchQueryModel(
            attributes=["ensembl_gene_id"],
            filter_name="ensembl_gene_id",
            filter_values=["A", "B", "C", "D", "E"],
            batch_size=2
        )
        batches = model.get_batches()
        assert len(batches) == 3
        assert batches[0] == ["A", "B"]
        assert batches[1] == ["C", "D"]
        assert batches[2] == ["E"]

    def test_get_batches_exact_fit(self):
        """Test batch splitting with exact fit."""
        model = BioMartBatchQueryModel(
            attributes=["ensembl_gene_id"],
            filter_name="ensembl_gene_id",
            filter_values=["A", "B", "C", "D"],
            batch_size=2
        )
        batches = model.get_batches()
        assert len(batches) == 2

    def test_build_query_for_batch(self):
        """Test building query for a batch."""
        model = BioMartBatchQueryModel(
            attributes=["ensembl_gene_id", "external_gene_name"],
            filter_name="ensembl_gene_id",
            filter_values=["A", "B", "C"],
            batch_size=2
        )
        batch = ["A", "B"]
        query_model = model.build_query_for_batch(batch)

        assert isinstance(query_model, BioMartQueryModel)
        assert query_model.attributes == ["ensembl_gene_id", "external_gene_name"]
        assert query_model.filters == {"ensembl_gene_id": ["A", "B"]}
