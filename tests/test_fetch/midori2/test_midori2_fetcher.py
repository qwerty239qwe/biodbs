"""Offline regression tests for MIDORI2's Zenodo migration."""

import hashlib
from io import BytesIO
from zipfile import BadZipFile, ZipFile

import pytest

from biodbs.exceptions import APIError, APINotFoundError
from biodbs.fetch.MIDORI2.midori2_fetcher import MIDORI2_Fetcher

VERSION = "GenBank271_2026-04-07"
BASE = "https://mirror.example/Databases/"


class DummyResponse:
    def __init__(self, *, data=None, content=b"", status_code=200):
        self.data = data
        self.content = content
        self.status_code = status_code
        self.text = ""
        self.headers = {}
        self.closed = False

    def json(self):
        return self.data

    def iter_content(self, chunk_size=8192):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start : start + chunk_size]

    def close(self):
        self.closed = True


def make_bundle(version="GB271", species=False):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zipped:
        for unique in (True, False):
            for kind in ("fasta", "taxon"):
                member = MIDORI2_Fetcher._member("CO1", version, kind, unique, species)
                zipped.writestr(member, f"{kind}:{unique}:{species}".encode())
        zipped.writestr("../unrequested.txt", b"must not extract")
    return buffer.getvalue()


@pytest.fixture
def zenodo(monkeypatch):
    responses = {}
    record = {"metadata": {"version": "GB271"}, "files": []}
    for species in (False, True):
        qiime = "QIIME_sp" if species else "QIIME"
        key = f"MIDORI2_GB271_{qiime}.zip"
        url = f"https://zenodo.org/files/{key}"
        body = make_bundle(species=species)
        record["files"].append(
            {
                "key": key,
                "links": {"self": url},
                "checksum": "md5:" + hashlib.md5(body).hexdigest(),
            }
        )
        responses[url] = DummyResponse(content=body)
    responses["https://zenodo.org/api/records/22849929"] = DummyResponse(
        data={
            "metadata": {"version": "supplementary"},
            "files": [],
            "links": {"versions": "https://zenodo.org/legacy/versions"},
        }
    )
    responses["https://zenodo.org/legacy/versions"] = DummyResponse(
        data={
            "hits": {"hits": [record]},
            "links": {},
        }
    )
    responses["https://zenodo.org/api/records/22685700"] = DummyResponse(
        data={
            "metadata": {"version": "GB273"},
            "files": [],
            "links": {"versions": "https://zenodo.org/current/versions"},
        }
    )
    responses["https://zenodo.org/current/versions"] = DummyResponse(
        data={
            "hits": {"hits": []},
            "links": {},
        }
    )
    calls = []

    def request(url, **kwargs):
        calls.append((url, kwargs))
        return responses[url]

    monkeypatch.setattr(
        "biodbs.fetch.MIDORI2.midori2_fetcher.request_with_retry", request
    )
    monkeypatch.setattr("biodbs.fetch._download.request_with_retry", request)
    return responses, record, calls


@pytest.mark.parametrize("version", [VERSION, "GB271", "GenBank271"])
@pytest.mark.parametrize("kind", ["fasta", "taxon"])
def test_build_url_resolves_requested_version(zenodo, version, kind):
    assert MIDORI2_Fetcher().build_url("CO1", version, kind=kind) == (
        "https://zenodo.org/files/MIDORI2_GB271_QIIME.zip"
    )
    assert all(
        response.closed
        for url, response in zenodo[0].items()
        if url in {call[0] for call in zenodo[2]}
    )


def test_build_url_species_bundle_and_metadata_reuse(zenodo):
    fetcher = MIDORI2_Fetcher()
    url = fetcher.build_url("srRNA", VERSION, species=True)
    assert url.endswith("MIDORI2_GB271_QIIME_sp.zip")
    assert (
        fetcher.build_url("CO1", VERSION, species=True, unique=False, kind="taxon")
        == url
    )
    assert len(zenodo[2]) == 2


def test_release_discovery_follows_pagination(zenodo):
    responses, record, _ = zenodo
    responses["https://zenodo.org/legacy/versions"].data = {
        "hits": {"hits": []},
        "links": {"next": "https://zenodo.org/legacy/page2"},
    }
    responses["https://zenodo.org/legacy/page2"] = DummyResponse(
        data={
            "hits": {"hits": [record]},
            "links": {},
        }
    )
    assert "GB271" in MIDORI2_Fetcher().build_url("CO1", VERSION)


def test_latest_published_release(zenodo):
    latest = zenodo[0]["https://zenodo.org/api/records/22685700"].data
    latest["files"] = [
        {"key": "MIDORI2_GB273_QIIME.zip", "links": {"self": "current.zip"}}
    ]
    assert MIDORI2_Fetcher().build_url("CO1", "GB273") == "current.zip"
    assert len(zenodo[2]) == 1


def test_unpublished_release_does_not_fall_back(zenodo):
    with pytest.raises(ValueError, match="GB999.*not published"):
        MIDORI2_Fetcher().build_url("CO1", "GB999")
    assert all(not call[1].get("stream") for call in zenodo[2])


def test_missing_bundle_raises_before_download(zenodo):
    zenodo[1]["files"] = []
    with pytest.raises(ValueError, match="does not publish"):
        MIDORI2_Fetcher().build_url("CO1", VERSION)


