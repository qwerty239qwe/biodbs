"""SILVA release-file fetcher."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from biodbs.data.SILVA import SILVAFile, SILVARelease, SILVAFileListData, SILVAReleaseListData, SILVATextData
from biodbs.exceptions import raise_for_status
from biodbs.fetch._download import download_binary
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_CURRENT_RELEASE_URL = "https://www.arb-silva.de/current-release/"
_ARCHIVE_URL = "https://www.arb-silva.de/archive/"
# SILVA's CMS serves current-release/ and archive/ as HTML browse pages; the
# actual downloadable files (VERSION.txt, .qza classifiers, ...) live here.
_FILE_BASE_URL = "https://www.arb-silva.de/fileadmin/silva_databases/current/"
_HOST = "www.arb-silva.de"

get_rate_limiter().set_rate(_HOST, 3)


class _ListingParser(HTMLParser):
    """Collect every href on an HTML page (SILVA's CMS uses root-relative links)."""

    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


class SILVA_Fetcher:
    """Fetcher for SILVA release listings and downloadable release files."""

    classifier_dirs = {
        "qiime2": "QIIME2",
        "dada2": "DADA2",
        "kraken2": "Kraken2",
        "megan": "MEGAN",
        "exports": "Exports",
    }

    def __init__(
        self,
        current_release_url: str = _CURRENT_RELEASE_URL,
        archive_url: str = _ARCHIVE_URL,
        file_base_url: str = _FILE_BASE_URL,
    ):
        self.current_release_url = current_release_url
        self.archive_url = archive_url
        self.file_base_url = file_base_url

    def list_current_files(self, path: str = "") -> SILVAFileListData:
        """List the immediate sub-entries of a current-release page.

        SILVA's CMS exposes a browsable tree (``QIIME2`` -> release -> marker ->
        ...). Directory entries link to ``/current-release/`` browse pages and have
        ``is_dir=True``; downloadable files link to their direct
        ``/fileadmin/silva_databases/current/`` URLs and have ``is_dir=False``.
        """
        entries = self._list_entries(self._release_url(path), self._file_url(path))
        return SILVAFileListData(
            [SILVAFile(name=name, url=url, is_dir=is_dir) for name, url, is_dir in entries]
        )

    def list_archive_releases(self) -> SILVAReleaseListData:
        """List archived SILVA releases."""
        return SILVAReleaseListData(
            [
                SILVARelease(name=name, url=url)
                for name, url, is_dir in self._list_entries(self.archive_url)
                if is_dir and name.startswith("release_")
            ]
        )

    def get_version(self) -> SILVATextData:
        """Fetch current SILVA VERSION.txt."""
        return self._get_text("VERSION.txt")

    def get_readme(self) -> SILVATextData:
        """Fetch current SILVA README.txt."""
        return self._get_text("README.txt")

    def get_citation(self) -> SILVATextData:
        """Fetch current SILVA CITATION.txt."""
        return self._get_text("CITATION.txt")

    def download_file(
        self,
        path: str,
        dest: str | Path,
        overwrite: bool = False,
        *,
        verify_md5: bool = False,
    ) -> Path:
        """Download a SILVA release file to *dest*.

        *path* is relative to the SILVA file base (``fileadmin/silva_databases/
        current/``), e.g. ``"VERSION.txt"`` or
        ``"QIIME2/2025.7/taxonomic-weights/<file>.qza"``. Set *verify_md5* to check
        the file against SILVA's published ``<file>.md5`` sidecar.
        """
        target = Path(dest)
        # Treat *dest* as a directory when it is one, ends with a separator, or
        # has no file suffix (e.g. "data/silva") — otherwise a fresh directory
        # path would be mistaken for the output filename.
        if target.is_dir() or str(dest).endswith(("/", "\\")) or target.suffix == "":
            target = target / Path(path).name
        url = self._file_url(path)
        return download_binary(
            url,
            target,
            "SILVA",
            overwrite=overwrite,
            md5_url=f"{url}.md5" if verify_md5 else None,
            reject_html=True,
        )

    def download_classifier(
        self,
        kind: str,
        filename: str,
        dest: str | Path,
        overwrite: bool = False,
        verify: bool = True,
    ) -> Path:
        """Download a classifier file from a common classifier directory.

        *filename* is the path **below** the classifier directory (SILVA nests
        classifiers by release/marker), e.g. for ``kind="qiime2"``::

            "2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza"
            "2025.7/SSU/V4V5-515f-926r/weighted/human-oral/SILVA138.2_..._human-oral.qza"

        Downloads are verified against SILVA's published ``.md5`` by default; pass
        ``verify=False`` to skip.
        """
        directory = self.classifier_dirs.get(kind.lower())
        if directory is None:
            valid = ", ".join(sorted(self.classifier_dirs))
            raise ValueError(f"Unsupported classifier kind: {kind!r}. Valid kinds: {valid}")
        return self.download_file(f"{directory}/{filename}", dest, overwrite, verify_md5=verify)

    def _get_text(self, path: str) -> SILVATextData:
        url = self._file_url(path)
        response = request_with_retry(url)
        raise_for_status(response, "SILVA", url=url)
        return SILVATextData(response.text, url=url)

    def _list_entries(
        self, page_url: str, file_url: str | None = None
    ) -> list[tuple[str, str, bool]]:
        """Return ``(name, url, is_dir)`` for the immediate children linked under *page_url*.

        SILVA's CMS lists sub-directories as ``/current-release/`` links and files
        as direct ``/fileadmin/silva_databases/current/`` links. Directory links are
        scoped to the page's own path; file links are scoped to the matching file
        base, so global navigation and unrelated links are excluded.
        """
        response = request_with_retry(page_url)
        raise_for_status(response, "SILVA", url=page_url)
        parser = _ListingParser()
        parser.feed(response.text)
        browse_prefix = urlparse(page_url).path.rstrip("/") + "/"
        file_prefix = urlparse(file_url).path.rstrip("/") + "/" if file_url else None
        entries: list[tuple[str, str, bool]] = []
        seen: set[tuple[str, bool]] = set()
        for href in parser.hrefs:
            url = urljoin(page_url, href)
            href_path = urlparse(url).path
            if href_path.startswith(browse_prefix):
                rest, is_dir = href_path[len(browse_prefix):].strip("/"), True
            elif file_prefix and href_path.startswith(file_prefix):
                rest, is_dir = href_path[len(file_prefix):].strip("/"), False
            else:
                continue
            if not rest or "/" in rest:
                continue
            key = (rest, is_dir)
            if key not in seen:
                seen.add(key)
                entries.append((rest, url, is_dir))
        return entries

    def _release_url(self, path: str = "") -> str:
        return urljoin(self.current_release_url, path)

    def _file_url(self, path: str = "") -> str:
        return urljoin(self.file_base_url, path)
