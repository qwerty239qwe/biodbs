"""Convenience functions for Human Protein Atlas (HPA) data fetching."""

from typing import List, Optional, Union
from biodbs.fetch.HPA.hpa_fetcher import HPA_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[HPA_Fetcher] = None


def _get_fetcher() -> HPA_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = HPA_Fetcher()
    return _fetcher


def hpa_get_gene(gene: str, fmt: str = "json"):
    """Get protein data for a single gene.

    Args:
        gene: Gene name (e.g., "TP53") or Ensembl ID (e.g., "ENSG00000141510").
        fmt: Response format ("json", "xml", or "tsv").

    Returns:
        HPAFetchedData with protein information.

    Example:
        >>> data = hpa_get_gene("TP53")
        >>> print(data.as_dict())
    """
    return _get_fetcher().get_gene(gene, fmt)


def hpa_get_genes(genes: List[str], fmt: str = "json"):
    """Get protein data for multiple genes.

    Args:
        genes: List of gene names or Ensembl IDs.
        fmt: Response format ("json", "xml", or "tsv").

    Returns:
        HPAFetchedData with protein information for all genes.

    Example:
        >>> data = hpa_get_genes(["TP53", "BRCA1", "EGFR"])
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_genes(genes, fmt)


def hpa_get_tissue_expression(genes: Union[str, List[str]]):
    """Get tissue expression data for genes.

    Args:
        genes: Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData with tissue expression data.

    Example:
        >>> data = hpa_get_tissue_expression("TP53")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_tissue_expression(genes)


def hpa_get_blood_expression(genes: Union[str, List[str]]):
    """Get blood cell expression data for genes.

    Args:
        genes: Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData with blood expression data.
    """
    return _get_fetcher().get_blood_expression(genes)


def hpa_get_brain_expression(genes: Union[str, List[str]]):
    """Get brain region expression data for genes.

    Args:
        genes: Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData with brain expression data.
    """
    return _get_fetcher().get_brain_expression(genes)


def hpa_get_subcellular_location(genes: Union[str, List[str]]):
    """Get subcellular location data for genes.

    Args:
        genes: Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData with subcellular location data.

    Example:
        >>> data = hpa_get_subcellular_location("TP53")
    """
    return _get_fetcher().get_subcellular_location(genes)


def hpa_get_pathology(genes: Union[str, List[str]]):
    """Get cancer/pathology data for genes.

    Args:
        genes: Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData with pathology data.

    Example:
        >>> data = hpa_get_pathology("TP53")
    """
    return _get_fetcher().get_pathology(genes)


def hpa_get_protein_class(genes: Union[str, List[str]]):
    """Get protein class information for genes.

    Args:
        genes: Gene name(s) or Ensembl ID(s).

    Returns:
        HPAFetchedData with protein class data.
    """
    return _get_fetcher().get_protein_class(genes)


def hpa_search(
    query: str,
    columns: Optional[List[str]] = None,
    fmt: str = "tsv",
    compress: str = "no",
):
    """Search HPA download data.

    Args:
        query: Search query string.
        columns: Columns to include in results.
        fmt: Format ("tsv" or "json").
        compress: Compression ("no", "gzip", or "zip").

    Returns:
        HPAFetchedData with search results.

    Example:
        >>> data = hpa_search("TP53", columns=["Gene", "Tissue", "Level"])
    """
    return _get_fetcher().search_download(query, columns, fmt, compress)
