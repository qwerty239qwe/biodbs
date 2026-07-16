"""Live reachability tests for NCBI static reference archives (network required).

Guards against NCBI moving the FTP archive paths. Uses HEAD requests so the large
archives are never downloaded.
"""

import pytest
import requests

from biodbs.fetch.NCBI.ncbi_fetcher import _BLAST_DB_URL, _TAXDUMP_URL

pytestmark = pytest.mark.integration


def _head_status(url: str) -> int:
    response = requests.head(url, allow_redirects=True, timeout=60)
    return response.status_code


def test_blast_16s_archive_and_md5_reachable():
    base = f"{_BLAST_DB_URL}16S_ribosomal_RNA.tar.gz"
    assert _head_status(base) == 200
    assert _head_status(f"{base}.md5") == 200


def test_new_taxdump_archive_reachable():
    assert _head_status(f"{_TAXDUMP_URL}new_taxdump.tar.gz") == 200
