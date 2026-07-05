"""Offline tests for the MIDORI2 fetcher."""

import pytest

from biodbs.fetch.MIDORI2.midori2_fetcher import MIDORI2_Fetcher

VERSION = "GenBank271_2026-04-07"
BASE = "https://www.reference-midori.info/download/Databases/"


class DummyResponse:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content
        self.text = ""
        self.headers = {}

    def iter_content(self, chunk_size=8192):
        yield self.content


def test_build_url_default_fasta():
    url = MIDORI2_Fetcher().build_url("CO1", VERSION)

    assert url == BASE + f"{VERSION}/QIIME/uniq/MIDORI2_UNIQ_NUC_GB271_CO1_QIIME.fasta.gz"


def test_build_url_taxon_sidecar():
    url = MIDORI2_Fetcher().build_url("CO1", VERSION, kind="taxon")

    assert url.endswith("MIDORI2_UNIQ_NUC_GB271_CO1_QIIME.taxon.gz")


def test_build_url_species_level():
    url = MIDORI2_Fetcher().build_url("srRNA", VERSION, species=True)

    assert url == BASE + f"{VERSION}/QIIME_sp/uniq/MIDORI2_UNIQ_NUC_SP_GB271_srRNA_QIIME.fasta.gz"


def test_build_url_longest():
    url = MIDORI2_Fetcher().build_url("CO1", VERSION, unique=False)

    assert url == BASE + f"{VERSION}/QIIME/longest/MIDORI2_LONGEST_NUC_GB271_CO1_QIIME.fasta.gz"


def test_build_url_invalid_kind_raises():
    with pytest.raises(ValueError, match="kind"):
        MIDORI2_Fetcher().build_url("CO1", VERSION, kind="blast")


def test_build_url_bad_version_raises():
    with pytest.raises(ValueError, match="version"):
        MIDORI2_Fetcher().build_url("CO1", "v271")


def test_download(tmp_path, monkeypatch):
    calls = []

    def fake_request(url, stream=False):
        calls.append((url, stream))
        return DummyResponse(content=b"gz")

    monkeypatch.setattr(
        "biodbs.fetch.MIDORI2.midori2_fetcher.request_with_retry", fake_request
    )
    fetcher = MIDORI2_Fetcher()

    path = fetcher.download("CO1", tmp_path, VERSION)

    assert path == tmp_path / "MIDORI2_UNIQ_NUC_GB271_CO1_QIIME.fasta.gz"
    assert path.read_bytes() == b"gz"
    assert calls[0][1] is True
    assert fetcher.download("CO1", tmp_path, VERSION) == path
    assert len(calls) == 1
