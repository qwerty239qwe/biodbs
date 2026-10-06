"""Chemical/Compound ID translation functions."""

from typing import List, Dict, Union
import logging
import pandas as pd
from requests.exceptions import RequestException

from biodbs.fetch.pubchem.funcs import (
        pubchem_search_by_name,
        pubchem_search_by_smiles,
        pubchem_search_by_inchikey,
        pubchem_get_properties,
    )

from biodbs.fetch.KEGG.funcs import kegg_conv
from biodbs.fetch.ChEMBL.funcs import chembl_get_molecule, chembl_search_molecules
from biodbs.exceptions import APIError, APIRateLimitError, APIServerError, APITimeoutError

logger = logging.getLogger(__name__)
_EXPECTED_TRANSLATION_ERRORS = (
    APIError,
    RequestException,
    KeyError,
    IndexError,
    ValueError,
)


def translate_chemical_ids(
    ids: List[str],
    from_type: str,
    to_type: Union[str, List[str]],
    return_dict: bool = False,
) -> Union[Dict[str, str], Dict[str, Dict[str, str]], "pd.DataFrame"]:
    """Translate chemical/compound IDs between different identifier types.

    Uses PubChem for ID conversion.

    Resolves duplicate inputs once, then fetches properties in batches of up to
    100 unique CIDs. Matches response records by CID and preserves input rows.

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
    if from_type not in {"cid", "name", "smiles", "inchikey"}:
        raise ValueError(f"Unsupported from_type: {from_type}")
    multiple = isinstance(to_type, list)
    to_types = to_type if multiple else [to_type]
    for target in to_types:
        if target not in _CHEMICAL_PROPERTIES:
            raise ValueError(f"Unsupported to_type: {target}")

    records = _chemical_records(ids, from_type, to_types)
    if return_dict:
        return {
            source: ({target: record.get(target) for target in to_types}
                     if multiple else record.get(to_type))
            for source, record in zip(ids, records)
        }
    columns = ([from_type, "cid", *to_types] if multiple
               else [from_type, to_type, "cid"])
    return pd.DataFrame(records, columns=list(dict.fromkeys(columns)))


_CHEMICAL_PROPERTIES = {
    "cid": "CID", "smiles": "CanonicalSMILES", "inchikey": "InChIKey",
    "inchi": "InChI", "formula": "MolecularFormula", "name": "IUPACName",
}
_CHEMICAL_RESPONSE_KEYS = {
    "smiles": ("CanonicalSMILES", "ConnectivitySMILES", "SMILES"),
    "name": ("IUPACName", "Title"),
}


def _chemical_records(ids, from_type, to_types):
    """Resolve each source once and fetch properties for up to 100 unique CIDs."""
    searches = {
        "name": pubchem_search_by_name, "smiles": pubchem_search_by_smiles,
        "inchikey": pubchem_search_by_inchikey,
    }
    resolved = {}
    for source in dict.fromkeys(ids):
        try:
            if from_type == "cid":
                cid = int(source)
            else:
                cids = searches[from_type](source).get_cids()
                cid = cids[0] if cids else None
            resolved[source] = cid
        except _EXPECTED_TRANSLATION_ERRORS as exc:
            logger.debug("Failed to resolve chemical ID %s", source, exc_info=exc)
            resolved[source] = None

    cids = list(dict.fromkeys(cid for cid in resolved.values() if cid is not None))
    properties = list(dict.fromkeys(
        _CHEMICAL_PROPERTIES[target] for target in to_types if target != "cid"
    ))
    fetched = {}

    def fetch_batch(batch):
        try:
            rows = pubchem_get_properties(
                batch[0] if len(batch) == 1 else batch, properties=properties,
            ).results
            for row in rows:
                # PubChem includes CID. Legacy single-record responses are unambiguous.
                cid = row.get("CID", batch[0] if len(batch) == 1 and len(rows) == 1 else None)
                if cid in batch:
                    fetched[cid] = row
        except (APIRateLimitError, APIServerError, APITimeoutError, RequestException) as exc:
            # A service outage is not compound-specific: don't fan out retries.
            logger.debug("Chemical property service unavailable for %s", batch, exc_info=exc)
            return
        except _EXPECTED_TRANSLATION_ERRORS as exc:
            logger.debug("Failed to fetch chemical properties for %s", batch, exc_info=exc)
            if isinstance(exc.__cause__, RequestException):
                return
        if len(batch) > 1:
            # A missing/invalid CID must not discard other compounds in the batch.
            for cid in batch:
                if cid not in fetched:
                    fetch_batch([cid])

    if properties:
        for offset in range(0, len(cids), 100):
            fetch_batch(cids[offset:offset + 100])

    records = []
    for source in ids:
        cid = resolved[source]
        row = fetched.get(cid, {})
        record = {from_type: source, "cid": cid}
        for target in to_types:
            keys = _CHEMICAL_RESPONSE_KEYS.get(target, (_CHEMICAL_PROPERTIES[target],))
            record[target] = (cid if target == "cid" else
                              next((row[key] for key in keys if key in row), None))
        records.append(record)
    return records


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
        - pubchem: PubChem Substance ID (SID), not Compound ID (CID)
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
                # A generic PubChem cross-reference may be a SID, not a CID.
                # Resolve the molecule's structure instead of relabelling that ID.
                pubchem_cid = None
                structs = mol.get("molecule_structures") or {}
                inchikey = structs.get("standard_inchi_key")
                if inchikey:
                    search_data = pubchem_search_by_inchikey(inchikey)
                    cids = search_data.get_cids()
                    pubchem_cid = cids[0] if cids else None

                results.append({"chembl_id": chembl_id, "pubchem_cid": pubchem_cid})
            else:
                results.append({"chembl_id": chembl_id, "pubchem_cid": None})
        except _EXPECTED_TRANSLATION_ERRORS as exc:
            logger.debug("Failed to translate ChEMBL ID %s", chembl_id, exc_info=exc)
            results.append({"chembl_id": chembl_id, "pubchem_cid": None})

    df = pd.DataFrame(results, columns=["chembl_id", "pubchem_cid"])

    if return_dict:
        return {record["chembl_id"]: record["pubchem_cid"] for record in results}

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
                        mol = search_data.results[0]
                        matched_key = (mol.get("molecule_structures") or {}).get("standard_inchi_key")
                        chembl_id = mol.get("molecule_chembl_id") if matched_key == inchikey else None
                        results.append({"pubchem_cid": cid, "chembl_id": chembl_id})
                    else:
                        results.append({"pubchem_cid": cid, "chembl_id": None})
                else:
                    results.append({"pubchem_cid": cid, "chembl_id": None})
            else:
                results.append({"pubchem_cid": cid, "chembl_id": None})
        except _EXPECTED_TRANSLATION_ERRORS as exc:
            logger.debug("Failed to translate PubChem CID %s", cid, exc_info=exc)
            results.append({"pubchem_cid": cid, "chembl_id": None})

    df = pd.DataFrame(results, columns=["pubchem_cid", "chembl_id"])

    if return_dict:
        return {record["pubchem_cid"]: record["chembl_id"] for record in results}

    return df
