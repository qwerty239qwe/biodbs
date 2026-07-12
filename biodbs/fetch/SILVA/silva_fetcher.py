"""SILVA release-file fetcher."""

from __future__ import annotations

import os
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from biodbs.data.SILVA import (
    SILVAFile,
    SILVARelease,
    SILVAFileListData,
    SILVAReleaseListData,
    SILVATextData,
)
from biodbs.exceptions import APIError, raise_for_status
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
        """List immediate directories and downloadable files at *path*."""
        page_url = self._release_url(path)
        files = [
            SILVAFile(name=name, url=url, is_dir=is_dir)
            for name, url, is_dir in self._list_entries(page_url, self._file_url(path))
        ]
        return SILVAFileListData(files)

    def list_archive_releases(self) -> SILVAReleaseListData:
        """List archived SILVA releases."""
        releases = [
            SILVARelease(name=name, url=url)
            for name, url, _ in self._list_entries(self.archive_url)
            if name.startswith("release_")
        ]
        return SILVAReleaseListData(releases)

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
        self, path: str, dest: str | Path, overwrite: bool = False
    ) -> Path:
        """Download a SILVA release file to *dest*.

        *path* is relative to the SILVA file base (``fileadmin/silva_databases/
        current/``), e.g. ``"VERSION.txt"`` or
        ``"QIIME2/2025.7/taxonomic-weights/<file>.qza"``.
        """
        target = Path(dest)
        # Treat *dest* as a directory when it is one, ends with a separator, or
        # has no file suffix (e.g. "data/silva") — otherwise a fresh directory
        # path would be mistaken for the output filename.
        if target.is_dir() or str(dest).endswith(("/", "\\")) or target.suffix == "":
            target = target / Path(path).name
        if target.exists() and not overwrite:
            return target
        url = self._file_url(path)
        response = request_with_retry(url, stream=True)
        raise_for_status(response, "SILVA", url=url)
        self._reject_html(response, url)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Stream to a temp file and atomically move into place, so an interrupted
        # transfer never leaves a partial file that later calls would reuse.
        part = target.with_name(target.name + ".part")
        try:
            with part.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
            os.replace(part, target)
        except BaseException:
            part.unlink(missing_ok=True)
            raise
        return target

    def download_classifier(
        self, kind: str, filename: str, dest: str | Path, overwrite: bool = False
    ) -> Path:
        """Download a classifier file from a common classifier directory.

        *filename* is the path **below** the classifier directory (SILVA nests
        classifiers by release/marker), e.g. for ``kind="qiime2"``::

            "2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza"
            "2025.7/SSU/V4V5-515f-926r/weighted/human-oral/SILVA138.2_..._human-oral.qza"
        """
        directory = self.classifier_dirs.get(kind.lower())
        if directory is None:
            valid = ", ".join(sorted(self.classifier_dirs))
            raise ValueError(
                f"Unsupported classifier kind: {kind!r}. Valid kinds: {valid}"
            )
        return self.download_file(
            f"{directory}/{filename}", dest=dest, overwrite=overwrite
        )

    def _get_text(self, path: str) -> SILVATextData:
        url = self._file_url(path)
        response = request_with_retry(url)
        raise_for_status(response, "SILVA", url=url)
        return SILVATextData(response.text, url=url)

    def _list_entries(
        self, page_url: str, file_url: str | None = None
    ) -> list[tuple[str, str, bool]]:
        """Return immediate browse directories and direct files linked on a page."""
        response = request_with_retry(page_url)
        raise_for_status(response, "SILVA", url=page_url)
        parser = _ListingParser()
        parser.feed(response.text)
        prefixes = [(page_url, True)]
        if file_url is not None:
            prefixes.append((file_url, False))
        entries: list[tuple[str, str, bool]] = []
        seen: set[tuple[str, bool]] = set()
        for href in parser.hrefs:
            absolute_url = urljoin(page_url, href)
            parsed_href = urlparse(absolute_url)
            for prefix_url, is_dir in prefixes:
                parsed_prefix = urlparse(prefix_url)
                base = parsed_prefix.path.rstrip("/") + "/"
                child = parsed_href.path.removeprefix(base).strip("/")
                if (
                    parsed_href.scheme == parsed_prefix.scheme
                    and parsed_href.netloc == parsed_prefix.netloc
                    and parsed_href.path.startswith(base)
                    and child
                    and "/" not in child
                    and (child, is_dir) not in seen
                ):
                    seen.add((child, is_dir))
                    entries.append((child, absolute_url, is_dir))
                    break
        return entries

    @staticmethod
    def _reject_html(response, url: str) -> None:
        """Guard against SILVA's CMS returning an HTML browse page for a file.

        SILVA serves ``current-release/`` and ``archive/`` paths as HTML pages;
        only ``fileadmin/silva_databases/current/`` paths return real files.
        Without this check a wrong path silently writes an HTML page to disk.
        """
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("text/html"):
            raise APIError(
                f"SILVA returned an HTML page instead of a file for {url!r}. "
                "This path is a CMS browse page, not a direct download; use a "
                "path under 'fileadmin/silva_databases/current/'.",
                service="SILVA",
                url=url,
            )

    def _release_url(self, path: str = "") -> str:
        return urljoin(self.current_release_url, path)

    def _file_url(self, path: str = "") -> str:
        return urljoin(self.file_base_url, path)
