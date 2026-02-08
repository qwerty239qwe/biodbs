# ChEMBL

Access bioactive molecule data via the [ChEMBL API](https://www.ebi.ac.uk/chembl/).

## Overview

ChEMBL is a manually curated database of bioactive molecules with drug-like properties. It provides:

- **Molecules** - Chemical compounds and drugs
- **Targets** - Drug targets (proteins, organisms)
- **Activities** - Bioassay results
- **Mechanisms** - Drug mechanisms of action

## Quick Start

```python
from biodbs.fetch import (
    chembl_get_molecule,
    chembl_get_target,
    chembl_search_molecules,
    chembl_get_activities_for_target,
)

# Get molecule
molecule = chembl_get_molecule("CHEMBL25")  # Aspirin
```

## Molecules

### Get by ChEMBL ID

```python
from biodbs.fetch import chembl_get_molecule

molecule = chembl_get_molecule("CHEMBL25")
```

### Search

```python
from biodbs.fetch import chembl_search_molecules

results = chembl_search_molecules("aspirin")
```

### Approved Drugs

```python
from biodbs.fetch import chembl_get_approved_drugs

drugs = chembl_get_approved_drugs(max_phase=4)
```

## Targets

### Get Target

```python
from biodbs.fetch import chembl_get_target

target = chembl_get_target("CHEMBL1862")  # COX-2
```

## Activities

### For Target

```python
from biodbs.fetch import chembl_get_activities_for_target

activities = chembl_get_activities_for_target("CHEMBL1862")
```

### For Molecule

```python
from biodbs.fetch import chembl_get_activities_for_molecule

activities = chembl_get_activities_for_molecule("CHEMBL25")
```

## Drug Information

### Indications

```python
from biodbs.fetch import chembl_get_drug_indications

indications = chembl_get_drug_indications("CHEMBL25")
```

### Mechanisms

```python
from biodbs.fetch import chembl_get_mechanisms

mechanisms = chembl_get_mechanisms("CHEMBL25")
```

## Using the Fetcher Class

```python
from biodbs.fetch.ChEMBL import ChEMBL_Fetcher

fetcher = ChEMBL_Fetcher()
molecule = fetcher.get_molecule("CHEMBL25")
```

## Related Resources

- **[UniProt](uniprot.md)** - Get detailed protein information for ChEMBL drug targets. Use `uniprot_map_ids()` to map ChEMBL target IDs to UniProt accessions.
- **[PubChem](pubchem.md)** - Look up additional chemical properties (SMILES, InChIKey, safety data) for ChEMBL molecules.
- **[ID Translation](../translate/chemicals.md)** - Translate between ChEMBL IDs and other chemical identifiers (PubChem CID, InChIKey, SMILES).
