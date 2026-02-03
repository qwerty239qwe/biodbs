"""Convenience functions for ChEMBL data fetching."""

from typing import Optional
from biodbs.data.ChEMBL.data import ChEMBLFetchedData
from biodbs.fetch.ChEMBL.chembl_fetcher import ChEMBL_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[ChEMBL_Fetcher] = None


def _get_fetcher() -> ChEMBL_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = ChEMBL_Fetcher()
    return _fetcher


def chembl_get_molecule(chembl_id: str) -> ChEMBLFetchedData:
    """Get molecule data by ChEMBL ID.

    Args:
        chembl_id (str): ChEMBL molecule ID (e.g., "CHEMBL25").

    Returns:
        ChEMBLFetchedData containing molecule information including
        structure, properties, and cross-references.

    Example:
        >>> data = chembl_get_molecule("CHEMBL25")  # Aspirin
        >>> print(data.results[0]["pref_name"])
    """
    return _get_fetcher().get_molecule(chembl_id)


def chembl_get_target(chembl_id: str) -> ChEMBLFetchedData:
    """Get target data by ChEMBL ID.

    Args:
        chembl_id (str): ChEMBL target ID (e.g., "CHEMBL2094253").

    Returns:
        ChEMBLFetchedData containing target information including
        protein classification, organism, and associated genes.

    Example:
        >>> data = chembl_get_target("CHEMBL2094253")
        >>> print(data.results[0]["pref_name"])
    """
    return _get_fetcher().get_target(chembl_id)


def chembl_search_molecules(query: str, limit: int = 100) -> ChEMBLFetchedData:
    """Search molecules by name, synonym, or structure.

    Args:
        query (str): Search query (name, synonym, or InChIKey).
        limit (int): Maximum number of results to return.

    Returns:
        ChEMBLFetchedData containing matching molecules.

    Example:
        >>> data = chembl_search_molecules("aspirin")
        >>> df = data.as_dataframe()
        >>> print(df[["molecule_chembl_id", "pref_name"]].head())
    """
    return _get_fetcher().search_molecules(query, limit)


def chembl_get_activities_for_target(
    target_chembl_id: str,
    limit: int = 1000,
) -> ChEMBLFetchedData:
    """Get bioactivity data for a target.

    Args:
        target_chembl_id (str): ChEMBL target ID.
        limit (int): Maximum number of activity records to return.

    Returns:
        ChEMBLFetchedData containing bioactivity measurements
        (IC50, Ki, EC50, etc.) for compounds tested against the target.

    Example:
        >>> data = chembl_get_activities_for_target("CHEMBL2094253")
        >>> df = data.as_dataframe()
        >>> print(df[["molecule_chembl_id", "standard_type", "standard_value"]].head())
    """
    return _get_fetcher().get_activities_for_target(target_chembl_id, limit)


def chembl_get_activities_for_molecule(
    molecule_chembl_id: str,
    limit: int = 1000,
) -> ChEMBLFetchedData:
    """Get bioactivity data for a molecule.

    Args:
        molecule_chembl_id (str): ChEMBL molecule ID.
        limit (int): Maximum number of activity records to return.

    Returns:
        ChEMBLFetchedData containing bioactivity measurements
        for the molecule across all tested targets.

    Example:
        >>> data = chembl_get_activities_for_molecule("CHEMBL25")
        >>> df = data.as_dataframe()
        >>> print(df[["target_chembl_id", "standard_type", "standard_value"]].head())
    """
    return _get_fetcher().get_activities_for_molecule(molecule_chembl_id, limit)


def chembl_get_approved_drugs(limit: int = 1000) -> ChEMBLFetchedData:
    """Get list of approved drugs from ChEMBL.

    Args:
        limit (int): Maximum number of drugs to return.

    Returns:
        ChEMBLFetchedData containing approved drug molecules
        with their names, structures, and approval information.

    Example:
        >>> data = chembl_get_approved_drugs(limit=100)
        >>> df = data.as_dataframe()
        >>> print(df[["molecule_chembl_id", "pref_name"]].head())
    """
    return _get_fetcher().get_approved_drugs(limit)


def chembl_get_drug_indications(
    molecule_chembl_id: str,
    limit: int = 100,
) -> ChEMBLFetchedData:
    """Get therapeutic indications for a drug molecule.

    Args:
        molecule_chembl_id (str): ChEMBL molecule ID.
        limit (int): Maximum number of indications to return.

    Returns:
        ChEMBLFetchedData containing disease indications
        with mesh IDs and max phase information.

    Example:
        >>> data = chembl_get_drug_indications("CHEMBL25")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_drug_indications(molecule_chembl_id, limit)


def chembl_get_mechanisms(
    molecule_chembl_id: str,
    limit: int = 100,
) -> ChEMBLFetchedData:
    """Get mechanism of action for a drug molecule.

    Args:
        molecule_chembl_id (str): ChEMBL molecule ID.
        limit (int): Maximum number of mechanisms to return.

    Returns:
        ChEMBLFetchedData containing mechanism of action data
        including target, action type, and references.

    Example:
        >>> data = chembl_get_mechanisms("CHEMBL25")
        >>> df = data.as_dataframe()
        >>> print(df[["mechanism_of_action", "target_chembl_id"]].head())
    """
    return _get_fetcher().get_mechanisms(molecule_chembl_id, limit)
