"""Unit tests for ora.py — high-level ORA functions and helpers.

All network calls are mocked. No integration tests here.
"""

import warnings
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

# Access the actual ora MODULE (not the function exported by the package __init__)
# since biodbs._funcs.analysis.__init__ shadows the module with the function.
# `import x.y.z as name` uses getattr(x.y, 'z') which returns the function here;
# importlib.import_module returns sys.modules entry directly — the actual module.
import importlib
_ora_mod = importlib.import_module('biodbs._funcs.analysis.ora')

from biodbs._funcs.analysis.ora import (
    ORAResult,
    ORATermResult,
    CorrectionMethod,
    GOAspect,
    Pathway,
    Species,
    TranslationDatabase,
    _normalize_id_type,
    _translate_ids_for_ora,
    _get_kegg_pathways,
    _get_go_terms,
    _get_reactome_pathways,
    ora,
    ora_kegg,
    ora_go,
    ora_enrichr,
    ora_reactome,
    ora_reactome_local,
    multiple_test_correction,
)


# =============================================================================
# Helpers
# =============================================================================

def _make_result(**kwargs) -> ORAResult:
    defaults = dict(
        results=[], query_genes=["A"], mapped_genes=["A"],
        unmapped_genes=[], background_size=100, database="test",
    )
    defaults.update(kwargs)
    return ORAResult(**defaults)


def _make_term(**kwargs) -> ORATermResult:
    defaults = dict(
        term_id="T1", term_name="Term One", p_value=0.01,
        adjusted_p_value=0.05, overlap_count=5, term_size=50,
        query_size=20, background_size=1000, fold_enrichment=2.0,
        overlap_genes=["A", "B"], database="test",
    )
    defaults.update(kwargs)
    return ORATermResult(**defaults)


def _mock_df_data(rows: list) -> MagicMock:
    m = MagicMock()
    m.as_dataframe.return_value = pd.DataFrame(rows)
    return m


def _mock_quickgo_data(results: list) -> MagicMock:
    m = MagicMock()
    m.results = results
    return m


def _sample_pathways() -> dict:
    return {
        "path1": Pathway(id="path1", name="Pathway One",
                         genes=frozenset({"A", "B", "C"}), database="KEGG"),
        "path2": Pathway(id="path2", name="Pathway Two",
                         genes=frozenset({"D", "E", "F"}), database="KEGG"),
    }


# =============================================================================
# ORAResult.as_dataframe — polars and invalid engine
# =============================================================================

class TestORAResultAsDataframe:
    def test_pandas_engine(self):
        result = _make_result(results=[_make_term()])
        df = result.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_invalid_engine_raises(self):
        result = _make_result(results=[_make_term()])
        with pytest.raises(ValueError, match="Unsupported engine"):
            result.as_dataframe(engine="invalid")

    def test_empty_pandas(self):
        result = _make_result(results=[])
        df = result.as_dataframe(engine="pandas")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


# =============================================================================
# multiple_test_correction — unknown method
# =============================================================================

class TestMultipleTestCorrectionEdge:
    def test_by_correction(self):
        p_values = [0.01, 0.05, 0.1]
        result = multiple_test_correction(p_values, "by")
        assert len(result) == 3
        assert all(r >= p for r, p in zip(result, p_values))

    def test_fdr_by_alias(self):
        p_values = [0.01, 0.05]
        result = multiple_test_correction(p_values, "fdr_by")
        assert len(result) == 2

    def test_unknown_method_resolves_to_bh(self):
        # Unknown method string falls back to BH in current implementation
        p_values = [0.01, 0.05]
        result = multiple_test_correction(p_values, "unknown_method_xyz")
        assert len(result) == 2

    def test_enum_by(self):
        p_values = [0.01, 0.05, 0.1]
        result = multiple_test_correction(p_values, CorrectionMethod.BY)
        assert len(result) == 3


# =============================================================================
# _normalize_id_type
# =============================================================================

class TestNormalizeIdType:
    def test_known_aliases(self):
        assert _normalize_id_type("gene_symbol") == "symbol"
        assert _normalize_id_type("entrezgene_id") == "entrez"
        assert _normalize_id_type("ensembl_gene_id") == "ensembl"
        assert _normalize_id_type("uniprot_id") == "uniprot"
        assert _normalize_id_type("refseq_mrna") == "refseq"

    def test_unknown_passes_through(self):
        assert _normalize_id_type("my_custom_type") == "my_custom_type"

    def test_case_insensitive(self):
        assert _normalize_id_type("SYMBOL") == "symbol"
        assert _normalize_id_type("Gene_Symbol") == "symbol"


