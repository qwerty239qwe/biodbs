"""Offline tests for SILVA fetcher."""

from pathlib import Path

import pytest

from biodbs.fetch.SILVA.silva_fetcher import SILVA_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, text="", content=b"", content_type=None):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode()
        self.headers = {"content-type": content_type} if content_type else {}

    def iter_content(self, chunk_size=8192):
        yield self.content


# SILVA's CMS links subpages with root-relative hrefs, mixed with global nav.
CURRENT_RELEASE_PAGE = """
<html><body>
<a href="/">Home</a>
<a href="/contact">Contact</a>
<a href="/current-release">Current release</a>
<a href="/current-release/QIIME2">QIIME2</a>
<a href="/current-release/DADA2">DADA2</a>
<a href="/current-release/QIIME2/2025.7">deep link, root should only show QIIME2</a>
<a href="/fileadmin/silva_databases/current/VERSION.txt">VERSION</a>
<a href="https://x.com/ARB_SILVA">external</a>
</body></html>
"""

LEAF_PAGE = """
<html><body>
<a href="/current-release/QIIME2/2025.7">Parent</a>
<a href="/fileadmin/silva_databases/current/QIIME2/2025.7/taxonomic-weights/human-oral.qza">human-oral.qza</a>
<a href="/fileadmin/silva_databases/current/QIIME2/2025.7/taxonomic-weights/human-oral.qza.md5">human-oral.qza.md5</a>
<a href="/fileadmin/silva_databases/current/QIIME2/2025.7/taxonomic-weights/deep/ignored.qza">deep file</a>
<a href="/contact">Contact</a>
</body></html>
"""


def test_list_current_files(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text=CURRENT_RELEASE_PAGE),
    )

    data = SILVA_Fetcher().list_current_files()

    # immediate browse children plus direct fileadmin-backed files
    assert data.names() == ["QIIME2", "DADA2", "VERSION.txt"]
    assert data["QIIME2"].is_dir is True
    assert data["DADA2"].is_dir is True
    assert data["VERSION.txt"].is_dir is False


def test_list_current_files_preserves_subdirectory_in_child_urls(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="/current-release/QIIME2/2025.7">2025.7</a>'
        ),
    )

    data = SILVA_Fetcher().list_current_files("QIIME2")

    assert data["2025.7"].url.endswith("/current-release/QIIME2/2025.7")


def test_list_current_files_returns_leaf_fileadmin_links(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text=LEAF_PAGE),
    )

    data = SILVA_Fetcher().list_current_files("QIIME2/2025.7/taxonomic-weights")

    assert data.names() == ["human-oral.qza", "human-oral.qza.md5"]
    assert data["human-oral.qza"].is_dir is False
    assert data["human-oral.qza"].url == (
        "https://www.arb-silva.de/fileadmin/silva_databases/current/"
        "QIIME2/2025.7/taxonomic-weights/human-oral.qza"
    )
    assert data["human-oral.qza.md5"].is_dir is False
    assert data["human-oral.qza.md5"].url == (
        "https://www.arb-silva.de/fileadmin/silva_databases/current/"
        "QIIME2/2025.7/taxonomic-weights/human-oral.qza.md5"
    )


def test_list_current_files_keeps_same_name_directory_and_file(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="/current-release/shared">directory</a>'
            '<a href="/current-release/shared">duplicate directory</a>'
            '<a href="/fileadmin/silva_databases/current/shared">file</a>'
        ),
    )

    data = SILVA_Fetcher().list_current_files()

    assert [(item.name, item.is_dir) for item in data] == [
        ("shared", True),
        ("shared", False),
    ]


def test_list_archive_releases(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="/archive/release_138">release_138</a>'
            '<a href="/archive/release_138/deep">deep</a>'
            '<a href="/archive/qiime">qiime</a>'
            '<a href="/current-release/release_fake">unrelated</a>'
        ),
    )

    data = SILVA_Fetcher().list_archive_releases()

    assert data.names() == ["release_138"]
    assert data["release_138"].url.endswith("/archive/release_138")


def test_get_text_files(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text="SILVA 138"),
    )

    data = SILVA_Fetcher().get_version()

    assert data.text == "SILVA 138"
    assert data.url.endswith("VERSION.txt")


def test_download_file_uses_shared_downloader(tmp_path, monkeypatch):
    seen = {}

    def fake_download(url, target, service, **kwargs):
        seen.update(url=url, target=Path(target), service=service, kwargs=kwargs)
        return Path(target)

    monkeypatch.setattr("biodbs.fetch.SILVA.silva_fetcher.download_binary", fake_download)
    dest = tmp_path / "data" / "silva"

    result = SILVA_Fetcher().download_file("README.txt", dest)

    assert result == dest / "README.txt"
    assert seen == {
        "url": "https://www.arb-silva.de/fileadmin/silva_databases/current/README.txt",
        "target": dest / "README.txt",
        "service": "SILVA",
        "kwargs": {"overwrite": False, "md5_url": None},
    }


def test_download_classifier_unknown_kind_raises_value_error(tmp_path):
    fetcher = SILVA_Fetcher()

    with pytest.raises(ValueError, match="Valid kinds"):
        fetcher.download_classifier("qiime", "taxonomy.qza", tmp_path)


def test_download_classifier_uses_published_md5(tmp_path, monkeypatch):
    seen = {}

    def fake_download(url, target, service, **kwargs):
        seen.update(url=url, target=Path(target), service=service, kwargs=kwargs)
        return Path(target)

    monkeypatch.setattr("biodbs.fetch.SILVA.silva_fetcher.download_binary", fake_download)

    result = SILVA_Fetcher().download_classifier(
        "qiime2", "2025.7/taxonomic-weights/human-oral.qza", tmp_path
    )

    expected_url = (
        "https://www.arb-silva.de/fileadmin/silva_databases/current/"
        "QIIME2/2025.7/taxonomic-weights/human-oral.qza"
    )
    assert result == tmp_path / "human-oral.qza"
    assert seen["url"] == expected_url
    assert seen["target"] == result
    assert seen["service"] == "SILVA"
    assert seen["kwargs"] == {"overwrite": False, "md5_url": f"{expected_url}.md5"}


def test_get_version_uses_fileadmin_base(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text="138.2", content_type="text/plain"),
    )

    data = SILVA_Fetcher().get_version()

    assert (
        data.url
        == "https://www.arb-silva.de/fileadmin/silva_databases/current/VERSION.txt"
    )
