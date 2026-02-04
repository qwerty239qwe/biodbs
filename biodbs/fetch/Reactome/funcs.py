"""Convenience functions for Reactome API access.

These functions provide a simple interface for common Reactome operations
without needing to instantiate a fetcher object.

Example:
    >>> from biodbs.fetch.Reactome.funcs import reactome_analyze
    >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
    >>> result = reactome_analyze(genes)
    >>> print(result.significant_pathways().as_dataframe())
"""

from typing import Dict, Any, List, Optional
from biodbs.data.Reactome.data import (
    ReactomeFetchedData,
    ReactomePathwaysData,
    ReactomeSpeciesData,
)

# Module-level fetcher instance (lazy initialization)
_fetcher = None


def _get_fetcher():
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        from biodbs.fetch.Reactome.reactome_fetcher import Reactome_Fetcher
        _fetcher = Reactome_Fetcher()
    return _fetcher


def reactome_analyze(
    identifiers: List[str],
    species: str = "Homo sapiens",
    interactors: bool = False,
    page_size: int = 100,
    sort_by: str = "ENTITIES_FDR",
    order: str = "ASC",
    resource: str = "TOTAL",
    p_value: float = 1.0,
    include_disease: bool = True,
    min_entities: Optional[int] = None,
    max_entities: Optional[int] = None,
) -> ReactomeFetchedData:
    """Perform Reactome pathway over-representation analysis.

    Args:
        identifiers: List of identifiers (gene symbols, UniProt IDs, etc.).
        species: Species name (e.g., "Homo sapiens", "Mus musculus").
        interactors: Include interactors in analysis.
        page_size: Number of results to return.
        sort_by: Sort field (ENTITIES_FDR, ENTITIES_PVALUE, NAME).
        order: Sort order (ASC, DESC).
        resource: Resource filter (TOTAL, UNIPROT, ENSEMBL, etc.).
        p_value: P-value cutoff for filtering.
        include_disease: Include disease pathways.
        min_entities: Minimum pathway size.
        max_entities: Maximum pathway size.

    Returns:
        ReactomeFetchedData with pathway enrichment results.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
        >>> result = reactome_analyze(genes)
        >>> df = result.significant_pathways(fdr_threshold=0.05).as_dataframe()
        >>> print(df[["name", "fdr", "found", "total"]].head())
    """
    fetcher = _get_fetcher()
    return fetcher.analyze(
        identifiers=identifiers,
        species=species,
        interactors=interactors,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
        resource=resource,
        p_value=p_value,
        include_disease=include_disease,
        min_entities=min_entities,
        max_entities=max_entities,
    )


def reactome_analyze_projection(
    identifiers: List[str],
    species: str = "Homo sapiens",
    interactors: bool = False,
    page_size: int = 100,
) -> ReactomeFetchedData:
    """Analyze identifiers and project results to Homo sapiens.

    Useful for analyzing data from other species while viewing results
    in the context of human pathways.

    Args:
        identifiers: List of identifiers.
        species: Source species name (for mapping).
        interactors: Include interactors.
        page_size: Results per page.

    Returns:
        ReactomeFetchedData with human-projected pathway results.

    Example:
        >>> # Analyze mouse genes projected to human pathways
        >>> result = reactome_analyze_projection(
        ...     ["Trp53", "Brca1", "Egfr"],
        ...     species="Mus musculus"
        ... )
    """
    fetcher = _get_fetcher()
    return fetcher.analyze_projection(
        identifiers=identifiers,
        species=species,
        interactors=interactors,
        page_size=page_size,
    )


def reactome_analyze_single(
    identifier: str,
    species: str = "Homo sapiens",
    interactors: bool = False,
) -> ReactomeFetchedData:
    """Analyze a single identifier.

    Args:
        identifier: Single identifier to analyze.
        species: Species filter.
        interactors: Include interactors.

    Returns:
        ReactomeFetchedData with pathways containing the identifier.

    Example:
        >>> result = reactome_analyze_single("TP53")
        >>> print(result.get_pathway_names()[:5])
    """
    fetcher = _get_fetcher()
    return fetcher.analyze_single(
        identifier=identifier,
        species=species,
        interactors=interactors,
    )


def reactome_get_result_by_token(
    token: str,
    species: Optional[str] = None,
    page_size: int = 100,
    page: int = 1,
) -> ReactomeFetchedData:
    """Retrieve analysis results by token.

    Args:
        token: Analysis token from previous analysis.
        species: Species filter.
        page_size: Results per page.
        page: Page number.

    Returns:
        ReactomeFetchedData with analysis results.

    Example:
        >>> # Get first result
        >>> result = reactome_analyze(genes)
        >>> token = result.token
        >>> # Later, retrieve the same results
        >>> result2 = reactome_get_result_by_token(token)
    """
    fetcher = _get_fetcher()
    return fetcher.get_result_by_token(
        token=token,
        species=species,
        page_size=page_size,
        page=page,
    )


