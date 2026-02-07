# Reactome

Access pathway data and analysis via the [Reactome API](https://reactome.org/dev/).

## Overview

Reactome provides:

- **Pathway Analysis** - Over-representation analysis (ORA)
- **Pathway Data** - Curated biological pathways via Content Service
- **Pathway-Gene Mappings** - Get genes for any pathway
- **Species Support** - Multiple organisms

## Quick Start

```python
from biodbs.fetch import reactome_analyze, reactome_get_pathway_genes

# Analyze gene list
result = reactome_analyze(["P04637", "P00533", "P38398"])
print(result)  # Shows pathway count and top result

# Get genes in a pathway
genes = reactome_get_pathway_genes("R-HSA-69278")  # Cell Cycle
print(f"Cell Cycle has {len(genes)} genes")
```

## Pathway Analysis (Analysis Service)

### Analyze Gene List

```python
from biodbs.fetch import reactome_analyze

# Analyze with UniProt IDs or gene symbols
result = reactome_analyze(
    ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    species="Homo sapiens"
)

# View results
print(result.summary())
df = result.as_dataframe()

# Get significant pathways
significant = result.significant_pathways(fdr_threshold=0.05)
print(f"Significant pathways: {len(significant)}")
```

### With Projection

```python
from biodbs.fetch import reactome_analyze_projection

# Project identifiers to Reactome space
result = reactome_analyze_projection(
    ["P04637", "P00533"],
    species="Homo sapiens"
)
```

### Analysis Result Methods

```python
result = reactome_analyze(genes)

# Summary statistics
print(result.summary())

# Top N pathways by FDR
top10 = result.top_pathways(n=10)

# Filter significant
significant = result.significant_pathways(fdr_threshold=0.05)

# Filter by attribute
lowest_level = result.filter(llp=True)  # Lowest-level pathways only
no_disease = result.filter(inDisease=False)  # Exclude disease pathways

# Get pathway IDs and names
ids = result.get_pathway_ids()
names = result.get_pathway_names()

# Export to DataFrame
df = result.as_dataframe()
```

### Retrieve Previous Analysis

```python
from biodbs.fetch import reactome_get_result_by_token

# Use token from previous analysis
result = reactome_get_result_by_token(token="MjAyNDAx...")
```

## Pathway Data (Content Service)

### Get Pathway Genes

```python
from biodbs.fetch import reactome_get_pathway_genes

# Get gene symbols for a pathway
genes = reactome_get_pathway_genes("R-HSA-69278")  # Cell Cycle
print(f"Found {len(genes)} genes")
print(genes[:10])  # ['PSMD6', 'MCM4', 'PLK1', ...]

# Get UniProt IDs instead
proteins = reactome_get_pathway_genes("R-HSA-69278", id_type="uniprot")
```

### Get All Pathways with Genes

```python
from biodbs.fetch import reactome_get_all_pathways_with_genes

# Get all human pathways with their genes (useful for local ORA)
pathway_genes = reactome_get_all_pathways_with_genes(species="Homo sapiens")
print(f"Found {len(pathway_genes)} pathways")

# Structure: {pathway_id: {"name": str, "genes": List[str]}}
for pid, data in list(pathway_genes.items())[:3]:
    print(f"{pid}: {data['name']} ({len(data['genes'])} genes)")
```

### Top-Level Pathways

```python
from biodbs.fetch import reactome_get_pathways_top

pathways = reactome_get_pathways_top(species="Homo sapiens")
print(f"Top-level pathways: {len(pathways)}")
```

### Pathways for Entity

```python
from biodbs.fetch import reactome_get_pathways_for_entity

# Find pathways containing a gene/protein
pathways = reactome_get_pathways_for_entity("P04637")  # TP53
for p in pathways[:5]:
    print(f"{p.get('stId')}: {p.get('displayName')}")
```

### Pathway Participants

```python
from biodbs.fetch import (
    reactome_get_participants,
    reactome_get_participants_reference_entities
)

# Get all participants in a pathway
participants = reactome_get_participants("R-HSA-69278")

# Get reference entities (proteins, genes)
ref_entities = reactome_get_participants_reference_entities("R-HSA-69278")
```

## Species Information

```python
from biodbs.fetch import reactome_get_species, reactome_get_species_main

# All supported species
all_species = reactome_get_species()

# Main/curated species only
main_species = reactome_get_species_main()
for sp in main_species[:5]:
    print(f"{sp.get('displayName')} (taxId: {sp.get('taxId')})")
```

## Additional Endpoints

### Event Ancestors

```python
from biodbs.fetch import reactome_get_event_ancestors

# Get pathway hierarchy
ancestors = reactome_get_event_ancestors("R-HSA-69278")
```

### Complex Subunits

```python
from biodbs.fetch import reactome_get_complex_subunits

# Get components of a complex
subunits = reactome_get_complex_subunits("R-HSA-83587")
```

### Disease Information

```python
from biodbs.fetch import reactome_get_diseases, reactome_get_diseases_doid

# Get all diseases in Reactome
diseases = reactome_get_diseases()

# Get diseases with DOID cross-references
diseases_doid = reactome_get_diseases_doid()
```

### ID Mapping

```python
from biodbs.fetch import reactome_map_identifiers, reactome_map_to_reactions

# Map identifiers to Reactome
mapped = reactome_map_identifiers(["P04637", "P00533"])

# Map to reactions
reactions = reactome_map_to_reactions("UniProt", "P04637")
```

### Database Version

```python
from biodbs.fetch import reactome_get_database_version

version = reactome_get_database_version()
print(f"Reactome version: {version}")
```

## Using the Fetcher Class

```python
from biodbs.fetch.Reactome import Reactome_Fetcher

fetcher = Reactome_Fetcher()

# Analysis
result = fetcher.analyze(["P04637", "P00533"])

# Content Service
genes = fetcher.get_pathway_genes("R-HSA-69278")
pathways = fetcher.get_pathways_top(species="Homo sapiens")
```

## Example: Local ORA with Custom Background

```python
from biodbs.analysis import ora_reactome_local

# Define your gene list
genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]

# Define custom background (e.g., all expressed genes)
background = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2",
              "EGFR", "MYC", "KRAS", "PIK3CA", "PTEN", ...]

# Run local ORA with custom background
result = ora_reactome_local(
    genes=genes,
    background=background,
    species="Homo sapiens",
    correction_method="fdr_bh"
)

print(result.summary())
```

See [Over-Representation Analysis](../analysis/ora.md) for more ORA options.
