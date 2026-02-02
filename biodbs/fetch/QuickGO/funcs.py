"""Convenience functions for QuickGO data fetching."""

from typing import List, Optional, Union
from biodbs.fetch.QuickGO.quickgo_fetcher import QuickGO_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[QuickGO_Fetcher] = None


def _get_fetcher() -> QuickGO_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = QuickGO_Fetcher()
    return _fetcher


def quickgo_search_terms(query: str, limit: int = 100):
    """Search GO terms by keyword.

    Args:
        query: Search query (e.g., "apoptosis", "cell cycle").
        limit: Maximum number of results.

    Returns:
        QuickGOFetchedData with matching GO terms.

    Example:
        >>> data = quickgo_search_terms("apoptosis")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="ontology",
        endpoint="search",
        query=query,
        limit=limit,
    )


def quickgo_get_terms(ids: Union[str, List[str]]):
    """Get GO term details by ID.

    Args:
        ids: GO term ID(s) (e.g., "GO:0008150", ["GO:0008150", "GO:0003674"]).

    Returns:
        QuickGOFetchedData with term details.

    Example:
        >>> data = quickgo_get_terms("GO:0006915")  # apoptotic process
        >>> print(data.results[0]["name"])
    """
    if isinstance(ids, str):
        ids = [ids]
    return _get_fetcher().get(
        category="ontology",
        endpoint="terms/{ids}",
        ids=ids,
    )


def quickgo_get_term_children(go_id: str):
    """Get child terms of a GO term.

    Args:
        go_id: GO term ID (e.g., "GO:0008150").

    Returns:
        QuickGOFetchedData with child terms.

    Example:
        >>> data = quickgo_get_term_children("GO:0008150")
    """
    return _get_fetcher().get(
        category="ontology",
        endpoint="terms/{ids}/children",
        ids=[go_id],
    )


def quickgo_get_term_ancestors(go_id: str):
    """Get ancestor terms of a GO term.

    Args:
        go_id: GO term ID (e.g., "GO:0006915").

    Returns:
        QuickGOFetchedData with ancestor terms.

    Example:
        >>> data = quickgo_get_term_ancestors("GO:0006915")
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
):
    """Search GO annotations.

    Args:
        go_id: GO term ID to filter by.
        taxon_id: NCBI taxonomy ID (e.g., 9606 for human).
        gene_product_id: Gene product ID (e.g., UniProt ID).
        evidence_code: Evidence code (e.g., "IDA", "IEA").
        limit: Maximum number of results.

    Returns:
        QuickGOFetchedData with annotations.

    Example:
        >>> # Get human apoptosis annotations
        >>> data = quickgo_search_annotations(go_id="GO:0006915", taxon_id=9606)
        >>> df = data.as_dataframe()
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
):
    """Search GO annotations with automatic pagination.

    Args:
        go_id: GO term ID to filter by.
        taxon_id: NCBI taxonomy ID.
        max_records: Maximum total records to fetch (None = all).
        **kwargs: Additional parameters (evidenceCode, aspect, etc.).

    Returns:
        QuickGOFetchedData with all matching annotations.

    Example:
        >>> data = quickgo_search_annotations_all(
        ...     go_id="GO:0006915",
        ...     taxon_id=9606,
        ...     max_records=5000
        ... )
        >>> print(len(data.results))
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
):
    """Download GO annotations in various formats.

    Args:
        go_id: GO term ID to filter by.
        taxon_id: NCBI taxonomy ID.
        download_format: Output format ("tsv", "gaf", "gpad").
        **kwargs: Additional parameters.

    Returns:
        QuickGOFetchedData with downloaded data (text format).

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


def quickgo_get_gene_product(gene_product_id: str):
    """Get gene product information.

    Args:
        gene_product_id: Gene product ID (e.g., UniProt accession).

    Returns:
        QuickGOFetchedData with gene product details.

    Example:
        >>> data = quickgo_get_gene_product("P04637")  # TP53
    """
    return _get_fetcher().get(
        category="geneproduct",
        endpoint="search",
        geneProductId=gene_product_id,
    )
