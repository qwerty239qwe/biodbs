"""Convenience functions for HOMD."""

from pathlib import Path

from biodbs.data.HOMD import HOMDFileListData, HOMDTableData, HOMDTextData
from biodbs.fetch.HOMD.homd_fetcher import HOMD_Fetcher

_fetcher: HOMD_Fetcher | None = None


def _get_fetcher() -> HOMD_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = HOMD_Fetcher()
    return _fetcher


def homd_list_ftp(path: str = "") -> HOMDFileListData:
    """List HOMD FTP files/directories."""
    return _get_fetcher().list_ftp(path)


def homd_list_downloads() -> HOMDFileListData:
    """List HOMD batch download links."""
    return _get_fetcher().list_downloads()


def homd_download_file(path_or_url: str, dest: str | Path, overwrite: bool = False) -> Path:
    """Download a HOMD file."""
    return _get_fetcher().download_file(path_or_url, dest, overwrite)


def homd_get_table(path_or_url: str, delimiter: str = "\t") -> HOMDTableData:
    """Fetch a HOMD tabular file."""
    return _get_fetcher().get_table(path_or_url, delimiter)


def homd_get_text(path_or_url: str) -> HOMDTextData:
    """Fetch a small HOMD text file."""
    return _get_fetcher().get_text(path_or_url)


def homd_get_taxon_table() -> HOMDTableData:
    """Fetch the HOMD taxon table."""
    return _get_fetcher().get_taxon_table()


def homd_get_taxonomic_hierarchy() -> HOMDTableData:
    """Fetch the HOMD taxonomic hierarchy."""
    return _get_fetcher().get_taxonomic_hierarchy()


def homd_get_hmt_lineage() -> HOMDTableData:
    """Fetch the HOMD HMT lineage table."""
    return _get_fetcher().get_hmt_lineage()


def homd_get_genome_metadata() -> HOMDTableData:
    """Fetch HOMD genome metadata."""
    return _get_fetcher().get_genome_metadata()


def homd_get_gtdb_taxonomy() -> HOMDTableData:
    """Fetch HOMD GTDB taxonomy."""
    return _get_fetcher().get_gtdb_taxonomy()


def homd_get_phage_table() -> HOMDTableData:
    """Fetch HOMD phage table."""
    return _get_fetcher().get_phage_table()


def homd_get_crispr_table() -> HOMDTableData:
    """Fetch HOMD CRISPR table."""
    return _get_fetcher().get_crispr_table()


def homd_list_16s_refseq(version: str = "current", source: str = "homd") -> HOMDFileListData:
    """List 16S RefSeq files for a HOMD/MOMD release."""
    return _get_fetcher().list_16s_refseq(version, source)


def homd_download_16s_refseq(
    dest: str | Path,
    filename: str = "",
    overwrite: bool = False,
    *,
    version: str = "current",
    source: str = "homd",
) -> Path:
    """Download a 16S RefSeq FASTA for a HOMD/MOMD release."""
    return _get_fetcher().download_16s_refseq(
        dest, filename, overwrite, version=version, source=source
    )


def homd_download_16s_taxonomy(
    dest: str | Path,
    overwrite: bool = False,
    *,
    version: str = "current",
    source: str = "homd",
) -> Path:
    """Download the QIIME-formatted 16S taxonomy for a HOMD/MOMD release."""
    return _get_fetcher().download_16s_taxonomy(
        dest, overwrite, version=version, source=source
    )