# =============================================================================
# _translate_ids_for_ora
# =============================================================================

class TestTranslateIdsForOra:
    def test_same_type_passthrough(self):
        genes = ["A", "B", "C"]
        mapped, mapping, unmapped = _translate_ids_for_ora(
            genes, "symbol", "symbol", Species.HUMAN
        )
        assert mapped == genes
        assert mapping == {"A": "A", "B": "B", "C": "C"}
        assert unmapped == []

    def test_unknown_from_type_warns_and_passthrough(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mapped, mapping, unmapped = _translate_ids_for_ora(
                ["A"], "unknown_type", "symbol", Species.HUMAN
            )
        assert any("Unknown ID type" in str(x.message) for x in w)
        assert mapped == ["A"]

    def test_unknown_to_type_warns_and_passthrough(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mapped, mapping, unmapped = _translate_ids_for_ora(
                ["A"], "symbol", "unknown_type", Species.HUMAN
            )
        assert any("Unknown ID type" in str(x.message) for x in w)

    @patch.object(_ora_mod, "translate_gene_ids")
    def test_successful_translation(self, mock_trans):
        mock_trans.return_value = {"ENS1": "7157", "ENS2": "672"}
        mapped, mapping, unmapped = _translate_ids_for_ora(
            ["ENS1", "ENS2"], "ensembl", "entrez", Species.HUMAN
        )
        assert "7157" in mapped
        assert "672" in mapped
        assert unmapped == []

    @patch.object(_ora_mod, "translate_gene_ids")
    def test_failed_translation_warns_and_passthrough(self, mock_trans):
        mock_trans.side_effect = RuntimeError("network fail")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mapped, mapping, unmapped = _translate_ids_for_ora(
                ["ENS1"], "ensembl", "entrez", Species.HUMAN
            )
        assert any("translation failed" in str(x.message) for x in w)
        assert mapped == ["ENS1"]

    @patch.object(_ora_mod, "translate_gene_ids")
    def test_partial_mapping(self, mock_trans):
        mock_trans.return_value = {"A": "1234"}  # "B" not in result
        mapped, mapping, unmapped = _translate_ids_for_ora(
            ["A", "B"], "symbol", "entrez", Species.HUMAN
        )
        assert "1234" in mapped
        assert "B" in unmapped


# =============================================================================
# _get_kegg_pathways
# =============================================================================

class TestGetKeggPathways:
    @patch.object(_ora_mod, "get_cached_pathways")
    def test_cache_hit(self, mock_cache):
        mock_cache.return_value = {
            "hsa00010": ("Glycolysis", frozenset({"1", "2", "3"}))
        }
        result = _get_kegg_pathways(Species.HUMAN)
        assert "hsa00010" in result
        assert isinstance(result["hsa00010"], Pathway)

    @patch.object(_ora_mod, "cache_pathways")
    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "kegg_link")
    @patch.object(_ora_mod, "kegg_list")
    def test_no_cache_fetches_and_caches(self, mock_list, mock_link, mock_get, mock_put):
        mock_get.return_value = None  # cache miss
        mock_list.return_value = _mock_df_data([
            {"entry_id": "path:hsa00010", "description": "Glycolysis - Homo sapiens"}
        ])
        mock_link.return_value = _mock_df_data([
            {"source_id": "hsa:1234", "target_id": "path:hsa00010"},
            {"source_id": "hsa:5678", "target_id": "path:hsa00010"},
            {"source_id": "hsa:9999", "target_id": "path:hsa00010"},
        ])
        result = _get_kegg_pathways(Species.HUMAN, use_cache=True)
        assert "hsa00010" in result
        assert len(result["hsa00010"].genes) == 3
        mock_put.assert_called_once()

    @patch.object(_ora_mod, "cache_pathways")
    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "kegg_link")
    @patch.object(_ora_mod, "kegg_list")
    def test_use_cache_false_skips_cache(self, mock_list, mock_link, mock_get, mock_put):
        mock_list.return_value = _mock_df_data([])
        mock_link.return_value = _mock_df_data([])
        _get_kegg_pathways(Species.HUMAN, use_cache=False)
        mock_get.assert_not_called()
        mock_put.assert_not_called()


