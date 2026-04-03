
import warnings
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, call

from biodbs._funcs import (
    translate_gene_ids,
    translate_gene_ids_kegg,
)
from biodbs._funcs.translate.genes import (
    _translate_via_biomart,
    _translate_via_ncbi,
    _translate_via_uniprot,
    _translate_via_hgnc,
    _translate_multiple_targets,
    _hgnc_extract_field,
    _ensembl_xref_first,
    _ensembl_lookup_parent,
    _ensembl_gene_id_for,
)
from biodbs._funcs.translate._id_types import GeneIDType, TranslationDatabase
from biodbs.data.HGNC._data_model import HGNCEntry
from biodbs.data.HGNC.data import HGNCFetchedData


# =============================================================================
# Helpers
# =============================================================================

def _mock_biomart_data(rows: list[dict]) -> MagicMock:
    """Return a mock BioMartFetchedData whose .as_dataframe() yields rows."""
    m = MagicMock()
    m.as_dataframe.return_value = pd.DataFrame(rows)
    return m


def _mock_ensembl_data(results: list[dict]) -> MagicMock:
    """Return a mock EnsemblFetchedData with .results."""
    m = MagicMock()
    m.results = results
    return m


def _mock_kegg_data(rows: list[dict]) -> MagicMock:
    m = MagicMock()
    m.as_dataframe.return_value = pd.DataFrame(rows)
    return m


def _hgnc_fetched(entry: HGNCEntry) -> HGNCFetchedData:
    return HGNCFetchedData(
        {"response": {"numFound": 1, "docs": [{
            "hgnc_id": entry.hgnc_id, "symbol": entry.symbol,
            "entrez_id": entry.entrez_id, "ensembl_gene_id": entry.ensembl_gene_id,
            "uniprot_ids": entry.uniprot_ids,
            "refseq_accession": entry.refseq_accession,
        }]}},
        is_search=False,
    )


TP53_ENTRY = HGNCEntry(
    hgnc_id="HGNC:11998", symbol="TP53", entrez_id="7157",
    ensembl_gene_id="ENSG00000141510", uniprot_ids=["P04637"],
    refseq_accession=["NM_000546"],
)


# =============================================================================
# resolve_id_type / database normalisation
# =============================================================================

class TestResolveIdType:
    def test_enum_member_resolved_for_biomart(self):
        result = translate_gene_ids(
            ["TP53"], from_type=GeneIDType.GENE_SYMBOL,
            to_type=GeneIDType.ENSEMBL_GENE_ID, database="biomart",
        ) if False else None  # just test that enum is accepted without error below
        from biodbs._funcs.translate._id_types import resolve_id_type
        assert resolve_id_type(GeneIDType.GENE_SYMBOL, "biomart") == "external_gene_name"
        assert resolve_id_type(GeneIDType.ENSEMBL_GENE_ID, "ncbi") == "ensembl_gene_id"
        assert resolve_id_type("external_gene_name", "biomart") == "external_gene_name"

    def test_unknown_string_passthrough(self):
        from biodbs._funcs.translate._id_types import resolve_id_type
        assert resolve_id_type("my_native_field", "ncbi") == "my_native_field"

    def test_translation_database_enum_accepted(self):
        with patch("biodbs._funcs.translate.genes.biomart_convert_ids") as mock_bm:
            mock_bm.return_value = _mock_biomart_data(
                [{"external_gene_name": "TP53", "ensembl_gene_id": "ENSG00000141510"}]
            )
            result = translate_gene_ids(
                ["TP53"], from_type="external_gene_name",
                to_type="ensembl_gene_id",
                database=TranslationDatabase.BIOMART,
            )
        assert isinstance(result, pd.DataFrame)

    def test_invalid_database_raises(self):
        with pytest.raises(ValueError, match="Unsupported database"):
            translate_gene_ids(["TP53"], from_type="symbol", to_type="gene_id", database="foobar")


# =============================================================================
# _translate_via_biomart (unit)
# =============================================================================

