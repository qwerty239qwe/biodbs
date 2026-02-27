#!/usr/bin/env python
"""Speed benchmark for biodbs library overhead.

Measures the time spent *inside the library* (URL construction, input
validation, rate-limit check, JSON parsing, FetchedData object construction)
by replacing HTTP calls with instant mocks.  Network latency is NOT measured.

Benchmarks included
-------------------
1. KEGG  -- single info/get/list call
2. ChEMBL -- single molecule fetch + filtered search
3. Ensembl -- single lookup call
4. Rate limiter -- per-call overhead of the singleton RateLimiter
5. Batch vs sequential -- 10-item KEGG batch vs 10 individual calls
6. pubchempy comparison -- if pubchempy is installed, compare PubChem fetch
   overhead side-by-side

Usage:
    uv run python benchmarks/speed_benchmark.py
    uv run python benchmarks/speed_benchmark.py --iterations 2000
    uv run python benchmarks/speed_benchmark.py --skip-pubchempy
"""

from __future__ import annotations

import argparse
import time
import timeit
from contextlib import contextmanager
from typing import Callable
from unittest.mock import Mock, patch

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="biodbs speed benchmark")
parser.add_argument(
    "--iterations", "-n", type=int, default=1000,
    help="Number of timeit iterations per benchmark (default: 1000)",
)
parser.add_argument(
    "--skip-pubchempy", action="store_true",
    help="Skip the pubchempy comparison even if it is installed",
)
args, _ = parser.parse_known_args()

N = args.iterations
SKIP_PUBCHEMPY = args.skip_pubchempy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(
    status: int = 200,
    json_data: object = None,
    text: str = "",
    content: bytes = b"",
) -> Mock:
    m = Mock()
    m.status_code = status
    m.text = text
    m.content = content
    m.headers = {}
    m.url = "http://mock"
    if json_data is not None:
        m.json.return_value = json_data
    else:
        m.json.side_effect = ValueError("no JSON")
    return m


def _fmt(seconds: float, n: int) -> str:
    per_call_us = seconds / n * 1_000_000
    return f"{per_call_us:8.2f} uss/call  (total {seconds*1000:.1f} ms for {n} calls)"


def _print_result(label: str, seconds: float, n: int) -> None:
    print(f"  {label:<45} {_fmt(seconds, n)}")


@contextmanager
def _high_rate_limits(*hosts: str):
    """Temporarily set very high rate limits so no real sleeping occurs."""
    from biodbs.fetch._rate_limit import get_rate_limiter
    limiter = get_rate_limiter()
    original = {}
    for host in hosts:
        original[host] = limiter._rates.get(host)
        limiter.set_rate(host, 1_000_000)   # 1 M req/s -> no sleep ever
    try:
        yield limiter
    finally:
        for host, rate in original.items():
            if rate is None:
                limiter._rates.pop(host, None)
            else:
                limiter.set_rate(host, rate)
        limiter._last_request.clear()


# ---------------------------------------------------------------------------
# Section 1: KEGG overhead
# ---------------------------------------------------------------------------

KEGG_MOCK_TEXT = "ENTRY   pathway\nNAME    Glycolysis\n"
KEGG_MOCK_JSON = {"name": "hsa05200"}

def bench_kegg() -> None:
    print("\n-- KEGG Fetcher -------------------------------------------------")

    from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher
    fetcher = KEGG_Fetcher()
    mock_text = _mock_response(200, text=KEGG_MOCK_TEXT)
    mock_text.text = KEGG_MOCK_TEXT
    mock_json = _mock_response(200, json_data=KEGG_MOCK_JSON)

    with _high_rate_limits("rest.kegg.jp"):
        # 1a. info (text response)
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = mock_text
            t = timeit.timeit(
                lambda: fetcher.get("info", database="pathway"), number=N
            )
        _print_result("kegg_info('pathway')", t, N)

        # 1b. get by entry (text response)
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = mock_text
            t = timeit.timeit(
                lambda: fetcher.get("get", dbentries=["hsa:7157"]), number=N
            )
        _print_result("kegg_get(['hsa:7157'])", t, N)

        # 1c. get with json option
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = mock_json
            t = timeit.timeit(
                lambda: fetcher.get("get", dbentries=["hsa:7157"], get_option="json"),
                number=N,
            )
        _print_result("kegg_get([..], get_option='json')", t, N)

        # 1d. find (text response)
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = mock_text
            t = timeit.timeit(
                lambda: fetcher.get("find", database="genes", query="tp53"),
                number=N,
            )
        _print_result("kegg_find('genes', 'tp53')", t, N)


