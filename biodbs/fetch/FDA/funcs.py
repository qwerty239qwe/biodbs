"""Convenience functions for FDA openFDA data fetching."""

from typing import Dict, Optional, Union
from biodbs.fetch.FDA.fda_fetcher import FDA_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[FDA_Fetcher] = None


def _get_fetcher() -> FDA_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = FDA_Fetcher()
    return _fetcher


def fda_search(
    category: str,
    endpoint: str,
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Generic FDA search function.

    Args:
        category: FDA category (drug, device, food, etc.).
        endpoint: Endpoint within category (event, label, enforcement, etc.).
        search: Search query string or dict.
        limit: Maximum results per request.
        **kwargs: Additional parameters (sort, count, skip).

    Returns:
        FDAFetchedData with search results.

    Example:
        >>> data = fda_search("drug", "event", search="patient.drug.openfda.brand_name:aspirin", limit=10)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category=category,
        endpoint=endpoint,
        search=search,
        limit=limit,
        **kwargs,
    )


def fda_search_all(
    category: str,
    endpoint: str,
    search: Optional[Union[str, Dict]] = None,
    max_records: Optional[int] = None,
    **kwargs,
):
    """FDA search with automatic pagination.

    Args:
        category: FDA category.
        endpoint: Endpoint within category.
        search: Search query.
        max_records: Maximum total records to fetch (None = all available).
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with all matching results.

    Example:
        >>> data = fda_search_all("drug", "event", search="aspirin", max_records=5000)
        >>> print(len(data.results))
    """
    return _get_fetcher().get_all(
        category=category,
        endpoint=endpoint,
        search=search,
        max_records=max_records,
        **kwargs,
    )


# =============================================================================
# Drug functions
# =============================================================================


def fda_drug_events(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA drug adverse event reports (FAERS).

    Args:
        search: Search query (e.g., "patient.drug.openfda.brand_name:aspirin").
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with adverse event reports.

    Example:
        >>> data = fda_drug_events(search={"receivedate": "[20200101 TO 20201231]"}, limit=50)
        >>> df = data.as_dataframe(columns=["receivedate", "patient.patientsex"])
    """
    return _get_fetcher().get(
        category="drug", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_drug_labels(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA drug labeling information.

    Args:
        search: Search query (e.g., "openfda.brand_name:aspirin").
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with drug labels.

    Example:
        >>> data = fda_drug_labels(search="openfda.brand_name:aspirin")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="drug", endpoint="label", search=search, limit=limit, **kwargs
    )


def fda_drug_enforcement(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA drug recall enforcement reports.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with enforcement reports.

    Example:
        >>> data = fda_drug_enforcement(limit=50)
    """
    return _get_fetcher().get(
        category="drug", endpoint="enforcement", search=search, limit=limit, **kwargs
    )


def fda_drug_ndc(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA National Drug Code (NDC) directory.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with NDC entries.

    Example:
        >>> data = fda_drug_ndc(search="brand_name:aspirin")
    """
    return _get_fetcher().get(
        category="drug", endpoint="ndc", search=search, limit=limit, **kwargs
    )


def fda_drug_drugsfda(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search Drugs@FDA database (approved drug products).

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with approved drug products.

    Example:
        >>> data = fda_drug_drugsfda(search="products.brand_name:aspirin")
    """
    return _get_fetcher().get(
        category="drug", endpoint="drugsfda", search=search, limit=limit, **kwargs
    )


# =============================================================================
# Device functions
# =============================================================================


def fda_device_events(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA medical device adverse event reports (MAUDE).

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with device adverse events.

    Example:
        >>> data = fda_device_events(limit=50)
    """
    return _get_fetcher().get(
        category="device", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_device_classification(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA device classification database.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with device classifications.
    """
    return _get_fetcher().get(
        category="device", endpoint="classification", search=search, limit=limit, **kwargs
    )


def fda_device_510k(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA 510(k) premarket notifications.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with 510(k) clearances.
    """
    return _get_fetcher().get(
        category="device", endpoint="510k", search=search, limit=limit, **kwargs
    )


def fda_device_pma(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA Premarket Approval (PMA) database.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with PMA approvals.
    """
    return _get_fetcher().get(
        category="device", endpoint="pma", search=search, limit=limit, **kwargs
    )


def fda_device_recall(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA device recall database.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with device recalls.
    """
    return _get_fetcher().get(
        category="device", endpoint="recall", search=search, limit=limit, **kwargs
    )


def fda_device_udi(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA Unique Device Identifier (UDI) database.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with UDI entries.
    """
    return _get_fetcher().get(
        category="device", endpoint="udi", search=search, limit=limit, **kwargs
    )


# =============================================================================
# Food functions
# =============================================================================


def fda_food_events(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA food adverse event reports (CAERS).

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with food adverse events.

    Example:
        >>> data = fda_food_events(limit=50)
    """
    return _get_fetcher().get(
        category="food", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_food_enforcement(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA food recall enforcement reports.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with food enforcement reports.
    """
    return _get_fetcher().get(
        category="food", endpoint="enforcement", search=search, limit=limit, **kwargs
    )


# =============================================================================
# Other categories
# =============================================================================


def fda_animalandveterinary_events(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA animal and veterinary adverse event reports.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with animal/vet adverse events.
    """
    return _get_fetcher().get(
        category="animalandveterinary", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_tobacco_problem(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
):
    """Search FDA tobacco problem reports.

    Args:
        search: Search query.
        limit: Maximum results.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData with tobacco problem reports.
    """
    return _get_fetcher().get(
        category="tobacco", endpoint="problem", search=search, limit=limit, **kwargs
    )
