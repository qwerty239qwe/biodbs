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
from biodbs._funcs.translate.mappers import ChemicalMapper
from biodbs._funcs.translate._kegg import convert_kegg

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
    *,
    database: str | None = None,
    mapper: ChemicalMapper | None = None,
    bulk: bool = False,
) -> Union[Dict[str, str], Dict[str, Dict[str, str]], "pd.DataFrame"]:
    """Translate chemical/compound IDs between different identifier types.

    Existing ID types use PubChem by default. Explicit ChEMBL and KEGG types
    also support cross-database conversion without requiring a mapper.

    Resolves duplicate inputs once, then fetches properties in batches of up to
    100 unique CIDs. Matches response records by CID and preserves input rows.

    Supported ID types:
        - cid: PubChem Compound ID
        - name: Compound name
        - smiles: SMILES string (canonical)
        - inchikey: InChIKey
        - inchi: InChI string
        - formula: Molecular formula
        - chembl_id: ChEMBL molecule ID, matched through structure identifiers
        - kegg_compound / kegg_drug, pubchem_sid, chebi: KEGG conversion namespaces

    Args:
        ids: List of compound identifiers to translate.
        from_type: Source ID type (cid, name, smiles, inchikey, chembl_id),
            or a KEGG conversion namespace listed above.
        to_type: Target ID type(s). Can be a single string or a list of strings.
            When a list is provided, multiple target IDs are returned.
            Valid PubChem/ChEMBL targets: cid, name, smiles, inchikey, inchi,
            formula, chembl_id. KEGG accepts a single conversion namespace.
        return_dict: If True, return dict mapping from_id -> to_id (or dict of to_ids
            when to_type is a list).
        database: Optional backend (auto, pubchem, chembl, kegg). None uses
            the mapper's backend, or auto routing when no mapper is supplied.
        mapper: Optional reusable ChemicalMapper. Conflicting database settings
            raise ValueError. Existing calls do not need a mapper.
        bulk: Explicitly convert an entire KEGG source database when ids is
            empty. Other backends reject bulk conversion.

    Returns:
        When to_type is a string:
            Dict or DataFrame with translated IDs.
        When to_type is a list:
            Dict mapping source IDs to dicts of {target_type: target_id}, or
            DataFrame with from_type column and one column per target type.
        KEGG uses native source_id/target_id DataFrame columns and retains ID
        prefixes. Its scalar dictionary selects the first mapping per source.

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
    if mapper is not None and not isinstance(mapper, ChemicalMapper):
        raise TypeError("mapper must be a ChemicalMapper")
    if mapper is not None and database is not None and database.lower() != mapper.database.lower():
        raise ValueError("database conflicts with mapper.database")
    selected = mapper if mapper is not None else ChemicalMapper(database=database or "auto")
    return selected.map(ids, from_type, to_type, return_dict, bulk=bulk)


def _translate_chemical_ids(ids, from_type, to_type, return_dict=False, *, database="auto", bulk=False):
    multiple = isinstance(to_type, list)
    to_types = to_type if multiple else [to_type]
    kegg_types = {"kegg_compound", "kegg_drug", "compound", "drug", "pubchem_sid", "chebi"}
    if database.lower() == "auto":
        database = ("kegg" if from_type in kegg_types or any(t in kegg_types for t in to_types)
                    else "chembl" if from_type == "chembl_id" or "chembl_id" in to_types
                    else "pubchem")
    database = database.lower()
    if database == "kegg":
        aliases = {"kegg_compound": "compound", "kegg_drug": "drug", "pubchem_sid": "pubchem"}
        if multiple:
            raise ValueError("KEGG chemical translation accepts a single target type")
        source, target = aliases.get(from_type, from_type), aliases.get(to_type, to_type)
        if source not in {"compound", "drug", "pubchem", "chebi"} or target not in {"compound", "drug", "pubchem", "chebi"}:
            raise ValueError("Unsupported KEGG chemical ID type; PubChem mappings use pubchem_sid, not cid")
        if source not in {"compound", "drug"} and target not in {"compound", "drug"}:
            raise ValueError("KEGG conversion requires a KEGG compound or drug namespace")
        return convert_kegg(ids, source, target, kegg_conv, bulk=bulk, return_dict=return_dict)
    if database not in {"pubchem", "chembl"}:
        raise ValueError(f"Unsupported database: {database!r}")
    if bulk:
        raise ValueError("bulk conversion is only supported by KEGG")
    if database == "pubchem" and (from_type == "chembl_id" or "chembl_id" in to_types):
        raise ValueError("ChEMBL ID conversion requires the chembl or auto backend")
    if from_type not in {"cid", "name", "smiles", "inchikey", "chembl_id"}:
        raise ValueError(f"Unsupported from_type: {from_type}")
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
    "chembl_id": "InChIKey",
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
            elif from_type == "chembl_id":
                molecules = chembl_get_molecule(source).results
                structures = (molecules[0].get("molecule_structures") or {}) if molecules else {}
                key = structures.get("standard_inchi_key")
                cids = pubchem_search_by_inchikey(key).get_cids() if key else []
                cid = cids[0] if cids else None
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

    chembl_ids = {}
    if "chembl_id" in to_types:
        for cid, row in fetched.items():
            matched_id = None
            key = row.get("InChIKey")
            if key:
                try:
                    molecules = chembl_search_molecules(key, limit=1).results
                    if molecules:
                        mol = molecules[0]
                        matched_key = (mol.get("molecule_structures") or {}).get("standard_inchi_key")
                        if matched_key == key:
                            matched_id = mol.get("molecule_chembl_id")
                except _EXPECTED_TRANSLATION_ERRORS as exc:
                    logger.debug("Failed to resolve ChEMBL ID for CID %s", cid, exc_info=exc)
            chembl_ids[cid] = matched_id

    records = []
    for source in ids:
        cid = resolved[source]
        row = fetched.get(cid, {})
        record = {from_type: source, "cid": cid}
        for target in to_types:
            if target == "chembl_id":
                record[target] = chembl_ids.get(cid)
                continue
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
    
    return convert_kegg(ids, from_db, to_db, kegg_conv, bulk=True)


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

    result = translate_chemical_ids(chembl_ids, "chembl_id", "cid", return_dict)
    return result if return_dict else result.rename(columns={"cid": "pubchem_cid"})


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

    result = translate_chemical_ids(cids, "cid", "chembl_id", return_dict)
    if return_dict:
        return result
    # Keep the legacy column order and the original input values (including strings).
    result["cid"] = cids
    return result.loc[:, ["cid", "chembl_id"]].rename(columns={"cid": "pubchem_cid"})
