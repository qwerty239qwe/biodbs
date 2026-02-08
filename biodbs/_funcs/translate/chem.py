"""Chemical/Compound ID translation functions."""

from typing import List, Dict, Union
import pandas as pd

from biodbs.fetch.pubchem.funcs import (
        pubchem_search_by_name,
        pubchem_search_by_smiles,
        pubchem_search_by_inchikey,
        pubchem_get_properties,
    )

from biodbs.fetch.KEGG.funcs import kegg_conv
from biodbs.fetch.ChEMBL.funcs import chembl_get_molecule, chembl_search_molecules


def translate_chemical_ids(
    ids: List[str],
    from_type: str,
    to_type: Union[str, List[str]],
    return_dict: bool = False,
) -> Union[Dict[str, str], Dict[str, Dict[str, str]], "pd.DataFrame"]:
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
        to_type: Target ID type(s). Can be a single string or a list of strings.
            When a list is provided, multiple target IDs are returned.
            Valid types: "cid", "name", "smiles", "inchikey", "inchi", "formula".
        return_dict: If True, return dict mapping from_id -> to_id (or dict of to_ids
            when to_type is a list).

    Returns:
        When to_type is a string:
            Dict or DataFrame with translated IDs.
        When to_type is a list:
            Dict mapping source IDs to dicts of {target_type: target_id}, or
            DataFrame with from_type column and one column per target type.

    Example:
        Names to CIDs:

        ```python
        result = translate_chemical_ids(
            ["aspirin", "ibuprofen"],
            from_type="name",
            to_type="cid",
        )
        print(result)
        #    name   cid    cid
        # 0  aspirin  2244  2244
        # 1  ibuprofen 3672  3672
        ```

        CIDs to SMILES:

        ```python
        result = translate_chemical_ids(
            ["2244", "3672"],
            from_type="cid",
            to_type="smiles",
            return_dict=True,
        )
        print(result)
        # {'2244': 'CC(=O)OC1=CC=CC=C1C(=O)O', '3672': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O'}
        ```

        Multiple target types:

        ```python
        result = translate_chemical_ids(
            ["aspirin"],
            from_type="name",
            to_type=["cid", "smiles", "inchikey"],
        )
        print(result)
        #      name   cid                      smiles                    inchikey
        # 0  aspirin  2244  CC(=O)OC1=CC=CC=C1C(=O)O  BSYNRYMUTXBXSQ-UHFFFAOYSA-N
        ```
    """
    # Supported from_types
    valid_from_types = {"cid", "name", "smiles", "inchikey"}
    if from_type not in valid_from_types:
        raise ValueError(f"Unsupported from_type: {from_type}. Valid types: {valid_from_types}")

    # Handle multiple target types
    if isinstance(to_type, list):
        return _translate_chemical_multiple_targets(ids, from_type, to_type, return_dict)

    # Map to_type to PubChem property names (for request)
    property_map = {
        "cid": "CID",
        "smiles": "CanonicalSMILES",
        "inchikey": "InChIKey",
        "inchi": "InChI",
        "formula": "MolecularFormula",
        "name": "IUPACName",
    }

    # PubChem API returns different keys than requested - map response keys
    response_key_map = {
        "CanonicalSMILES": ["CanonicalSMILES", "ConnectivitySMILES", "SMILES"],
        "IsomericSMILES": ["IsomericSMILES", "SMILES"],
        "InChIKey": ["InChIKey"],
        "InChI": ["InChI"],
        "MolecularFormula": ["MolecularFormula"],
        "IUPACName": ["IUPACName", "Title"],
        "CID": ["CID"],
    }

    if to_type not in property_map:
        raise ValueError(f"Unsupported to_type: {to_type}. Valid types: {set(property_map.keys())}")

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

            if cid is None:
                results.append({from_type: id_val, to_type: None})
                continue

            # Now get the target property
            if to_type == "cid":
                to_val = cid
            else:
                prop_name = property_map[to_type]
                prop_data = pubchem_get_properties(cid, properties=[prop_name])
                prop_results = prop_data.results
                to_val = None
                if prop_results:
                    result_dict = prop_results[0]
                    # Try each possible response key
                    for key in response_key_map.get(prop_name, [prop_name]):
                        if key in result_dict:
                            to_val = result_dict[key]
                            break

            results.append({from_type: id_val, to_type: to_val, "cid": cid})

        except Exception:
            results.append({from_type: id_val, to_type: None})

    df = pd.DataFrame(results)

    if return_dict:
        return dict(zip(df[from_type], df[to_type]))

    return df


def _translate_chemical_multiple_targets(
    ids: List[str],
    from_type: str,
    to_types: List[str],
    return_dict: bool,
) -> Union[Dict[str, Dict[str, str]], "pd.DataFrame"]:
    """Translate chemical IDs to multiple target types."""
    # Map to_type to PubChem property names
    property_map = {
        "cid": "CID",
        "smiles": "CanonicalSMILES",
        "inchikey": "InChIKey",
        "inchi": "InChI",
        "formula": "MolecularFormula",
        "name": "IUPACName",
    }

    response_key_map = {
        "CanonicalSMILES": ["CanonicalSMILES", "ConnectivitySMILES", "SMILES"],
        "IsomericSMILES": ["IsomericSMILES", "SMILES"],
        "InChIKey": ["InChIKey"],
        "InChI": ["InChI"],
        "MolecularFormula": ["MolecularFormula"],
        "IUPACName": ["IUPACName", "Title"],
        "CID": ["CID"],
    }

    valid_to_types = set(property_map.keys())
    for tt in to_types:
        if tt not in valid_to_types:
            raise ValueError(f"Unsupported to_type: {tt}. Valid types: {valid_to_types}")

    results = []

    for id_val in ids:
        record = {from_type: id_val}
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

            if cid is None:
                for tt in to_types:
                    record[tt] = None
                results.append(record)
                continue

            record["cid"] = cid

            # Get all target properties in one request if possible
            props_to_fetch = [
                property_map[tt] for tt in to_types
                if tt != "cid" and tt in property_map
            ]

            if props_to_fetch:
                prop_data = pubchem_get_properties(cid, properties=props_to_fetch)
                prop_results = prop_data.results
                result_dict = prop_results[0] if prop_results else {}

                for tt in to_types:
                    if tt == "cid":
                        record[tt] = cid
                    else:
                        prop_name = property_map[tt]
                        to_val = None
                        for key in response_key_map.get(prop_name, [prop_name]):
                            if key in result_dict:
                                to_val = result_dict[key]
                                break
                        record[tt] = to_val
            else:
                # Only cid was requested
                for tt in to_types:
                    record[tt] = cid if tt == "cid" else None

        except Exception:
            for tt in to_types:
                record[tt] = None

        results.append(record)

    df = pd.DataFrame(results)

    if return_dict:
        result_dict = {}
        for _, row in df.iterrows():
            from_id = row[from_type]
            result_dict[from_id] = {tt: row.get(tt) for tt in to_types}
        return result_dict

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
        KEGG compound to PubChem:

        ```python
        result = translate_chemical_ids_kegg(
            ["cpd:C00022", "cpd:C00031"],
            from_db="compound",
            to_db="pubchem",
        )
        print(result)
        #         source          target
        # 0  cpd:C00022  pubchem:3324
        # 1  cpd:C00031  pubchem:5793
        ```
    """
    
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
        ```python
        result = translate_chembl_to_pubchem(["CHEMBL25", "CHEMBL1201585"])
        print(result)
        #       chembl_id  pubchem_cid
        # 0       CHEMBL25         2244
        # 1  CHEMBL1201585      5284616
        ```
    """

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
        ```python
        result = translate_pubchem_to_chembl([2244, 3672])
        print(result)
        #    pubchem_cid    chembl_id
        # 0         2244     CHEMBL25
        # 1         3672    CHEMBL521
        ```
    """

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