# ---------------------------------------------------------------------------
# Section 2: ChEMBL overhead
# ---------------------------------------------------------------------------

CHEMBL_MOLECULE_JSON = {
    "molecule_chembl_id": "CHEMBL25",
    "pref_name": "ASPIRIN",
    "max_phase": 4,
    "molecular_formula": "C9H8O4",
    "molecular_weight": "180.16",
}

CHEMBL_SEARCH_JSON = {
    "molecules": [
        {"molecule_chembl_id": "CHEMBL25", "pref_name": "ASPIRIN"},
        {"molecule_chembl_id": "CHEMBL1697753", "pref_name": "ASPIRIN CALCIUM"},
    ]
}


def bench_chembl() -> None:
    print("\n-- ChEMBL Fetcher -----------------------------------------------")

    from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher
    fetcher = ChEMBL_Fetcher()
    mock_mol  = _mock_response(200, json_data=CHEMBL_MOLECULE_JSON)
    mock_srch = _mock_response(200, json_data=CHEMBL_SEARCH_JSON)
    mock_acts = _mock_response(200, json_data={"activities": []})

    with _high_rate_limits("www.ebi.ac.uk"):
        # 2a. get single molecule by ID
        with patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests") as m:
            m.get.return_value = mock_mol
            t = timeit.timeit(
                lambda: fetcher.get(resource="molecule", chembl_id="CHEMBL25"),
                number=N,
            )
        _print_result("chembl_get_molecule('CHEMBL25')", t, N)

        # 2b. search molecules
        with patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests") as m:
            m.get.return_value = mock_srch
            t = timeit.timeit(
                lambda: fetcher.get(resource="molecule", search_query="aspirin", limit=10),
                number=N,
            )
        _print_result("chembl_search_molecules('aspirin')", t, N)

        # 2c. filtered activity query
        with patch("biodbs.fetch.ChEMBL.chembl_fetcher.requests") as m:
            m.get.return_value = mock_acts
            t = timeit.timeit(
                lambda: fetcher.get(
                    resource="activity",
                    filters={"target_chembl_id": "CHEMBL240"},
                    limit=10,
                ),
                number=N,
            )
        _print_result("chembl_get_activities(target='CHEMBL240')", t, N)


# ---------------------------------------------------------------------------
# Section 3: Ensembl overhead
# ---------------------------------------------------------------------------

ENSEMBL_LOOKUP_JSON = {
    "id": "ENSG00000141510",
    "display_name": "TP53",
    "biotype": "protein_coding",
    "species": "homo_sapiens",
}


def bench_ensembl() -> None:
    print("\n-- Ensembl Fetcher ----------------------------------------------")

    from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher
    fetcher = Ensembl_Fetcher()
    mock_resp = _mock_response(200, json_data=ENSEMBL_LOOKUP_JSON)

    with _high_rate_limits("rest.ensembl.org"):
        # 3a. lookup by Ensembl ID
        with patch("biodbs.fetch.ensembl.ensembl_fetcher.requests") as m:
            m.get.return_value = mock_resp
            m.post.return_value = mock_resp
            t = timeit.timeit(
                lambda: fetcher.get(endpoint="lookup/id", id="ENSG00000141510"),
                number=N,
            )
        _print_result("ensembl_lookup('ENSG00000141510')", t, N)

        # 3b. sequence endpoint
        mock_seq = _mock_response(200, json_data={"seq": "ATGCATGC", "id": "ENST00000269305"})
        with patch("biodbs.fetch.ensembl.ensembl_fetcher.requests") as m:
            m.get.return_value = mock_seq
            m.post.return_value = mock_seq
            t = timeit.timeit(
                lambda: fetcher.get(endpoint="sequence/id", id="ENST00000269305"),
                number=N,
            )
        _print_result("ensembl_get_sequence('ENST...')", t, N)


# ---------------------------------------------------------------------------
# Section 4: Rate limiter overhead
# ---------------------------------------------------------------------------

