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


# SILVA's CMS lists sub-directories as /current-release/ links and downloadable
# files as direct /fileadmin/silva_databases/current/ links, mixed with global nav.
CURRENT_RELEASE_PAGE = """
<html><body>
<a href="/">Home</a>
<a href="/contact">Contact</a>
<a href="/current-release">Current release</a>
<a href="/current-release/QIIME2">QIIME2</a>
<a href="/current-release/DADA2">DADA2</a>
<a href="/current-release/QIIME2/2025.7">deep link, root should only show QIIME2</a>
<a href="https://x.com/ARB_SILVA">external</a>
</body></html>
"""

CLASSIFIER_PAGE = """
<html><body>
<a href="/current-release/QIIME2/2025.7">..</a>
<a href="/fileadmin/silva_databases/current/QIIME2/2025.7/taxonomic-weights/human-oral.qza">human-oral.qza</a>
<a href="/fileadmin/silva_databases/current/QIIME2/2025.7/taxonomic-weights/human-oral.qza.md5">human-oral.qza.md5</a>
</body></html>
"""


def test_list_current_files(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text=CURRENT_RELEASE_PAGE),
    )

    data = SILVA_Fetcher().list_current_files()

    # only immediate child dirs under /current-release/, nav/deep-link/external excluded
    assert data.names() == ["QIIME2", "DADA2"]
    assert data["QIIME2"].is_dir is True


def test_list_current_files_returns_fileadmin_leaves(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text=CLASSIFIER_PAGE),
    )

    data = SILVA_Fetcher().list_current_files("QIIME2/2025.7/taxonomic-weights")

    assert data.names() == ["human-oral.qza", "human-oral.qza.md5"]
    assert data["human-oral.qza"].is_dir is False
    assert "/fileadmin/silva_databases/current/" in data["human-oral.qza"].url


def test_list_current_files_preserves_subdirectory_in_child_urls(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="/current-release/QIIME2/2025.7">2025.7</a>'
        ),
    )

    data = SILVA_Fetcher().list_current_files("QIIME2")

    assert data["2025.7"].url.endswith("/current-release/QIIME2/2025.7")


def test_list_archive_releases(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(
            text='<a href="/archive/release_138">release_138</a>'
            '<a href="/archive/qiime">qiime</a>'
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


def _capture_download_binary(monkeypatch):
    """Patch the shared downloader and record the arguments SILVA passes it."""
    seen = {}

    def fake(url, target, service, *, overwrite=False, md5_url=None, reject_html=False):
        seen.update(
            url=url,
            target=Path(target),
            service=service,
            overwrite=overwrite,
            md5_url=md5_url,
            reject_html=reject_html,
        )
        return Path(target)

    monkeypatch.setattr("biodbs.fetch.SILVA.silva_fetcher.download_binary", fake)
    return seen


def test_download_file(tmp_path, monkeypatch):
    seen = _capture_download_binary(monkeypatch)

    path = SILVA_Fetcher().download_file("README.txt", tmp_path)

    assert path == tmp_path / "README.txt"
    assert seen["target"] == tmp_path / "README.txt"
    assert seen["url"].endswith("/fileadmin/silva_databases/current/README.txt")
    assert seen["service"] == "SILVA"
    assert seen["reject_html"] is True
    assert seen["md5_url"] is None  # verify_md5 defaults off for plain files


def test_download_classifier_maps_directory(tmp_path, monkeypatch):
    seen = {}

    def fake_download(path, dest, overwrite=False, *, verify_md5=False):
        seen["path"] = path
        seen["verify_md5"] = verify_md5
        return Path(dest) / Path(path).name

    fetcher = SILVA_Fetcher()
    monkeypatch.setattr(fetcher, "download_file", fake_download)

    result = fetcher.download_classifier("qiime2", "taxonomy.qza", tmp_path)

    assert seen["path"] == "QIIME2/taxonomy.qza"
    assert seen["verify_md5"] is True  # classifiers are MD5-verified by default
    assert result == tmp_path / "taxonomy.qza"


def test_download_classifier_unknown_kind_raises_value_error(tmp_path):
    fetcher = SILVA_Fetcher()

    with pytest.raises(ValueError, match="Valid kinds"):
        fetcher.download_classifier("qiime", "taxonomy.qza", tmp_path)


def test_download_file_uses_fileadmin_base(tmp_path, monkeypatch):
    seen = _capture_download_binary(monkeypatch)

    SILVA_Fetcher().download_file("QIIME2/2025.7/taxonomic-weights/w.qza", tmp_path)

    assert seen["url"] == (
        "https://www.arb-silva.de/fileadmin/silva_databases/current/"
        "QIIME2/2025.7/taxonomic-weights/w.qza"
    )
    assert seen["target"] == tmp_path / "w.qza"


def test_download_classifier_builds_fileadmin_classifier_url(tmp_path, monkeypatch):
    seen = _capture_download_binary(monkeypatch)

    SILVA_Fetcher().download_classifier(
        "qiime2", "2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza", tmp_path
    )

    base = (
        "https://www.arb-silva.de/fileadmin/silva_databases/current/"
        "QIIME2/2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza"
    )
    assert seen["url"] == base
    assert seen["md5_url"] == base + ".md5"  # verified by default


def test_download_classifier_can_skip_verification(tmp_path, monkeypatch):
    seen = _capture_download_binary(monkeypatch)

    SILVA_Fetcher().download_classifier("qiime2", "2025.7/x.qza", tmp_path, verify=False)

    assert seen["md5_url"] is None


def test_download_file_writes_into_fresh_directory(tmp_path, monkeypatch):
    seen = _capture_download_binary(monkeypatch)
    dest = tmp_path / "data" / "silva"  # does not exist yet, no suffix -> a directory

    path = SILVA_Fetcher().download_file("QIIME2/x.qza", dest)

    assert path == dest / "x.qza"
    assert seen["target"] == dest / "x.qza"


def test_get_version_uses_fileadmin_base(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.SILVA.silva_fetcher.request_with_retry",
        lambda url: DummyResponse(text="138.2", content_type="text/plain"),
    )

    data = SILVA_Fetcher().get_version()

    assert data.url == "https://www.arb-silva.de/fileadmin/silva_databases/current/VERSION.txt"
