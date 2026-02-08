# KEGG

Access pathway and biological systems data via the [KEGG API](https://www.kegg.jp/kegg/rest/keggapi.html).

## Overview

KEGG (Kyoto Encyclopedia of Genes and Genomes) provides data on:

- **Pathways** - Metabolic and signaling pathways
- **Genes** - Organism-specific gene information
- **Compounds** - Chemical compounds and reactions
- **Diseases** - Disease information and drug targets

## Quick Start

```python
from biodbs.fetch import kegg_get, kegg_find, kegg_list, kegg_link

# Get a pathway
pathway = kegg_get("hsa00010")  # Glycolysis

# Find genes
genes = kegg_find("genes", "shiga toxin")
```

## Basic Operations

### Get Entry

```python
from biodbs.fetch import kegg_get, kegg_get_batch

# Single entry
entry = kegg_get("hsa:7157")  # TP53 gene
pathway = kegg_get("hsa00010")  # Pathway
compound = kegg_get("C00001")  # Water

# Multiple entries (max 10 per request)
entries = kegg_get_batch(["hsa:7157", "hsa:672", "hsa:675"])
```

### Database Info

```python
from biodbs.fetch import kegg_info

info = kegg_info("pathway")
info = kegg_info("hsa")  # Human genes
```

### List Entries

```python
from biodbs.fetch import kegg_list

# List all human pathways
pathways = kegg_list("pathway", organism="hsa")

# List all compounds
compounds = kegg_list("compound")
```

### Search

```python
from biodbs.fetch import kegg_find

# Search genes
genes = kegg_find("genes", "shiga toxin")

# Search compounds
compounds = kegg_find("compound", "aspirin")

# Search pathways
pathways = kegg_find("pathway", "cancer")
```

## ID Conversion

```python
from biodbs.fetch import kegg_conv

# KEGG to NCBI Gene ID
converted = kegg_conv("ncbi-geneid", ["hsa:7157", "hsa:672"])

# KEGG to UniProt
converted = kegg_conv("uniprot", "hsa:7157")

# Organism-wide conversion
all_human = kegg_conv("ncbi-geneid", "hsa")
```

## Cross-References

```python
from biodbs.fetch import kegg_link

# Genes in a pathway
genes = kegg_link("hsa", "hsa00010")

# Pathways for genes
pathways = kegg_link("pathway", ["hsa:7157", "hsa:672"])

# Compounds in a pathway
compounds = kegg_link("compound", "hsa00010")
```

## Drug-Drug Interactions

```python
from biodbs.fetch import kegg_ddi

# Check drug interactions
interactions = kegg_ddi(["D00001", "D00002"])
```

## Using the Fetcher Class

```python
from biodbs.fetch.KEGG import KEGG_Fetcher

fetcher = KEGG_Fetcher()
pathway = fetcher.get("hsa00010")
```

## Related Resources

- **[Reactome](reactome.md)** - Alternative pathway database with more detailed reaction-level data. Good for complementary analysis.
- **[UniProt](uniprot.md)** - Get detailed protein information for KEGG genes using `kegg_conv("uniprot", ...)`.
- **[PubChem](pubchem.md)** - Additional chemical information for KEGG compounds.
- **[Over-Representation Analysis](../analysis/ora.md)** - Use KEGG pathways for gene set enrichment analysis with `ora_kegg()`.
- **[Knowledge Graphs](../graph/building.md)** - Build knowledge graphs from KEGG data with `build_kegg_graph()`.