# =============================================================================
# _get_go_terms
# =============================================================================

class TestGetGoTerms:
    @patch.object(_ora_mod, "get_cached_pathways")
    def test_cache_hit(self, mock_cache):
        mock_cache.return_value = {
            "GO:0006915": ("apoptotic process", frozenset({"A", "B", "C", "D", "E"}))
        }
        result = _get_go_terms(Species.HUMAN)
        assert "GO:0006915" in result
        assert isinstance(result["GO:0006915"], Pathway)

    @patch.object(_ora_mod, "get_cached_pathways")
    def test_cache_hit_size_filter_applied(self, mock_cache):
        mock_cache.return_value = {
            "GO:small": ("tiny term", frozenset({"A"})),  # too small
            "GO:big": ("big term", frozenset(set(str(i) for i in range(600)))),  # too large
            "GO:ok": ("ok term", frozenset({"A", "B", "C", "D", "E", "F"})),
        }
        result = _get_go_terms(Species.HUMAN, min_term_size=5, max_term_size=500)
        assert "GO:small" not in result
        assert "GO:big" not in result
        assert "GO:ok" in result

    @patch.object(_ora_mod, "cache_pathways")
    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "quickgo_search_annotations_all")
    def test_no_cache_fetches_annotations(self, mock_qgo, mock_get, mock_put):
        mock_get.return_value = None
        annots = [
            {"goId": "GO:0006915", "goName": "apoptotic process",
             "geneProductId": f"UniProtKB:{chr(65+i)}"} for i in range(6)
        ]
        mock_qgo.return_value = _mock_quickgo_data(annots)
        result = _get_go_terms(Species.HUMAN, use_cache=True)
        assert "GO:0006915" in result
        assert len(result["GO:0006915"].genes) == 6

    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "quickgo_search_annotations_all")
    def test_failed_fetch_returns_empty(self, mock_qgo, mock_get):
        mock_get.return_value = None
        mock_qgo.side_effect = RuntimeError("network down")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _get_go_terms(Species.HUMAN, use_cache=False)
        assert result == {}
        assert any("Failed to fetch GO annotations" in str(x.message) for x in w)

    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "quickgo_search_annotations_all")
    def test_aspect_all_no_filter(self, mock_qgo, mock_get):
        mock_get.return_value = None
        mock_qgo.return_value = _mock_quickgo_data([])
        _get_go_terms(Species.HUMAN, aspect="all", use_cache=False)
        _, kwargs = mock_qgo.call_args
        assert "aspect" not in kwargs


# =============================================================================
# _get_reactome_pathways
# =============================================================================

class TestGetReactomePathways:
    @patch.object(_ora_mod, "get_cached_pathways")
    def test_cache_hit(self, mock_cache):
        mock_cache.return_value = {
            "R-HSA-1": ("DNA Repair", frozenset({"TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"}))
        }
        result = _get_reactome_pathways(Species.HUMAN)
        assert "R-HSA-1" in result

    @patch.object(_ora_mod, "cache_pathways")
    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "Reactome_Fetcher")
    def test_no_cache_fetches(self, MockFetcher, mock_get, mock_put):
        mock_get.return_value = None
        inst = MockFetcher.return_value
        inst.get_events_hierarchy.return_value = MagicMock()
        inst._extract_pathway_ids_from_hierarchy.return_value = [
            ("R-HSA-1", "DNA Repair")
        ]
        inst.get_pathway_genes.return_value = {"TP53", "BRCA1", "BRCA2", "ATM", "CHEK2", "RAD51"}
        result = _get_reactome_pathways(Species.HUMAN, use_cache=True)
        assert "R-HSA-1" in result
        mock_put.assert_called_once()

    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "Reactome_Fetcher")
    def test_failed_hierarchy_returns_empty(self, MockFetcher, mock_get):
        mock_get.return_value = None
        inst = MockFetcher.return_value
        inst.get_events_hierarchy.side_effect = RuntimeError("API down")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _get_reactome_pathways(Species.HUMAN, use_cache=False)
        assert result == {}
        assert any("Failed to fetch Reactome hierarchy" in str(x.message) for x in w)

    @patch.object(_ora_mod, "cache_pathways")
    @patch.object(_ora_mod, "get_cached_pathways")
    @patch.object(_ora_mod, "Reactome_Fetcher")
    def test_size_filter(self, MockFetcher, mock_get, mock_put):
        mock_get.return_value = None
        inst = MockFetcher.return_value
        inst.get_events_hierarchy.return_value = MagicMock()
        inst._extract_pathway_ids_from_hierarchy.return_value = [
            ("R-HSA-1", "Tiny"), ("R-HSA-2", "Normal")
        ]
        inst.get_pathway_genes.side_effect = [
            {"A"},  # too small (min=5)
            {"A", "B", "C", "D", "E", "F"},  # OK
        ]
        result = _get_reactome_pathways(Species.HUMAN, use_cache=False, min_term_size=5)
        assert "R-HSA-1" not in result
        assert "R-HSA-2" in result


