"""GTDB release-file fetcher."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from biodbs.data.GTDB import GTDBFile, GTDBFileListData, GTDBTableData, GTDBTextData
from biodbs.exceptions import APIValidationError, raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_BASE_URL = "https://data.gtdb.ecogenomic.org/releases/"
_HOST = "data.gtdb.ecogenomic.org"
_DOMAINS = {"bac120", "ar53"}

get_rate_limiter().set_rate(_HOST, 3)


class _ListingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        if href and href not in ("../", "/") and not href.startswith(("?", "/", "mailto:", "#")):
            self.links.append(href)


class GTDB_Fetcher:
    """Fetcher for GTDB release listings, taxonomy files, and downloads."""

    def __init__(self, base_url: str = _BASE_URL):
        self.base_url = base_url

    def list_releases(self) -> GTDBFileListData:
        """List GTDB release directories."""
        files = [
            item
            for item in self._list_url(self.base_url)
            if item.is_dir and (item.name == "latest" or item.name.startswith("release"))
        ]
        return GTDBFileListData(files)

    def list_release_files(self, release: str = "latest", path: str = "") -> GTDBFileListData:
        """List files/directories for a GTDB release."""
        url = self._release_url(release, path)
        if not url.endswith("/"):
            url += "/"
        return self._list_url(url)

    def get_version(self, release: str = "latest") -> GTDBTextData:
        """Fetch VERSION.txt for a GTDB release."""
        return self.get_text(f"{release}/VERSION.txt")

    def get_release_notes(self, release: str = "latest") -> GTDBTextData:
        """Fetch RELEASE_NOTES.txt for a GTDB release."""
        return self.get_text(f"{release}/RELEASE_NOTES.txt")

    def get_file_descriptions(self, release: str = "latest") -> GTDBTextData:
        """Fetch FILE_DESCRIPTIONS.txt for a GTDB release."""
        return self.get_text(f"{release}/FILE_DESCRIPTIONS.txt")

    def get_md5sums(self, release: str = "latest") -> GTDBTextData:
        """Fetch MD5SUM.txt for a GTDB release."""
        return self.get_text(f"{release}/MD5SUM.txt")

    def get_taxonomy(self, domain: str = "bac120", release: str = "latest") -> GTDBTableData:
        """Fetch GTDB taxonomy table for bac120 or ar53."""
        return self.get_table(
            self._find_release_file(release, domain, "taxonomy", ".tsv"),
            fieldnames=["accession", "classification"],
        )

    def get_metadata(self, domain: str = "bac120", release: str = "latest") -> GTDBTableData:
        """Fetch GTDB metadata table for bac120 or ar53."""
        return self.get_table(self._find_release_file(release, domain, "metadata", ".tsv"))

    def get_tree(self, domain: str = "bac120", release: str = "latest") -> GTDBTextData:
        """Fetch GTDB tree text for bac120 or ar53."""
        return self.get_text(self._find_release_file(release, domain, "tree", ".tree"))

    def download_file(self, path_or_url: str, dest: str | Path, overwrite: bool = False) -> Path:
        """Download a GTDB file to *dest*."""
        target = Path(dest)
        if target.is_dir() or str(dest).endswith(("/", "\\")):
            target = target / Path(path_or_url.rstrip("/")).name
        if target.exists() and not overwrite:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        url = self._url(path_or_url)
        response = request_with_retry(url, stream=True)
        raise_for_status(response, "GTDB", url=url)
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return target

    def download_taxonomy(
        self,
        domain: str = "bac120",
        dest: str | Path = ".",
        release: str = "latest",
        compressed: bool = True,
        overwrite: bool = False,
    ) -> Path:
        """Download GTDB taxonomy for bac120 or ar53."""
        suffix = ".tsv.gz" if compressed else ".tsv"
        return self.download_file(self._find_release_file(release, domain, "taxonomy", suffix), dest, overwrite)

    def download_metadata(
        self,
        domain: str = "bac120",
        dest: str | Path = ".",
        release: str = "latest",
        overwrite: bool = False,
    ) -> Path:
        """Download GTDB metadata for bac120 or ar53."""
        return self.download_file(self._find_release_file(release, domain, "metadata", ".tsv"), dest, overwrite)

    def download_tree(
        self,
        domain: str = "bac120",
        dest: str | Path = ".",
        release: str = "latest",
        compressed: bool = True,
        overwrite: bool = False,
    ) -> Path:
        """Download GTDB tree for bac120 or ar53."""
        suffix = ".tree.gz" if compressed else ".tree"
        return self.download_file(self._find_release_file(release, domain, "tree", suffix), dest, overwrite)

    def get_table(
        self,
        path_or_url: str,
        delimiter: str = "\t",
        fieldnames: list[str] | None = None,
    ) -> GTDBTableData:
        """Fetch a GTDB tabular text file."""
        url = self._url(path_or_url)
        response = request_with_retry(url)
        raise_for_status(response, "GTDB", url=url)
        return GTDBTableData(response.text, url=url, delimiter=delimiter, fieldnames=fieldnames)

    def get_text(self, path_or_url: str) -> GTDBTextData:
        """Fetch a small GTDB text file."""
        url = self._url(path_or_url)
        response = request_with_retry(url)
        raise_for_status(response, "GTDB", url=url)
        return GTDBTextData(response.text, url=url)

    def _find_release_file(
        self,
        release: str,
        domain: str,
        keyword: str,
        suffix: str = "",
    ) -> str:
        domain = self._validate_domain(domain)
        # ponytail: GTDB currently has one file per (domain, keyword, suffix); rank matches if layout expands.
        for item in self.list_release_files(release):
            name = item.name.lower()
            if domain in name and keyword in name and (not suffix or name.endswith(suffix)):
                return item.url
        raise APIValidationError("GTDB", detail=f"No {domain} {keyword} file found in {release}.")

    def _list_url(self, url: str) -> GTDBFileListData:
        response = request_with_retry(url)
        raise_for_status(response, "GTDB", url=url)
        parser = _ListingParser()
        parser.feed(response.text)
        return GTDBFileListData(
            [
                GTDBFile(name=self._display_name(href), url=urljoin(url, href), is_dir=href.endswith("/"))
                for href in parser.links
            ]
        )

    def _release_url(self, release: str = "latest", path: str = "") -> str:
        return urljoin(self.base_url, f"{release.rstrip('/')}/{path.lstrip('/')}")

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith(("http://", "https://")):
            return path_or_url
        return urljoin(self.base_url, path_or_url)

    @staticmethod
    def _validate_domain(domain: str) -> str:
        domain = domain.lower()
        if domain not in _DOMAINS:
            raise ValueError(f"Unsupported GTDB domain: {domain!r}. Valid domains: {', '.join(sorted(_DOMAINS))}")
        return domain

    @staticmethod
    def _display_name(href: str) -> str:
        return href.rstrip("/").split("/")[-1]
