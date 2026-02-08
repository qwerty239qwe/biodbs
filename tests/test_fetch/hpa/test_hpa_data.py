"""Tests for Human Protein Atlas fetched data classes."""

import pytest
from biodbs.data.HPA.data import HPAFetchedData


class TestHPAFetchedData:
    """Tests for HPAFetchedData parsing."""

    def test_json_list_format(self):
        """Test JSON list response format."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
            {"Gene": "BRCA1", "Ensembl": "ENSG00000012048"},
        ]
        data = HPAFetchedData(content, format="json", query_type="search_download")
        assert len(data.results) == 2
        assert data.results[0]["Gene"] == "TP53"

    def test_single_dict_format(self):
        """Test single dict response format."""
        content = {"Gene": "TP53", "Ensembl": "ENSG00000141510"}
        data = HPAFetchedData(content, format="json", query_type="entry")
        assert len(data.results) == 1
        assert data.results[0]["Gene"] == "TP53"

    def test_get_ensembl_ids(self):
        """Test Ensembl ID extraction."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
            {"Gene": "BRCA1", "Ensembl": "ENSG00000012048"},
        ]
        data = HPAFetchedData(content)
        ids = data.get_ensembl_ids()
        assert "ENSG00000141510" in ids
        assert "ENSG00000012048" in ids

    def test_get_ensembl_ids_with_eg_key(self):
        """Test Ensembl ID extraction with 'eg' key."""
        content = [
            {"Gene": "TP53", "eg": "ENSG00000141510"},
        ]
        data = HPAFetchedData(content)
        ids = data.get_ensembl_ids()
        assert "ENSG00000141510" in ids

    def test_get_gene_names(self):
        """Test gene name extraction."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
            {"Gene": "BRCA1", "Ensembl": "ENSG00000012048"},
        ]
        data = HPAFetchedData(content)
        names = data.get_gene_names()
        assert "TP53" in names
        assert "BRCA1" in names

    def test_get_gene_names_with_g_key(self):
        """Test gene name extraction with 'g' key."""
        content = [
            {"g": "TP53", "eg": "ENSG00000141510"},
        ]
        data = HPAFetchedData(content)
        names = data.get_gene_names()
        assert "TP53" in names

    def test_as_dataframe_pandas(self):
        """Test DataFrame conversion with pandas."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
            {"Gene": "BRCA1", "Ensembl": "ENSG00000012048"},
        ]
        data = HPAFetchedData(content)
        df = data.as_dataframe(engine="pandas")
        assert len(df) == 2
        assert "Gene" in df.columns
        assert "Ensembl" in df.columns

    def test_as_dataframe_polars(self):
        """Test DataFrame conversion with polars."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
        ]
        data = HPAFetchedData(content)
        df = data.as_dataframe(engine="polars")
        assert len(df) == 1

    def test_as_dataframe_empty(self):
        """Test DataFrame conversion with empty data."""
        data = HPAFetchedData([])
        df = data.as_dataframe(engine="pandas")
        assert len(df) == 0

    def test_iadd(self):
        """Test += operator for combining results."""
        data1 = HPAFetchedData([{"Gene": "TP53"}])
        data2 = HPAFetchedData([{"Gene": "BRCA1"}])
        data1 += data2
        assert len(data1.results) == 2

    def test_len(self):
        """Test __len__ method."""
        content = [
            {"Gene": "TP53"},
            {"Gene": "BRCA1"},
            {"Gene": "EGFR"},
        ]
        data = HPAFetchedData(content)
        assert len(data) == 3

    def test_filter(self):
        """Test filtering results."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
            {"Gene": "BRCA1", "Ensembl": "ENSG00000012048"},
        ]
        data = HPAFetchedData(content)
        filtered = data.filter(Gene="TP53")
        assert len(filtered.results) == 1
        assert filtered.results[0]["Gene"] == "TP53"

    def test_filter_with_callable(self):
        """Test filtering with callable."""
        content = [
            {"Gene": "TP53", "Score": 10},
            {"Gene": "BRCA1", "Score": 5},
        ]
        data = HPAFetchedData(content)
        filtered = data.filter(Score=lambda x: x > 7)
        assert len(filtered.results) == 1
        assert filtered.results[0]["Gene"] == "TP53"

    def test_filter_no_match(self):
        """Test filtering with no matches."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
        ]
        data = HPAFetchedData(content)
        filtered = data.filter(Gene="NOTEXIST")
        assert len(filtered.results) == 0

    def test_show_columns(self):
        """Test showing available columns."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510", "Score": 10},
        ]
        data = HPAFetchedData(content)
        columns = data.show_columns()
        assert "Gene" in columns
        assert "Ensembl" in columns
        assert "Score" in columns

    def test_show_columns_nested(self):
        """Test showing columns with nested structure."""
        content = [
            {"Gene": "TP53", "Data": {"Value": 10, "Unit": "nM"}},
        ]
        data = HPAFetchedData(content)
        columns = data.show_columns()
        assert "Gene" in columns
        assert "Data.Value" in columns
        assert "Data.Unit" in columns

    def test_format_results(self):
        """Test formatting results with specific columns."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510", "Score": 10},
        ]
        data = HPAFetchedData(content)
        formatted = data.format_results(["Gene", "Score"])
        assert formatted[0] == {"Gene": "TP53", "Score": 10}

    def test_format_results_invalid_column(self):
        """Test format_results with invalid column raises error."""
        content = [
            {"Gene": "TP53"},
        ]
        data = HPAFetchedData(content)
        with pytest.raises(ValueError):
            data.format_results(["InvalidColumn"])

    def test_as_dict(self):
        """Test as_dict method."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
        ]
        data = HPAFetchedData(content)
        result = data.as_dict()
        assert result == content

    def test_as_dict_with_columns(self):
        """Test as_dict with specific columns."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510", "Score": 10},
        ]
        data = HPAFetchedData(content)
        result = data.as_dict(columns=["Gene"])
        assert result == [{"Gene": "TP53"}]

    def test_subcellular_location_extraction(self):
        """Test subcellular location data extraction."""
        content = [
            {
                "Gene": "TP53",
                "Ensembl": "ENSG00000141510",
                "Subcellular location": ["Nucleoplasm", "Cytosol"],
                "Subcellular main location": ["Nucleoplasm"],
            },
        ]
        data = HPAFetchedData(content)
        locations = data.get_subcellular_location()
        assert len(locations) == 1
        assert locations[0]["Subcellular main location"] == ["Nucleoplasm"]

    def test_subcellular_location_no_data(self):
        """Test subcellular location extraction with no data."""
        content = [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510"},
        ]
        data = HPAFetchedData(content)
        locations = data.get_subcellular_location()
        assert len(locations) == 0

    def test_expression_data_extraction(self):
        """Test expression data extraction."""
        content = [
            {
                "Gene": "TP53",
                "Ensembl": "ENSG00000141510",
                "rna_liver": 10.5,
                "rna_brain": 5.2,
            },
        ]
        data = HPAFetchedData(content)
        expression = data.get_expression_data()
        assert len(expression) == 1
        assert expression[0]["rna_liver"] == 10.5

    def test_expression_data_filter_by_tissue(self):
        """Test expression data extraction filtered by tissue."""
        content = [
            {
                "Gene": "TP53",
                "Ensembl": "ENSG00000141510",
                "rna_liver": 10.5,
                "rna_brain": 5.2,
            },
        ]
        data = HPAFetchedData(content)
        expression = data.get_expression_data(tissue="liver")
        assert len(expression) == 1
        assert "rna_liver" in expression[0]
        assert "rna_brain" not in expression[0]

    def test_has_error(self):
        """Test error detection."""
        content = {"error": "Invalid query"}
        data = HPAFetchedData(content)
        assert data.has_error()
        assert "Invalid query" in data.get_error_message()

    def test_has_error_capital(self):
        """Test error detection with capital Error key."""
        content = {"Error": "Something went wrong"}
        data = HPAFetchedData(content)
        assert data.has_error()
        assert "Something went wrong" in data.get_error_message()

    def test_no_error(self):
        """Test no error condition."""
        content = [{"Gene": "TP53"}]
        data = HPAFetchedData(content)
        assert not data.has_error()
        assert data.get_error_message() is None

    def test_empty_content(self):
        """Test handling empty content."""
        data = HPAFetchedData([])
        assert len(data.results) == 0

    def test_tsv_parsing(self):
        """Test TSV content parsing."""
        content = "Gene\tEnsembl\nTP53\tENSG00000141510\nBRCA1\tENSG00000012048"
        data = HPAFetchedData(content, format="tsv")
        assert len(data.results) == 2
        assert data.results[0]["Gene"] == "TP53"
        assert data.results[1]["Gene"] == "BRCA1"

    def test_tsv_parsing_empty(self):
        """Test TSV parsing with empty content."""
        content = ""
        data = HPAFetchedData(content, format="tsv")
        assert len(data.results) == 0

    def test_tsv_parsing_header_only(self):
        """Test TSV parsing with header only."""
        content = "Gene\tEnsembl"
        data = HPAFetchedData(content, format="tsv")
        assert len(data.results) == 0

    def test_binary_content(self):
        """Test binary content handling."""
        content = b"binary data"
        data = HPAFetchedData(content, format="xml")
        assert data.binary_data == content
        assert len(data.results) == 0

    def test_format_attribute(self):
        """Test format attribute is set correctly."""
        data = HPAFetchedData([], format="json")
        assert data.format == "json"

    def test_query_type_attribute(self):
        """Test query_type attribute is set correctly."""
        data = HPAFetchedData([], query_type="entry")
        assert data.query_type == "entry"

    def test_raw_content_preserved(self):
        """Test raw content is preserved."""
        content = [{"Gene": "TP53"}]
        data = HPAFetchedData(content)
        assert data.raw_content == content