# =============================================================================
# ora_kegg
# =============================================================================

class TestOraKegg:
    @patch.object(_ora_mod, "_get_kegg_pathways")
    def test_entrez_passthrough(self, mock_get):
        mock_get.return_value = _sample_pathways()
        result = ora_kegg(["1234", "5678"], from_id_type="entrez")
        assert isinstance(result, ORAResult)
        assert result.database == "KEGG"
        mock_get.assert_called_once()

    @patch.object(_ora_mod, "_translate_ids_for_ora")
    @patch.object(_ora_mod, "_get_kegg_pathways")
    def test_symbol_triggers_translation(self, mock_get, mock_trans):
        mock_trans.return_value = (["1234", "5678"], {}, [])
        mock_get.return_value = _sample_pathways()
        result = ora_kegg(["TP53", "BRCA1"], from_id_type="symbol")
        mock_trans.assert_called_once()
        assert result.database == "KEGG"

    @patch.object(_ora_mod, "_get_kegg_pathways")
    def test_kegg_id_type_strips_prefix(self, mock_get):
        mock_get.return_value = _sample_pathways()
        result = ora_kegg(["hsa:7157"], from_id_type="kegg")
        assert isinstance(result, ORAResult)

    @patch.object(_ora_mod, "_get_kegg_pathways")
    def test_empty_pathways_returns_empty_result(self, mock_get):
        mock_get.return_value = {}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = ora_kegg(["7157"], from_id_type="entrez")
        assert len(result.results) == 0
        assert result.background_size == 0

    @patch.object(_ora_mod, "_get_kegg_pathways")
    def test_deprecated_organism_warns(self, mock_get):
        mock_get.return_value = _sample_pathways()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ora_kegg(["7157"], organism="hsa")
        assert any("deprecated" in str(x.message).lower() for x in w)

    @patch.object(_ora_mod, "_get_kegg_pathways")
    def test_result_has_parameters(self, mock_get):
        mock_get.return_value = _sample_pathways()
        result = ora_kegg(["A"], from_id_type="entrez")
        assert "species" in result.parameters
        assert "from_id_type" in result.parameters


# =============================================================================
# ora_go
# =============================================================================

class TestOraGo:
    @patch.object(_ora_mod, "_get_go_terms")
    def test_uniprot_passthrough(self, mock_get):
        mock_get.return_value = {
            "GO:0006915": Pathway(id="GO:0006915", name="apoptotic process",
                                  genes=frozenset({"P04637", "P38398", "Q13315",
                                                   "P00533", "P42345"}),
                                  database="GO:biological_process"),
        }
        result = ora_go(["P04637", "P38398", "Q13315"], from_id_type="uniprot", min_overlap=2)
        assert isinstance(result, ORAResult)
        assert "GO" in result.database

    @patch.object(_ora_mod, "_translate_ids_for_ora")
    @patch.object(_ora_mod, "_get_go_terms")
    def test_non_uniprot_triggers_translation(self, mock_get, mock_trans):
        mock_trans.return_value = (["P04637"], {}, [])
        mock_get.return_value = {}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            ora_go(["TP53"], from_id_type="symbol")
        mock_trans.assert_called_once()

    @patch.object(_ora_mod, "_get_go_terms")
    def test_go_aspect_enum_accepted(self, mock_get):
        mock_get.return_value = {}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = ora_go(["P04637"], aspect=GOAspect.MOLECULAR_FUNCTION)
        assert isinstance(result, ORAResult)

    @patch.object(_ora_mod, "_get_go_terms")
    def test_string_species_accepted(self, mock_get):
        mock_get.return_value = {}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = ora_go(["P04637"], species="human")
        assert isinstance(result, ORAResult)


