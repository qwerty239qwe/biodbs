# Disease Ontology

Access disease terms via the [Disease Ontology API](https://disease-ontology.org/).

## Overview

The Disease Ontology provides:

- **Disease Terms** - Standardized disease vocabulary
- **Cross-References** - Links to MeSH, UMLS, ICD
- **Hierarchy** - Parent/child relationships

## Quick Start

```python
from biodbs.fetch import do_get_term, do_search

# Get term by DOID
term = do_get_term("DOID:162")  # Cancer
```

## Disease Terms

### Get Term

```python
from biodbs.fetch import do_get_term, do_get_terms

# Single term
term = do_get_term("DOID:162")

# Multiple terms
terms = do_get_terms(["DOID:162", "DOID:9256"])
```

### Search

```python
from biodbs.fetch import do_search

results = do_search("breast cancer")
```

## Hierarchy

### Parents

```python
from biodbs.fetch import do_get_parents

parents = do_get_parents("DOID:1612")  # Breast cancer
```

### Children

```python
from biodbs.fetch import do_get_children

children = do_get_children("DOID:162")  # Cancer
```

### Ancestors

```python
from biodbs.fetch import do_get_ancestors

ancestors = do_get_ancestors("DOID:1612")
```

### Descendants

```python
from biodbs.fetch import do_get_descendants

descendants = do_get_descendants("DOID:162")
```

## Cross-References

### To MeSH

```python
from biodbs.fetch import doid_to_mesh

mesh_ids = doid_to_mesh(["DOID:162", "DOID:1612"])
```

### To UMLS

```python
from biodbs.fetch import doid_to_umls

umls_ids = doid_to_umls(["DOID:162"])
```

### To ICD-10

```python
from biodbs.fetch import doid_to_icd10

icd_codes = doid_to_icd10(["DOID:162"])
```

### Generic Mapping

```python
from biodbs.fetch import do_xref_mapping

mapping = do_xref_mapping(
    ["DOID:162"],
    target_db="MESH"
)
```

## Using the Fetcher Class

```python
from biodbs.fetch.DiseaseOntology import DiseaseOntology_Fetcher

fetcher = DiseaseOntology_Fetcher()
term = fetcher.get_term("DOID:162")
```
