"""Tests for PubChem fetched data classes (PUG REST and PUG View)."""

import pytest
from biodbs.data.PubChem.data import PUGRestFetchedData, PUGViewFetchedData


# =============================================================================
# PUGRestFetchedData Tests
# =============================================================================

class TestPUGRestFetchedData:
    """Tests for PUGRestFetchedData parsing."""

    def test_pc_compounds_format(self):
        """Test PC_Compounds response format."""
        content = {"PC_Compounds": [{"id": {"id": {"cid": 2244}}}]}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 1

    def test_pc_compounds_multiple(self):
        """Test PC_Compounds with multiple compounds."""
        content = {
            "PC_Compounds": [
                {"id": {"id": {"cid": 2244}}},
                {"id": {"id": {"cid": 3672}}},
            ]
        }
        data = PUGRestFetchedData(content)
        assert len(data.results) == 2

    def test_property_table_format(self):
        """Test PropertyTable response format."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularFormula": "C9H8O4"},
                    {"CID": 3672, "MolecularFormula": "C10H13N5O4"},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        assert len(data.results) == 2
        assert data.results[0]["CID"] == 2244

    def test_property_table_empty(self):
        """Test PropertyTable with empty properties."""
        content = {"PropertyTable": {"Properties": []}}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 0

    def test_information_list_format(self):
        """Test InformationList response format."""
        content = {
            "InformationList": {
                "Information": [
                    {"CID": 2244, "Synonym": ["aspirin", "acetylsalicylic acid"]}
                ]
            }
        }
        data = PUGRestFetchedData(content)
        assert len(data.results) == 1

    def test_identifier_list_cid_format(self):
        """Test IdentifierList CID response format."""
        content = {"IdentifierList": {"CID": [2244, 3672, 5988]}}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 3
        assert data.results[0] == {"CID": 2244}

    def test_identifier_list_sid_format(self):
        """Test IdentifierList SID response format."""
        content = {"IdentifierList": {"SID": [123, 456]}}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 2
        assert data.results[0] == {"SID": 123}

    def test_identifier_list_aid_format(self):
        """Test IdentifierList AID response format."""
        content = {"IdentifierList": {"AID": [1000, 2000]}}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 2
        assert data.results[0] == {"AID": 1000}

    def test_pc_assay_container_format(self):
        """Test PC_AssayContainer response format."""
        content = {"PC_AssayContainer": [{"assay": {"descr": {"aid": {"id": 1000}}}}]}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 1

    def test_table_format(self):
        """Test Table response format."""
        content = {
            "Table": {
                "Columns": {"Column": ["CID", "Name"]},
                "Row": [
                    {"Cell": [2244, "Aspirin"]},
                    {"Cell": [3672, "Adenosine"]},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        assert len(data.results) == 2
        assert data.results[0]["CID"] == 2244
        assert data.results[0]["Name"] == "Aspirin"

    def test_get_cids(self):
        """Test CID extraction."""
        content = {"IdentifierList": {"CID": [2244, 3672]}}
        data = PUGRestFetchedData(content)
        cids = data.get_cids()
        assert cids == [2244, 3672]

    def test_get_cids_from_pc_compounds(self):
        """Test CID extraction from PC_Compounds format."""
        content = {
            "PC_Compounds": [
                {"id": {"id": {"cid": 2244}}},
                {"id": {"id": {"cid": 3672}}},
            ]
        }
        data = PUGRestFetchedData(content)
        cids = data.get_cids()
        assert 2244 in cids
        assert 3672 in cids

    def test_get_sids(self):
        """Test SID extraction."""
        content = {"IdentifierList": {"SID": [123, 456]}}
        data = PUGRestFetchedData(content)
        sids = data.get_sids()
        assert sids == [123, 456]

    def test_binary_data(self):
        """Test binary content handling."""
        content = b"\x89PNG\r\n\x1a\n..."
        data = PUGRestFetchedData(content)
        assert data.binary_data == content
        assert len(data.results) == 0

    def test_has_error(self):
        """Test error detection."""
        content = {"Fault": {"Message": "Invalid CID"}}
        data = PUGRestFetchedData(content)
        assert data.has_error()
        assert "Invalid CID" in data.get_error_message()

    def test_no_error(self):
        """Test no error condition."""
        content = {"IdentifierList": {"CID": [2244]}}
        data = PUGRestFetchedData(content)
        assert not data.has_error()
        assert data.get_error_message() is None

    def test_waiting_response(self):
        """Test Waiting response returns empty results."""
        content = {"Waiting": {"ListKey": 12345}}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 0

    def test_as_dataframe_pandas(self):
        """Test DataFrame conversion with pandas."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularWeight": 180.16},
                    {"CID": 3672, "MolecularWeight": 267.24},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        df = data.as_dataframe(engine="pandas")
        assert len(df) == 2
        assert list(df.columns) == ["CID", "MolecularWeight"]

    def test_as_dataframe_polars(self):
        """Test DataFrame conversion with polars."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularWeight": 180.16},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        df = data.as_dataframe(engine="polars")
        assert len(df) == 1

    def test_as_dataframe_empty(self):
        """Test DataFrame conversion with empty data."""
        content = {"PropertyTable": {"Properties": []}}
        data = PUGRestFetchedData(content)
        df = data.as_dataframe(engine="pandas")
        assert len(df) == 0

    def test_iadd(self):
        """Test += operator for combining results."""
        data1 = PUGRestFetchedData({"IdentifierList": {"CID": [1, 2]}})
        data2 = PUGRestFetchedData({"IdentifierList": {"CID": [3, 4]}})
        data1 += data2
        assert len(data1.results) == 4

    def test_len(self):
        """Test __len__ method."""
        content = {"IdentifierList": {"CID": [1, 2, 3]}}
        data = PUGRestFetchedData(content)
        assert len(data) == 3

    def test_filter(self):
        """Test filtering results."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularWeight": 180.16},
                    {"CID": 3672, "MolecularWeight": 267.24},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        filtered = data.filter(CID=2244)
        assert len(filtered.results) == 1
        assert filtered.results[0]["CID"] == 2244

    def test_filter_with_callable(self):
        """Test filtering with callable."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularWeight": 180.16},
                    {"CID": 3672, "MolecularWeight": 267.24},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        filtered = data.filter(MolecularWeight=lambda x: x > 200)
        assert len(filtered.results) == 1
        assert filtered.results[0]["CID"] == 3672

    def test_filter_no_match(self):
        """Test filtering with no matches."""
        content = {"IdentifierList": {"CID": [2244, 3672]}}
        data = PUGRestFetchedData(content)
        filtered = data.filter(CID=9999)
        assert len(filtered.results) == 0

    def test_show_columns(self):
        """Test showing available columns."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularWeight": 180.16, "Formula": "C9H8O4"},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        columns = data.show_columns()
        assert "CID" in columns
        assert "MolecularWeight" in columns
        assert "Formula" in columns

    def test_show_columns_nested(self):
        """Test showing columns with nested structure."""
        content = {"PC_Compounds": [{"id": {"id": {"cid": 2244}}}]}
        data = PUGRestFetchedData(content)
        columns = data.show_columns()
        assert "id.id.cid" in columns

    def test_format_results(self):
        """Test formatting results with specific columns."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularWeight": 180.16, "Formula": "C9H8O4"},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        formatted = data.format_results(["CID", "Formula"])
        assert formatted[0] == {"CID": 2244, "Formula": "C9H8O4"}

    def test_format_results_invalid_column(self):
        """Test format_results with invalid column raises error."""
        content = {"PropertyTable": {"Properties": [{"CID": 2244}]}}
        data = PUGRestFetchedData(content)
        with pytest.raises(ValueError):
            data.format_results(["InvalidColumn"])

    def test_as_dict(self):
        """Test as_dict method."""
        content = {"IdentifierList": {"CID": [2244]}}
        data = PUGRestFetchedData(content)
        result = data.as_dict()
        assert result == [{"CID": 2244}]

    def test_as_dict_with_columns(self):
        """Test as_dict with specific columns."""
        content = {
            "PropertyTable": {
                "Properties": [
                    {"CID": 2244, "MolecularWeight": 180.16},
                ]
            }
        }
        data = PUGRestFetchedData(content)
        result = data.as_dict(columns=["CID"])
        assert result == [{"CID": 2244}]

    def test_domain_attribute(self):
        """Test domain attribute is set correctly."""
        content = {"IdentifierList": {"CID": [2244]}}
        data = PUGRestFetchedData(content, domain="compound")
        assert data.domain == "compound"

    def test_operation_attribute(self):
        """Test operation attribute is set correctly."""
        content = {"IdentifierList": {"CID": [2244]}}
        data = PUGRestFetchedData(content, operation="cids")
        assert data.operation == "cids"

    def test_raw_content_preserved(self):
        """Test raw content is preserved."""
        content = {"IdentifierList": {"CID": [2244]}}
        data = PUGRestFetchedData(content)
        assert data.raw_content == content

    def test_empty_dict_content(self):
        """Test empty dict content."""
        data = PUGRestFetchedData({})
        assert len(data.results) == 0

    def test_single_wrapped_dict(self):
        """Test single dict wrapped in response."""
        content = {"Compound": {"CID": 2244, "Name": "Aspirin"}}
        data = PUGRestFetchedData(content)
        assert len(data.results) == 1


# =============================================================================
# PUGViewFetchedData Tests
# =============================================================================

class TestPUGViewFetchedData:
    """Tests for PUGViewFetchedData parsing."""

    def test_record_parsing(self):
        """Test basic record parsing."""
        content = {
            "Record": {
                "RecordType": "CID",
                "RecordNumber": 2244,
                "Section": [
                    {"TOCHeading": "Names and Identifiers", "Information": []},
                    {"TOCHeading": "Safety and Hazards", "Section": []},
                ]
            }
        }
        data = PUGViewFetchedData(content)
        assert data.record_id == 2244
        assert len(data.sections) == 2

    def test_get_section(self):
        """Test getting a specific section."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [
                    {"TOCHeading": "Names and Identifiers", "Information": [{"Name": "Test"}]},
                ]
            }
        }
        data = PUGViewFetchedData(content)
        section = data.get_section("Names and Identifiers")
        assert section is not None
        assert section["TOCHeading"] == "Names and Identifiers"

    def test_get_section_not_found(self):
        """Test getting a non-existent section returns None."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [
                    {"TOCHeading": "Names and Identifiers"},
                ]
            }
        }
        data = PUGViewFetchedData(content)
        section = data.get_section("Non Existent Section")
        assert section is None

    def test_get_all_headings(self):
        """Test getting all headings."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [
                    {"TOCHeading": "Names and Identifiers"},
                    {"TOCHeading": "Safety and Hazards"},
                    {"TOCHeading": "Toxicity"},
                ]
            }
        }
        data = PUGViewFetchedData(content)
        headings = data.get_all_headings()
        assert "Names and Identifiers" in headings
        assert "Safety and Hazards" in headings
        assert "Toxicity" in headings

    def test_get_information(self):
        """Test getting information from a section."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [
                    {
                        "TOCHeading": "Names and Identifiers",
                        "Information": [{"Name": "Aspirin"}, {"Name": "Acetylsalicylic acid"}]
                    },
                ]
            }
        }
        data = PUGViewFetchedData(content)
        info = data.get_information("Names and Identifiers")
        assert len(info) == 2

    def test_get_information_empty(self):
        """Test getting information from section without Information key."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [
                    {"TOCHeading": "Names and Identifiers"},
                ]
            }
        }
        data = PUGViewFetchedData(content)
        info = data.get_information("Names and Identifiers")
        assert info == []

    def test_get_subsections(self):
        """Test getting subsections."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [
                    {
                        "TOCHeading": "Names and Identifiers",
                        "Section": [
                            {"TOCHeading": "Computed Descriptors"},
                            {"TOCHeading": "Synonyms"},
                        ]
                    },
                ]
            }
        }
        data = PUGViewFetchedData(content)
        subsections = data.get_subsections("Names and Identifiers")
        assert len(subsections) == 2

    def test_find_value(self):
        """Test navigating through section hierarchy."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [
                    {
                        "TOCHeading": "Names and Identifiers",
                        "Section": [
                            {
                                "TOCHeading": "Computed Descriptors",
                                "Information": [{"Value": "Test Value"}]
                            },
                        ]
                    },
                ]
            }
        }
        data = PUGViewFetchedData(content)
        result = data.find_value("Names and Identifiers", "Computed Descriptors")
        assert result is not None
        assert result[0]["Value"] == "Test Value"

    def test_find_value_not_found(self):
        """Test find_value returns None for non-existent path."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [{"TOCHeading": "Names and Identifiers"}]
            }
        }
        data = PUGViewFetchedData(content)
        result = data.find_value("Non Existent")
        assert result is None

    def test_has_error(self):
        """Test error detection in PUG View response."""
        content = {"Fault": {"Message": "Record not found"}}
        data = PUGViewFetchedData(content)
        assert data.has_error()
        assert "not found" in data.get_error_message()

    def test_no_error(self):
        """Test no error condition."""
        content = {"Record": {"RecordNumber": 2244, "Section": []}}
        data = PUGViewFetchedData(content)
        assert not data.has_error()
        assert data.get_error_message() is None

    def test_empty_content(self):
        """Test handling empty content."""
        data = PUGViewFetchedData({})
        assert data.record == {}
        assert data.sections == []
        assert data.record_id is None

    def test_as_dict(self):
        """Test as_dict method returns parsed data."""
        content = {
            "Record": {
                "RecordNumber": 2244,
                "Section": [{"TOCHeading": "Test", "Information": [{"Name": "Value"}]}]
            }
        }
        data = PUGViewFetchedData(content)
        result = data.as_dict()
        assert isinstance(result, dict)
        assert "Test" in result

    def test_record_type_attribute(self):
        """Test record_type attribute is set correctly."""
        content = {"Record": {"RecordNumber": 2244, "Section": []}}
        data = PUGViewFetchedData(content, record_type="compound")
        assert data.record_type == "compound"

    def test_raw_content_preserved(self):
        """Test raw content is preserved."""
        content = {"Record": {"RecordNumber": 2244, "Section": []}}
        data = PUGViewFetchedData(content)
        assert data.raw_content == content
