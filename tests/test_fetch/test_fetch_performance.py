"""Offline correctness and request-count regressions for faster fetching."""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from biodbs.fetch._base import BaseDataFetcher
from biodbs.fetch import _rate_limit
from biodbs.fetch.pubchem import pubchem_fetcher
from biodbs.fetch.QuickGO.quickgo_fetcher import QuickGO_Fetcher
from biodbs.data.QuickGO.data import QuickGOFetchedData
from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher
from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher
from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher
from biodbs.fetch.HPA.hpa_fetcher import HPA_Fetcher
from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher


def test_pubchem_concurrent_batches_keep_their_own_parameters(monkeypatch):
    barrier = threading.Barrier(2)
    validate = pubchem_fetcher.PUGRestNameSpaceValidator.validate

    def overlap(self, **kwargs):
        result = validate(self, **kwargs)
        if kwargs["identifiers"] != [1]:
            barrier.wait(timeout=2)
        return result

    calls = []

    def request(url, params=None):
        cid = int(url.split("/cid/")[1].split("/")[0])
        calls.append(cid)
        return SimpleNamespace(status_code=200, json=lambda: {
            "PropertyTable": {"Properties": [{"CID": cid, "MolecularFormula": str(cid)}]},
        })

    monkeypatch.setattr(pubchem_fetcher.PUGRestNameSpaceValidator, "validate", overlap)
    monkeypatch.setattr(pubchem_fetcher, "request_with_retry", request)
    result = pubchem_fetcher.PubChem_Fetcher().get_all(
        "compound", "cid", [1, 2, 3], batch_size=1, operation="property",
        properties=["MolecularFormula"], rate_limit_per_second=1000, max_concurrency=2,
    )
    assert sorted(calls) == [1, 2, 3]
    assert [row["CID"] for row in result.results] == [1, 2, 3]


def test_pubchem_concurrent_views_keep_heading_and_record(monkeypatch):
    barrier = threading.Barrier(2)
    validate = pubchem_fetcher.PUGViewNameSpaceValidator.validate

    def overlap(self, **kwargs):
        result = validate(self, **kwargs)
        barrier.wait(timeout=2)
        return result

    calls = []

    def request(url, params=None):
        record = int(url.split("/compound/")[1].split("/")[0])
        calls.append((record, params["heading"]))
        return SimpleNamespace(status_code=200, json=lambda: {"Record": {"RecordNumber": record}})

    monkeypatch.setattr(pubchem_fetcher.PUGViewNameSpaceValidator, "validate", overlap)
    monkeypatch.setattr(pubchem_fetcher, "request_with_retry", request)
    fetcher = pubchem_fetcher.PubChem_Fetcher()
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(fetcher.get_view, 1, heading="Safety and Hazards")
        second = executor.submit(fetcher.get_view, 2, heading="Names and Identifiers")
        assert [first.result().record_id, second.result().record_id] == [1, 2]
    assert sorted(calls) == [(1, "Safety and Hazards"), (2, "Names and Identifiers")]


