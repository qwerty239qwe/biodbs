"""Tests for HGNC-backed gene ID translation.

All HTTP calls are mocked — no real network access.
"""

import warnings
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from biodbs._funcs.translate.genes import _hgnc_extract_field, _translate_via_hgnc
from biodbs._funcs.translate._id_types import HGNC_ID_MAP, GeneIDType, TranslationDatabase
from biodbs.data.HGNC._data_model import HGNCEntry
from biodbs.data.HGNC.data import HGNCFetchedData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TP53_ENTRY = HGNCEntry(
    hgnc_id="HGNC:11998",
    symbol="TP53",
    name="tumor protein p53",
    entrez_id="7157",
    ensembl_gene_id="ENSG00000141510",
    uniprot_ids=["P04637"],
    refseq_accession=["NM_000546"],
    location="17p13.1",
)

BRCA1_ENTRY = HGNCEntry(
    hgnc_id="HGNC:1100",
    symbol="BRCA1",
    entrez_id="672",
    ensembl_gene_id="ENSG00000012048",
    uniprot_ids=["P38398"],
    refseq_accession=["NM_007294"],
)


def _fetched(entry: HGNCEntry) -> HGNCFetchedData:
    """Wrap a single HGNCEntry in a HGNCFetchedData."""
    return HGNCFetchedData(
        {"response": {"numFound": 1, "docs": [
            {"hgnc_id": entry.hgnc_id, "symbol": entry.symbol,
             "entrez_id": entry.entrez_id, "ensembl_gene_id": entry.ensembl_gene_id,
             "uniprot_ids": entry.uniprot_ids, "refseq_accession": entry.refseq_accession,
             "location": entry.location, "name": entry.name}
        ]}},
        is_search=False,
    )


def _empty_fetched() -> HGNCFetchedData:
    return HGNCFetchedData({"response": {"numFound": 0, "docs": []}})


# =============================================================================
# _hgnc_extract_field
# =============================================================================


class TestHgncExtractField:
    def test_scalar_field(self):
        assert _hgnc_extract_field(TP53_ENTRY, "symbol") == "TP53"
        assert _hgnc_extract_field(TP53_ENTRY, "entrez_id") == "7157"
        assert _hgnc_extract_field(TP53_ENTRY, "hgnc_id") == "HGNC:11998"

    def test_list_field_returns_first_element(self):
        assert _hgnc_extract_field(TP53_ENTRY, "uniprot_ids") == "P04637"
        assert _hgnc_extract_field(TP53_ENTRY, "refseq_accession") == "NM_000546"

    def test_empty_list_returns_none(self):
        entry = HGNCEntry(hgnc_id="HGNC:1", symbol="X", uniprot_ids=[])
        assert _hgnc_extract_field(entry, "uniprot_ids") is None

    def test_none_field_returns_none(self):
        assert _hgnc_extract_field(TP53_ENTRY, "mirbase") is None

    def test_unknown_field_returns_none(self):
        assert _hgnc_extract_field(TP53_ENTRY, "does_not_exist") is None


# =============================================================================
# HGNC_ID_MAP
# =============================================================================


class TestHGNCIdMap:
    def test_core_types_present(self):
        for id_type in (
            GeneIDType.GENE_SYMBOL,
            GeneIDType.HGNC_ID,
            GeneIDType.ENTREZ_ID,
            GeneIDType.ENSEMBL_GENE_ID,
            GeneIDType.UNIPROT_ID,
            GeneIDType.REFSEQ_MRNA,
        ):
            assert id_type in HGNC_ID_MAP

    def test_symbol_maps_to_symbol(self):
        assert HGNC_ID_MAP[GeneIDType.GENE_SYMBOL] == "symbol"
        assert HGNC_ID_MAP[GeneIDType.HGNC_SYMBOL] == "symbol"

    def test_hgnc_id_maps_to_hgnc_id(self):
        assert HGNC_ID_MAP[GeneIDType.HGNC_ID] == "hgnc_id"

    def test_list_fields_mapped(self):
        assert HGNC_ID_MAP[GeneIDType.UNIPROT_ID] == "uniprot_ids"
        assert HGNC_ID_MAP[GeneIDType.REFSEQ_MRNA] == "refseq_accession"
        assert HGNC_ID_MAP[GeneIDType.REFSEQ_PROTEIN] == "refseq_accession"

    def test_hgnc_in_translation_database_enum(self):
        assert TranslationDatabase.HGNC.value == "hgnc"


# =============================================================================
# _translate_via_hgnc
# =============================================================================