def reactome_get_found_entities(
    token: str,
    pathway_id: str,
) -> List[Dict[str, Any]]:
    """Get entities found in a specific pathway.

    Args:
        token: Analysis token.
        pathway_id: Pathway stable ID (e.g., "R-HSA-123456").

    Returns:
        List of found entity dictionaries.

    Example:
        >>> result = reactome_analyze(genes)
        >>> entities = reactome_get_found_entities(result.token, "R-HSA-69278")
        >>> print([e["id"] for e in entities])
    """
    fetcher = _get_fetcher()
    return fetcher.get_found_entities(token=token, pathway_id=pathway_id)


def reactome_get_not_found(token: str) -> List[str]:
    """Get identifiers that were not found in Reactome.

    Args:
        token: Analysis token.

    Returns:
        List of unmapped identifier strings.

    Example:
        >>> result = reactome_analyze(genes)
        >>> not_found = reactome_get_not_found(result.token)
        >>> print(f"Unmapped: {not_found}")
    """
    fetcher = _get_fetcher()
    return fetcher.get_not_found_identifiers(token=token)


def reactome_map_identifiers(
    identifiers: List[str],
    interactors: bool = False,
) -> List[Dict[str, Any]]:
    """Map identifiers to Reactome entities without analysis.

    Args:
        identifiers: List of identifiers to map.
        interactors: Include interactor mapping.

    Returns:
        List of mapped entity dictionaries.

    Example:
        >>> mapped = reactome_map_identifiers(["TP53", "BRCA1"])
        >>> for entity in mapped:
        ...     print(f"{entity['identifier']} -> {entity.get('mapsTo', [])}")
    """
    fetcher = _get_fetcher()
    return fetcher.map_identifiers(
        identifiers=identifiers,
        interactors=interactors,
    )


def reactome_get_pathways_top(
    species: str = "Homo sapiens",
) -> ReactomePathwaysData:
    """Get top-level pathways for a species.

    Args:
        species: Species name (e.g., "Homo sapiens").

    Returns:
        ReactomePathwaysData with top-level pathway information.

    Example:
        >>> pathways = reactome_get_pathways_top("Homo sapiens")
        >>> print(pathways.get_pathway_names())
    """
    fetcher = _get_fetcher()
    return fetcher.get_pathways_top(species=species)


def reactome_get_pathways_for_entity(
    entity_id: str,
) -> ReactomePathwaysData:
    """Get pathways containing a specific entity.

    Args:
        entity_id: Entity identifier (UniProt, gene symbol, etc.).

    Returns:
        ReactomePathwaysData with pathways containing the entity.

    Example:
        >>> pathways = reactome_get_pathways_for_entity("P04637")  # TP53
        >>> print(f"TP53 is in {len(pathways)} pathways")
    """
    fetcher = _get_fetcher()
    return fetcher.get_pathways_for_entity(entity_id=entity_id)


def reactome_get_species() -> ReactomeSpeciesData:
    """Get all species in Reactome.

    Returns:
        ReactomeSpeciesData with species information.

    Example:
        >>> species = reactome_get_species()
        >>> print(species.get_species_names()[:10])
    """
    fetcher = _get_fetcher()
    return fetcher.get_species()


def reactome_get_species_main() -> ReactomeSpeciesData:
    """Get main species with curated or inferred pathways.

    Returns:
        ReactomeSpeciesData with main species information.

    Example:
        >>> species = reactome_get_species_main()
        >>> for s in species.species:
        ...     print(f"{s['displayName']}: taxId={s.get('taxId')}")
    """
    fetcher = _get_fetcher()
    return fetcher.get_species_main()


def reactome_get_database_version() -> str:
    """Get current Reactome database version.

    Returns:
        Database version string.

    Example:
        >>> version = reactome_get_database_version()
        >>> print(f"Reactome version: {version}")
    """
    fetcher = _get_fetcher()
    return fetcher.get_database_version()


def reactome_query_entry(entry_id: str) -> Dict[str, Any]:
    """Query a Reactome entry by ID.

    Args:
        entry_id: Reactome stable ID (e.g., "R-HSA-123456").

    Returns:
        Entry details dictionary.

    Example:
        >>> entry = reactome_query_entry("R-HSA-69278")
        >>> print(f"{entry['displayName']}: {entry.get('summation', [{}])[0].get('text', '')[:100]}")
    """
    fetcher = _get_fetcher()
    return fetcher.query_entry(entry_id=entry_id)
