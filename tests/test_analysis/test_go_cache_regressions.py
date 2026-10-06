"""Exercise real GO cache files with overlapping term IDs and query filters."""

from types import SimpleNamespace
from unittest.mock import Mock
from importlib import import_module

import pytest

from biodbs._funcs.analysis.ora import _get_go_terms, Species
from biodbs._funcs.analysis._cache import cache_pathways, get_cached_pathways, clear_cache

ora_module = import_module("biodbs._funcs.analysis.ora")


@pytest.mark.parametrize("first,second", [(["IDA"], ["IEA"]), (["IEA"], ["IDA"])])
def test_evidence_filters_do_not_share_go_cache(monkeypatch, tmp_path, first, second):
    def annotations(**kwargs):
        evidence = kwargs["goEvidence"][0]
        return SimpleNamespace(results=[{"goId": "GO:1", "geneProductId": f"UniProtKB:{evidence}"}])

    fetch = Mock(side_effect=annotations)
    monkeypatch.setattr(ora_module, "quickgo_search_annotations_all", fetch)
    for codes in (first, second, first):
        result = _get_go_terms(Species.HUMAN, evidence_codes=codes, cache_dir=str(tmp_path), min_term_size=1)
        assert result["GO:1"].genes == frozenset(codes)
        assert result["GO:1"].name == "GO:1"
        assert result["GO:1"].species == Species.HUMAN.scientific_name
    assert fetch.call_count == 2


def test_go_cache_normalizes_evidence_order_and_duplicates(monkeypatch, tmp_path):
    fetch = Mock(return_value=SimpleNamespace(results=[{"goId": "GO:1", "geneProductId": "UniProtKB:A"}]))
    monkeypatch.setattr(ora_module, "quickgo_search_annotations_all", fetch)
    for codes in (["IDA", "IMP"], ["IMP", "IDA", "IDA"]):
        assert _get_go_terms(Species.HUMAN, evidence_codes=codes, cache_dir=str(tmp_path), min_term_size=1)
    assert fetch.call_count == 1


def test_go_cache_keeps_terms_excluded_by_first_size_filter(monkeypatch, tmp_path):
    rows = [{"goId": "GO:1", "geneProductId": f"UniProtKB:{i}"} for i in range(3)]
    fetch = Mock(return_value=SimpleNamespace(results=rows))
    monkeypatch.setattr(ora_module, "quickgo_search_annotations_all", fetch)
    assert _get_go_terms(Species.HUMAN, cache_dir=str(tmp_path), min_term_size=5) == {}
    wide = _get_go_terms(Species.HUMAN, cache_dir=str(tmp_path), min_term_size=1, max_term_size=4)
    assert wide["GO:1"].genes == frozenset({"0", "1", "2"})
    assert _get_go_terms(Species.HUMAN, cache_dir=str(tmp_path), min_term_size=1, max_term_size=2) == {}
    assert fetch.call_count == 1


def test_overlapping_go_ids_are_isolated_by_species(monkeypatch, tmp_path):
    def annotations(**kwargs):
        return SimpleNamespace(results=[{"goId": "GO:1", "geneProductId": f"UniProtKB:{kwargs['taxonId']}"}])

    fetch = Mock(side_effect=annotations)
    monkeypatch.setattr(ora_module, "quickgo_search_annotations_all", fetch)
    for species in (Species.HUMAN, Species.MOUSE, Species.HUMAN):
        result = _get_go_terms(species, cache_dir=str(tmp_path), min_term_size=1)
        assert result["GO:1"].genes == frozenset({str(species.taxon_id)})
    assert fetch.call_count == 2


def test_json_cache_helpers_can_clear_go_cache(tmp_path):
    data = {"GO:1": ("term", frozenset({"A"}))}
    assert cache_pathways("go_test", data, str(tmp_path), backend="json")
    assert get_cached_pathways("go_test", str(tmp_path), backend="json") == data
    assert clear_cache("go_test", str(tmp_path), backend="json")
    assert get_cached_pathways("go_test", str(tmp_path), backend="json") is None
