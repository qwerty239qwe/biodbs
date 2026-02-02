"""Chemical/Compound ID translation functions."""

from typing import List, Dict, Union


def translate_chemical_ids(
    ids: List[str],
    from_type: str,
    to_type: str,
    return_dict: bool = False,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate chemical/compound IDs between different identifier types.

    Uses PubChem for ID conversion.

    Supported ID types:
        - cid: PubChem Compound ID
        - name: Compound name
        - smiles: SMILES string (canonical)
        - inchikey: InChIKey
        - inchi: InChI string
        - formula: Molecular formula

    Args:
        ids: List of compound identifiers to translate.
        from_type: Source ID type ("cid", "name", "smiles", "inchikey").
        to_type: Target ID type ("cid", "name", "smiles", "inchikey", "inchi", "formula").
        return_dict: If True, return dict mapping from_id -> to_id.

    Returns:
        Dict or DataFrame with translated IDs.

    Example:
        >>> # Names to CIDs
        >>> result = translate_chemical_ids(
        ...     ["aspirin", "ibuprofen"],
        ...     from_type="name",
        ...     to_type="cid"
        ... )

        >>> # CIDs to SMILES
        >>> result = translate_chemical_ids(
        ...     ["2244", "3672"],
        ...     from_type="cid",
        ...     to_type="smiles",
        ...     return_dict=True
        ... )
    """
    import pandas as pd
    from biodbs.fetch.pubchem.funcs import (
        pubchem_search_by_name,
        pubchem_search_by_smiles,
        pubchem_search_by_inchikey,
        pubchem_get_properties,
    )

    # Map to_type to PubChem property names
    property_map = {
        "cid": "CID",
        "smiles": "CanonicalSMILES",
        "inchikey": "InChIKey",
        "inchi": "InChI",
        "formula": "MolecularFormula",
        "name": "IUPACName",
    }

    results = []

    for id_val in ids:
        try:
            # First, get the CID based on from_type
            if from_type == "cid":
                cid = int(id_val)
            elif from_type == "name":
                data = pubchem_search_by_name(id_val)
                cids = data.get_cids()
                cid = cids[0] if cids else None
            elif from_type == "smiles":
                data = pubchem_search_by_smiles(id_val)
                cids = data.get_cids()
                cid = cids[0] if cids else None
            elif from_type == "inchikey":
                data = pubchem_search_by_inchikey(id_val)
                cids = data.get_cids()
                cid = cids[0] if cids else None
            else:
                raise ValueError(f"Unsupported from_type: {from_type}")

            if cid is None:
                results.append({from_type: id_val, to_type: None})
                continue

            # Now get the target property
            if to_type == "cid":
                to_val = cid
            else:
                prop_name = property_map.get(to_type)
                if not prop_name:
                    raise ValueError(f"Unsupported to_type: {to_type}")

                prop_data = pubchem_get_properties(cid, properties=[prop_name])
                prop_results = prop_data.results
                if prop_results:
                    to_val = prop_results[0].get(prop_name)
                else:
                    to_val = None

            results.append({from_type: id_val, to_type: to_val, "cid": cid})

        except Exception:
            results.append({from_type: id_val, to_type: None})

    df = pd.DataFrame(results)

    if return_dict:
        return dict(zip(df[from_type], df[to_type]))

    return df


def translate_chemical_ids_kegg(
    ids: List[str],
    from_db: str,
    to_db: str,
) -> "pd.DataFrame":
    """Translate chemical/compound IDs using KEGG database.

    Useful for converting between KEGG compound/drug IDs and external databases.

    Supported databases:
        - compound: KEGG Compound
        - drug: KEGG Drug
        - pubchem: PubChem CID
        - chebi: ChEBI ID

    Args:
        ids: List of compound IDs to translate (e.g., ["cpd:C00022", "dr:D00001"]).
            If empty, converts entire database.
        from_db: Source database (compound, drug, or entries).
        to_db: Target database name.

    Returns:
        DataFrame with source and target ID columns.

    Example:
        >>> # KEGG compound to PubChem
        >>> result = translate_chemical_ids_kegg(
        ...     ["cpd:C00022", "cpd:C00031"],
        ...     from_db="compound",
        ...     to_db="pubchem"
        ... )
    """
    from biodbs.fetch.KEGG.funcs import kegg_conv

    if ids:
        data = kegg_conv(target_db=to_db, source=ids)
    else:
        data = kegg_conv(target_db=to_db, source=from_db)

    return data.as_dataframe()


def translate_chembl_to_pubchem(
    chembl_ids: List[str],
    return_dict: bool = False,
) -> Union[Dict[str, int], "pd.DataFrame"]:
    """Translate ChEMBL molecule IDs to PubChem CIDs.

    Args:
        chembl_ids: List of ChEMBL IDs (e.g., ["CHEMBL25", "CHEMBL1201585"]).
        return_dict: If True, return dict mapping ChEMBL ID -> PubChem CID.

    Returns:
        Dict or DataFrame with ChEMBL IDs and corresponding PubChem CIDs.

    Example:
        >>> result = translate_chembl_to_pubchem(["CHEMBL25", "CHEMBL1201585"])
    """
    import pandas as pd
    from biodbs.fetch.ChEMBL.funcs import chembl_get_molecule
    from biodbs.fetch.pubchem.funcs import pubchem_search_by_inchikey

    results = []
    for chembl_id in chembl_ids:
        try:
            data = chembl_get_molecule(chembl_id)
            if data.results:
                mol = data.results[0]
                # ChEMBL stores cross-references
                xrefs = mol.get("cross_references", [])
                pubchem_cid = None
                for xref in xrefs:
                    if xref.get("xref_src") == "PubChem":
                        pubchem_cid = xref.get("xref_id")
                        break
                # Also try molecule_structures for InChIKey lookup
                if not pubchem_cid:
                    structs = mol.get("molecule_structures", {})
                    inchikey = structs.get("standard_inchi_key") if structs else None
                    if inchikey:
                        try:
                            search_data = pubchem_search_by_inchikey(inchikey)
                            cids = search_data.get_cids()
                            pubchem_cid = cids[0] if cids else None
                        except Exception:
                            pass

                results.append({"chembl_id": chembl_id, "pubchem_cid": pubchem_cid})
            else:
                results.append({"chembl_id": chembl_id, "pubchem_cid": None})
        except Exception:
            results.append({"chembl_id": chembl_id, "pubchem_cid": None})

    df = pd.DataFrame(results)

    if return_dict:
        return dict(zip(df["chembl_id"], df["pubchem_cid"]))

    return df


def translate_pubchem_to_chembl(
    cids: List[int],
    return_dict: bool = False,
) -> Union[Dict[int, str], "pd.DataFrame"]:
    """Translate PubChem CIDs to ChEMBL molecule IDs.

    Args:
        cids: List of PubChem CIDs (e.g., [2244, 3672]).
        return_dict: If True, return dict mapping CID -> ChEMBL ID.

    Returns:
        Dict or DataFrame with PubChem CIDs and corresponding ChEMBL IDs.

    Example:
        >>> result = translate_pubchem_to_chembl([2244, 3672])
    """
    import pandas as pd
    from biodbs.fetch.pubchem.funcs import pubchem_get_properties
    from biodbs.fetch.ChEMBL.funcs import chembl_search_molecules

    results = []
    for cid in cids:
        try:
            # Get InChIKey from PubChem
            prop_data = pubchem_get_properties(cid, properties=["InChIKey"])
            if prop_data.results:
                inchikey = prop_data.results[0].get("InChIKey")
                if inchikey:
                    # Search ChEMBL by InChIKey (structure search)
                    search_data = chembl_search_molecules(inchikey, limit=1)
                    if search_data.results:
                        chembl_id = search_data.results[0].get("molecule_chembl_id")
                        results.append({"pubchem_cid": cid, "chembl_id": chembl_id})
                    else:
                        results.append({"pubchem_cid": cid, "chembl_id": None})
                else:
                    results.append({"pubchem_cid": cid, "chembl_id": None})
            else:
                results.append({"pubchem_cid": cid, "chembl_id": None})
        except Exception:
            results.append({"pubchem_cid": cid, "chembl_id": None})

    df = pd.DataFrame(results)

    if return_dict:
        return dict(zip(df["pubchem_cid"], df["chembl_id"]))

    return df
