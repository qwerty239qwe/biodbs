"""Convenience functions for Disease Ontology API."""

from typing import List, Dict, Optional, Union
import pandas as pd

from biodbs.fetch.DiseaseOntology.do_fetcher import DO_Fetcher
from biodbs.data.DiseaseOntology.data import DOFetchedData, DOSearchFetchedData


def do_get_term(
    doid: str,
    use_ols: bool = True,
) -> DOFetchedData:
    """Get a disease term by DOID.

    This is a convenience function that wraps the DO_Fetcher.

    Args:
        doid: Disease Ontology ID (e.g., "DOID:162", "162").
        use_ols: If True, use OLS API for more detailed data.

    Returns:
        DOFetchedData containing the disease term.

    Example:
        >>> term = do_get_term("DOID:162")  # Cancer
        >>> print(term.terms[0].name)
        'cancer'
    """
    fetcher = DO_Fetcher()
    return fetcher.get_term(doid, use_ols=use_ols)


def do_get_terms(
    doids: List[str],
    use_ols: bool = True,
) -> DOFetchedData:
    """Get multiple disease terms by DOIDs.

    Args:
        doids: List of Disease Ontology IDs.
        use_ols: If True, use OLS API for more detailed data.

    Returns:
        DOFetchedData containing all disease terms.

    Example:
        >>> terms = do_get_terms(["DOID:162", "DOID:1612"])
        >>> print(terms.get_names())
    """
    fetcher = DO_Fetcher()
    return fetcher.get_terms(doids, use_ols=use_ols)


def do_search(
    query: str,
    exact: bool = False,
    rows: int = 20,
    obsoletes: bool = False,
) -> DOSearchFetchedData:
    """Search for disease terms.

    Args:
        query: Search query string.
        exact: If True, search for exact matches only.
        rows: Maximum number of results to return.
        obsoletes: If True, include obsolete terms.

    Returns:
        DOSearchFetchedData with search results.

    Example:
        >>> results = do_search("breast cancer")
        >>> print(results.get_doids())
    """
    fetcher = DO_Fetcher()
    return fetcher.search(query, exact=exact, rows=rows, obsoletes=obsoletes)


def do_get_parents(doid: str) -> DOFetchedData:
    """Get parent terms of a disease.

    Args:
        doid: Disease Ontology ID.

    Returns:
        DOFetchedData with parent terms.

    Example:
        >>> parents = do_get_parents("DOID:1612")  # Breast cancer
        >>> for term in parents.terms:
        ...     print(f"{term.doid}: {term.name}")
    """
    fetcher = DO_Fetcher()
    return fetcher.get_parents(doid)


def do_get_children(doid: str) -> DOFetchedData:
    """Get child terms of a disease.

    Args:
        doid: Disease Ontology ID.

    Returns:
        DOFetchedData with child terms.

    Example:
        >>> children = do_get_children("DOID:162")  # Cancer
        >>> print(f"Cancer has {len(children)} child terms")
    """
    fetcher = DO_Fetcher()
    return fetcher.get_children(doid)


def do_get_ancestors(doid: str) -> DOFetchedData:
    """Get all ancestor terms of a disease.

    Args:
        doid: Disease Ontology ID.

    Returns:
        DOFetchedData with ancestor terms.
    """
    fetcher = DO_Fetcher()
    return fetcher.get_ancestors(doid)


def do_get_descendants(doid: str) -> DOFetchedData:
    """Get all descendant terms of a disease.

    Args:
        doid: Disease Ontology ID.

    Returns:
        DOFetchedData with descendant terms.
    """
    fetcher = DO_Fetcher()
    return fetcher.get_descendants(doid)


def doid_to_mesh(
    doids: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, Optional[str]], "pd.DataFrame"]:
    """Convert DOIDs to MeSH IDs.

    Args:
        doids: List of Disease Ontology IDs.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary mapping DOIDs to MeSH IDs, or DataFrame.

    Example:
        >>> mapping = doid_to_mesh(["DOID:162", "DOID:1612"])
        >>> print(mapping)
    """
    fetcher = DO_Fetcher()
    mapping = fetcher.doid_to_mesh(doids)

    if return_dict:
        return mapping

    records = [{"doid": k, "mesh_id": v} for k, v in mapping.items()]
    return pd.DataFrame(records)


def doid_to_umls(
    doids: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, Optional[str]], "pd.DataFrame"]:
    """Convert DOIDs to UMLS CUIs.

    Args:
        doids: List of Disease Ontology IDs.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary mapping DOIDs to UMLS CUIs, or DataFrame.

    Example:
        >>> mapping = doid_to_umls(["DOID:162", "DOID:1612"])
        >>> print(mapping)
    """
    fetcher = DO_Fetcher()
    mapping = fetcher.doid_to_umls(doids)

    if return_dict:
        return mapping

    records = [{"doid": k, "umls_cui": v} for k, v in mapping.items()]
    return pd.DataFrame(records)


def doid_to_icd10(
    doids: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, Optional[str]], "pd.DataFrame"]:
    """Convert DOIDs to ICD-10 codes.

    Args:
        doids: List of Disease Ontology IDs.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary mapping DOIDs to ICD-10 codes, or DataFrame.

    Example:
        >>> mapping = doid_to_icd10(["DOID:162", "DOID:1612"])
        >>> print(mapping)
    """
    fetcher = DO_Fetcher()
    mapping = fetcher.doid_to_icd10(doids)

    if return_dict:
        return mapping

    records = [{"doid": k, "icd10_code": v} for k, v in mapping.items()]
    return pd.DataFrame(records)


def do_xref_mapping(
    doids: List[str],
    database: str,
    return_dict: bool = True,
) -> Union[Dict[str, Optional[str]], "pd.DataFrame"]:
    """Get cross-reference mapping for DOIDs to any database.

    Args:
        doids: List of Disease Ontology IDs.
        database: Target database name (e.g., "MESH", "UMLS_CUI", "ICD10CM", "NCI").
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary mapping DOIDs to external IDs, or DataFrame.

    Example:
        >>> mapping = do_xref_mapping(["DOID:162"], "NCI")
        >>> print(mapping)
    """
    fetcher = DO_Fetcher()
    terms = fetcher.get_terms(doids)
    mapping = terms.to_xref_mapping(database)

    if return_dict:
        return mapping

    records = [{"doid": k, database.lower(): v} for k, v in mapping.items()]
    return pd.DataFrame(records)
