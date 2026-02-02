"""Convenience functions for PubChem data fetching."""

from typing import List, Optional, Union
from biodbs.fetch.pubchem.pubchem_fetcher import PubChem_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[PubChem_Fetcher] = None


def _get_fetcher() -> PubChem_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = PubChem_Fetcher()
    return _fetcher


def pubchem_get_compound(cid: int):
    """Get compound data by CID.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGRestFetchedData with compound information.

    Example:
        >>> data = pubchem_get_compound(2244)  # Aspirin
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_compound(cid)


def pubchem_get_compounds(cids: List[int]):
    """Get multiple compounds by CIDs.

    Args:
        cids: List of PubChem Compound IDs.

    Returns:
        PUGRestFetchedData with compounds information.
    """
    return _get_fetcher().get_compounds(cids)


def pubchem_search_by_name(name: str):
    """Search compounds by name.

    Args:
        name: Compound name to search.

    Returns:
        PUGRestFetchedData with matching compounds.

    Example:
        >>> data = pubchem_search_by_name("aspirin")
    """
    return _get_fetcher().search_by_name(name)


def pubchem_search_by_smiles(smiles: str):
    """Search compounds by SMILES string.

    Args:
        smiles: SMILES structure string.

    Returns:
        PUGRestFetchedData with matching compounds.
    """
    return _get_fetcher().search_by_smiles(smiles)


def pubchem_search_by_inchikey(inchikey: str):
    """Search compounds by InChIKey.

    Args:
        inchikey: InChIKey identifier.

    Returns:
        PUGRestFetchedData with matching compounds.
    """
    return _get_fetcher().search_by_inchikey(inchikey)


def pubchem_search_by_formula(formula: str):
    """Search compounds by molecular formula.

    Args:
        formula: Molecular formula (e.g., "C9H8O4").

    Returns:
        PUGRestFetchedData with matching compounds.
    """
    return _get_fetcher().search_by_formula(formula)


def pubchem_get_properties(
    cids: Union[int, List[int]],
    properties: Optional[List[str]] = None,
):
    """Get specific properties for compounds.

    Args:
        cids: Single CID or list of CIDs.
        properties: List of property names. If None, returns common properties.

    Returns:
        PUGRestFetchedData with property values.

    Example:
        >>> data = pubchem_get_properties(2244, ["MolecularWeight", "MolecularFormula"])
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_properties(cids, properties)


def pubchem_get_synonyms(cid: int):
    """Get synonyms for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGRestFetchedData with synonyms.
    """
    return _get_fetcher().get_synonyms(cid)


def pubchem_get_description(cid: int):
    """Get description for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGRestFetchedData with description.
    """
    return _get_fetcher().get_description(cid)


def pubchem_get_safety(cid: int):
    """Get safety data for a compound (GHS classification, hazards, etc.).

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGViewFetchedData with safety information.
    """
    return _get_fetcher().get_safety_data(cid)


def pubchem_get_pharmacology(cid: int):
    """Get pharmacology data for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGViewFetchedData with pharmacology information.
    """
    return _get_fetcher().get_pharmacology(cid)


def pubchem_get_drug_info(cid: int):
    """Get drug information for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGViewFetchedData with drug information.
    """
    return _get_fetcher().get_drug_info(cid)