class TestTranslateViaBiomartUnit:
    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_returns_dataframe(self, mock_bm):
        mock_bm.return_value = _mock_biomart_data(
            [{"external_gene_name": "TP53", "ensembl_gene_id": "ENSG00000141510"}]
        )
        result = _translate_via_biomart(["TP53"], "external_gene_name", "ensembl_gene_id", "human", False)
        assert isinstance(result, pd.DataFrame)
        assert "external_gene_name" in result.columns

    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_return_dict(self, mock_bm):
        mock_bm.return_value = _mock_biomart_data(
            [{"external_gene_name": "TP53", "ensembl_gene_id": "ENSG00000141510"}]
        )
        result = _translate_via_biomart(["TP53"], "external_gene_name", "ensembl_gene_id", "human", True)
        assert isinstance(result, dict)
        assert result["TP53"] == "ENSG00000141510"

    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_species_mapped_to_dataset(self, mock_bm):
        mock_bm.return_value = _mock_biomart_data([])
        _translate_via_biomart(["Trp53"], "external_gene_name", "ensembl_gene_id", "mouse", False)
        _, kwargs = mock_bm.call_args
        assert kwargs.get("dataset") == "mmusculus_gene_ensembl" or mock_bm.call_args[0][2] == "mmusculus_gene_ensembl"

    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_unknown_species_uses_default_pattern(self, mock_bm):
        mock_bm.return_value = _mock_biomart_data([])
        _translate_via_biomart([], "symbol", "id", "dog", False)
        args, kwargs = mock_bm.call_args
        dataset_arg = kwargs.get("dataset") or args[2]
        assert "dog" in dataset_arg

    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_duplicates_resolved_last_wins(self, mock_bm):
        mock_bm.return_value = _mock_biomart_data([
            {"external_gene_name": "TP53", "ensembl_gene_id": "ENSG1"},
            {"external_gene_name": "TP53", "ensembl_gene_id": "ENSG2"},
        ])
        result = _translate_via_biomart(["TP53"], "external_gene_name", "ensembl_gene_id", "human", True)
        assert result["TP53"] == "ENSG2"


# =============================================================================
# _translate_via_ncbi (unit)
# =============================================================================

class TestTranslateViaNcbiUnit:
    @patch("biodbs.fetch.NCBI.funcs.ncbi_translate_gene_ids")
    def test_returns_dataframe(self, mock_fn):
        mock_fn.return_value = pd.DataFrame([{"symbol": "TP53", "ensembl_gene_id": "ENSG00000141510"}])
        result = _translate_via_ncbi(["TP53"], "symbol", "ensembl_gene_id", "human", False)
        assert isinstance(result, pd.DataFrame)

    @patch("biodbs.fetch.NCBI.funcs.ncbi_translate_gene_ids")
    def test_return_dict_passthrough(self, mock_fn):
        mock_fn.return_value = {"TP53": "ENSG00000141510"}
        result = _translate_via_ncbi(["TP53"], "symbol", "ensembl_gene_id", "human", True)
        assert result == {"TP53": "ENSG00000141510"}

    @patch("biodbs.fetch.NCBI.funcs.ncbi_translate_gene_ids")
    def test_species_mapping(self, mock_fn):
        mock_fn.return_value = {}
        _translate_via_ncbi([], "symbol", "gene_id", "fly", True)
        _, kwargs = mock_fn.call_args
        assert kwargs["taxon"] == "fruit fly"

    @patch("biodbs.fetch.NCBI.funcs.ncbi_translate_gene_ids")
    def test_unknown_species_uses_name(self, mock_fn):
        mock_fn.return_value = {}
        _translate_via_ncbi([], "symbol", "gene_id", "alpaca", True)
        _, kwargs = mock_fn.call_args
        assert kwargs["taxon"] == "alpaca"

    @patch("biodbs.fetch.NCBI.funcs.ncbi_translate_gene_ids")
    def test_dispatched_through_translate_gene_ids(self, mock_fn):
        mock_fn.return_value = pd.DataFrame([{"symbol": "TP53", "gene_id": "7157"}])
        result = translate_gene_ids(["TP53"], from_type="symbol", to_type="gene_id", database="ncbi")
        assert isinstance(result, pd.DataFrame)
        mock_fn.assert_called_once()


# =============================================================================
# _translate_via_uniprot (unit)
# =============================================================================

