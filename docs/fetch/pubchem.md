# PubChem

Access chemical compound data via the [PubChem PUG REST API](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest).

## Overview

PubChem is the world's largest collection of freely accessible chemical information. biodbs provides access to:

- **Compound Data** - Properties, structures, synonyms
- **Search** - By name, SMILES, InChIKey, formula
- **Bioassays** - Biological activity data
- **Safety/Pharmacology** - Drug information

## Quick Start

```python
from biodbs.fetch import (
    pubchem_get_compound,
    pubchem_search_by_name,
    pubchem_get_properties,
)

# Get compound by CID
compound = pubchem_get_compound(2244)  # Aspirin
print(compound.results)
```

## Compound Retrieval

### Get by CID

```python
from biodbs.fetch import pubchem_get_compound, pubchem_get_compounds

# Single compound
compound = pubchem_get_compound(2244)

# Multiple compounds
compounds = pubchem_get_compounds([2244, 2519, 5090])
```

### Get Properties

```python
from biodbs.fetch import pubchem_get_properties

props = pubchem_get_properties(
    2244,
    properties=[
        "MolecularWeight",
        "MolecularFormula",
        "CanonicalSMILES",
        "InChIKey",
        "XLogP",
        "TPSA"
    ]
)
```

## Searching

### By Name

```python
from biodbs.fetch import pubchem_search_by_name

results = pubchem_search_by_name("aspirin")
cids = results.get_cids()
```

### By SMILES

```python
from biodbs.fetch import pubchem_search_by_smiles

results = pubchem_search_by_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")
```

### By InChIKey

```python
from biodbs.fetch import pubchem_search_by_inchikey

results = pubchem_search_by_inchikey("BSYNRYMUTXBXSQ-UHFFFAOYSA-N")
```

### By Formula

```python
from biodbs.fetch import pubchem_search_by_formula

results = pubchem_search_by_formula("C9H8O4")
```

## Additional Data

### Synonyms

```python
from biodbs.fetch import pubchem_get_synonyms

synonyms = pubchem_get_synonyms(2244)
```

### Description

```python
from biodbs.fetch import pubchem_get_description

desc = pubchem_get_description(2244)
```

### Safety Data

```python
from biodbs.fetch import pubchem_get_safety

safety = pubchem_get_safety(2244)
```

### Pharmacology

```python
from biodbs.fetch import pubchem_get_pharmacology

pharma = pubchem_get_pharmacology(2244)
```

### Drug Information

```python
from biodbs.fetch import pubchem_get_drug_info

drug = pubchem_get_drug_info(2244)
```

## Using the Fetcher Class

```python
from biodbs.fetch.pubchem import PubChem_Fetcher

fetcher = PubChem_Fetcher()
compound = fetcher.get_compound(2244)
```

## Related Resources

- **[ChEMBL](chembl.md)** - Access bioactivity data, drug mechanisms, and target interactions for chemical compounds.
- **[FDA](fda.md)** - Get FDA approval status and drug labeling information.
- **[KEGG](kegg.md)** - Find compound involvement in metabolic pathways.
- **[ID Translation](../translate/chemicals.md)** - Translate between PubChem CIDs and other chemical identifiers (SMILES, InChIKey, ChEMBL ID).
