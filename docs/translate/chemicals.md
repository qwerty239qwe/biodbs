# Chemical ID Translation

Translate between chemical identifiers using PubChem, KEGG, and ChEMBL.

## Quick Start

```python
from biodbs.translate import (
    translate_chemical_ids,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
)

# Compound names to PubChem CIDs
result = translate_chemical_ids(
    ["aspirin", "caffeine"],
    from_type="name",
    to_type="cid"
)
```

## translate_chemical_ids

Translate between chemical identifier types using PubChem.

```python
from biodbs.translate import translate_chemical_ids

# Name to CID
result = translate_chemical_ids(
    ids=["aspirin", "caffeine", "ibuprofen"],
    from_type="name",
    to_type="cid",
    return_dict=True
)
# {'aspirin': 2244, 'caffeine': 2519, 'ibuprofen': 3672}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ids` | List[str] | required | Compound identifiers to translate |
| `from_type` | str | required | Source ID type (cid, name, smiles, inchikey) |
| `to_type` | str or List[str] | required | Target ID type(s). Pass a list for multiple targets. |
| `return_dict` | bool | False | Return dict instead of DataFrame |

### Multiple Target Types

Get multiple ID types in one call (more efficient than separate calls):

Target properties are fetched together in batches of up to **100 unique CIDs**.
Repeated inputs are resolved once, and aliases sharing a CID reuse its properties.
Name/SMILES/InChIKey inputs first require a CID lookup. Responses are matched by
CID, not row position; missing or failed batch members fall back to individual
requests so invalid compounds do not discard valid mappings. Rate limits, server
outages, and timeouts do not trigger a per-compound retry storm. DataFrames preserve
input order and duplicate rows.
Dictionaries retain the original input keys, including string CIDs, and use
`None` for unresolved mappings. Name searches select the first returned CID;
use structure identifiers when names are ambiguous.

```python
result = translate_chemical_ids(
    ["aspirin", "caffeine"],
    from_type="name",
    to_type=["cid", "smiles", "inchikey", "formula"],
)
#       name   cid                      smiles                    inchikey formula
# 0  aspirin  2244  CC(=O)OC1=CC=CC=C1C(=O)O  BSYNRYMUTXBXSQ-UHFFFAOYSA-N  C9H8O4
# 1  caffeine 2519               Cn1cnc2...       RYYVLZVUVIJVGH-UHFFFAOYSA-N C8H10N4O2

# As dict with nested structure
result_dict = translate_chemical_ids(
    ["aspirin"],
    from_type="name",
    to_type=["cid", "smiles", "inchikey"],
    return_dict=True
)
# {'aspirin': {'cid': 2244, 'smiles': 'CC(=O)...', 'inchikey': 'BSYNR...'}}
```

### Supported ID Types

| ID Type | Description | Example |
|---------|-------------|---------|
| `name` | Compound name | aspirin |
| `cid` | PubChem Compound ID | 2244 |
| `smiles` | SMILES string | CC(=O)OC1=CC=CC=C1C(=O)O |
| `inchikey` | InChIKey | BSYNRYMUTXBXSQ-UHFFFAOYSA-N |
| `formula` | Molecular formula | C9H8O4 |

### Examples

```python
# Name to various IDs
cids = translate_chemical_ids(["aspirin"], "name", "cid")
smiles = translate_chemical_ids([2244], "cid", "smiles")
inchikey = translate_chemical_ids([2244], "cid", "inchikey")
formula = translate_chemical_ids([2244], "cid", "formula")

# SMILES to CID
result = translate_chemical_ids(
    ["CC(=O)OC1=CC=CC=C1C(=O)O"],
    from_type="smiles",
    to_type="cid"
)

# InChIKey to CID
result = translate_chemical_ids(
    ["BSYNRYMUTXBXSQ-UHFFFAOYSA-N"],
    from_type="inchikey",
    to_type="cid"
)
```

## translate_chemical_ids_kegg

Translate using KEGG compound database.

```python
from biodbs.translate import translate_chemical_ids_kegg

# KEGG compound to PubChem
result = translate_chemical_ids_kegg(
    ids=["C00001", "C00002"],  # Water, ATP
    from_db="compound",
    to_db="pubchem"
)

# KEGG drug to PubChem
result = translate_chemical_ids_kegg(
    ids=["D00109"],  # Aspirin
    from_db="drug",
    to_db="pubchem"
)
```

### KEGG Database Codes

