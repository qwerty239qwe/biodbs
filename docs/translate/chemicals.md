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
| `pubchem` | PubChem CID |
| `chebi` | ChEBI ID |

## Cross-Database Translation

### ChEMBL to PubChem

```python
from biodbs.translate import translate_chembl_to_pubchem

result = translate_chembl_to_pubchem(
    chembl_ids=["CHEMBL25", "CHEMBL521"],  # Aspirin, Caffeine
    return_dict=True
)
# {'CHEMBL25': 2244, 'CHEMBL521': 2519}
```

### PubChem to ChEMBL

```python
from biodbs.translate import translate_pubchem_to_chembl

result = translate_pubchem_to_chembl(
    cids=[2244, 2519],
    return_dict=True
)
# {2244: 'CHEMBL25', 2519: 'CHEMBL521'}
```

## Examples

### Build Compound Table

```python
from biodbs.translate import translate_chemical_ids
import pandas as pd

compounds = ["aspirin", "caffeine", "ibuprofen", "acetaminophen"]

# Get all identifiers
cids = translate_chemical_ids(compounds, "name", "cid", return_dict=True)

cid_list = [cids[c] for c in compounds if c in cids]
smiles = translate_chemical_ids(cid_list, "cid", "smiles", return_dict=True)
inchikeys = translate_chemical_ids(cid_list, "cid", "inchikey", return_dict=True)
formulas = translate_chemical_ids(cid_list, "cid", "formula", return_dict=True)

# Build table
data = []
for name in compounds:
    cid = cids.get(name)
    if cid:
        data.append({
            "name": name,
            "cid": cid,
            "smiles": smiles.get(cid),
            "inchikey": inchikeys.get(cid),
            "formula": formulas.get(cid),
        })

df = pd.DataFrame(data)
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
