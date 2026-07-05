"""Live integration tests for the MIDORI2 fetcher (network required).

Checks that the constructed static URL resolves on the live server without
downloading the archive body. Bump ``VERSION`` if MIDORI2 retires this release.
"""

import pytest
import requests

from biodbs.fetch.MIDORI2 import MIDORI2_Fetcher

pytestmark = pytest.mark.integration

VERSION = "GenBank271_2026-04-07"


def _url_is_reachable(url: str) -> int:
    response = requests.get(url, stream=True, timeout=60)
    status = response.status_code
    response.close()
    return status


def test_fasta_url_resolves_live():
    url = MIDORI2_Fetcher().build_url("CO1", VERSION)
    assert _url_is_reachable(url) == 200, url


def test_taxon_sidecar_url_resolves_live():
    url = MIDORI2_Fetcher().build_url("CO1", VERSION, kind="taxon")
    assert _url_is_reachable(url) == 200, url