def bench_rate_limiter() -> None:
    print("\n-- Rate Limiter Overhead ----------------------------------------")
    print("  (comparing identical KEGG calls with/without rate limit check)")

    from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher
    fetcher = KEGG_Fetcher()
    mock_text = _mock_response(200, text=KEGG_MOCK_TEXT)
    mock_text.text = KEGG_MOCK_TEXT

    # Baseline: very high rate limit (effectively no sleep, but check still runs)
    with _high_rate_limits("rest.kegg.jp"):
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = mock_text
            t_with = timeit.timeit(
                lambda: fetcher.get("info", database="pathway"), number=N
            )

    # Patch out the rate-limit check entirely
    from biodbs.fetch import _rate_limit as _rl_mod

    def _noop_acquire(_self, _host: str) -> None:
        pass

    with patch.object(_rl_mod.RateLimiter, "acquire", _noop_acquire):
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = mock_text
            t_without = timeit.timeit(
                lambda: fetcher.get("info", database="pathway"), number=N
            )

    per_call_with    = t_with    / N * 1_000_000
    per_call_without = t_without / N * 1_000_000
    overhead         = per_call_with - per_call_without

    print(f"  {'with rate limit check':<45} {per_call_with:8.2f} uss/call")
    print(f"  {'without rate limit check':<45} {per_call_without:8.2f} uss/call")
    print(f"  {'rate limiter overhead':<45} {overhead:8.2f} uss/call")


# ---------------------------------------------------------------------------
# Section 5: Batch vs sequential
# ---------------------------------------------------------------------------

BATCH_SIZE = 10