class TestTranslateViaHgnc:
    def _mock_fetcher(self, mapping: dict):
        """Return a mock HGNC_Fetcher whose fetch() returns data based on mapping.

        mapping: {input_id -> HGNCFetchedData}
        """
        fetcher = MagicMock()
        fetcher.fetch.side_effect = lambda field, term: mapping.get(
            term, _empty_fetched()
        )
        return fetcher

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_symbol_to_entrez(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({
            "TP53": _fetched(TP53_ENTRY),
            "BRCA1": _fetched(BRCA1_ENTRY),
        })
        result = _translate_via_hgnc(
            ["TP53", "BRCA1"], "symbol", "entrez_id", "human", return_dict=True
        )
        assert result == {"TP53": "7157", "BRCA1": "672"}

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_entrez_to_ensembl(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({
            "7157": _fetched(TP53_ENTRY),
        })
        result = _translate_via_hgnc(
            ["7157"], "entrez_id", "ensembl_gene_id", "human", return_dict=True
        )
        assert result == {"7157": "ENSG00000141510"}

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_list_field_takes_first_element(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({
            "TP53": _fetched(TP53_ENTRY),
        })
        result = _translate_via_hgnc(
            ["TP53"], "symbol", "uniprot_ids", "human", return_dict=True
        )
        assert result == {"TP53": "P04637"}

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_missing_id_excluded_from_dict(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({
            "TP53": _fetched(TP53_ENTRY),
            "FAKE": _empty_fetched(),
        })
        result = _translate_via_hgnc(
            ["TP53", "FAKE"], "symbol", "entrez_id", "human", return_dict=True
        )
        assert "TP53" in result
        assert "FAKE" not in result

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_returns_dataframe_when_return_dict_false(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({
            "TP53": _fetched(TP53_ENTRY),
        })
        result = _translate_via_hgnc(
            ["TP53"], "symbol", "entrez_id", "human", return_dict=False
        )
        assert isinstance(result, pd.DataFrame)
        assert "symbol" in result.columns
        assert "entrez_id" in result.columns

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_non_human_species_warns(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _translate_via_hgnc(
                ["Tp53"], "symbol", "entrez_id", "mouse", return_dict=True
            )
        messages = [str(w.message) for w in caught]
        assert any("HGNC only covers human" in m for m in messages)

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_human_species_no_warning(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({
            "TP53": _fetched(TP53_ENTRY),
        })
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _translate_via_hgnc(
                ["TP53"], "symbol", "entrez_id", "human", return_dict=True
            )
        assert not any("HGNC only covers human" in str(w.message) for w in caught)

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_exception_during_fetch_skips_id(self, MockFetcher):
        fetcher = MagicMock()
        fetcher.fetch.side_effect = RuntimeError("Network error")
        MockFetcher.return_value = fetcher
        result = _translate_via_hgnc(
            ["TP53"], "symbol", "entrez_id", "human", return_dict=True
        )
        assert result == {}

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_empty_input(self, MockFetcher):
        MockFetcher.return_value = self._mock_fetcher({})
        result = _translate_via_hgnc(
            [], "symbol", "entrez_id", "human", return_dict=True
        )
        assert result == {}

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_homo_sapiens_string_not_warned(self, MockFetcher):
        """'Homo sapiens' should be treated as human without a warning."""
        MockFetcher.return_value = self._mock_fetcher({
            "TP53": _fetched(TP53_ENTRY),
        })
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _translate_via_hgnc(
                ["TP53"], "symbol", "entrez_id", "Homo sapiens", return_dict=True
            )
        assert not any("HGNC only covers human" in str(w.message) for w in caught)


# =============================================================================
# Integration with translate_gene_ids (mocked HTTP)
# =============================================================================


class TestTranslateGeneIdsHgnc:
    """Test that translate_gene_ids correctly routes to HGNC."""

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_database_hgnc_routes_correctly(self, MockFetcher):
        from biodbs.translate import translate_gene_ids

        fetcher = MagicMock()
        fetcher.fetch.side_effect = lambda field, term: (
            _fetched(TP53_ENTRY) if term == "TP53" else _empty_fetched()
        )
        MockFetcher.return_value = fetcher

        result = translate_gene_ids(
            ["TP53"],
            from_type="gene_symbol",
            to_type="entrez_id",
            database="hgnc",
            return_dict=True,
        )
        assert result.get("TP53") == "7157"

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_database_enum_hgnc(self, MockFetcher):
        from biodbs.translate import translate_gene_ids

        fetcher = MagicMock()
        fetcher.fetch.return_value = _fetched(TP53_ENTRY)
        MockFetcher.return_value = fetcher

        result = translate_gene_ids(
            ["TP53"],
            from_type="gene_symbol",
            to_type="hgnc_id",
            database=TranslationDatabase.HGNC,
            return_dict=True,
        )
        assert "TP53" in result
