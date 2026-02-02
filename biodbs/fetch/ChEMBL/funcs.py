"""Convenience functions for ChEMBL data fetching."""

from typing import Optional
from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[ChEMBL_Fetcher] = None


def _get_fetcher() -> ChEMBL_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = ChEMBL_Fetcher()
    return _fetcher


def chembl_get_molecule(chembl_id: str):
    """Get molecule data by ChEMBL ID.

    Args:
        chembl_id: ChEMBL molecule ID (e.g., "CHEMBL25").

    Returns:
        ChEMBLFetchedData with molecule information.

    Example:
        >>> data = chembl_get_molecule("CHEMBL25")  # Aspirin
        >>> print(data.as_dict())
    """
    return _get_fetcher().get_molecule(chembl_id)


def chembl_get_target(chembl_id: str):
    """Get target data by ChEMBL ID.

    Args:
        chembl_id: ChEMBL target ID (e.g., "CHEMBL2094253").

    Returns:
        ChEMBLFetchedData with target information.

    Example:
        >>> data = chembl_get_target("CHEMBL2094253")
    """
    return _get_fetcher().get_target(chembl_id)


def chembl_search_molecules(query: str, limit: int = 100):
    """Search molecules by name or synonym.

    Args:
        query: Search query string.
        limit: Maximum number of results.

    Returns:
        ChEMBLFetchedData with matching molecules.

    Example:
        >>> data = chembl_search_molecules("aspirin")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().search_molecules(query, limit)


def chembl_get_activities_for_target(target_chembl_id: str, limit: int = 1000):
    """Get bioactivity data for a target.

    Args:
        target_chembl_id: ChEMBL target ID.
        limit: Maximum number of results.

    Returns:
        ChEMBLFetchedData with activity data.

    Example:
        >>> data = chembl_get_activities_for_target("CHEMBL2094253")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_activities_for_target(target_chembl_id, limit)


def chembl_get_activities_for_molecule(molecule_chembl_id: str, limit: int = 1000):
    """Get bioactivity data for a molecule.

    Args:
        molecule_chembl_id: ChEMBL molecule ID.
        limit: Maximum number of results.

    Returns:
        ChEMBLFetchedData with activity data.

    Example:
        >>> data = chembl_get_activities_for_molecule("CHEMBL25")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_activities_for_molecule(molecule_chembl_id, limit)


def chembl_get_approved_drugs(limit: int = 1000):
    """Get list of approved drugs.

    Args:
        limit: Maximum number of results.

    Returns:
        ChEMBLFetchedData with approved drugs.

    Example:
        >>> data = chembl_get_approved_drugs(limit=100)
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_approved_drugs(limit)


def chembl_get_drug_indications(molecule_chembl_id: str, limit: int = 100):
    """Get drug indications for a molecule.

    Args:
        molecule_chembl_id: ChEMBL molecule ID.
        limit: Maximum number of results.

    Returns:
        ChEMBLFetchedData with indication data.

    Example:
        >>> data = chembl_get_drug_indications("CHEMBL25")
    """
    return _get_fetcher().get_drug_indications(molecule_chembl_id, limit)


def chembl_get_mechanisms(molecule_chembl_id: str, limit: int = 100):
    """Get mechanism of action for a molecule.

    Args:
        molecule_chembl_id: ChEMBL molecule ID.
        limit: Maximum number of results.

    Returns:
        ChEMBLFetchedData with mechanism data.

    Example:
        >>> data = chembl_get_mechanisms("CHEMBL25")
    """
    return _get_fetcher().get_mechanisms(molecule_chembl_id, limit)
