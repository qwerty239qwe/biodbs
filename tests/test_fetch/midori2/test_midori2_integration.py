"""Live integration tests for the MIDORI2 fetcher (network required).

Checks legacy and current releases, including both QIIME variants, using 64 KiB
range requests, never downloading the complete reference bundles.
"""

from io import BytesIO
from zipfile import ZipFile

import pytest
import requests

from biodbs.fetch.MIDORI2 import MIDORI2_Fetcher

pytestmark = pytest.mark.integration

VERSION = "GenBank271_2026-04-07"


@pytest.fixture(
    scope="module",
    params=[(VERSION, False), (VERSION, True), ("GB273", False), ("GB273", True)],
)
def bundle_members(request):
    version, species = request.param
    fetcher = MIDORI2_Fetcher()
    url = fetcher.build_url("CO1", version, species=species)
    qiime = "QIIME_sp" if species else "QIIME"
    num = "271" if version == VERSION else "273"
    assert f"MIDORI2_GB{num}_{qiime}.zip" in url
    assert fetcher.build_url("CO1", version, kind="taxon", species=species) == url
    with requests.get(
        url, headers={"Range": "bytes=-65536"}, stream=True, timeout=60
    ) as response:
        assert response.status_code == 206, url
        assert response.headers["Content-Range"].startswith("bytes ")
        tail = response.raw.read(65536)
    with ZipFile(BytesIO(tail)) as zipped:
        return qiime, num, species, set(zipped.namelist())


def test_fasta_url_resolves_live(bundle_members):
    _assert_members(bundle_members, "fasta")


def test_taxon_sidecar_url_resolves_live(bundle_members):
    _assert_members(bundle_members, "taxon")


def _assert_members(bundle_members, kind):
    qiime, num, species, members = bundle_members
    sp_tag = "SP_" if species else ""
    for directory, tag in (("uniq", "UNIQ"), ("longest", "LONGEST")):
        for gene in ("CO1", "srRNA"):
            name = f"MIDORI2_{tag}_NUC_{sp_tag}GB{num}_{gene}_QIIME.{kind}.gz"
            assert f"{qiime}/{directory}/{name}" in members
