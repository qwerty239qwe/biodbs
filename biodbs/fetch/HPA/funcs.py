"""Convenience functions for Human Protein Atlas (HPA) data fetching."""

from typing import List, Optional, Union
from biodbs.data.HPA.data import HPAFetchedData
from biodbs.fetch.HPA.hpa_fetcher import HPA_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[HPA_Fetcher] = None


def _get_fetcher() -> HPA_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = HPA_Fetcher()
    return _fetcher


def hpa_get_gene(gene: str, fmt: str = "json") -> HPAFetchedData:
    """Get protein data for a single gene.

    Args:
        gene (str): Gene name (e.g., "TP53") or Ensembl ID (e.g., "ENSG00000141510").
        fmt (str): Response format ("json", "xml", or "tsv").

    Returns:
        HPAFetchedData containing protein information including
        expression data, antibody information, and references.

    Example:
        >>> data = hpa_get_gene("TP53")
        >>> print(data.results[0].keys())
    """
    return _get_fetcher().get_gene(gene, fmt)


def hpa_get_genes(genes: List[str], fmt: str = "json") -> HPAFetchedData:
    """Get protein data for multiple genes.

    Args:
        genes (List[str]): List of gene names or Ensembl IDs.
        fmt (str): Response format ("json", "xml", or "tsv").

    Returns:
        HPAFetchedData containing protein information for all genes.

    Example:
        >>> data = hpa_get_genes(["TP53", "BRCA1", "EGFR"])
        >>> df = data.as_dataframe()
        >>> print(df[["Gene", "Gene synonym"]].head())
    """
    return _get_fetcher().get_genes(genes, fmt)


def hpa_get_tissue_expression(genes: Union[str, List[str]]) -> HPAFetchedData:
    """Get tissue expression data for genes.

    Args:
        genes (Union[str, List[str]]): Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData containing tissue expression levels
        across different human tissues and organs.

    Example:
        >>> data = hpa_get_tissue_expression("TP53")
        >>> df = data.as_dataframe()
        >>> print(df[["Gene", "Tissue", "Level"]].head())
    """
    return _get_fetcher().get_tissue_expression(genes)


def hpa_get_blood_expression(genes: Union[str, List[str]]) -> HPAFetchedData:
    """Get blood cell expression data for genes.

    Args:
        genes (Union[str, List[str]]): Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData containing expression levels across
        different blood cell types.

    Example:
        >>> data = hpa_get_blood_expression("TP53")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_blood_expression(genes)


def hpa_get_brain_expression(genes: Union[str, List[str]]) -> HPAFetchedData:
    """Get brain region expression data for genes.

    Args:
        genes (Union[str, List[str]]): Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData containing expression levels across
        different brain regions.

    Example:
        >>> data = hpa_get_brain_expression("TP53")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_brain_expression(genes)


def hpa_get_subcellular_location(genes: Union[str, List[str]]) -> HPAFetchedData:
    """Get subcellular location data for genes.

    Args:
        genes (Union[str, List[str]]): Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData containing subcellular localization data
        based on immunofluorescence microscopy.

    Example:
        >>> data = hpa_get_subcellular_location("TP53")
        >>> df = data.as_dataframe()
        >>> print(df[["Gene", "Main location"]].head())
    """
    return _get_fetcher().get_subcellular_location(genes)


def hpa_get_pathology(genes: Union[str, List[str]]) -> HPAFetchedData:
    """Get cancer/pathology data for genes.

    Args:
        genes (Union[str, List[str]]): Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData containing cancer-related expression data
        across different tumor types.

    Example:
        >>> data = hpa_get_pathology("TP53")
        >>> df = data.as_dataframe()
        >>> print(df[["Gene", "Cancer", "High", "Medium", "Low"]].head())
    """
    return _get_fetcher().get_pathology(genes)


def hpa_get_protein_class(genes: Union[str, List[str]]) -> HPAFetchedData:
    """Get protein class information for genes.

    Args:
        genes (Union[str, List[str]]): Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData containing protein classification data
        including enzyme classes, membrane proteins, etc.

    Example:
        >>> data = hpa_get_protein_class("TP53")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_protein_class(genes)


def hpa_search(
    query: str,
    columns: Optional[List[str]] = None,
    fmt: str = "tsv",
    compress: str = "no",
) -> HPAFetchedData:
    """Search HPA download data.

    Args:
        query (str): Search query string.
        columns (Optional[List[str]]): Columns to include in results.
        fmt (str): Output format ("tsv" or "json").
        compress (str): Compression ("no", "gzip", or "zip").

    Returns:
        HPAFetchedData containing search results matching the query.

    Example:
        >>> data = hpa_search("TP53", columns=["Gene", "Tissue", "Level"])
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().search_download(query, columns, fmt, compress)
