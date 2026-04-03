"""Tests for ClinVarFetchedData.

Pure unit tests, no network access.
"""

import pytest
import pandas as pd

from biodbs.data.ClinVar._data_model import ClinVarVariant
from biodbs.data.ClinVar.data import ClinVarFetchedData
from tests.test_fetch.clinvar.fixtures import (
    TP53_DOC, BRCA1_DOC, BENIGN_DOC, MULTI_GENE_DOC, MINIMAL_DOC,
    esummary_response,
)


# =============================================================================
# Construction
# =============================================================================

class TestConstruction:
    def test_parses_results(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC, BRCA1_DOC))
        assert len(data.results) == 2
        assert all(isinstance(r, ClinVarVariant) for r in data.results)

    def test_uids_in_order(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC, BRCA1_DOC))
        assert data.uids == ["12375", "65533"]

    def test_total_count(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC), total_count=42)
        assert data.total_count == 42

    def test_empty_response(self):
        data = ClinVarFetchedData({"result": {"uids": []}})
        assert len(data) == 0
        assert data.uids == []

    def test_missing_result_key(self):
        data = ClinVarFetchedData({})
        assert len(data) == 0


# =============================================================================
# Sequence protocol
# =============================================================================

class TestSequenceProtocol:
    def _data(self):
        return ClinVarFetchedData(esummary_response(TP53_DOC, BRCA1_DOC, BENIGN_DOC))

    def test_len(self):
        assert len(self._data()) == 3

    def test_iter(self):
        variants = list(self._data())
        assert len(variants) == 3
        assert all(isinstance(v, ClinVarVariant) for v in variants)

    def test_getitem_int(self):
        data = self._data()
        assert data[0].variation_id == "12375"
        assert data[1].variation_id == "65533"

    def test_getitem_negative_int(self):
        data = self._data()
        assert data[-1].variation_id == "99999"

    def test_getitem_slice(self):
        data = self._data()
        sliced = data[0:2]
        assert len(sliced) == 2

    def test_getitem_by_variation_id(self):
        data = self._data()
        v = data["12375"]
        assert v.accession == "VCV000012375"

    def test_getitem_by_vcv_accession(self):
        data = self._data()
        v = data["VCV000065533"]
        assert v.gene_symbols == ["BRCA1"]

    def test_getitem_by_vcv_accession_version(self):
        data = self._data()
        v = data["VCV000012375.28"]
        assert v.variation_id == "12375"

    def test_getitem_by_rcv(self):
        data = self._data()
        v = data["RCV000031124"]
        assert v.variation_id == "65533"

    def test_getitem_missing_raises_key_error(self):
        data = self._data()
        with pytest.raises(KeyError):
            _ = data["NONEXISTENT"]

    def test_getitem_wrong_type_raises(self):
        data = self._data()
        with pytest.raises(TypeError):
            _ = data[3.14]

    def test_repr_without_total(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC))
        r = repr(data)
        assert "1 variants" in r
        assert "of" not in r

    def test_repr_with_total(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC), total_count=500)
        r = repr(data)
        assert "of 500 found" in r


# =============================================================================
# Accessors
# =============================================================================

class TestAccessors:
    def _data(self):
        return ClinVarFetchedData(esummary_response(TP53_DOC, BRCA1_DOC))

    def test_variation_ids(self):
        assert self._data().variation_ids() == ["12375", "65533"]

    def test_accessions(self):
        assert self._data().accessions() == ["VCV000012375", "VCV000065533"]

    def test_gene_symbols_unique(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC, BENIGN_DOC))
        # Both TP53_DOC and BENIGN_DOC have TP53 — should appear once
        syms = data.gene_symbols()
        assert syms.count("TP53") == 1

    def test_gene_symbols_multiple_genes(self):
        data = ClinVarFetchedData(esummary_response(MULTI_GENE_DOC))
        syms = data.gene_symbols()
        assert set(syms) == {"BRCA1", "NBR1"}


# =============================================================================
# pathogenic() filter
# =============================================================================

class TestPathogenicFilter:
    def test_returns_only_pathogenic(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC, BRCA1_DOC, BENIGN_DOC))
        path = data.pathogenic()
        assert all(v.is_pathogenic for v in path)
        assert len(path) == 2

    def test_total_count_updated(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC, BRCA1_DOC, BENIGN_DOC))
        path = data.pathogenic()
        assert path.total_count == 2

    def test_empty_when_none_pathogenic(self):
        data = ClinVarFetchedData(esummary_response(BENIGN_DOC))
        assert len(data.pathogenic()) == 0


# =============================================================================
# Conversion
# =============================================================================

class TestConversion:
    def test_as_dict(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC))
        dicts = data.as_dict()
        assert isinstance(dicts, list)
        assert len(dicts) == 1
        assert dicts[0]["variation_id"] == "12375"

    def test_as_dataframe_shape(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC, BRCA1_DOC))
        df = data.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_as_dataframe_columns(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC))
        df = data.as_dataframe()
        for col in ("variation_id", "accession", "title", "clinical_significance",
                    "gene_symbols", "conditions"):
            assert col in df.columns

    def test_as_dataframe_list_cols_joined(self):
        data = ClinVarFetchedData(esummary_response(TP53_DOC))
        df = data.as_dataframe()
        # gene_symbols should be a semicolon-joined string, not a list
        gene_col = df["gene_symbols"].iloc[0]
        assert isinstance(gene_col, str)
        assert gene_col == "TP53"

    def test_as_dataframe_multi_gene_joined(self):
        data = ClinVarFetchedData(esummary_response(MULTI_GENE_DOC))
        df = data.as_dataframe()
        gene_col = df["gene_symbols"].iloc[0]
        assert ";" in gene_col

    def test_as_dataframe_empty(self):
        data = ClinVarFetchedData({"result": {"uids": []}})
        df = data.as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
