"""Convenience functions for FDA openFDA data fetching."""

from typing import Any, Dict, Optional, Union
from biodbs.data.FDA.data import FDAFetchedData
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
    **kwargs: Any,
) -> FDAFetchedData:
    """Search FDA openFDA database.

    Args:
        category (str): FDA category ("drug", "device", "food", etc.).
        endpoint (str): Endpoint within category ("event", "label", "enforcement", etc.).
        search (Optional[Union[str, Dict]]): Search query string or dict of field:value pairs.
        limit (int): Maximum results per request.
        **kwargs: Additional parameters (sort, count, skip).

    Returns:
        FDAFetchedData containing search results.

    Example:
        >>> data = fda_search("drug", "event", search="aspirin", limit=10)
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
    **kwargs: Any,
) -> FDAFetchedData:
    """Search FDA openFDA database with automatic pagination.

    Args:
        category (str): FDA category.
        endpoint (str): Endpoint within category.
        search (Optional[Union[str, Dict]]): Search query.
        max_records (Optional[int]): Maximum total records to fetch. If None, fetches all available.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing all matching results.

    Example:
        >>> data = fda_search_all("drug", "event", search="aspirin", max_records=5000)
        >>> print(f"Found {len(data.results)} records")
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
    **kwargs: Any,
) -> FDAFetchedData:
    """Search FDA drug adverse event reports (FAERS).

    Args:
        search (Optional[Union[str, Dict]]): Search query (e.g., "patient.drug.openfda.brand_name:aspirin").
        limit (int): Maximum results to return.
        **kwargs: Additional parameters (sort, count, skip).

    Returns:
        FDAFetchedData containing adverse event reports with
        patient information, drug details, and outcomes.

    Example:
        >>> data = fda_drug_events(search="aspirin", limit=50)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="drug", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_drug_labels(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA drug labeling information (SPL).

    Args:
        search (Optional[Union[str, Dict]]): Search query (e.g., "openfda.brand_name:aspirin").
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing drug labels with
        indications, warnings, dosage, and contraindications.

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
) -> FDAFetchedData:
    """Search FDA drug recall enforcement reports.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing drug recall and enforcement
        actions with classification and distribution details.

    Example:
        >>> data = fda_drug_enforcement(limit=50)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="drug", endpoint="enforcement", search=search, limit=limit, **kwargs
    )


def fda_drug_ndc(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA National Drug Code (NDC) directory.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing NDC entries with
        product and packaging information.

    Example:
        >>> data = fda_drug_ndc(search="brand_name:aspirin")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="drug", endpoint="ndc", search=search, limit=limit, **kwargs
    )


def fda_drug_drugsfda(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search Drugs@FDA database (approved drug products).

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing approved drug products
        with application numbers and approval details.

    Example:
        >>> data = fda_drug_drugsfda(search="products.brand_name:aspirin")
        >>> df = data.as_dataframe()
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
) -> FDAFetchedData:
    """Search FDA medical device adverse event reports (MAUDE).

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing device adverse events
        with device and patient information.

    Example:
        >>> data = fda_device_events(search="pacemaker", limit=50)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="device", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_device_classification(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA device classification database.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing device classifications
        with regulatory class and product codes.

    Example:
        >>> data = fda_device_classification(search="pacemaker")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="device", endpoint="classification", search=search, limit=limit, **kwargs
    )


def fda_device_510k(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA 510(k) premarket notifications.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing 510(k) clearance records.

    Example:
        >>> data = fda_device_510k(search="pacemaker")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="device", endpoint="510k", search=search, limit=limit, **kwargs
    )


def fda_device_pma(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA Premarket Approval (PMA) database.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing PMA approval records.

    Example:
        >>> data = fda_device_pma(search="pacemaker")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="device", endpoint="pma", search=search, limit=limit, **kwargs
    )


def fda_device_recall(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA device recall database.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing device recall records.

    Example:
        >>> data = fda_device_recall(limit=50)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="device", endpoint="recall", search=search, limit=limit, **kwargs
    )


def fda_device_udi(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA Unique Device Identifier (UDI) database.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing UDI entries with
        device identification and labeling information.

    Example:
        >>> data = fda_device_udi(search="pacemaker")
        >>> df = data.as_dataframe()
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
) -> FDAFetchedData:
    """Search FDA food adverse event reports (CAERS).

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing food adverse event reports.

    Example:
        >>> data = fda_food_events(search="salmonella", limit=50)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="food", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_food_enforcement(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA food recall enforcement reports.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing food enforcement reports.

    Example:
        >>> data = fda_food_enforcement(limit=50)
        >>> df = data.as_dataframe()
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
) -> FDAFetchedData:
    """Search FDA animal and veterinary adverse event reports.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing animal/veterinary adverse events.

    Example:
        >>> data = fda_animalandveterinary_events(search="dog", limit=50)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="animalandveterinary", endpoint="event", search=search, limit=limit, **kwargs
    )


def fda_tobacco_problem(
    search: Optional[Union[str, Dict]] = None,
    limit: int = 100,
    **kwargs,
) -> FDAFetchedData:
    """Search FDA tobacco problem reports.

    Args:
        search (Optional[Union[str, Dict]]): Search query.
        limit (int): Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        FDAFetchedData containing tobacco problem reports.

    Example:
        >>> data = fda_tobacco_problem(search="cigarette", limit=50)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get(
        category="tobacco", endpoint="problem", search=search, limit=limit, **kwargs
    )