def bench_batch_vs_sequential() -> None:
    print(f"\n-- Batch vs Sequential ({BATCH_SIZE} KEGG entries) ----------------------")

    from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher
    fetcher = KEGG_Fetcher()
    mock_text = _mock_response(200, text=KEGG_MOCK_TEXT * BATCH_SIZE)
    mock_text.text = KEGG_MOCK_TEXT * BATCH_SIZE
    entries = [f"hsa:{i}" for i in range(BATCH_SIZE)]

    with _high_rate_limits("rest.kegg.jp"):
        # Batch call (get_all builds one concatenated request)
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = mock_text
            t_batch = timeit.timeit(
                lambda: fetcher.get_all("get", dbentries=entries),
                number=max(N // 10, 100),
            )
        n_batch = max(N // 10, 100)
        per_batch = t_batch / n_batch * 1_000_000

        # Sequential (10 individual calls)
        single_mock = _mock_response(200, text=KEGG_MOCK_TEXT)
        single_mock.text = KEGG_MOCK_TEXT
        with patch("biodbs.utils.fetch.requests") as m:
            m.get.return_value = single_mock
            t_seq = timeit.timeit(
                lambda: [fetcher.get("get", dbentries=[e]) for e in entries],
                number=max(N // 10, 100),
            )
        per_seq = t_seq / n_batch * 1_000_000

    print(f"  {'get_all (batch, 1 HTTP call)':<45} {per_batch:8.2f} uss/10-entry batch")
    print(f"  {'10x individual get calls':<45} {per_seq:8.2f} uss/10-entry batch")
    speedup = per_seq / per_batch if per_batch > 0 else float("inf")
    print(f"  {'batch speedup':<45} {speedup:8.2f}x")


# ---------------------------------------------------------------------------
# Section 6: biodbs vs pubchempy (PubChem comparison)
# ---------------------------------------------------------------------------

PUBCHEM_PUG_JSON = {
    "PC_Compounds": [
        {
            "id": {"id": {"cid": 2244}},
            "props": [
                {
                    "urn": {"label": "MolecularFormula", "name": "Molecular Formula"},
                    "value": {"sval": "C9H8O4"},
                },
                {
                    "urn": {"label": "MolecularWeight", "name": "Molecular Weight"},
                    "value": {"fval": 180.16},
                },
            ],
        }
    ]
}


def bench_pubchem_comparison() -> None:
    if SKIP_PUBCHEMPY:
        return

    try:
        import pubchempy as pcp
    except ImportError:
        print("\n-- PubChem Comparison -------------------------------------------")
        print("  pubchempy not installed -- skipping (install with: pip install pubchempy)")
        return

    print("\n-- PubChem Comparison (biodbs vs pubchempy) ---------------------")

    # --- biodbs ---
    from biodbs.fetch.pubchem.pubchem_fetcher import PubChem_Fetcher
    pc_fetcher = PubChem_Fetcher()
    mock_pug = _mock_response(200, json_data=PUBCHEM_PUG_JSON)

    with _high_rate_limits("pubchem.ncbi.nlm.nih.gov"):
        with patch("biodbs.fetch.pubchem.pubchem_fetcher.requests") as m:
            m.get.return_value = mock_pug
            t_biodbs = timeit.timeit(
                lambda: pc_fetcher.get_compound(2244),
                number=N,
            )
    per_biodbs = t_biodbs / N * 1_000_000

    # --- pubchempy ---
    # pubchempy uses urllib internally; patch at the urllib level
    import urllib.request

    class _FakeHTTPResponse:
        def __init__(self, data: bytes):
            self._data = data

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    import json as _json
    fake_body = _json.dumps(PUBCHEM_PUG_JSON).encode()
    fake_resp = _FakeHTTPResponse(fake_body)

    with patch("urllib.request.urlopen", return_value=fake_resp):
        try:
            t_pcp = timeit.timeit(
                lambda: pcp.get_compounds(2244, "cid"),
                number=N,
            )
            per_pcp = t_pcp / N * 1_000_000
            pcp_ok = True
        except Exception as exc:
            per_pcp = 0.0
            pcp_ok = False
            pcp_err = str(exc)

    print(f"  {'biodbs pubchem_get_compound(2244)':<45} {per_biodbs:8.2f} uss/call")
    if pcp_ok:
        print(f"  {'pubchempy get_compounds(2244)':<45} {per_pcp:8.2f} uss/call")
        ratio = per_biodbs / per_pcp if per_pcp > 0 else float("inf")
        sign = "faster" if ratio < 1 else "slower"
        print(f"  biodbs is {abs(ratio - 1) * 100:.0f}% {sign} than pubchempy per call")
        print(
            "  (biodbs adds rate-limiting, pydantic validation, FetchedData construction;\n"
            "   pubchempy returns simpler Compound objects with no built-in rate limiting)"
        )
    else:
        print(f"  pubchempy mocking failed: {pcp_err}")


# ---------------------------------------------------------------------------
# Section 7: Baseline -- raw requests
# ---------------------------------------------------------------------------

def bench_raw_requests_baseline() -> None:
    print("\n-- Raw requests Baseline ----------------------------------------")
    print("  (pure requests.get -> .text / .json() with instant mock -- no library overhead)")

    import requests

    mock_text = _mock_response(200, text=KEGG_MOCK_TEXT)
    mock_text.text = KEGG_MOCK_TEXT
    mock_json = _mock_response(200, json_data=CHEMBL_MOLECULE_JSON)

    with patch("requests.get") as m:
        m.return_value = mock_text
        t_text = timeit.timeit(
            lambda: requests.get("http://rest.kegg.jp/info/pathway").text,
            number=N,
        )
    _print_result("requests.get().text (text response)", t_text, N)

    with patch("requests.get") as m:
        m.return_value = mock_json
        t_json = timeit.timeit(
            lambda: requests.get("http://www.ebi.ac.uk/chembl/api").json(),
            number=N,
        )
    _print_result("requests.get().json() (JSON response)", t_json, N)

    print(
        "\n  Interpretation: The difference between these baselines and the biodbs\n"
        "  numbers above represents the total library overhead per call\n"
        "  (URL construction, validation, rate-limit check, FetchedData wrapping)."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\nbioDBs Speed Benchmark  (N={N} iterations per benchmark)")
    print("Generated by benchmarks/speed_benchmark.py")
    print("HTTP is mocked -- only in-process library overhead is measured.\n")

    bench_raw_requests_baseline()
    bench_kegg()
    bench_chembl()
    bench_ensembl()
    bench_rate_limiter()
    bench_batch_vs_sequential()
    bench_pubchem_comparison()

    print("\n" + "=" * 70)
    print("Done.")
    print(
        "Tip: run with --iterations 5000 for more stable averages,\n"
        "     or --skip-pubchempy to omit the pubchempy comparison."
    )


if __name__ == "__main__":
    main()
