"""GreenGenes release-directory fetcher (open HTTP index at ftp.microbio.me)."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from biodbs.data.GreenGenes import (
    GreenGenesFile,
    GreenGenesRelease,
    GreenGenesFileListData,
    GreenGenesReleaseListData,
)
from biodbs.exceptions import raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_BASE_URL = "http://ftp.microbio.me/greengenes_release/"
_HOST = "ftp.microbio.me"

get_rate_limiter().set_rate(_HOST, 3)


class _ListingParser(HTMLParser):
    # ponytail: same Apache-autoindex parse as SILVA; copy 12 lines rather than
    # share a module for 2 users — extract when a 3rd needs it.
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href and href not in ("../", "/") and not href.startswith(
            ("?", "/", "http://", "https://", "mailto:")
        ):
            self.links.append(href)


class GreenGenes_Fetcher:
    """Fetcher for GreenGenes release directories and downloadable files."""

    def __init__(self, base_url: str = _BASE_URL):
        self.base_url = base_url

    def list_releases(self) -> GreenGenesReleaseListData:
        """List top-level GreenGenes release directories."""
        releases = [
            GreenGenesRelease(name=self._display_name(href), url=urljoin(self.base_url, href))
            for href in self._list_links(self.base_url)
            if href.endswith("/")
        ]
        return GreenGenesReleaseListData(releases)

    def list_files(self, path: str = "") -> GreenGenesFileListData:
        """List files/directories under *path* within the release tree."""
        url = self._url(path)
        if path and not url.endswith("/"):
            url += "/"
        files = [
            GreenGenesFile(name=self._display_name(href), url=urljoin(url, href), is_dir=href.endswith("/"))
            for href in self._list_links(url)
        ]
        return GreenGenesFileListData(files)

    def download_file(self, path: str, dest: str | Path, overwrite: bool = False) -> Path:
        """Download a GreenGenes file to *dest*."""
        target = Path(dest)
        if target.is_dir() or str(dest).endswith(("/", "\\")):
            target = target / Path(path).name
        if target.exists() and not overwrite:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        url = self._url(path)
        response = request_with_retry(url, stream=True)
        raise_for_status(response, "GreenGenes", url=url)
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return target

    def _list_links(self, url: str) -> list[str]:
        response = request_with_retry(url)
        raise_for_status(response, "GreenGenes", url=url)
        parser = _ListingParser()
        parser.feed(response.text)
        return parser.links

    def _url(self, path: str = "") -> str:
        return urljoin(self.base_url, path)

    @staticmethod
    def _display_name(href: str) -> str:
        return href.rstrip("/").split("/")[-1]