class TestTranslateViaUniprotUnit:
    @patch("biodbs._funcs.translate.proteins.translate_protein_ids")
    def test_returns_dataframe(self, mock_fn):
        mock_fn.return_value = pd.DataFrame([{"from": "P04637", "to": "7157"}])
        result = _translate_via_uniprot(["P04637"], "UniProtKB_AC-ID", "GeneID", "human", False)
        assert isinstance(result, pd.DataFrame)

    @patch("biodbs._funcs.translate.proteins.translate_protein_ids")
    def test_return_dict(self, mock_fn):
        mock_fn.return_value = {"P04637": "7157"}
        result = _translate_via_uniprot(["P04637"], "UniProtKB_AC-ID", "GeneID", "human", True)
        assert result == {"P04637": "7157"}

    @patch("biodbs._funcs.translate.proteins.translate_protein_ids")
    def test_species_mapped_to_taxid(self, mock_fn):
        mock_fn.return_value = {}
        _translate_via_uniprot([], "UniProtKB_AC-ID", "GeneID", "mouse", True)
        _, kwargs = mock_fn.call_args
        assert kwargs["organism"] == 10090

    @patch("biodbs._funcs.translate.proteins.translate_protein_ids")
    def test_unknown_species_defaults_9606(self, mock_fn):
        mock_fn.return_value = {}
        _translate_via_uniprot([], "UniProtKB_AC-ID", "GeneID", "unicorn", True)
        _, kwargs = mock_fn.call_args
        assert kwargs["organism"] == 9606


# =============================================================================
# _translate_via_hgnc (unit)
# =============================================================================

