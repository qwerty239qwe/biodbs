"""Tests for Human Protein Atlas data models."""

import pytest
from biodbs.data.HPA._data_model import (
    HPAEntryModel,
    HPASearchModel,
    HPASearchDownloadModel,
    HPABulkDownloadModel,
    HPAFormat,
    HPASearchFormat,
    HPACompress,
    HPA_COLUMNS,
    DEFAULT_GENE_COLUMNS,
    DEFAULT_EXPRESSION_COLUMNS,
    DEFAULT_SUBCELLULAR_COLUMNS,
    DEFAULT_PATHOLOGY_COLUMNS,
)
from pydantic import ValidationError


# =============================================================================
# HPAEntryModel Tests
# =============================================================================

class TestHPAEntryModel:
    """Tests for HPAEntryModel validation and URL building."""

    def test_valid_ensembl_id_json(self):
        """Test valid Ensembl ID with JSON format."""
        model = HPAEntryModel(
            ensembl_id="ENSG00000141510",
            format="json"
        )
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/ENSG00000141510.json"

    def test_valid_ensembl_id_tsv(self):
        """Test valid Ensembl ID with TSV format."""
        model = HPAEntryModel(
            ensembl_id="ENSG00000134057",
            format="tsv"
        )
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/ENSG00000134057.tsv"

    def test_valid_ensembl_id_xml(self):
        """Test valid Ensembl ID with XML format."""
        model = HPAEntryModel(
            ensembl_id="ENSG00000012048",
            format="xml"
        )
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/ENSG00000012048.xml"

    def test_invalid_ensembl_id_format(self):
        """Test invalid Ensembl ID format raises error."""
        with pytest.raises(ValidationError):
            HPAEntryModel(
                ensembl_id="ENSG1234",  # Wrong number of digits
                format="json"
            )

    def test_invalid_ensembl_id_prefix(self):
        """Test Ensembl ID without ENSG prefix raises error."""
        with pytest.raises(ValidationError):
            HPAEntryModel(
                ensembl_id="00000141510",  # Missing ENSG prefix
                format="json"
            )

    def test_default_format_is_json(self):
        """Test default format is JSON."""
        model = HPAEntryModel(ensembl_id="ENSG00000141510")
        assert model.format == HPAFormat.JSON


# =============================================================================
# HPASearchModel Tests
# =============================================================================

class TestHPASearchModel:
    """Tests for HPASearchModel validation and URL building."""

    def test_basic_search(self):
        """Test basic search query."""
        model = HPASearchModel(
            query="TP53",
            format="json",
            compress="no"
        )
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/search/TP53"
        params = model.build_query_params()
        assert params["format"] == "json"
        assert params["compress"] == "no"

    def test_search_with_compression(self):
        """Test search with compression enabled."""
        model = HPASearchModel(
            query="kinase",
            format="tsv",
            compress="yes"
        )
        params = model.build_query_params()
        assert params["compress"] == "yes"

    def test_empty_query_raises_error(self):
        """Test empty query raises error."""
        with pytest.raises(ValidationError):
            HPASearchModel(
                query="",
                format="json"
            )

    def test_whitespace_query_raises_error(self):
        """Test whitespace-only query raises error."""
        with pytest.raises(ValidationError):
            HPASearchModel(
                query="   ",
                format="json"
            )


# =============================================================================
# HPASearchDownloadModel Tests
# =============================================================================

class TestHPASearchDownloadModel:
    """Tests for HPASearchDownloadModel validation and URL building."""

    def test_basic_search_download(self):
        """Test basic search download API."""
        model = HPASearchDownloadModel(
            search="TP53",
            format="json",
            columns=["g", "eg", "gd"]
        )
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/api/search_download.php"
        params = model.build_query_params()
        assert params["search"] == "TP53"
        assert params["format"] == "json"
        assert params["columns"] == "g,eg,gd"
        assert params["compress"] == "no"

    def test_multiple_columns(self):
        """Test multiple columns."""
        model = HPASearchDownloadModel(
            search="BRCA1",
            format="tsv",
            columns=["g", "gs", "eg", "gd", "scl", "pc"]
        )
        params = model.build_query_params()
        assert params["columns"] == "g,gs,eg,gd,scl,pc"

    def test_empty_search_raises_error(self):
        """Test empty search raises error."""
        with pytest.raises(ValidationError):
            HPASearchDownloadModel(
                search="",
                format="json",
                columns=["g"]
            )

    def test_empty_columns_raises_error(self):
        """Test empty columns list raises error."""
        with pytest.raises(ValidationError):
            HPASearchDownloadModel(
                search="TP53",
                format="json",
                columns=[]
            )

    def test_compression_option(self):
        """Test compression option."""
        model = HPASearchDownloadModel(
            search="kinase",
            format="json",
            columns=["g", "eg"],
            compress="yes"
        )
        params = model.build_query_params()
        assert params["compress"] == "yes"


# =============================================================================
# HPABulkDownloadModel Tests
# =============================================================================

class TestHPABulkDownloadModel:
    """Tests for HPABulkDownloadModel validation and URL building."""

    def test_json_bulk_download(self):
        """Test JSON bulk download URL."""
        model = HPABulkDownloadModel(file_type="json")
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/download/proteinatlas.json.gz"

    def test_tsv_bulk_download(self):
        """Test TSV bulk download URL."""
        model = HPABulkDownloadModel(file_type="tsv")
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/download/proteinatlas.tsv.zip"

    def test_xml_bulk_download(self):
        """Test XML bulk download URL."""
        model = HPABulkDownloadModel(file_type="xml")
        url = model.build_url()
        assert url == "https://www.proteinatlas.org/download/proteinatlas.xml.gz"

    def test_versioned_download(self):
        """Test versioned download URL."""
        model = HPABulkDownloadModel(file_type="json", version="24")
        url = model.build_url()
        assert url == "https://v24.proteinatlas.org/download/proteinatlas.json.gz"

    def test_invalid_file_type_raises_error(self):
        """Test invalid file type raises error."""
        with pytest.raises(ValidationError):
            HPABulkDownloadModel(file_type="csv")


# =============================================================================
# Column Constants Tests
# =============================================================================

class TestColumnConstants:
    """Tests for HPA column constants."""

    def test_hpa_columns_dict(self):
        """Test HPA_COLUMNS dictionary."""
        assert "g" in HPA_COLUMNS
        assert "eg" in HPA_COLUMNS
        assert HPA_COLUMNS["g"] == "Gene"
        assert HPA_COLUMNS["eg"] == "Ensembl"

    def test_default_gene_columns(self):
        """Test default gene columns."""
        assert "g" in DEFAULT_GENE_COLUMNS
        assert "eg" in DEFAULT_GENE_COLUMNS

    def test_default_expression_columns(self):
        """Test default expression columns."""
        assert "g" in DEFAULT_EXPRESSION_COLUMNS
        assert "eg" in DEFAULT_EXPRESSION_COLUMNS

    def test_default_subcellular_columns(self):
        """Test default subcellular columns."""
        assert "g" in DEFAULT_SUBCELLULAR_COLUMNS
        assert "scl" in DEFAULT_SUBCELLULAR_COLUMNS

    def test_default_pathology_columns(self):
        """Test default pathology columns."""
        assert "g" in DEFAULT_PATHOLOGY_COLUMNS
        assert "eg" in DEFAULT_PATHOLOGY_COLUMNS
