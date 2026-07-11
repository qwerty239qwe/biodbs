import pytest

from biodbs.exceptions import APIError
from biodbs.fetch._download import download_binary


class Response:
    status_code = 200
    headers = {"content-type": "application/octet-stream"}

    def __init__(self, chunks=(), text=""):
        self.chunks = chunks
        self.text = text
        self.closed = False

    def iter_content(self, chunk_size=1024 * 1024):
        yield from self.chunks

    def close(self):
        self.closed = True


def test_download_binary_atomically_installs_stream(tmp_path, monkeypatch):
    target = tmp_path / "db.tar.gz"

    def chunks():
        assert not target.exists()
        assert len(list(tmp_path.glob("*.part"))) == 1
        yield b"abc"
        yield b"def"

    response = Response(chunks())
    monkeypatch.setattr(
        "biodbs.fetch._download.request_with_retry",
        lambda url, stream=False: response,
    )

    assert download_binary("https://example/db.tar.gz", target, "test") == target
    assert target.read_bytes() == b"abcdef"
    assert list(tmp_path.glob("*.part")) == []
    assert response.closed


def test_download_binary_removes_partial_on_stream_failure(tmp_path, monkeypatch):
    def broken_chunks():
        yield b"partial"
        raise OSError("connection dropped")

    response = Response(broken_chunks())
    monkeypatch.setattr(
        "biodbs.fetch._download.request_with_retry",
        lambda url, stream=False: response,
    )
    target = tmp_path / "db.tar.gz"

    with pytest.raises(OSError, match="connection dropped"):
        download_binary("https://example/db.tar.gz", target, "test")

    assert not target.exists()
    assert list(tmp_path.glob("*.part")) == []
    assert response.closed


def test_download_binary_rejects_bad_md5(tmp_path, monkeypatch):
    binary = Response([b"abc"])
    checksum = Response(text="deadbeef  db.tar.gz\n")
    responses = iter([binary, checksum])
    monkeypatch.setattr(
        "biodbs.fetch._download.request_with_retry",
        lambda url, stream=False: next(responses),
    )
    target = tmp_path / "db.tar.gz"

    with pytest.raises(APIError, match="checksum"):
        download_binary(
            "https://example/db.tar.gz",
            target,
            "test",
            md5_url="https://example/db.tar.gz.md5",
        )

    assert not target.exists()
    assert list(tmp_path.glob("*.part")) == []
    assert binary.closed
    assert checksum.closed
