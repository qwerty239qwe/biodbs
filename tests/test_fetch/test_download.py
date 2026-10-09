"""Focused tests for the shared atomic binary downloader."""

from pathlib import Path

import pytest

from biodbs.exceptions import APIError
from biodbs.fetch._download import download_binary
from biodbs.fetch.GTDB.gtdb_fetcher import GTDB_Fetcher
from biodbs.fetch.HOMD.homd_fetcher import HOMD_Fetcher
from biodbs.fetch.GreenGenes.greengenes_fetcher import GreenGenes_Fetcher


class Response:
    status_code = 200
    headers = {"content-type": "application/octet-stream"}

    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def iter_content(self, chunk_size=1024 * 1024):
        yield from self.chunks

    @property
    def text(self):
        return b"".join(self.chunks).decode()

    def close(self):
        self.closed = True


@pytest.mark.parametrize("fetcher_class", [GTDB_Fetcher, HOMD_Fetcher, GreenGenes_Fetcher])
@pytest.mark.parametrize("overwrite", [False, True])
def test_fetcher_download_is_atomic_and_can_retry(fetcher_class, overwrite, tmp_path, monkeypatch):
    target = tmp_path / "taxonomy.tsv"
    if overwrite:
        target.write_bytes(b"original")

    def broken_chunks():
        yield b"partial"
        raise OSError("connection dropped")

    broken = Response(broken_chunks())
    complete = Response([b"complete"])
    responses = iter([broken, complete])
    calls = []

    def request(url, stream=False):
        calls.append((url, stream))
        return next(responses)

    # Exercise both the old direct path and the shared helper without networking.
    monkeypatch.setattr(f"{fetcher_class.__module__}.request_with_retry", request)
    monkeypatch.setattr("biodbs.fetch._download.request_with_retry", request)
    fetcher = fetcher_class()
    with pytest.raises(OSError, match="connection dropped"):
        fetcher.download_file("taxonomy.tsv", target, overwrite=overwrite)
    if overwrite:
        assert target.read_bytes() == b"original"
    else:
        assert not target.exists()
    assert not list(tmp_path.glob("*.part"))
    assert broken.closed

    assert fetcher.download_file("taxonomy.tsv", target, overwrite=overwrite) == target
    assert target.read_bytes() == b"complete"
    assert complete.closed
    assert fetcher.download_file("taxonomy.tsv", target) == target
    assert len(calls) == 2
    assert all(stream for _, stream in calls)
    assert not list(tmp_path.glob("*.part"))


def test_download_binary_replaces_target_only_after_success(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch._download.request_with_retry",
        lambda url, stream=False: Response([b"abc", b"def"]),
    )
    target = tmp_path / "db.tar.gz"
    assert download_binary("https://example/db.tar.gz", target, "test") == target
    assert target.read_bytes() == b"abcdef"
    assert list(tmp_path.glob("*.part")) == []


def test_download_binary_removes_partial_file_on_failure(tmp_path, monkeypatch):
    def broken_chunks():
        yield b"partial"
        raise OSError("connection dropped")

    monkeypatch.setattr(
        "biodbs.fetch._download.request_with_retry",
        lambda url, stream=False: Response(broken_chunks()),
    )
    target = tmp_path / "db.tar.gz"
    with pytest.raises(OSError, match="connection dropped"):
        download_binary("https://example/db.tar.gz", target, "test")
    assert not target.exists()
    assert list(tmp_path.glob("*.part")) == []


def test_download_binary_rejects_html_when_requested(tmp_path, monkeypatch):
    class HtmlResponse:
        status_code = 200
        headers = {"content-type": "text/html; charset=utf-8"}

        def iter_content(self, chunk_size=1024 * 1024):
            yield b"<!DOCTYPE html><html>..."

        def close(self):
            pass

    monkeypatch.setattr(
        "biodbs.fetch._download.request_with_retry",
        lambda url, stream=False: HtmlResponse(),
    )
    target = tmp_path / "foo.qza"
    with pytest.raises(APIError, match="HTML page"):
        download_binary("https://example/foo.qza", target, "SILVA", reject_html=True)
    assert not target.exists()
    assert list(tmp_path.glob("*.part")) == []


def test_download_binary_rejects_bad_md5(tmp_path, monkeypatch):
    responses = iter([Response([b"abc"]), Response([b"deadbeef  db.tar.gz\n"])])
    monkeypatch.setattr(
        "biodbs.fetch._download.request_with_retry",
        lambda url, stream=False: next(responses),
    )
    with pytest.raises(APIError, match="checksum"):
        download_binary(
            "https://example/db.tar.gz",
            tmp_path / "db.tar.gz",
            "test",
            md5_url="https://example/db.tar.gz.md5",
        )
