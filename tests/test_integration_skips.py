"""Tests for integration-test external service skip handling."""

from pathlib import Path

import pytest
import yaml
from requests.exceptions import JSONDecodeError

from biodbs.exceptions import APIRateLimitError, APIServerError, APITimeoutError, APIValidationError
from tests.conftest import _external_service_skip_reason
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
