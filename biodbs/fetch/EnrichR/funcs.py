"""Convenience functions for EnrichR gene set enrichment analysis."""

from typing import Dict, List, Optional
from biodbs.data.EnrichR.data import EnrichRFetchedData, EnrichRLibrariesData
from biodbs.fetch.EnrichR.enrichr_fetcher import EnrichR_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[EnrichR_Fetcher] = None


def _get_fetcher(organism: str = "human") -> EnrichR_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None or _fetcher._organism != organism.lower():
        _fetcher = EnrichR_Fetcher(organism=organism)
    return _fetcher


def enrichr_get_libraries(organism: str = "human") -> EnrichRLibrariesData:
    """Get available gene set libraries.

    Args:
        organism (str): Target organism (human, mouse, fly, yeast, worm, fish).

    Returns:
        EnrichRLibrariesData containing library statistics including
        library names, number of terms, gene coverage, and categories.

    Example:
        >>> libs = enrichr_get_libraries()
        >>> kegg = libs.search("KEGG")
        >>> print(kegg.get_library_names())
    """
    return _get_fetcher(organism).get_libraries()


def enrichr_enrich(
    genes: List[str],
    library: str,
    organism: str = "human",
    description: str = "biodbs gene list",
) -> EnrichRFetchedData:
    """Perform gene set enrichment analysis.

    Args:
        genes (List[str]): List of gene symbols to analyze.
        library (str): Name of the gene set library (e.g., "KEGG_2021_Human").
        organism (str): Target organism (human, mouse, fly, yeast, worm, fish).
        description (str): Description for the gene list.

    Returns:
        EnrichRFetchedData containing enrichment results with
        term names, p-values, combined scores, and overlapping genes.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
        >>> result = enrichr_enrich(genes, "KEGG_2021_Human")
        >>> top = result.top_terms(5)
        >>> print(top.get_term_names())
    """
    return _get_fetcher(organism).enrich(genes, library, description)


def enrichr_enrich_multiple(
    genes: List[str],
    libraries: List[str],
    organism: str = "human",
    description: str = "biodbs gene list",
) -> Dict[str, EnrichRFetchedData]:
    """Perform enrichment analysis against multiple libraries.

    Args:
        genes (List[str]): List of gene symbols to analyze.
        libraries (List[str]): List of library names to query.
        organism (str): Target organism.
        description (str): Description for the gene list.

    Returns:
        Dictionary mapping library names to EnrichRFetchedData objects.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR"]
        >>> results = enrichr_enrich_multiple(
        ...     genes,
        ...     ["KEGG_2021_Human", "GO_Biological_Process_2023"]
        ... )
        >>> for lib, data in results.items():
        ...     print(f"{lib}: {len(data)} terms")
    """
    return _get_fetcher(organism).enrich_multiple(genes, libraries, description)


def enrichr_enrich_with_background(
    genes: List[str],
    background: List[str],
    library: str,
    description: str = "biodbs gene list",
) -> EnrichRFetchedData:
    """Perform enrichment analysis with a custom background gene set.

    Args:
        genes (List[str]): List of query gene symbols.
        background (List[str]): List of background gene symbols.
        library (str): Name of the gene set library.
        description (str): Description for the gene list.

    Returns:
        EnrichRFetchedData containing enrichment results computed
        against the custom background.

    Example:
        >>> genes = ["TP53", "BRCA1"]
        >>> background = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS", "AKT1"]
        >>> result = enrichr_enrich_with_background(
        ...     genes, background, "GO_Biological_Process_2023"
        ... )
    """
    return _get_fetcher().enrich_with_background(genes, background, library, description)


def enrichr_kegg(
    genes: List[str],
    year: str = "2021",
    organism: str = "human",
) -> EnrichRFetchedData:
    """Perform KEGG pathway enrichment.

    Args:
        genes (List[str]): List of gene symbols.
        year (str): KEGG library year version.
        organism (str): Target organism.

    Returns:
        EnrichRFetchedData with KEGG pathway enrichment results.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
        >>> result = enrichr_kegg(genes)
        >>> print(result.significant_terms().get_term_names()[:5])
    """
    return _get_fetcher(organism).enrich_kegg(genes, year)


def enrichr_go_bp(
    genes: List[str],
    year: str = "2023",
    organism: str = "human",
) -> EnrichRFetchedData:
    """Perform GO Biological Process enrichment.

    Args:
        genes (List[str]): List of gene symbols.
        year (str): GO library year version.
        organism (str): Target organism.

    Returns:
        EnrichRFetchedData with GO Biological Process enrichment.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR"]
        >>> result = enrichr_go_bp(genes)
        >>> print(result.top_terms(5).get_term_names())
    """
    return _get_fetcher(organism).enrich_go_bp(genes, year)


def enrichr_go_mf(
    genes: List[str],
    year: str = "2023",
    organism: str = "human",
) -> EnrichRFetchedData:
    """Perform GO Molecular Function enrichment.

    Args:
        genes (List[str]): List of gene symbols.
        year (str): GO library year version.
        organism (str): Target organism.

    Returns:
        EnrichRFetchedData with GO Molecular Function enrichment.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR"]
        >>> result = enrichr_go_mf(genes)
        >>> print(result.top_terms(5).get_term_names())
    """
    return _get_fetcher(organism).enrich_go_mf(genes, year)


def enrichr_go_cc(
    genes: List[str],
    year: str = "2023",
    organism: str = "human",
) -> EnrichRFetchedData:
    """Perform GO Cellular Component enrichment.

    Args:
        genes (List[str]): List of gene symbols.
        year (str): GO library year version.
        organism (str): Target organism.

    Returns:
        EnrichRFetchedData with GO Cellular Component enrichment.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR"]
        >>> result = enrichr_go_cc(genes)
        >>> print(result.top_terms(5).get_term_names())
    """
    return _get_fetcher(organism).enrich_go_cc(genes, year)


def enrichr_reactome(
    genes: List[str],
    year: str = "2022",
    organism: str = "human",
) -> EnrichRFetchedData:
    """Perform Reactome pathway enrichment.

    Args:
        genes (List[str]): List of gene symbols.
        year (str): Reactome library year version.
        organism (str): Target organism.

    Returns:
        EnrichRFetchedData with Reactome pathway enrichment.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR"]
        >>> result = enrichr_reactome(genes)
        >>> print(result.top_terms(5).get_term_names())
    """
    return _get_fetcher(organism).enrich_reactome(genes, year)


def enrichr_wikipathways(
    genes: List[str],
    year: str = "2023",
    organism: str = "human",
) -> EnrichRFetchedData:
    """Perform WikiPathways enrichment.

    Args:
        genes (List[str]): List of gene symbols.
        year (str): WikiPathways library year version.
        organism (str): Target organism.

    Returns:
        EnrichRFetchedData with WikiPathways enrichment.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR"]
        >>> result = enrichr_wikipathways(genes)
        >>> print(result.top_terms(5).get_term_names())
    """
    return _get_fetcher(organism).enrich_wikipathways(genes, year)
