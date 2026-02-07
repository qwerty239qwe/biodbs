"""Convenience functions for UniProt REST API."""

from typing import List, Dict, Optional, Union
import pandas as pd

from biodbs.fetch.uniprot.uniprot_fetcher import UniProt_Fetcher
from biodbs.data.uniprot.data import UniProtFetchedData, UniProtSearchResult


def uniprot_get_entry(accession: str) -> UniProtFetchedData:
    """Get a UniProt entry by accession.

    Args:
        accession: UniProt accession (e.g., "P05067").

    Returns:
        UniProtFetchedData with the entry.

    Example:
        ```python
        entry = uniprot_get_entry("P05067")
        print(entry.entries[0].protein_name)
        # Amyloid-beta precursor protein
        ```
    """
    fetcher = UniProt_Fetcher()
    return fetcher.get_entry(accession)


def uniprot_get_entries(accessions: List[str]) -> UniProtFetchedData:
    """Get multiple UniProt entries by accessions.

    Args:
        accessions: List of UniProt accessions.

    Returns:
        UniProtFetchedData with all entries.

    Example:
        ```python
        entries = uniprot_get_entries(["P05067", "P04637", "P00533"])
        print(entries.get_gene_names())
        # ['APP', 'TP53', 'EGFR']
        ```
    """
    fetcher = UniProt_Fetcher()
    return fetcher.get_entries(accessions)


def uniprot_search(
    query: str,
    size: int = 25,
    reviewed_only: bool = False,
) -> UniProtSearchResult:
    """Search UniProtKB.

    Args:
        query: Search query (e.g., "gene:TP53 AND organism_id:9606").
        size: Number of results per page (max 500).
        reviewed_only: Only return reviewed (Swiss-Prot) entries.

    Returns:
        UniProtSearchResult with matching entries.

    Example:
        ```python
        results = uniprot_search("kinase AND organism_id:9606", reviewed_only=True)
        print(results.as_dataframe()[["accession", "gene_name"]].head())
        #   accession gene_name
        # 0    P00533      EGFR
        # 1    P04629      NTRK1
        ```
    """
    fetcher = UniProt_Fetcher()
    if reviewed_only:
        query = f"({query}) AND reviewed:true"
    return fetcher.search(query, size=size)


def uniprot_search_by_gene(
    gene_name: str,
    organism: Optional[Union[int, str]] = 9606,
    reviewed_only: bool = True,
) -> UniProtSearchResult:
    """Search UniProt by gene name.

    Args:
        gene_name: Gene name to search.
        organism: Organism tax ID or name (default: human).
        reviewed_only: Only return reviewed entries.

    Returns:
        UniProtSearchResult with matching entries.

    Example:
        ```python
        results = uniprot_search_by_gene("TP53")
        print(results.entries[0].accession)
        # P04637
        ```
    """
    fetcher = UniProt_Fetcher()
    return fetcher.search_by_gene(gene_name, organism=organism, reviewed_only=reviewed_only)


def uniprot_search_by_keyword(
    keyword: str,
    organism: Optional[Union[int, str]] = None,
    reviewed_only: bool = False,
    size: int = 25,
) -> UniProtSearchResult:
    """Search UniProt by keyword.

    Args:
        keyword: Keyword to search (e.g., "kinase", "receptor").
        organism: Optional organism filter.
        reviewed_only: Only return reviewed entries.
        size: Results per page.

    Returns:
        UniProtSearchResult with matching entries.

    Example:
        ```python
        results = uniprot_search_by_keyword("apoptosis", organism=9606)
        print(len(results.entries))
        # 25
        ```
    """
    fetcher = UniProt_Fetcher()
    return fetcher.search_by_keyword(
        keyword, organism=organism, reviewed_only=reviewed_only, size=size
    )


def gene_to_uniprot(
    gene_names: List[str],
    organism: int = 9606,
    reviewed_only: bool = True,
    return_dict: bool = True,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Map gene names to UniProt accessions.

    Args:
        gene_names: List of gene names.
        organism: Organism tax ID (default: human).
        reviewed_only: Only return reviewed entries.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary or DataFrame mapping gene names to accessions.

    Example:
        ```python
        mapping = gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
        print(mapping)
        # {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}
        ```
    """
    fetcher = UniProt_Fetcher()
    mapping = fetcher.gene_to_uniprot(gene_names, organism=organism, reviewed_only=reviewed_only)

    if return_dict:
        return mapping

    records = [{"gene_name": k, "accession": v} for k, v in mapping.items()]
    return pd.DataFrame(records)


def uniprot_to_gene(
    accessions: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Map UniProt accessions to gene names.

    Args:
        accessions: List of UniProt accessions.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary or DataFrame mapping accessions to gene names.

    Example:
        ```python
        mapping = uniprot_to_gene(["P04637", "P38398", "P00533"])
        print(mapping)
        # {'P04637': 'TP53', 'P38398': 'BRCA1', 'P00533': 'EGFR'}
        ```
    """
    fetcher = UniProt_Fetcher()
    mapping = fetcher.uniprot_to_gene(accessions)

    if return_dict:
        return mapping

    records = [{"accession": k, "gene_name": v} for k, v in mapping.items()]
    return pd.DataFrame(records)


def uniprot_get_sequences(
    accessions: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, str], str]:
    """Get protein sequences for UniProt accessions.

    Args:
        accessions: List of UniProt accessions.
        return_dict: If True, return dict. If False, return FASTA string.

    Returns:
        Dictionary mapping accessions to sequences, or FASTA string.

    Example:
        ```python
        seqs = uniprot_get_sequences(["P04637", "P00533"])
        print(seqs["P04637"][:50])
        # MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDD
        ```
    """
    fetcher = UniProt_Fetcher()

    if return_dict:
        return fetcher.get_sequences(accessions)

    entries = fetcher.get_entries(accessions)
    return entries.to_fasta()


def uniprot_map_ids(
    ids: List[str],
    from_db: str,
    to_db: str,
) -> Dict[str, List[str]]:
    """Map IDs between databases using UniProt ID mapping.

    Args:
        ids: List of IDs to map.
        from_db: Source database (e.g., "UniProtKB_AC-ID", "Gene_Name", "GeneID", "Ensembl").
        to_db: Target database (e.g., "UniProtKB", "GeneID", "PDB", "Ensembl").

    Returns:
        Dictionary mapping input IDs to lists of output IDs.

    Common database names:
        - UniProtKB_AC-ID: UniProt accession
        - UniProtKB: UniProt (returns full entries)
        - Gene_Name: Gene name
        - GeneID: NCBI Gene ID
        - Ensembl: Ensembl ID
        - PDB: PDB structure ID
        - RefSeq_Protein: RefSeq protein ID

    Example:
        ```python
        mapping = uniprot_map_ids(["P05067", "P04637"], "UniProtKB_AC-ID", "GeneID")
        print(mapping)
        # {'P05067': ['351'], 'P04637': ['7157']}
        ```
    """
    fetcher = UniProt_Fetcher()
    return fetcher.map_ids(ids, from_db=from_db, to_db=to_db)
