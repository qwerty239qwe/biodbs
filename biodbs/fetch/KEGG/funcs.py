"""Convenience functions for KEGG data fetching."""

from typing import List, Optional, Union

from biodbs.data.KEGG.data import KEGGFetchedData
from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[KEGG_Fetcher] = None


def _get_fetcher() -> KEGG_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = KEGG_Fetcher()
    return _fetcher


def kegg_info(database: str) -> KEGGFetchedData:
    """Get information about a KEGG database.

    Args:
        database: Database name (e.g., "kegg", "pathway", "compound", "drug").

    Returns:
        KEGGFetchedData containing database information and statistics.

    Example:
        >>> data = kegg_info("pathway")
        >>> print(data.text)
    """
    return _get_fetcher().get(operation="info", database=database)


def kegg_list(
    database: str,
    organism: Optional[str] = None,
) -> KEGGFetchedData:
    """List entries in a KEGG database.

    Args:
        database: Database name (e.g., "pathway", "module", "compound").
        organism: Organism code for pathway/module lists (e.g., "hsa" for human).

    Returns:
        KEGGFetchedData containing a list of entries with IDs and descriptions.

    Example:
        >>> data = kegg_list("pathway", organism="hsa")
        >>> df = data.as_dataframe()
    """
    kwargs = {"operation": "list", "database": database}
    if organism:
        kwargs["organism"] = organism
    return _get_fetcher().get(**kwargs)


def kegg_find(
    database: str,
    query: str,
    option: Optional[str] = None,
) -> KEGGFetchedData:
    """Search for entries in a KEGG database.

    Args:
        database: Database to search (e.g., "compound", "drug", "genes").
        query: Search query string.
        option: Search option (e.g., "formula", "exact_mass", "mol_weight").

    Returns:
        KEGGFetchedData containing search results with matching entries.

    Example:
        >>> data = kegg_find("compound", "aspirin")
        >>> df = data.as_dataframe()
    """
    kwargs = {"operation": "find", "database": database, "query": query}
    if option:
        kwargs["find_option"] = option
    return _get_fetcher().get(**kwargs)


def kegg_get(
    dbentries: Union[str, List[str]],
    option: Optional[str] = None,
) -> KEGGFetchedData:
    """Retrieve entry data from KEGG database.

    Args:
        dbentries: Entry ID or list of IDs (e.g., "hsa:7157").
        option: Output format ("aaseq", "ntseq", "mol", "kcf", "image", "json").

    Returns:
        KEGGFetchedData containing entry data.

    Example:
        >>> data = kegg_get("hsa:7157")  # TP53 gene
        >>> print(data.text)

        >>> data = kegg_get("cpd:C00022", option="mol")
        >>> print(data.text)
    """
    if isinstance(dbentries, str):
        dbentries = [dbentries]
    kwargs = {"operation": "get", "dbentries": dbentries}
    if option:
        kwargs["get_option"] = option
    return _get_fetcher().get(**kwargs)


def kegg_get_batch(
    dbentries: List[str],
    option: Optional[str] = None,
    batch_size: int = 10,
) -> KEGGFetchedData:
    """Retrieve data for many entries using batched concurrent requests.

    Args:
        dbentries: List of entry IDs to fetch.
        option: Output format (e.g., "aaseq", "ntseq", "json").
        batch_size: Number of entries per request (default 10, KEGG's limit).

    Returns:
        KEGGFetchedData containing combined results from all batches.

    Example:
        >>> genes = ["hsa:10458", "hsa:7157", "hsa:672", "hsa:675"]
        >>> data = kegg_get_batch(genes)
        >>> print(len(data.records))
    """
    return _get_fetcher().get_all(
        operation="get",
        dbentries=dbentries,
        get_option=option,
        batch_size=batch_size,
    )


def kegg_conv(
    target_db: str,
    source: Union[str, List[str]],
) -> KEGGFetchedData:
    """Convert entry IDs between KEGG and external databases.

    Args:
        target_db: Target database (e.g., "ncbi-geneid", "ncbi-proteinid", "uniprot").
        source: Source database name OR list of entry IDs to convert.

    Returns:
        KEGGFetchedData containing ID mappings between databases.

    Example:
        >>> # Convert entire database
        >>> data = kegg_conv("ncbi-geneid", "hsa")

        >>> # Convert specific entries
        >>> data = kegg_conv("ncbi-geneid", ["hsa:10458", "hsa:7157"])
        >>> df = data.as_dataframe()
    """
    if isinstance(source, list):
        return _get_fetcher().get(
            operation="conv", target_db=target_db, dbentries=source
        )
    return _get_fetcher().get(
        operation="conv", target_db=target_db, source_db=source
    )


def kegg_link(
    target_db: str,
    source: Union[str, List[str]],
) -> KEGGFetchedData:
    """Find related entries between KEGG databases.

    Args:
        target_db: Target database (e.g., "pathway", "module", "disease").
        source: Source database name OR list of entry IDs.

    Returns:
        KEGGFetchedData containing linked entries between databases.

    Example:
        >>> # Link genes to pathways
        >>> data = kegg_link("pathway", ["hsa:10458", "hsa:7157"])
        >>> df = data.as_dataframe()

        >>> # Link all compounds to reactions
        >>> data = kegg_link("reaction", "compound")
    """
    if isinstance(source, list):
        return _get_fetcher().get(
            operation="link", target_db=target_db, dbentries=source
        )
    return _get_fetcher().get(
        operation="link", target_db=target_db, source_db=source
    )


def kegg_ddi(drug_entries: List[str]) -> KEGGFetchedData:
    """Get drug-drug interaction information.

    Args:
        drug_entries: List of drug entry IDs (e.g., ["D00001", "D00002"]).

    Returns:
        KEGGFetchedData containing drug-drug interaction data.

    Example:
        >>> data = kegg_ddi(["D00564", "D00109"])
        >>> print(data.text)
    """
    return _get_fetcher().get(operation="ddi", dbentries=drug_entries)
