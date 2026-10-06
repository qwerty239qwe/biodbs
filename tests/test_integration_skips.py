"""Tests for integration-test external service skip handling."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml
from requests.exceptions import JSONDecodeError, ConnectionError as RequestsConnectionError, ReadTimeout

from biodbs.exceptions import APIRateLimitError, APIServerError, APITimeoutError, APIValidationError
from tests.conftest import _external_service_skip_reason, _require_live_service
from tests.test_translate import test_quality
from biodbs.fetch.ensembl import Ensembl_Fetcher
from biodbs.fetch.ChEMBL import ChEMBL_Fetcher
from biodbs.fetch.pubchem import PubChem_Fetcher
from tests.test_fetch.disease_ontology import test_do_fetcher
from tests.test_fetch.ncbi import test_ncbi_fetcher
from tests.test_fetch.uniprot import test_uniprot_fetcher


@pytest.mark.parametrize("cls", [
    test_do_fetcher.TestDOFetcherTermAPI,
    test_do_fetcher.TestDOFetcherSearchAPI,
    test_do_fetcher.TestDOFetcherHierarchyAPI,
    test_do_fetcher.TestDOFetcherXrefAPI,
    test_do_fetcher.TestDOFetcherOntologyInfo,
    test_do_fetcher.TestDOConvenienceFunctions,
    test_ncbi_fetcher.TestNCBIFetcherGeneAPI,
    test_ncbi_fetcher.TestNCBIFetcherTaxonomyAPI,
    test_ncbi_fetcher.TestNCBIFetcherGenomeAPI,
    test_ncbi_fetcher.TestNCBIConvenienceFunctions,
    test_uniprot_fetcher.TestUniProtFetcherEntryAPI,
    test_uniprot_fetcher.TestUniProtFetcherSearchAPI,
    test_uniprot_fetcher.TestUniProtFetcherIDMappingAPI,
    test_uniprot_fetcher.TestUniProtFetcherConvenienceMethods,
    test_uniprot_fetcher.TestUniProtConvenienceFunctions,
])
def test_live_fetcher_tests_are_marked_integration(cls):
    assert any(mark.name == "integration" for mark in getattr(cls, "pytestmark", []))


@pytest.mark.parametrize("cls", [
    test_do_fetcher.TestDOFetcherBasic,
    test_ncbi_fetcher.TestNCBIFetcherBasic,
    test_uniprot_fetcher.TestUniProtFetcherBasic,
])
def test_offline_fetcher_tests_remain_in_unit_suite(cls):
    assert not getattr(cls, "pytestmark", [])


@pytest.mark.parametrize("service,target", [
    ("disease-ontology", "tests/test_fetch/disease_ontology"),
    ("ncbi", "tests/test_fetch/ncbi"),
    ("uniprot", "tests/test_fetch/uniprot"),
    ("translator-quality", "tests/test_translate/test_quality.py"),
])
def test_live_fetcher_tests_have_integration_ci_jobs(service, target):
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    services = workflow["jobs"]["integration"]["strategy"]["matrix"]["include"]
    assert {"service": service, "target": target} in services


@pytest.mark.parametrize(
    "exc",
    [
        APIRateLimitError("EnrichR"),
        APIServerError("Reactome", 500),
        APITimeoutError("Ensembl"),
        JSONDecodeError("Expecting value", "", 0),
    ],
)
def test_external_service_errors_are_skippable(exc):
    assert _external_service_skip_reason(exc)


def test_ci_runs_for_dev_pushes_and_pull_requests():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
                         Loader=yaml.BaseLoader)
    for event in ("push", "pull_request"):
        assert "dev" in workflow["on"][event]["branches"]


def test_quickgo_ora_runs_separately_with_a_longer_timeout():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    integration = workflow["jobs"]["integration"]
    services = {job["service"]: job for job in integration["strategy"]["matrix"]["include"]}
    assert services["quickgo"]["target"] == "tests/test_fetch/quickgo"
    assert services["quickgo-ora"]["target"] == "tests/test_analysis/test_ora.py::TestORAGo"
    assert services["quickgo-ora"]["timeout_minutes"] == 25
    assert integration["timeout-minutes"] == "${{ matrix.timeout_minutes || 12 }}"


def test_validation_errors_still_fail():
    assert _external_service_skip_reason(APIValidationError("KEGG")) is None


@pytest.mark.parametrize("exc", [
    APIServerError("EBI", 500), APIRateLimitError("EBI"), APITimeoutError("EBI"),
    RequestsConnectionError("offline"), ReadTimeout("timed out"),
])
@pytest.mark.parametrize("service", ["ensembl", "chembl", "pubchem"])
def test_live_accuracy_checks_report_dependency_outages(monkeypatch, exc, service):
    if service == "ensembl":
        # Match the CI failure: resolving the symbol succeeds, but its xrefs fail.
        fetch = Mock(side_effect=[SimpleNamespace(results=[{"id": "ENSG00000141510", "type": "gene"}]), exc])
        monkeypatch.setattr(Ensembl_Fetcher, "get", _require_live_service(fetch))
        def check():
            test_quality.test_live_gene_reference_ids("ensembl", "human", "TP53", "7157")
    else:
        molecule = SimpleNamespace(results=[{"molecule_structures": {"standard_inchi_key": "ASPIRIN-KEY"}}])
        fetch = Mock(side_effect=exc) if service == "chembl" else Mock(return_value=molecule)
        monkeypatch.setattr(ChEMBL_Fetcher, "get", _require_live_service(fetch))
        if service == "pubchem":
            monkeypatch.setattr(PubChem_Fetcher, "get", _require_live_service(Mock(side_effect=exc)))
        check = test_quality.test_live_aspirin_chembl_pubchem_round_trip
    with pytest.raises(pytest.skip.Exception, match="External service unavailable"):
        check()


@pytest.mark.parametrize("payload", [
    SimpleNamespace(results=[]),
    SimpleNamespace(results=[{"dbname": "EntrezGene", "primary_id": "9999"}]),
])
def test_ensembl_successful_empty_or_wrong_mapping_still_fails(monkeypatch, payload):
    fetch = Mock(side_effect=[SimpleNamespace(results=[{"id": "ENSG00000141510", "type": "gene"}]), payload])
    monkeypatch.setattr(Ensembl_Fetcher, "get", _require_live_service(fetch))
    with pytest.raises(AssertionError):
        test_quality.test_live_gene_reference_ids("ensembl", "human", "TP53", "7157")


@pytest.mark.parametrize("payload", [
    SimpleNamespace(results=[]),
    SimpleNamespace(results=[{"molecule_structures": {}}]),
])
def test_chembl_successful_missing_structure_still_fails(monkeypatch, payload):
    monkeypatch.setattr(ChEMBL_Fetcher, "get", _require_live_service(Mock(return_value=payload)))
    with pytest.raises(AssertionError):
        test_quality.test_live_aspirin_chembl_pubchem_round_trip()


@pytest.mark.parametrize("exc", [APIValidationError("Ensembl"), ValueError("bad input"), RuntimeError("bug")])
def test_live_service_guard_does_not_hide_validation_or_code_errors(exc):
    with pytest.raises(type(exc)):
        _require_live_service(Mock(side_effect=exc))()


def test_live_ensembl_guard_accepts_correct_reference_mapping(monkeypatch):
    fetch = Mock(side_effect=[
        SimpleNamespace(results=[{"id": "ENSG00000141510", "type": "gene"}]),
        SimpleNamespace(results=[{"dbname": "EntrezGene", "primary_id": "7157"}]),
    ])
    monkeypatch.setattr(Ensembl_Fetcher, "get", _require_live_service(fetch))
    test_quality.test_live_gene_reference_ids("ensembl", "human", "TP53", "7157")
    assert fetch.call_count == 2


@pytest.mark.parametrize("cid", [2244, 9999])
def test_live_chemical_guard_keeps_round_trip_assertions(monkeypatch, cid):
    key = "ASPIRIN-KEY"
    molecule = SimpleNamespace(results=[{
        "molecule_chembl_id": "CHEMBL25", "molecule_structures": {"standard_inchi_key": key},
    }])
    chembl = Mock(return_value=molecule)
    pubchem = Mock(side_effect=[
        SimpleNamespace(get_cids=lambda: [cid]), SimpleNamespace(results=[{"InChIKey": key}]),
    ])
    monkeypatch.setattr(ChEMBL_Fetcher, "get", _require_live_service(chembl))
    monkeypatch.setattr(PubChem_Fetcher, "get", _require_live_service(pubchem))
    if cid == 2244:
        test_quality.test_live_aspirin_chembl_pubchem_round_trip()
        assert chembl.call_count == pubchem.call_count == 2
    else:
        with pytest.raises(AssertionError):
            test_quality.test_live_aspirin_chembl_pubchem_round_trip()