@pytest.mark.parametrize("concurrency", [1, 3, 10])
def test_scheduler_concurrency_is_independent_of_start_rate(monkeypatch, concurrency):
    clock = [100.0]
    starts = []
    active = [0, 0]
    real_sleep = asyncio.sleep

    async def sleep(delay):
        clock[0] += delay
        await real_sleep(0)

    async def fetch(index):
        starts.append(clock[0])
        active[0] += 1
        active[1] = max(active)
        if active[0] == concurrency:
            release.set()
        await asyncio.wait_for(release.wait(), timeout=2)
        await real_sleep(0)
        active[0] -= 1
        return index

    release = asyncio.Event()
    monkeypatch.setattr("biodbs.fetch._base.time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr("biodbs.fetch._base.asyncio.sleep", sleep)
    result = BaseDataFetcher(None, None, {}).schedule_process(
        fetch, args_list=[(i,) for i in range(12)], rate_limit_per_second=1,
        max_concurrency=concurrency,
    )
    assert result == list(range(12))
    assert active[1] == concurrency
    assert starts == pytest.approx([100 + i for i in range(12)])


@pytest.mark.parametrize("concurrency", [0, -1, 1.5])
def test_scheduler_rejects_invalid_concurrency(concurrency):
    with pytest.raises(ValueError, match="max_concurrency"):
        BaseDataFetcher(None, None, {}).schedule_process(lambda: None, max_concurrency=concurrency)


def test_sessions_are_reused_per_thread_and_isolated_between_workers(monkeypatch):
    monkeypatch.setattr(_rate_limit, "_http_local", threading.local())
    barrier = threading.Barrier(2)

    def sessions():
        session = _rate_limit.get_http_session()
        barrier.wait(timeout=2)
        return session, _rate_limit.get_http_session()

    with ThreadPoolExecutor(max_workers=2) as executor:
        one, two = list(executor.map(lambda _: sessions(), range(2)))
    main = _rate_limit.get_http_session()
    try:
        assert one[0] is one[1]
        assert two[0] is two[1]
        assert len({id(main), id(one[0]), id(two[0])}) == 3
    finally:
        for session in (main, one[0], two[0]):
            session.close()


def test_shared_transport_reuses_a_real_http_connection(monkeypatch):
    """Loopback only: verify pooling, not just reuse of a Python object."""
    ports = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            ports.append(self.client_address[1])
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    monkeypatch.setattr(_rate_limit, "_http_local", threading.local())
    session = _rate_limit.get_http_session()
    session.trust_env = False
    thread.start()
    try:
        for _ in range(3):
            response = _rate_limit.request_with_retry(
                f"http://127.0.0.1:{server.server_port}/", rate_limit=False, timeout=2,
            )
            assert response.content == b"ok"
            response.close()
        assert len(ports) == 3
        assert len(set(ports)) == 1
    finally:
        session.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("method", ["GET", "POST", "PATCH"])
@pytest.mark.parametrize("status", [429, 503])
def test_retries_reuse_session_and_close_failed_streams(monkeypatch, method, status):
    session = MagicMock()
    failed = MagicMock(status_code=status, headers={"Retry-After": "0"}, text="temporary")
    success = MagicMock(status_code=200)
    transport = session.get if method == "GET" else session.post if method == "POST" else session.request
    transport.side_effect = [failed, success]
    monkeypatch.setattr(_rate_limit, "get_http_session", lambda: session)
    monkeypatch.setattr(_rate_limit.time, "sleep", lambda _: None)
    result = _rate_limit.request_with_retry(
        "https://example.test", method=method, rate_limit=False, stream=True,
        params={"page": 2}, timeout=7,
    )
    assert result is success
    assert transport.call_count == 2
    for call in transport.call_args_list:
        assert call.kwargs["stream"] is True
        assert call.kwargs["timeout"] == 7
        assert call.kwargs["params"] == {"page": 2}
    failed.close.assert_called_once()
    success.close.assert_not_called()


def test_ensembl_reuses_transport_for_get_and_post(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr("biodbs.fetch.ensembl.ensembl_fetcher.get_http_session", lambda: session)
    fetcher = Ensembl_Fetcher()
    assert fetcher._make_request("https://example.test", {}) is session.get.return_value
    assert fetcher._make_request("https://example.test", {}, True, {"ids": ["gene"]}) is session.post.return_value
    assert session.get.call_args.kwargs["timeout"] == 30
    assert session.post.call_args.kwargs["headers"]["Content-Type"] == "application/json"


@pytest.mark.parametrize("limit,requests", [(100, 100), (200, 50)])
def test_quickgo_page_size_reduces_requests_without_losing_rows(monkeypatch, limit, requests):
    fetcher = QuickGO_Fetcher()
    calls = []

    def page(url, params, endpoint, download_format=None):
        calls.append(params.copy())
        offset = (params["page"] - 1) * params["limit"]
        return QuickGOFetchedData({
            "results": [{"id": i} for i in range(offset, min(offset + params["limit"], 10000))],
            "numberOfHits": 10000,
        }, endpoint=endpoint)

    def schedule(**kwargs):
        assert kwargs["max_concurrency"] == 7
        return [kwargs["get_func"](*args) for args in kwargs["args_list"]]

    monkeypatch.setattr(fetcher, "_fetch_page", page)
    monkeypatch.setattr(fetcher, "schedule_process", schedule)
    options = {} if limit == 200 else {"limit_per_page": limit}
    result = fetcher.get_all("annotation", "search", taxonId=9606, max_concurrency=7, **options)
    assert len(calls) == requests
    assert [row["id"] for row in result.results] == list(range(10000))


@pytest.mark.parametrize("limit", [0, -1, 201])
def test_quickgo_rejects_invalid_annotation_page_size_before_fetch(monkeypatch, limit):
    transport = MagicMock()
    monkeypatch.setattr("biodbs.fetch.QuickGO.quickgo_fetcher.get_http_session", transport)
    with pytest.raises(ValueError, match="limit"):
        QuickGO_Fetcher().get_all("annotation", "search", limit_per_page=limit)
    transport.assert_not_called()


@pytest.mark.parametrize("max_records", [0, 3])
def test_quickgo_single_page_honors_record_cap(monkeypatch, max_records):
    fetcher = QuickGO_Fetcher()
    page = MagicMock(return_value=QuickGOFetchedData({
        "results": [{"id": i} for i in range(10)], "numberOfHits": 10,
    }, endpoint="search"))
    monkeypatch.setattr(fetcher, "_fetch_page", page)
    result = fetcher.get_all("annotation", "search", max_records=max_records)
    assert len(result.results) == max_records
    assert page.call_count == bool(max_records)


@pytest.mark.parametrize("factory,args", [
    (QuickGO_Fetcher, ("annotation", "search")),
    (pubchem_fetcher.PubChem_Fetcher, ("compound", "cid", [1])),
    (ChEMBL_Fetcher, ("molecule",)),
    (FDA_Fetcher, ("drug", "event")),
    (KEGG_Fetcher, ("get", ["hsa:7157"])),
    (HPA_Fetcher, (["ENSG00000141510"],)),
])
@pytest.mark.parametrize("option,value", [
    ("max_concurrency", 0), ("max_concurrency", -1), ("max_concurrency", 1.5),
    ("rate_limit_per_second", 0),
])
def test_batch_entrypoints_validate_scheduling_options_before_fetch(factory, args, option, value, tmp_path):
    fetcher = factory(storage_path=tmp_path) if factory is FDA_Fetcher else factory()
    method = fetcher.get_genes if isinstance(fetcher, HPA_Fetcher) else fetcher.get_all
    with pytest.raises(ValueError, match=option):
        method(*args, **{option: value})
