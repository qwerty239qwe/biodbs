"""Tests for biodbs.data.Ensembl.data module."""

import pytest
import pandas as pd
from biodbs.data.Ensembl.data import EnsemblFetchedData


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def json_list_response():
    return [
        {"id": "ENSG00000141510", "display_name": "TP53", "biotype": "protein_coding"},
        {"id": "ENSG00000012048", "display_name": "BRCA1", "biotype": "protein_coding"},
    ]


@pytest.fixture
def homology_response():
    return {
        "data": [
            {
                "id": "ENSG00000141510",
                "homologies": [
                    {"type": "ortholog", "target": {"id": "ENSMUSG00000059552"}},
                    {"type": "ortholog", "target": {"id": "ENSDARG00000035559"}},
                ],
            }
        ]
    }


@pytest.fixture
def mapping_response():
    return {"mappings": [{"mapped": {"start": 100, "end": 200}}, {"mapped": {"start": 300, "end": 400}}]}


@pytest.fixture
def gene_tree_response():
    return {"tree": {"type": "gene_tree", "id": "ENSGT00390000000001"}}


@pytest.fixture
def single_object_response():
    return {"id": "ENSG00000141510", "display_name": "TP53", "biotype": "protein_coding"}


@pytest.fixture
def fasta_text():
    return ">ENSP00000269305 pep:known\nMEEPQSDPSVEPPLSQETFS\nDLWKLLPENNVLSPLPSQAM\n>ENSP00000418986 pep:known\nMEEPQSDPSVEPP\n"


# =============================================================================
# Tests
# =============================================================================


class TestExtractResults:
    def test_list_response(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        assert len(data.results) == 2

    def test_homology_response(self, homology_response):
        data = EnsemblFetchedData(homology_response)
        assert len(data.results) == 2
        assert data.results[0]["type"] == "ortholog"

    def test_mapping_response(self, mapping_response):
        data = EnsemblFetchedData(mapping_response)
        assert len(data.results) == 2

    def test_gene_tree_response(self, gene_tree_response):
        data = EnsemblFetchedData(gene_tree_response)
        assert len(data.results) == 1

    def test_single_object(self, single_object_response):
        data = EnsemblFetchedData(single_object_response)
        assert len(data.results) == 1
        assert data.results[0]["id"] == "ENSG00000141510"

    def test_none_content(self):
        data = EnsemblFetchedData(None)
        assert data.results == []

    def test_string_content(self):
        data = EnsemblFetchedData("some text", content_type="text")
        assert data.results == []
        assert data.text == "some text"


class TestParseFasta:
    def test_parse_two_sequences(self, fasta_text):
        data = EnsemblFetchedData(fasta_text, content_type="fasta")
        assert data.sequence is not None
        assert len(data.sequence) == 2
        assert data.sequence[0]["id"] == "ENSP00000269305"
        assert "MEEPQSDPSVEPPLSQETFS" in data.sequence[0]["sequence"]

    def test_get_sequences(self, fasta_text):
        data = EnsemblFetchedData(fasta_text, content_type="fasta")
        seqs = data.get_sequences()
        assert len(seqs) == 2

    def test_get_sequences_no_fasta(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        assert data.get_sequences() == []


class TestGetIds:
    def test_extracts_ids(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        ids = data.get_ids()
        assert ids == ["ENSG00000141510", "ENSG00000012048"]

    def test_no_id_fields(self):
        data = EnsemblFetchedData([{"foo": "bar"}])
        assert data.get_ids() == []


class TestFilter:
    def test_filter_exact(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        filtered = data.filter(display_name="TP53")
        assert len(filtered) == 1
        assert filtered.results[0]["id"] == "ENSG00000141510"

    def test_filter_callable(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        filtered = data.filter(display_name=lambda x: x.startswith("B"))
        assert len(filtered) == 1
        assert filtered.results[0]["display_name"] == "BRCA1"

    def test_filter_no_match(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        filtered = data.filter(display_name="NONEXISTENT")
        assert len(filtered) == 0


class TestAsDataframe:
    def test_pandas(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        df = data.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_empty(self):
        data = EnsemblFetchedData([])
        df = data.as_dataframe()
        assert len(df) == 0

    def test_fasta_raises(self, fasta_text):
        data = EnsemblFetchedData(fasta_text, content_type="fasta", endpoint="sequence")
        with pytest.raises(ValueError, match="sequence/text"):
            data.as_dataframe()

    def test_flatten(self):
        data = EnsemblFetchedData([{"a": {"b": 1}}, {"a": {"b": 2}}])
        df = data.as_dataframe(flatten=True)
        assert "a.b" in df.columns


class TestFormatResults:
    def test_select_columns(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        result = data.format_results(columns=["id"])
        assert len(result) == 2
        assert list(result[0].keys()) == ["id"]

    def test_invalid_column_raises(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        with pytest.raises(ValueError, match="not valid"):
            data.format_results(columns=["nonexistent"])


class TestMisc:
    def test_iadd(self, json_list_response):
        data1 = EnsemblFetchedData(json_list_response)
        data2 = EnsemblFetchedData([{"id": "ENSG99999", "display_name": "TEST"}])
        data1 += data2
        assert len(data1) == 3

    def test_len(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        assert len(data) == 2

    def test_repr(self, json_list_response):
        data = EnsemblFetchedData(json_list_response, endpoint="lookup")
        r = repr(data)
        assert "EnsemblFetchedData" in r
        assert "2 results" in r

    def test_show_columns(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        cols = data.show_columns()
        assert "id" in cols
        assert "display_name" in cols

    def test_as_dict_no_columns(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        assert data.as_dict() is data.results

    def test_as_dict_with_columns(self, json_list_response):
        data = EnsemblFetchedData(json_list_response)
        result = data.as_dict(columns=["id"])
        assert list(result[0].keys()) == ["id"]
