"""Convenience functions for QuickGO data fetching."""

from typing import List, Optional, Union
from biodbs.data.QuickGO.data import QuickGOFetchedData
from biodbs.fetch.QuickGO.quickgo_fetcher import QuickGO_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[QuickGO_Fetcher] = None


def _get_fetcher() -> QuickGO_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = QuickGO_Fetcher()
    return _fetcher


def quickgo_search_terms(query: str, limit: int = 100) -> QuickGOFetchedData:
    """Search GO terms by keyword.

    Args:
        query (str): Search query (e.g., "apoptosis", "cell cycle").
        limit (int): Maximum number of results to return.

    Returns:
        QuickGOFetchedData containing matching GO terms with
        their IDs, names, definitions, and aspects.

    Example:
        >>> data = quickgo_search_terms("apoptosis")
        >>> df = data.as_dataframe()
        >>> print(df[["id", "name", "aspect"]].head())
    """
    return _get_fetcher().get(
        category="ontology",
        endpoint="search",
        query=query,
        limit=limit,
    )


def quickgo_get_terms(ids: Union[str, List[str]]) -> QuickGOFetchedData:
    """Get GO term details by ID.

    Args:
        ids (Union[str, List[str]]): GO term ID or list of IDs
            (e.g., "GO:0008150" or ["GO:0008150", "GO:0003674"]).

    Returns:
        QuickGOFetchedData containing term details including
        name, definition, aspect, and synonyms.

    Example:
        ```python
        data = quickgo_get_terms("GO:0006915")  # apoptotic process
        print(data.results[0]["name"])
        ```
    """
    if isinstance(ids, str):
        ids = [ids]
    return _get_fetcher().get(
        category="ontology",
        endpoint="terms/{ids}",
        ids=ids,
    )


def quickgo_get_term_children(go_id: str) -> QuickGOFetchedData:
    """Get child terms of a GO term.

    Args:
        go_id (str): GO term ID (e.g., "GO:0008150").

    Returns:
        QuickGOFetchedData containing direct child terms
        in the GO hierarchy.

    Example:
        >>> data = quickgo_get_term_children("GO:0008150")  # biological_process
        >>> print(len(data.results))  # Number of child terms
    """
    return _get_fetcher().get(
        category="ontology",
        endpoint="terms/{ids}/children",
        ids=[go_id],
    )


def quickgo_get_term_ancestors(go_id: str) -> QuickGOFetchedData:
    """Get ancestor terms of a GO term.

    Args:
        go_id (str): GO term ID (e.g., "GO:0006915").

    Returns:
        QuickGOFetchedData containing ancestor terms
        up to the root of the GO hierarchy.

    Example:
        >>> data = quickgo_get_term_ancestors("GO:0006915")  # apoptotic process
        >>> print([r["name"] for r in data.results])
    """
    return _get_fetcher().get(
        category="ontology",
        endpoint="terms/{ids}/ancestors",
        ids=[go_id],
    )


def quickgo_search_annotations(
    go_id: Optional[str] = None,
    taxon_id: Optional[int] = None,
    gene_product_id: Optional[str] = None,
    evidence_code: Optional[str] = None,
    limit: int = 100,
) -> QuickGOFetchedData:
    """Search GO annotations with filters.

    Args:
        go_id (Optional[str]): GO term ID to filter by.
        taxon_id (Optional[int]): NCBI taxonomy ID (e.g., 9606 for human).
        gene_product_id (Optional[str]): Gene product ID (e.g., "UniProtKB:P04637").
        evidence_code (Optional[str]): Evidence code (e.g., "IDA", "IEA").
        limit (int): Maximum number of results to return.

    Returns:
        QuickGOFetchedData containing matching GO annotations
        with gene products, GO terms, and evidence codes.

    Example:
        >>> data = quickgo_search_annotations(go_id="GO:0006915", taxon_id=9606)
        >>> df = data.as_dataframe()
        >>> print(df[["geneProductId", "goId", "goName"]].head())
    """
    kwargs = {"category": "annotation", "endpoint": "search", "limit": limit}
    if go_id:
        kwargs["goId"] = go_id
    if taxon_id:
        kwargs["taxonId"] = taxon_id
    if gene_product_id:
        kwargs["geneProductId"] = gene_product_id
    if evidence_code:
        kwargs["evidenceCode"] = evidence_code
    return _get_fetcher().get(**kwargs)


def quickgo_search_annotations_all(
    go_id: Optional[str] = None,
    taxon_id: Optional[int] = None,
    max_records: Optional[int] = None,
    **kwargs,
) -> QuickGOFetchedData:
    """Search GO annotations with automatic pagination.

    Fetches all matching annotations by handling pagination automatically.

    Args:
        go_id (Optional[str]): GO term ID to filter by.
        taxon_id (Optional[int]): NCBI taxonomy ID.
        max_records (Optional[int]): Maximum total records to fetch. If None, fetches all.
        **kwargs: Additional filter parameters (goEvidence, aspect, assignedBy, etc.).

    Returns:
        QuickGOFetchedData containing all matching annotations.

    Example:
        >>> data = quickgo_search_annotations_all(
        ...     go_id="GO:0006915",
        ...     taxon_id=9606,
        ...     max_records=5000
        ... )
        >>> print(f"Found {len(data.results)} annotations")
    """
    params = dict(kwargs)
    if go_id:
        params["goId"] = go_id
    if taxon_id:
        params["taxonId"] = taxon_id
    return _get_fetcher().get_all(
        category="annotation",
        endpoint="search",
        max_records=max_records,
        **params,
    )


def quickgo_download_annotations(
    go_id: Optional[str] = None,
    taxon_id: Optional[int] = None,
    download_format: str = "tsv",
    **kwargs,
) -> QuickGOFetchedData:
    """Download GO annotations in various formats.

    Args:
        go_id (Optional[str]): GO term ID to filter by.
        taxon_id (Optional[int]): NCBI taxonomy ID.
        download_format (str): Output format ("tsv", "gaf", or "gpad").
        **kwargs: Additional filter parameters.

    Returns:
        QuickGOFetchedData containing downloaded data in text format.

    Example:
        >>> data = quickgo_download_annotations(
        ...     go_id="GO:0006915",
        ...     taxon_id=9606,
        ...     download_format="gaf"
        ... )
        >>> print(data.text[:500])
    """
    params = {"downloadFormat": download_format, **kwargs}
    if go_id:
        params["goId"] = go_id
    if taxon_id:
        params["taxonId"] = taxon_id
    return _get_fetcher().get(
        category="annotation",
        endpoint="downloadSearch",
        **params,
    )


def quickgo_get_gene_product(gene_product_id: str) -> QuickGOFetchedData:
    """Get gene product information by ID.

    Args:
        gene_product_id (str): Gene product ID (e.g., UniProt accession "P04637").

    Returns:
        QuickGOFetchedData containing gene product details
        including name, synonyms, and database references.

    Example:
        >>> data = quickgo_get_gene_product("P04637")  # TP53
        >>> print(data.results[0])
    """
    return _get_fetcher().get(
        category="geneproduct",
        endpoint="search",
        geneProductId=gene_product_id,
    )