class TestTranslateViaHgncUnit:
    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_returns_dataframe(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.fetch.return_value = _hgnc_fetched(TP53_ENTRY)
        result = _translate_via_hgnc(["TP53"], "symbol", "entrez_id", "human", False)
        assert isinstance(result, pd.DataFrame)
        assert result["entrez_id"].iloc[0] == "7157"

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_return_dict(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.fetch.return_value = _hgnc_fetched(TP53_ENTRY)
        result = _translate_via_hgnc(["TP53"], "symbol", "entrez_id", "human", True)
        assert result == {"TP53": "7157"}

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_non_human_warns(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.fetch.return_value = _hgnc_fetched(TP53_ENTRY)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _translate_via_hgnc(["Trp53"], "symbol", "entrez_id", "mouse", False)
        assert any("HGNC only covers human" in str(warning.message) for warning in w)

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_missing_entry_returns_none(self, MockFetcher):
        inst = MockFetcher.return_value
        empty = HGNCFetchedData({"response": {"numFound": 0, "docs": []}})
        inst.fetch.return_value = empty
        result = _translate_via_hgnc(["UNKNOWN"], "symbol", "entrez_id", "human", True)
        assert result == {}

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_exception_per_id_produces_none(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.fetch.side_effect = RuntimeError("network down")
        result = _translate_via_hgnc(["TP53"], "symbol", "entrez_id", "human", False)
        assert isinstance(result, pd.DataFrame)
        assert pd.isna(result["entrez_id"].iloc[0])

    @patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher")
    def test_list_field_returns_first_element(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.fetch.return_value = _hgnc_fetched(TP53_ENTRY)
        result = _translate_via_hgnc(["TP53"], "symbol", "uniprot_ids", "human", True)
        assert result == {"TP53": "P04637"}


# =============================================================================
# _translate_multiple_targets (unit)
# =============================================================================

class TestTranslateMultipleTargetsUnit:
    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_returns_dataframe_with_all_columns(self, mock_bm):
        mock_bm.return_value = _mock_biomart_data(
            [{"external_gene_name": "TP53", "ensembl_gene_id": "ENSG00000141510"},
             {"external_gene_name": "TP53", "entrezgene_id": "7157"}]
        )
        result = translate_gene_ids(
            ["TP53"], from_type="external_gene_name",
            to_type=["ensembl_gene_id", "entrezgene_id"],
            database="biomart",
        )
        assert isinstance(result, pd.DataFrame)
        assert "external_gene_name" in result.columns

    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_returns_dict_with_nested_targets(self, mock_bm):
        mock_bm.return_value = _mock_biomart_data(
            [{"external_gene_name": "TP53", "ensembl_gene_id": "ENSG00000141510"}]
        )
        result = translate_gene_ids(
            ["TP53"], from_type="external_gene_name",
            to_type=["ensembl_gene_id"],
            database="biomart", return_dict=True,
        )
        assert isinstance(result, dict)
        assert "TP53" in result
        assert isinstance(result["TP53"], dict)

    @patch("biodbs._funcs.translate.genes.biomart_convert_ids")
    def test_partial_failure_sets_none(self, mock_bm):
        # First call raises, second call succeeds
        mock_bm.side_effect = [
            RuntimeError("fail"),
            _mock_biomart_data([{"external_gene_name": "TP53", "entrezgene_id": "7157"}]),
        ]
        result = _translate_multiple_targets(
            ["TP53"], "external_gene_name", ["ensembl_gene_id", "entrezgene_id"],
            "human", "biomart", False,
        )
        assert isinstance(result, pd.DataFrame)
        # entrezgene_id succeeded; ensembl_gene_id failed → None
        assert result["ensembl_gene_id"].iloc[0] is None


# =============================================================================
# _translate_via_ensembl helpers (unit)
# =============================================================================

class TestEnsemblHelpers:
    def test_ensembl_xref_first_matches_dbname(self):
        xrefs = MagicMock()
        xrefs.results = [
            {"dbname": "EntrezGene", "primary_id": "7157"},
            {"dbname": "HGNC", "display_id": "TP53", "primary_id": "HGNC:11998"},
        ]
        assert _ensembl_xref_first(xrefs, "EntrezGene") == "7157"

    def test_ensembl_xref_first_hgnc_returns_display_id(self):
        xrefs = MagicMock()
        xrefs.results = [{"dbname": "HGNC", "display_id": "TP53", "primary_id": "HGNC:11998"}]
        assert _ensembl_xref_first(xrefs, "HGNC") == "TP53"

    def test_ensembl_xref_first_no_match_returns_none(self):
        xrefs = MagicMock()
        xrefs.results = [{"dbname": "EntrezGene", "primary_id": "7157"}]
        assert _ensembl_xref_first(xrefs, "HGNC") is None

    def test_ensembl_lookup_parent_returns_parent(self):
        lookup_fn = MagicMock()
        lookup_fn.return_value = _mock_ensembl_data([{"Parent": "ENSG00000141510"}])
        assert _ensembl_lookup_parent("ENST000001", lookup_fn) == "ENSG00000141510"

    def test_ensembl_lookup_parent_empty_results(self):
        lookup_fn = MagicMock()
        lookup_fn.return_value = _mock_ensembl_data([])
        assert _ensembl_lookup_parent("ENST000001", lookup_fn) is None

    def test_ensembl_gene_id_for_gene_passthrough(self):
        lookup_fn = MagicMock()
        assert _ensembl_gene_id_for("ENSG1", "ensembl_gene_id", lookup_fn) == "ENSG1"
        lookup_fn.assert_not_called()

    def test_ensembl_gene_id_for_transcript(self):
        lookup_fn = MagicMock()
        lookup_fn.return_value = _mock_ensembl_data([{"Parent": "ENSG00000141510"}])
        assert _ensembl_gene_id_for("ENST1", "ensembl_transcript_id", lookup_fn) == "ENSG00000141510"

    def test_ensembl_gene_id_for_protein_chains_two_lookups(self):
        lookup_fn = MagicMock()
        lookup_fn.side_effect = [
            _mock_ensembl_data([{"Parent": "ENST1"}]),   # protein → transcript
            _mock_ensembl_data([{"Parent": "ENSG1"}]),   # transcript → gene
        ]
        assert _ensembl_gene_id_for("ENSP1", "ensembl_protein_id", lookup_fn) == "ENSG1"


# =============================================================================
# _translate_via_ensembl — gene→external (unit)
# =============================================================================

class TestTranslateViaEnsemblUnit:
    def _patch_ensembl(self, xref=None, xref_symbol=None, lookup=None):
        """Context manager that patches all three ensembl funcs."""
        patches = [
            patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs", return_value=xref or _mock_ensembl_data([])),
            patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol", return_value=xref_symbol or _mock_ensembl_data([])),
            patch("biodbs.fetch.ensembl.funcs.ensembl_lookup", return_value=lookup or _mock_ensembl_data([])),
        ]
        return patches

    def test_ensembl_gene_to_external_entrezgene(self):
        xref_data = _mock_ensembl_data([{"dbname": "EntrezGene", "primary_id": "7157"}])
        with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs", return_value=xref_data), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_lookup"):
            result = translate_gene_ids(
                ["ENSG00000141510"], from_type="ensembl_gene_id",
                to_type="EntrezGene", database="ensembl",
            )
        assert isinstance(result, pd.DataFrame)
        assert result["EntrezGene"].iloc[0] == "7157"

    def test_external_symbol_to_ensembl_gene(self):
        xref_data = _mock_ensembl_data([{"id": "ENSG00000141510"}])
        with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol", return_value=xref_data), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_lookup"):
            result = translate_gene_ids(
                ["TP53"], from_type="HGNC", to_type="ensembl_gene_id",
                database="ensembl",
            )
        assert result["ensembl_gene_id"].iloc[0] == "ENSG00000141510"

    def test_external_to_non_ensembl_warns(self):
        xref_data = _mock_ensembl_data([{"id": "ENSG00000141510"}])
        with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol", return_value=xref_data), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_lookup"):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                translate_gene_ids(
                    ["TP53"], from_type="HGNC", to_type="EntrezGene",
                    database="ensembl",
                )
            assert any("always returns Ensembl gene IDs" in str(x.message) for x in w)

    def test_gene_to_transcript_ensembl(self):
        lookup_data = _mock_ensembl_data([{
            "Transcript": [{"id": "ENST00000269305", "is_canonical": 1}]
        }])
        with patch("biodbs.fetch.ensembl.funcs.ensembl_lookup", return_value=lookup_data), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol"):
            result = translate_gene_ids(
                ["ENSG00000141510"], from_type="ensembl_gene_id",
                to_type="ensembl_transcript_id", database="ensembl",
            )
        assert result["ensembl_transcript_id"].iloc[0] == "ENST00000269305"

    def test_gene_to_protein_ensembl(self):
        lookup_data = _mock_ensembl_data([{
            "Transcript": [{"id": "ENST1", "is_canonical": 1,
                            "Translation": {"id": "ENSP00000269305"}}]
        }])
        with patch("biodbs.fetch.ensembl.funcs.ensembl_lookup", return_value=lookup_data), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol"):
            result = translate_gene_ids(
                ["ENSG00000141510"], from_type="ensembl_gene_id",
                to_type="ensembl_protein_id", database="ensembl",
            )
        assert result["ensembl_protein_id"].iloc[0] == "ENSP00000269305"

    def test_transcript_to_gene_ensembl(self):
        lookup_data = _mock_ensembl_data([{"Parent": "ENSG00000141510"}])
        with patch("biodbs.fetch.ensembl.funcs.ensembl_lookup", return_value=lookup_data), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol"):
            result = translate_gene_ids(
                ["ENST00000269305"], from_type="ensembl_transcript_id",
                to_type="ensembl_gene_id", database="ensembl",
            )
        assert result["ensembl_gene_id"].iloc[0] == "ENSG00000141510"

    def test_return_dict_ensembl(self):
        xref_data = _mock_ensembl_data([{"dbname": "EntrezGene", "primary_id": "7157"}])
        with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs", return_value=xref_data), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_lookup"):
            result = translate_gene_ids(
                ["ENSG00000141510"], from_type="ensembl_gene_id",
                to_type="EntrezGene", database="ensembl", return_dict=True,
            )
        assert result == {"ENSG00000141510": "7157"}

    def test_exception_per_id_produces_none(self):
        with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs", side_effect=RuntimeError("fail")), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol"), \
             patch("biodbs.fetch.ensembl.funcs.ensembl_lookup"):
            result = translate_gene_ids(
                ["ENSG00000141510"], from_type="ensembl_gene_id",
                to_type="EntrezGene", database="ensembl",
            )
        assert pd.isna(result["EntrezGene"].iloc[0])


