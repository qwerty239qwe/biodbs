"""NCBI Datasets API fetcher module."""

from biodbs.fetch.NCBI.ncbi_fetcher import NCBI_Fetcher, NCBI_APIConfig
from biodbs.fetch.NCBI.funcs import (
    ncbi_download_blast_database,
    ncbi_download_taxdump,
    ncbi_get_gene,
    ncbi_symbol_to_id,
    ncbi_id_to_symbol,
    ncbi_get_taxonomy,
    ncbi_translate_gene_ids,
)

__all__ = [
    "NCBI_Fetcher",
    "NCBI_APIConfig",
    "ncbi_download_blast_database",
    "ncbi_download_taxdump",
    "ncbi_get_gene",
    "ncbi_symbol_to_id",
    "ncbi_id_to_symbol",
    "ncbi_get_taxonomy",
    "ncbi_translate_gene_ids",
]
