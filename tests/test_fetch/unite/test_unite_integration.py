"""Live integration tests for the UNITE fetcher (network required).

Exercises the real PlutoF DOI API resolution (a lightweight metadata call, not a
full archive download).
"""

import pytest
import requests

from biodbs.fetch.UNITE import UNITE_Fetcher

pytestmark = pytest.mark.integration


def test_get_download_url_live():
    url = UNITE_Fetcher().get_download_url("2025-02-19", "fungi")

    assert url.startswith("http")
    assert url.endswith((".tgz", ".gz", ".zip"))


def test_resolved_archive_url_resolves_live():
    fetcher = UNITE_Fetcher()
    url = fetcher.get_download_url("2025-02-19", "fungi")

    response = requests.get(url, stream=True, timeout=60)
    status = response.status_code
    response.close()
    assert status == 200, url