# =============================================================================
# ora_enrichr
# =============================================================================

class TestOraEnrichr:
    def _make_enrichr_term(self, name, p, adj_p, overlap):
        t = MagicMock()
        t.term_name = name
        t.p_value = p
        t.adjusted_p_value = adj_p
        t.overlapping_genes = overlap
        t.combined_score = 5.0
        return t

    @patch.object(_ora_mod, "EnrichR_Fetcher")
    def test_symbol_passthrough_returns_result(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.enrich.return_value = MagicMock()
        inst.enrich.return_value.get_enrichment_terms.return_value = [
            self._make_enrichr_term("p53 pathway", 0.001, 0.01, ["TP53", "MDM2"]),
        ]
        result = ora_enrichr(["TP53", "MDM2"], from_id_type="symbol")
        assert isinstance(result, ORAResult)
        assert "EnrichR" in result.database
        assert len(result.results) == 1

    @patch.object(_ora_mod, "EnrichR_Fetcher")
    def test_overlap_as_string_parsed(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.enrich.return_value = MagicMock()
        # overlapping_genes as semicolon-separated string
        inst.enrich.return_value.get_enrichment_terms.return_value = [
            self._make_enrichr_term("pathway", 0.001, 0.01, "TP53;MDM2;BRCA1"),
        ]
        result = ora_enrichr(["TP53", "MDM2", "BRCA1"], from_id_type="symbol")
        assert result.results[0].overlap_count == 3

    @patch.object(_ora_mod, "_translate_ids_for_ora")
    @patch.object(_ora_mod, "EnrichR_Fetcher")
    def test_non_symbol_triggers_translation(self, MockFetcher, mock_trans):
        mock_trans.return_value = (["TP53"], {}, [])
        inst = MockFetcher.return_value
        inst.enrich.return_value = MagicMock()
        inst.enrich.return_value.get_enrichment_terms.return_value = []
        ora_enrichr(["ENSG00000141510"], from_id_type="ensembl")
        mock_trans.assert_called_once()

    @patch.object(_ora_mod, "EnrichR_Fetcher")
    def test_empty_terms_returns_empty_result(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.enrich.return_value = MagicMock()
        inst.enrich.return_value.get_enrichment_terms.return_value = []
        result = ora_enrichr(["TP53"], from_id_type="symbol")
        assert len(result.results) == 0

    @patch.object(_ora_mod, "EnrichR_Fetcher")
    def test_result_has_correct_database_name(self, MockFetcher):
        inst = MockFetcher.return_value
        inst.enrich.return_value = MagicMock()
        inst.enrich.return_value.get_enrichment_terms.return_value = []
        result = ora_enrichr(["TP53"], gene_set_library="GO_Biological_Process_2021")
        assert "GO_Biological_Process_2021" in result.database


# =============================================================================
# ora_reactome
# =============================================================================

class TestOraReactome:
    def _make_pathway(self, stId, name, p, fdr, found, total, ratio=0.01):
        p_obj = MagicMock()
        p_obj.stId = stId
        p_obj.name = name
        p_obj.p_value = p
        p_obj.fdr = fdr
        p_obj.found_entities = found
        p_obj.total_entities = total
        p_obj.entities = MagicMock()
        p_obj.entities.ratio = ratio
        return p_obj

    @patch.object(_ora_mod, "Reactome_Fetcher")
    def test_symbol_passthrough_returns_result(self, MockFetcher):
        inst = MockFetcher.return_value
        reactome_data = MagicMock()
        reactome_data.pathways = [
            self._make_pathway("R-HSA-1", "DNA Repair", 0.001, 0.01, 3, 50),
        ]
        reactome_data.token = "TOKEN123"
        reactome_data.identifiers_not_found = 0
        inst.analyze.return_value = reactome_data
        inst.get_not_found_identifiers.return_value = []
        result = ora_reactome(["TP53", "BRCA1"], species="Homo sapiens")
        assert isinstance(result, ORAResult)
        assert result.database == "Reactome"
        assert len(result.results) == 1
        assert result.results[0].term_id == "R-HSA-1"

    @patch.object(_ora_mod, "_translate_ids_for_ora")
    @patch.object(_ora_mod, "Reactome_Fetcher")
    def test_non_symbol_triggers_translation(self, MockFetcher, mock_trans):
        mock_trans.return_value = (["TP53"], {}, [])
        inst = MockFetcher.return_value
        reactome_data = MagicMock()
        reactome_data.pathways = []
        reactome_data.token = None
        reactome_data.identifiers_not_found = 0
        inst.analyze.return_value = reactome_data
        ora_reactome(["ENSG00000141510"], from_id_type="ensembl")
        mock_trans.assert_called_once()

    @patch.object(_ora_mod, "Reactome_Fetcher")
    def test_no_token_skips_unmapped_fetch(self, MockFetcher):
        inst = MockFetcher.return_value
        reactome_data = MagicMock()
        reactome_data.pathways = []
        reactome_data.token = None
        reactome_data.identifiers_not_found = 0
        inst.analyze.return_value = reactome_data
        result = ora_reactome(["TP53"])
        inst.get_not_found_identifiers.assert_not_called()
        assert isinstance(result, ORAResult)

    @patch.object(_ora_mod, "Reactome_Fetcher")
    def test_result_parameters_set(self, MockFetcher):
        inst = MockFetcher.return_value
        reactome_data = MagicMock()
        reactome_data.pathways = []
        reactome_data.token = "TOKEN"
        reactome_data.identifiers_not_found = 0
        inst.analyze.return_value = reactome_data
        inst.get_not_found_identifiers.return_value = []
        result = ora_reactome(["TP53"], species="Mus musculus", include_disease=False)
        assert result.parameters["species"] == "Mus musculus"
        assert result.parameters["include_disease"] is False
        assert result.parameters["method"] == "reactome_api"


# =============================================================================
# ora_reactome_local
# =============================================================================

class TestOraReactomeLocal:
    @patch.object(_ora_mod, "_get_reactome_pathways")
    def test_symbol_passthrough_with_pathways(self, mock_get):
        mock_get.return_value = {
            "R-HSA-1": Pathway(id="R-HSA-1", name="DNA Repair",
                               genes=frozenset({"TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"}),
                               database="Reactome"),
        }
        result = ora_reactome_local(["TP53", "BRCA1", "BRCA2"], from_id_type="symbol", min_overlap=2)
        assert isinstance(result, ORAResult)
        assert result.database == "Reactome"
        assert result.parameters["method"] == "local"

    @patch.object(_ora_mod, "_get_reactome_pathways")
    def test_empty_pathways_returns_empty_result(self, mock_get):
        mock_get.return_value = {}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = ora_reactome_local(["TP53"], from_id_type="symbol")
        assert len(result.results) == 0
        assert any("No Reactome pathways" in str(x.message) for x in w)

    @patch.object(_ora_mod, "_translate_ids_for_ora")
    @patch.object(_ora_mod, "_get_reactome_pathways")
    def test_non_symbol_triggers_translation(self, mock_get, mock_trans):
        mock_trans.return_value = (["TP53"], {}, [])
        mock_get.return_value = {}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            ora_reactome_local(["ENSG00000141510"], from_id_type="ensembl")
        mock_trans.assert_called_once()

    @patch.object(_ora_mod, "_get_reactome_pathways")
    def test_result_parameters_include_method_and_sizes(self, mock_get):
        mock_get.return_value = {
            "R-HSA-1": Pathway(id="R-HSA-1", name="DNA Repair",
                               genes=frozenset({"TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"}),
                               database="Reactome"),
        }
        result = ora_reactome_local(
            ["TP53", "BRCA1"], min_term_size=10, max_term_size=300, min_overlap=2
        )
        assert result.parameters.get("min_term_size") == 10
        assert result.parameters.get("max_term_size") == 300
        assert result.parameters.get("method") == "local"

    @patch.object(_ora_mod, "_get_reactome_pathways")
    def test_string_translation_database_accepted(self, mock_get):
        mock_get.return_value = {}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = ora_reactome_local(["TP53"], translation_database="ncbi")
        assert isinstance(result, ORAResult)