# =============================================================================
# translate_gene_ids_kegg (unit)
# =============================================================================

class TestTranslateGeneIdsKeggUnit:
    @patch("biodbs._funcs.translate.genes.kegg_conv")
    def test_with_ids(self, mock_conv):
        mock_conv.return_value = _mock_kegg_data([
            {"source_id": "hsa:7157", "target_id": "ncbi-geneid:7157"}
        ])
        result = translate_gene_ids_kegg(["hsa:7157"], from_db="hsa", to_db="ncbi-geneid")
        assert isinstance(result, pd.DataFrame)
        mock_conv.assert_called_once_with(target_db="ncbi-geneid", source=["hsa:7157"])

    @patch("biodbs._funcs.translate.genes.kegg_conv")
    def test_empty_ids_uses_from_db(self, mock_conv):
        mock_conv.return_value = _mock_kegg_data([])
        translate_gene_ids_kegg([], from_db="hsa", to_db="ncbi-geneid")
        mock_conv.assert_called_once_with(target_db="ncbi-geneid", source="hsa")


# =============================================================================
# Gene ID Translation Tests (BioMart)
# =============================================================================

class TestTranslateGeneIds:
    """Tests for translate_gene_ids function using BioMart."""

    @pytest.mark.integration
    def test_gene_symbol_to_ensembl(self):
        """Test translating gene symbols to Ensembl IDs."""
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2
        assert "external_gene_name" in result.columns
        assert "ensembl_gene_id" in result.columns
        # Verify TP53 translation
        tp53_rows = result[result["external_gene_name"] == "TP53"]
        assert len(tp53_rows) >= 1
        assert tp53_rows["ensembl_gene_id"].iloc[0].startswith("ENSG")

    @pytest.mark.integration
    def test_ensembl_to_entrez(self):
        """Test translating Ensembl IDs to Entrez Gene IDs."""
        result = translate_gene_ids(
            ["ENSG00000141510"],  # TP53
            from_type="ensembl_gene_id",
            to_type="entrezgene_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1
        assert "ensembl_gene_id" in result.columns
        assert "entrezgene_id" in result.columns

    @pytest.mark.integration
    def test_gene_symbol_to_hgnc(self):
        """Test translating gene symbols to HGNC IDs."""
        result = translate_gene_ids(
            ["TP53"],
            from_type="external_gene_name",
            to_type="hgnc_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @pytest.mark.integration
    def test_return_dict(self):
        """Test returning result as dictionary."""
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
            return_dict=True,
        )
        assert isinstance(result, dict)
        if not result:
            pytest.skip("BioMart API returned empty results")
        assert "TP53" in result
        assert result["TP53"].startswith("ENSG")

    @pytest.mark.integration
    def test_mouse_species(self):
        """Test translation for mouse genes."""
        result = translate_gene_ids(
            ["Trp53"],  # Mouse TP53 homolog
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
            species="mouse",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1
        # Mouse Ensembl IDs start with ENSMUSG
        if len(result) > 0 and result["ensembl_gene_id"].iloc[0]:
            assert "ENSMUS" in result["ensembl_gene_id"].iloc[0]

    @pytest.mark.integration
    def test_multiple_genes(self):
        """Test translation with multiple genes."""
        genes = ["TP53", "BRCA1", "EGFR", "MYC"]
        result = translate_gene_ids(
            genes,
            from_type="external_gene_name",
            to_type="ensembl_gene_id",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= len(genes)


# =============================================================================
# Multiple Target Types Tests
# =============================================================================

class TestTranslateGeneIdsMultipleTargets:
    """Tests for translate_gene_ids with multiple target types."""

    @pytest.mark.integration
    def test_multiple_to_types_dataframe(self):
        """Test translating to multiple ID types, returning DataFrame."""
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="external_gene_name",
            to_type=["ensembl_gene_id", "entrezgene_id"],
        )
        assert isinstance(result, pd.DataFrame)
        assert "external_gene_name" in result.columns
        # Skip if BioMart returned empty results (no target columns)
        if "ensembl_gene_id" not in result.columns:
            pytest.skip("BioMart API returned empty results")
        assert "entrezgene_id" in result.columns
        assert len(result) == 2
        # Check that TP53 has valid values
        tp53_row = result[result["external_gene_name"] == "TP53"]
        assert len(tp53_row) == 1
        assert tp53_row["ensembl_gene_id"].iloc[0] is not None

    @pytest.mark.integration
    def test_multiple_to_types_dict(self):
        """Test translating to multiple ID types, returning dict."""
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="external_gene_name",
            to_type=["ensembl_gene_id", "entrezgene_id"],
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "TP53" in result
        assert "BRCA1" in result
        assert isinstance(result["TP53"], dict)
        # Skip if BioMart returned empty results
        if not result["TP53"]:
            pytest.skip("BioMart API returned empty results")
        assert "ensembl_gene_id" in result["TP53"]
        assert "entrezgene_id" in result["TP53"]

    @pytest.mark.integration
    def test_multiple_to_types_three_targets(self):
        """Test translating to three different ID types."""
        result = translate_gene_ids(
            ["TP53"],
            from_type="external_gene_name",
            to_type=["ensembl_gene_id", "entrezgene_id", "hgnc_id"],
        )
        assert isinstance(result, pd.DataFrame)
        # Skip if BioMart returned empty results (no target columns)
        if "ensembl_gene_id" not in result.columns:
            pytest.skip("BioMart API returned empty results")
        assert "entrezgene_id" in result.columns
        assert "hgnc_id" in result.columns

    @pytest.mark.integration
    def test_multiple_to_types_partial_failure(self):
        """Test that partial failures in multi-target don't break the entire call."""
        # One valid target, one that might fail
        result = translate_gene_ids(
            ["TP53"],
            from_type="external_gene_name",
            to_type=["ensembl_gene_id", "entrezgene_id"],
        )
        assert isinstance(result, pd.DataFrame)
        # At least one target should have been resolved
        assert len(result) == 1


# =============================================================================
# Gene ID Translation Tests (KEGG)
# =============================================================================

# =============================================================================
# Gene ID Translation Tests (Ensembl REST API)
# =============================================================================

class TestTranslateGeneIdsEnsembl:
    """Tests for translate_gene_ids function using Ensembl REST API."""

    @pytest.mark.integration
    def test_ensembl_to_hgnc(self):
        """Test translating Ensembl IDs to HGNC using Ensembl REST API."""
        result = translate_gene_ids(
            ["ENSG00000141510"],  # TP53
            from_type="ensembl_gene_id",
            to_type="HGNC",
            database="ensembl",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1
        assert "ensembl_gene_id" in result.columns
        assert "HGNC" in result.columns

    @pytest.mark.integration
    def test_ensembl_to_entrezgene(self):
        """Test translating Ensembl IDs to EntrezGene using Ensembl REST API."""
        result = translate_gene_ids(
            ["ENSG00000141510", "ENSG00000012048"],  # TP53, BRCA1
            from_type="ensembl_gene_id",
            to_type="EntrezGene",
            database="ensembl",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2

    @pytest.mark.integration
    def test_symbol_to_ensembl_via_rest(self):
        """Test looking up Ensembl ID from gene symbol using REST API."""
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="gene_symbol",
            to_type="ensembl_gene_id",
            species="human",
            database="ensembl",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2

    @pytest.mark.integration
    def test_ensembl_return_dict(self):
        """Test Ensembl REST returning result as dictionary."""
        result = translate_gene_ids(
            ["ENSG00000141510"],  # TP53
            from_type="ensembl_gene_id",
            to_type="HGNC",
            database="ensembl",
            return_dict=True,
        )
        assert isinstance(result, dict)
        assert "ENSG00000141510" in result

    def test_invalid_database(self):
        """Test that invalid database raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported database"):
            translate_gene_ids(
                ["TP53"],
                from_type="external_gene_name",
                to_type="ensembl_gene_id",
                database="invalid_db",
            )


class TestTranslateGeneIdsKegg:
    """Tests for translate_gene_ids_kegg function using KEGG."""

    @pytest.mark.integration
    def test_kegg_to_ncbi_geneid(self):
        """Test converting KEGG gene IDs to NCBI Entrez Gene IDs."""
        result = translate_gene_ids_kegg(
            ["hsa:7157", "hsa:672"],  # TP53, BRCA1
            from_db="hsa",
            to_db="ncbi-geneid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "source_id" in result.columns
        assert "target_id" in result.columns
        # Verify target IDs have ncbi-geneid prefix
        for _, row in result.iterrows():
            assert "ncbi-geneid:" in row["target_id"]

    @pytest.mark.integration
    def test_kegg_to_uniprot(self):
        """Test converting KEGG gene IDs to UniProt accessions."""
        result = translate_gene_ids_kegg(
            ["hsa:7157"],  # TP53
            from_db="hsa",
            to_db="uniprot",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @pytest.mark.integration
    @pytest.mark.slow
    def test_entire_organism_conversion(self):
        """Test converting entire organism's genes (slow)."""
        # This fetches all human gene ID conversions - may be slow
        result = translate_gene_ids_kegg(
            [],  # Empty list means convert all
            from_db="hsa",
            to_db="ncbi-geneid",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 1000  # Human has many genes


@pytest.mark.integration
@pytest.mark.slow
def test_empty_list_gene():
    """Test translation with empty list for genes.

    Note: When passing an empty list to BioMart, it returns all genes
    rather than an empty result (no filter = return all).
    """
    result = translate_gene_ids(
        [],
        from_type="external_gene_name",
        to_type="ensembl_gene_id",
    )
    assert isinstance(result, pd.DataFrame)
    # Empty list means no filter, so BioMart returns all genes
    assert len(result) > 0