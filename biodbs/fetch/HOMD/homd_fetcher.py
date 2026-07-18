"""HOMD public download fetcher."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from biodbs.data.HOMD import HOMDFile, HOMDFileListData, HOMDTableData, HOMDTextData
from biodbs.exceptions import APIValidationError, raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_BASE_URL = "https://www.homd.org/"
_FTP_URL = "https://www.homd.org/ftp/"
_DOWNLOADS_URL = "https://www.homd.org/download/download/all"
_HOST = "www.homd.org"

get_rate_limiter().set_rate(_HOST, 3)

# 16S rRNA RefSeq releases are published per source on separate hosts.
_REFSEQ_SOURCES = {
    "homd": ("HOMD", "https://www.homd.org/ftp/"),
    "momd": ("MOMD", "https://www.momd.org/ftp/"),
}


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str, str]] = []
        self._current_href = ""
        self._current_text: list[str] = []
        self._category = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4"}:
            self._category = ""
        if tag == "a":
            href = attrs_dict.get("href", "")
            if href and href not in ("../", "/") and not href.startswith(("?", "mailto:", "#")):
                self._current_href = href
                self._current_text = []

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._current_href:
            self._current_text.append(text)
        elif not self._category:
            self._category = text

    def handle_endtag(self, tag):
        if tag == "a" and self._current_href:
            text = " ".join(self._current_text).strip() or self._current_href
            self.links.append((self._current_href, text, self._category))
            self._current_href = ""
            self._current_text = []


class HOMD_Fetcher:
    """Fetcher for HOMD public listings, tables, and downloads."""

    def __init__(
        self,
        base_url: str = _BASE_URL,
        ftp_url: str = _FTP_URL,
        downloads_url: str = _DOWNLOADS_URL,
    ):
        self.base_url = base_url
        self.ftp_url = ftp_url
        self.downloads_url = downloads_url

    def list_ftp(self, path: str = "") -> HOMDFileListData:
        """List HOMD FTP files/directories."""
        url = self._ftp_url(path)
        if path and not url.endswith("/"):
            url += "/"
        return HOMDFileListData(
            [
                HOMDFile(name=self._display_name(href), url=urljoin(url, href), is_dir=href.endswith("/"))
                for href, _, _ in self._list_links(url)
                if not href.startswith(("/", "http://", "https://"))
            ]
        )

    def list_downloads(self) -> HOMDFileListData:
        """List HOMD batch download links."""
        files = [
            HOMDFile(
                name=text,
                url=urljoin(self.base_url, href),
                is_dir=href.endswith("/"),
                category=category,
            )
            for href, text, category in self._list_links(self.downloads_url)
            if not href.startswith(("http://", "https://")) or "homd.org" in href
        ]
        return HOMDFileListData(files)

    def download_file(self, path_or_url: str, dest: str | Path, overwrite: bool = False) -> Path:
        """Download a HOMD file to *dest*."""
        target = Path(dest)
        if target.is_dir() or str(dest).endswith(("/", "\\")):
            target = target / Path(path_or_url.rstrip("/")).name
        if target.exists() and not overwrite:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        url = self._url(path_or_url)
        response = request_with_retry(url, stream=True)
        raise_for_status(response, "HOMD", url=url)
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return target

    def get_table(self, path_or_url: str, delimiter: str = "\t") -> HOMDTableData:
        """Fetch a HOMD tabular file."""
        url = self._url(path_or_url)
        response = request_with_retry(url)
        raise_for_status(response, "HOMD", url=url)
        return HOMDTableData(response.text, url=url, delimiter=delimiter)

    def get_text(self, path_or_url: str) -> HOMDTextData:
        """Fetch a small HOMD text/FASTA/Newick file."""
        url = self._url(path_or_url)
        response = request_with_retry(url)
        raise_for_status(response, "HOMD", url=url)
        return HOMDTextData(response.text, url=url)

    def get_taxon_table(self) -> HOMDTableData:
        """Fetch the HOMD taxon table from batch downloads."""
        return self._get_table_by_keywords("taxon")

    def get_taxonomic_hierarchy(self) -> HOMDTableData:
        """Fetch the HOMD taxonomic hierarchy file."""
        return self._get_table_by_keywords("hierarchy")

    def get_hmt_lineage(self) -> HOMDTableData:
        """Fetch the HOMD HMT lineage file."""
        return self._get_table_by_keywords("lineage")

    def get_genome_metadata(self) -> HOMDTableData:
        """Fetch HOMD genome metadata."""
        return self._get_table_by_keywords("genome")

    def get_gtdb_taxonomy(self) -> HOMDTableData:
        """Fetch HOMD GTDB taxonomy."""
        return self._get_table_by_keywords("gtdb")

    def get_phage_table(self) -> HOMDTableData:
        """Fetch HOMD phage table."""
        return self._get_table_by_keywords("phage")

    def get_crispr_table(self) -> HOMDTableData:
        """Fetch HOMD CRISPR table."""
        return self._get_table_by_keywords("crispr")

    def list_16s_refseq(self, version: str = "current", source: str = "homd") -> HOMDFileListData:
        """List 16S rRNA RefSeq files for a HOMD/MOMD release.

        *version* is a release like ``"15.22"`` (``"current"`` for the latest);
        *source* is ``"homd"`` or ``"momd"``.
        """
        _, url = self._refseq_dir_url(version, source)
        return self.list_ftp(url)

    def download_16s_refseq(
        self,
        dest: str | Path,
        filename: str = "",
        overwrite: bool = False,
        *,
        version: str = "current",
        source: str = "homd",
    ) -> Path:
        """Download a 16S RefSeq FASTA for a HOMD/MOMD release.

        Without *filename*, the unaligned ``.fasta`` reference is selected; pass an
        explicit *filename* to fetch a specific file from the release directory.
        """
        if filename:
            _, dir_url = self._refseq_dir_url(version, source)
            url = f"{dir_url}/{filename}"
        else:
            url = self._select_16s_file(version, source, ".fasta").url
        return self.download_file(url, dest, overwrite)

    def download_16s_taxonomy(
        self,
        dest: str | Path,
        overwrite: bool = False,
        *,
        version: str = "current",
        source: str = "homd",
    ) -> Path:
        """Download the QIIME-formatted 16S taxonomy for a HOMD/MOMD release."""
        url = self._select_16s_file(version, source, ".qiime.taxonomy").url
        return self.download_file(url, dest, overwrite)

    def _get_table_by_keywords(self, keyword: str) -> HOMDTableData:
        lower_keyword = keyword.lower()
        for item in self.list_downloads():
            haystack = f"{item.name} {item.url}".lower()
            if lower_keyword in haystack:
                delimiter = "," if item.url.lower().endswith(".csv") else "\t"
                return self.get_table(item.url, delimiter=delimiter)
        raise APIValidationError("HOMD", detail=f"No download found for keyword: {keyword}")

    @staticmethod
    def _refseq_dir_url(version: str, source: str) -> tuple[str, str]:
        """Return ``(tag, directory_url)`` for a 16S RefSeq release."""
        try:
            tag, host = _REFSEQ_SOURCES[source.lower()]
        except KeyError:
            raise APIValidationError("HOMD", detail=f"Unsupported 16S source: {source!r}") from None
        directory = "current" if version.lower() in {"", "current", "latest"} else f"V{version.removeprefix('V')}"
        return tag, f"{host}16S_rRNA_refseq/{tag}_16S_rRNA_RefSeq/{directory}"

    def _select_16s_file(self, version: str, source: str, suffix: str) -> HOMDFile:
        tag, _ = self._refseq_dir_url(version, source)
        pattern = re.compile(rf"^{tag}_16S_rRNA_RefSeq_V[0-9.]+{re.escape(suffix)}$")
        for item in self.list_16s_refseq(version=version, source=source):
            if pattern.fullmatch(item.name):
                return item
        raise APIValidationError(
            "HOMD",
            detail=f"No {source.upper()} 16S file ending in {suffix!r} for version {version!r}.",
        )

    def _list_links(self, url: str) -> list[tuple[str, str, str]]:
        response = request_with_retry(url)
        raise_for_status(response, "HOMD", url=url)
        parser = _LinkParser()
        parser.feed(response.text)
        return parser.links

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith(("http://", "https://")):
            return path_or_url
        return urljoin(self.base_url, path_or_url)

    def _ftp_url(self, path: str = "") -> str:
        return urljoin(self.ftp_url, path)

    @staticmethod
    def _display_name(href: str) -> str:
        return href.rstrip("/").split("/")[-1]
