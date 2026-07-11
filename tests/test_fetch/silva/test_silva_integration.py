"""Live integration tests for the SILVA fetcher (network required).

Guards against SILVA's CMS migration: real files must come from the
``fileadmin/silva_databases/current/`` base, not the ``current-release/`` browse
pages. Checks headers only so the large ``.qza`` body is not downloaded.
"""

import pytest
import requests

from biodbs.fetch.SILVA import SILVA_Fetcher

pytestmark = pytest.mark.integration

# A real classifier file confirmed to be served as a binary download.
_CLASSIFIER = "QIIME2/2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza"


def _content_type(url: str):
    response = requests.get(url, stream=True, timeout=60)
    ct = response.headers.get("content-type", "")
    status = response.status_code
    response.close()
    return status, ct


def test_fileadmin_classifier_url_serves_real_file():
    url = SILVA_Fetcher().file_base_url + _CLASSIFIER
    status, ct = _content_type(url)
    assert status == 200
    assert "html" not in ct.lower(), f"expected a binary file, got {ct!r}"


def test_current_release_path_is_a_cms_html_page():
    # Documents the trap the fetcher must avoid: the browse path returns HTML.
    url = "https://www.arb-silva.de/current-release/" + _CLASSIFIER
    _, ct = _content_type(url)
    assert "html" in ct.lower()


def test_get_version_returns_plain_text():
    data = SILVA_Fetcher().get_version()
    assert data.text.strip()
    assert "<html" not in data.text.lower()