| Code | Description |
|------|-------------|
| `compound` | KEGG Compound |
| `drug` | KEGG Drug |
| `pubchem` | PubChem Substance ID (SID), **not** Compound ID (CID) |
| `chebi` | ChEBI ID |

KEGG's `pubchem:` identifiers are SIDs, as specified in the
[KEGG API manual](https://www.kegg.jp/kegg/rest/keggapi.html). Do not pass them to
`translate_chemical_ids(..., from_type="cid")` without resolving the SID to a CID.

ChEMBL-to-PubChem mapping resolves the molecule's standard InChIKey, rather than
assuming a generic PubChem cross-reference is a CID. The reverse mapping verifies
the returned molecule's standard InChIKey before accepting its ChEMBL ID. Missing
or mismatched structures remain unresolved.

## Cross-Database Translation

### ChEMBL to PubChem

```python
from biodbs.translate import translate_chembl_to_pubchem

result = translate_chembl_to_pubchem(
    chembl_ids=["CHEMBL25", "CHEMBL521"],  # Aspirin, Caffeine
    return_dict=True
)
# {'CHEMBL25': 2244, 'CHEMBL521': 3672}
```

### PubChem to ChEMBL

```python
from biodbs.translate import translate_pubchem_to_chembl

result = translate_pubchem_to_chembl(
    cids=[2244, 3672],
    return_dict=True
)
# {2244: 'CHEMBL25', 3672: 'CHEMBL521'}
```

Expected lookup failures, including upstream server errors, currently also produce
`None` and are logged at DEBUG level. Do not interpret every `None` as proof that
no mapping exists; use the fetch helpers directly when service failures must raise.

## Examples

### Build Compound Table

Using multiple target types (shares the property lookup for each compound):

```python
from biodbs.translate import translate_chemical_ids

compounds = ["aspirin", "caffeine", "ibuprofen", "acetaminophen"]

# Get all identifiers in one call
df = translate_chemical_ids(
    compounds,
    from_type="name",
    to_type=["cid", "smiles", "inchikey", "formula"],
)
#             name   cid                      smiles                    inchikey  formula
# 0        aspirin  2244  CC(=O)OC1=CC=CC=C1C(=O)O  BSYNRYMUTXBXSQ-UHFFFAOYSA-N   C9H8O4
# 1       caffeine  2519               Cn1cnc2...  RYYVLZVUVIJVGH-UHFFFAOYSA-N C8H10N4O2
# 2      ibuprofen  3672  CC(C)CC1=CC=C(C=C1)...  HEFNNWSXXWATRW-UHFFFAOYSA-N  C13H18O2
# 3  acetaminophen  1983         CC(=O)NC1=CC=...  RZVAJINKPMORJF-UHFFFAOYSA-N   C8H9NO2
```

Alternative approach with separate calls:

```python
# Get all identifiers (less efficient - multiple requests)
cids = translate_chemical_ids(compounds, "name", "cid", return_dict=True)

cid_list = [str(cids[c]) for c in compounds if c in cids]
smiles = translate_chemical_ids(cid_list, "cid", "smiles", return_dict=True)
inchikeys = translate_chemical_ids(cid_list, "cid", "inchikey", return_dict=True)
formulas = translate_chemical_ids(cid_list, "cid", "formula", return_dict=True)
```

### Round-Trip Validation

```python
from biodbs.translate import (
    translate_chemical_ids,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
)

# Name -> CID -> Name
name = "aspirin"
cid = translate_chemical_ids([name], "name", "cid", return_dict=True)[name]
print(f"{name} -> CID:{cid}")

# ChEMBL <-> PubChem
chembl_id = "CHEMBL25"
pubchem_cid = translate_chembl_to_pubchem([chembl_id], return_dict=True)[chembl_id]
back_to_chembl = translate_pubchem_to_chembl([pubchem_cid], return_dict=True)[pubchem_cid]
print(f"{chembl_id} -> {pubchem_cid} -> {back_to_chembl}")
```

## Related Resources

### Backend Data Sources

- **[PubChem](../fetch/pubchem.md)** - Chemical compound data and properties.
- **[ChEMBL](../fetch/chembl.md)** - Bioactivity data and drug information.
- **[KEGG](../fetch/kegg.md)** - KEGG compound and drug identifiers.

### Other Translation

- **[Gene Translation](genes.md)** - Translate gene identifiers.
- **[Protein Translation](proteins.md)** - Translate protein identifiers.
