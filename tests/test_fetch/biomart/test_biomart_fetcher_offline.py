"""Offline tests for BioMart fetcher behavior."""

import pytest
import requests

from biodbs.data.BioMart.data import BioMartQueryData
from biodbs.exceptions import APIServerError
from biodbs.fetch.biomart import BioMart_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


def test_biomart_make_request_success_query_error_and_retry(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.biomart.biomart_fetcher.requests.get",
        lambda url, params=None, timeout=120: DummyResponse(text="ok"),
    )
    assert BioMart_Fetcher()._make_request("https://example.test", {}).text == "ok"

    monkeypatch.setattr(
        "biodbs.fetch.biomart.biomart_fetcher.requests.get",
        lambda url, params=None, timeout=120: DummyResponse(text="Query ERROR: bad filter"),
    )
    with pytest.raises(ValueError, match="bad filter"):
        BioMart_Fetcher()._make_request("https://example.test", {})

    monkeypatch.setattr(
        "biodbs.fetch.biomart.biomart_fetcher.requests.get",
        lambda url, params=None, timeout=120: DummyResponse(
            text="Query ERROR: Exception::Database mysql database down"
        ),
    )
    with pytest.raises(APIServerError):
        BioMart_Fetcher()._make_request("https://example.test", {})

    calls = []

    def flaky_get(url, params=None, timeout=120):
        calls.append(1)
        if len(calls) == 1:
            raise requests.exceptions.Timeout()
        return DummyResponse(status_code=500, text="still down")

    monkeypatch.setattr("biodbs.fetch.biomart.biomart_fetcher.requests.get", flaky_get)
    monkeypatch.setattr("biodbs.fetch.biomart.biomart_fetcher.time.sleep", lambda value: None)
    with pytest.raises(APIServerError):
        BioMart_Fetcher()._make_request("https://example.test", {}, retries=2, retry_delay=0)


def test_biomart_query_and_batch_paths(monkeypatch):
    fetcher = BioMart_Fetcher()
    monkeypatch.setattr(
        fetcher,
        "_make_request",
        lambda url, params: DummyResponse(text="ENSG1\tTP53\nENSG2\tBRCA1\n"),
    )

    data = fetcher.query(
        attributes=["ensembl_gene_id", "external_gene_name"],
        filters={"ensembl_gene_id": ["ENSG1"]},
    )
    assert isinstance(data, BioMartQueryData)
    assert len(data) == 1

    assert len(fetcher.batch_query(attributes=["a"], filter_values=[])) == 0
    single = fetcher.batch_query(
        attributes=["ensembl_gene_id", "external_gene_name"],
        filter_values=["ENSG1"],
        batch_size=10,
    )
    assert len(single) == 1


def test_biomart_discovery_cache_and_list_delegation(monkeypatch):
    fetcher = BioMart_Fetcher()
    config = type(
        "Config",
        (),
        {
            "get_attributes": lambda self, contain=None, pattern=None: ["attr", contain, pattern],
            "get_filters": lambda self, contain=None, pattern=None: ["filter", contain, pattern],
        },
    )()
    monkeypatch.setattr(fetcher, "get_config", lambda dataset="x", use_cache=True: config)

    assert fetcher.list_attributes("dataset", contain="gene") == ["attr", "gene", None]
    assert fetcher.list_filters("dataset", pattern="id") == ["filter", None, "id"]


def test_biomart_empty_registry_raises_server_error(monkeypatch):
    fetcher = BioMart_Fetcher()
    monkeypatch.setattr(
        fetcher,
        "_make_request",
        lambda url, params: DummyResponse(text="<root></root>"),
    )

    with pytest.raises(APIServerError, match="empty mart registry"):
        fetcher.list_marts()


def test_biomart_convenience_methods_delegate_query_or_batch(monkeypatch):
    fetcher = BioMart_Fetcher()
    query_calls = []
    batch_calls = []

    def fake_query(**kwargs):
        query_calls.append(kwargs)
        return BioMartQueryData("ENSG1\tTP53\n", columns=kwargs["attributes"])

    def fake_batch_query(**kwargs):
        batch_calls.append(kwargs)
        return BioMartQueryData("ENSG1\tTP53\n", columns=kwargs["attributes"])

    monkeypatch.setattr(fetcher, "query", fake_query)
    monkeypatch.setattr(fetcher, "batch_query", fake_batch_query)

    fetcher.get_genes(["ENSG1"])
    fetcher.get_genes(["ENSG1", "ENSG2"], batch_size=1)
    fetcher.get_genes_by_name(["TP53"])
    fetcher.get_genes_by_name(["TP53", "BRCA1"], batch_size=1)
    fetcher.get_genes_by_chromosome("17", start=1, end=2)
    fetcher.get_transcripts(["ENSG1"])
    fetcher.get_transcripts(["ENSG1", "ENSG2"], batch_size=1)
    fetcher.get_go_annotations(["ENSG1"])
    fetcher.get_go_annotations(["ENSG1", "ENSG2"], batch_size=1)
    fetcher.get_homologs(["ENSG1"], target_species="mmusculus")
    fetcher.get_homologs(["ENSG1", "ENSG2"], target_species="mmusculus", batch_size=1)
    fetcher.convert_ids(["ENSG1"])
    fetcher.convert_ids(["ENSG1", "ENSG2"], batch_size=1)

    assert len(query_calls) == 7
    assert len(batch_calls) == 6
    assert {"chromosome_name": "17", "start": "1", "end": "2"} in [
        call["filters"] for call in query_calls
    ]
    assert batch_calls[-1]["filter_name"] == "ensembl_gene_id"