@pytest.mark.parametrize(
    "gene,version,kind,error",
    [
        ("CO1", VERSION, "blast", "kind"),
        ("CO1", "v271", "fasta", "version"),
        ("CO1", "prefixGenBank271_2026-04-07", "fasta", "version"),
        ("CO1", "GenBank271_2026-04-07/../", "fasta", "version"),
        ("../CO1", VERSION, "fasta", "gene"),
        ("unknown", VERSION, "fasta", "gene"),
    ],
)
def test_invalid_input_never_requests(zenodo, gene, version, kind, error):
    with pytest.raises(ValueError, match=error):
        MIDORI2_Fetcher().build_url(gene, version, kind=kind)
    assert not zenodo[2]


@pytest.mark.parametrize("unique", [True, False])
@pytest.mark.parametrize("species", [True, False])
@pytest.mark.parametrize("kind", ["fasta", "taxon"])
def test_download_extracts_only_requested_member(
    zenodo, tmp_path, unique, species, kind
):
    directory = tmp_path / "new-directory"
    fetcher = MIDORI2_Fetcher()
    path = fetcher.download(
        "CO1", directory, VERSION, kind=kind, unique=unique, species=species
    )
    assert (
        path.name
        == fetcher._member("CO1", VERSION, kind, unique, species).rsplit("/", 1)[-1]
    )
    assert path.read_bytes() == f"{kind}:{unique}:{species}".encode()
    assert list(directory.iterdir()) == [path]
    assert list(tmp_path.iterdir()) == [directory]
    assert zenodo[2][-1][1]["stream"] is True
    count = len(zenodo[2])
    assert (
        MIDORI2_Fetcher().download("CO1", directory, VERSION, kind, unique, species)
        == path
    )
    assert len(zenodo[2]) == count


def test_custom_filename_and_successful_overwrite(zenodo, tmp_path):
    target = tmp_path / "custom.fasta.gz"
    target.write_bytes(b"old")
    assert MIDORI2_Fetcher().download("CO1", target, VERSION, overwrite=True) == target
    assert target.read_bytes() == b"fasta:True:False"
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("overwrite", [True, False])
def test_existing_suffixless_file_is_not_a_directory(zenodo, tmp_path, overwrite):
    target = tmp_path / "existing"
    target.write_bytes(b"old")
    result = MIDORI2_Fetcher().download("CO1", target, VERSION, overwrite=overwrite)
    assert result == target
    assert target.read_bytes() == (b"fasta:True:False" if overwrite else b"old")
    if not overwrite:
        assert not zenodo[2]


@pytest.mark.parametrize(
    "failure", ["checksum", "missing", "corrupt", "interrupted", "extraction"]
)
def test_failed_overwrite_keeps_old_file_and_cleans_up(
    zenodo, tmp_path, monkeypatch, failure
):
    responses, record, _ = zenodo
    archive = record["files"][0]
    response = responses[archive["links"]["self"]]
    error = APIError
    if failure == "checksum":
        archive["checksum"] = "md5:" + "0" * 32
    elif failure == "missing":
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zipped:
            zipped.writestr("other.file", b"unrelated")
        response.content = buffer.getvalue()
        error = ValueError
    elif failure == "corrupt":
        response.content = b"not a zip"
        error = BadZipFile
    elif failure == "interrupted":

        def interrupted(**kwargs):
            yield b"partial"
            raise OSError("connection interrupted")

        monkeypatch.setattr(response, "iter_content", interrupted)
        error = OSError
    elif failure == "extraction":

        def interrupted_copy(source, output, **kwargs):
            output.write(b"partial")
            raise OSError("disk full")

        monkeypatch.setattr(
            "biodbs.fetch.MIDORI2.midori2_fetcher.shutil.copyfileobj", interrupted_copy
        )
        error = OSError
    if failure in ("missing", "corrupt"):
        archive["checksum"] = "md5:" + hashlib.md5(response.content).hexdigest()
    target = tmp_path / "existing.gz"
    target.write_bytes(b"old")
    with pytest.raises(error):
        MIDORI2_Fetcher().download("CO1", target, VERSION, overwrite=True)
    assert target.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [target]
    assert response.closed


def test_invalid_published_checksum_never_downloads(zenodo, tmp_path):
    zenodo[1]["files"][0]["checksum"] = "sha256:unverified"
    with pytest.raises(APIError, match="valid Zenodo MD5"):
        MIDORI2_Fetcher().download("CO1", tmp_path, VERSION)
    assert not list(tmp_path.iterdir())
    assert all(not call[1].get("stream") for call in zenodo[2])


def test_metadata_http_error_closes_response(zenodo):
    response = zenodo[0]["https://zenodo.org/api/records/22849929"]
    response.status_code = 404
    with pytest.raises(APINotFoundError):
        MIDORI2_Fetcher().build_url("CO1", VERSION)
    assert response.closed


@pytest.mark.parametrize(
    "unique,species,kind",
    [
        (True, False, "fasta"),
        (True, False, "taxon"),
        (True, True, "fasta"),
        (False, False, "fasta"),
    ],
)
def test_explicit_legacy_mirror_still_builds_direct_urls(zenodo, unique, species, kind):
    member = MIDORI2_Fetcher._member("CO1", VERSION, kind, unique, species)
    assert MIDORI2_Fetcher(BASE).build_url("CO1", VERSION, kind, unique, species) == (
        f"{BASE}{VERSION}/{member}"
    )
    assert not zenodo[2]


def test_legacy_mirror_download(zenodo, tmp_path):
    fetcher = MIDORI2_Fetcher(BASE)
    url = fetcher.build_url("CO1", VERSION)
    zenodo[0][url] = DummyResponse(content=b"legacy gzip")
    target = fetcher.download("CO1", tmp_path, VERSION)
    assert target.read_bytes() == b"legacy gzip"
    assert len(zenodo[2]) == 1
    assert zenodo[0][url].closed
