"""Focused tests for the shared atomic binary downloader."""

from pathlib import Path

import pytest

from biodbs.exceptions import APIError
from biodbs.fetch._download import download_binary


class Response:
    status_code = 200
    headers = {"content-type": "application/octet-stream"}

    def __init__(self, chunks):
        self.chunks = chunks

    def iter_content(self, chunk_size=1024 * 1024):
        yield from self.chunks

    @property
    def text(self):
        return b"".join(self.chunks).decode()

    def close(self):
        pass


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
