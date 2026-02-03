"""Convenience functions for PubChem data fetching."""

from typing import List, Optional, Union

from biodbs.data.PubChem.data import PUGRestFetchedData, PUGViewFetchedData
from biodbs.fetch.pubchem.pubchem_fetcher import PubChem_Fetcher

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[PubChem_Fetcher] = None


def _get_fetcher() -> PubChem_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = PubChem_Fetcher()
    return _fetcher


def pubchem_get_compound(cid: int) -> PUGRestFetchedData:
    """Get compound data by PubChem CID.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGRestFetchedData containing compound information.

    Example:
        >>> data = pubchem_get_compound(2244)  # Aspirin
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_compound(cid)


def pubchem_get_compounds(cids: List[int]) -> PUGRestFetchedData:
    """Get multiple compounds by PubChem CIDs.

    Args:
        cids: List of PubChem Compound IDs.

    Returns:
        PUGRestFetchedData containing compounds information.

    Example:
        >>> data = pubchem_get_compounds([2244, 5988, 2519])  # Aspirin, Glucose, Caffeine
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_compounds(cids)


def pubchem_search_by_name(name: str) -> PUGRestFetchedData:
    """Search compounds by name.

    Args:
        name: Compound name to search.

    Returns:
        PUGRestFetchedData containing matching compounds.

    Example:
        >>> data = pubchem_search_by_name("aspirin")
        >>> cids = data.get_cids()
    """
    return _get_fetcher().search_by_name(name)


def pubchem_search_by_smiles(smiles: str) -> PUGRestFetchedData:
    """Search compounds by SMILES string.

    Args:
        smiles: SMILES structure string.

    Returns:
        PUGRestFetchedData containing matching compounds.

    Example:
        >>> data = pubchem_search_by_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")  # Aspirin
        >>> cids = data.get_cids()
    """
    return _get_fetcher().search_by_smiles(smiles)


def pubchem_search_by_inchikey(inchikey: str) -> PUGRestFetchedData:
    """Search compounds by InChIKey.

    Args:
        inchikey: InChIKey identifier.

    Returns:
        PUGRestFetchedData containing matching compounds.

    Example:
        >>> data = pubchem_search_by_inchikey("BSYNRYMUTXBXSQ-UHFFFAOYSA-N")  # Aspirin
        >>> cids = data.get_cids()
    """
    return _get_fetcher().search_by_inchikey(inchikey)


def pubchem_search_by_formula(formula: str) -> PUGRestFetchedData:
    """Search compounds by molecular formula.

    Args:
        formula: Molecular formula (e.g., "C9H8O4").

    Returns:
        PUGRestFetchedData containing matching compounds.

    Example:
        >>> data = pubchem_search_by_formula("C9H8O4")  # Aspirin formula
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().search_by_formula(formula)


def pubchem_get_properties(
    cids: Union[int, List[int]],
    properties: Optional[List[str]] = None,
) -> PUGRestFetchedData:
    """Get specific properties for compounds.

    Args:
        cids: Single CID or list of CIDs.
        properties: List of property names. If None, returns common properties.

    Returns:
        PUGRestFetchedData containing property values.

    Example:
        >>> data = pubchem_get_properties(2244, ["MolecularWeight", "MolecularFormula"])
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_properties(cids, properties)


def pubchem_get_synonyms(cid: int) -> PUGRestFetchedData:
    """Get synonyms for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGRestFetchedData containing synonyms.

    Example:
        >>> data = pubchem_get_synonyms(2244)  # Aspirin
        >>> synonyms = data.results[0].get("Synonym", [])
    """
    return _get_fetcher().get_synonyms(cid)


def pubchem_get_description(cid: int) -> PUGRestFetchedData:
    """Get description for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGRestFetchedData containing description.

    Example:
        >>> data = pubchem_get_description(2244)  # Aspirin
        >>> description = data.results[0].get("Description", "")
    """
    return _get_fetcher().get_description(cid)


def pubchem_get_safety(cid: int) -> PUGViewFetchedData:
    """Get safety data for a compound (GHS classification, hazards, etc.).

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGViewFetchedData containing safety information.

    Example:
        >>> data = pubchem_get_safety(2244)  # Aspirin
        >>> safety_info = data.as_dict()
    """
    return _get_fetcher().get_safety_data(cid)


def pubchem_get_pharmacology(cid: int) -> PUGViewFetchedData:
    """Get pharmacology data for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGViewFetchedData containing pharmacology information.

    Example:
        >>> data = pubchem_get_pharmacology(2244)  # Aspirin
        >>> pharmacology_info = data.as_dict()
    """
    return _get_fetcher().get_pharmacology(cid)


def pubchem_get_drug_info(cid: int) -> PUGViewFetchedData:
    """Get drug information for a compound.

    Args:
        cid: PubChem Compound ID.

    Returns:
        PUGViewFetchedData containing drug information.

    Example:
        >>> data = pubchem_get_drug_info(2244)  # Aspirin
        >>> drug_info = data.as_dict()
    """
    return _get_fetcher().get_drug_info(cid)
