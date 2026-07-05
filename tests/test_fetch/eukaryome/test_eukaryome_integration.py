"""Live integration tests for the EUKARYOME fetcher (network required).

These check that the constructed static URL resolves on the live server without
downloading the (large) archive body.
"""

import pytest
import requests

from biodbs.fetch.EUKARYOME import EUKARYOME_Fetcher, MARKERS

pytestmark = pytest.mark.integration


def _url_is_reachable(url: str) -> int:
    response = requests.get(url, stream=True, timeout=60)
    status = response.status_code
    response.close()
    return status


def test_build_url_resolves_for_each_marker_live():
    fetcher = EUKARYOME_Fetcher()
    for marker in MARKERS:
        url = fetcher.build_url(marker)
        assert _url_is_reachable(url) == 200, url
