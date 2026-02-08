"""UniProt REST API fetcher module."""

from biodbs.fetch.uniprot.uniprot_fetcher import UniProt_Fetcher, UniProt_APIConfig
from biodbs.fetch.uniprot.funcs import (
    uniprot_get_entry,
    uniprot_get_entries,
    uniprot_search,
    uniprot_search_by_gene,
    uniprot_search_by_keyword,
    gene_to_uniprot,
    uniprot_to_gene,
    uniprot_get_sequences,
    uniprot_map_ids,
)

__all__ = [
    "UniProt_Fetcher",
    "UniProt_APIConfig",
    "uniprot_get_entry",
    "uniprot_get_entries",
    "uniprot_search",
    "uniprot_search_by_gene",
    "uniprot_search_by_keyword",
    "gene_to_uniprot",
    "uniprot_to_gene",
    "uniprot_get_sequences",
    "uniprot_map_ids",
]
