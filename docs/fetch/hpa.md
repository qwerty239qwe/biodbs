# Human Protein Atlas (HPA)

Access protein expression data via the [HPA API](https://www.proteinatlas.org/).

## Overview

The Human Protein Atlas provides data on:

- **Tissue Expression** - Protein levels across tissues
- **Blood Expression** - Protein levels in blood
- **Brain Expression** - Brain region-specific expression
- **Subcellular Location** - Where proteins are located in cells
- **Pathology** - Cancer expression data

## Quick Start

```python
from biodbs.fetch import (
    hpa_get_gene,
    hpa_get_tissue_expression,
    hpa_get_subcellular_location,
)

# Get gene data
gene = hpa_get_gene("TP53")
```

## Gene Data

### Get Gene

```python
from biodbs.fetch import hpa_get_gene, hpa_get_genes

gene = hpa_get_gene("TP53")
genes = hpa_get_genes(["TP53", "BRCA1", "EGFR"])
```

### Search

```python
from biodbs.fetch import hpa_search

results = hpa_search("kinase")
```

## Expression Data

### Tissue Expression

```python
from biodbs.fetch import hpa_get_tissue_expression

expression = hpa_get_tissue_expression("TP53")
df = expression.as_dataframe()
```

### Blood Expression

```python
from biodbs.fetch import hpa_get_blood_expression

expression = hpa_get_blood_expression("TP53")
```

### Brain Expression

```python
from biodbs.fetch import hpa_get_brain_expression

expression = hpa_get_brain_expression("TP53")
```

## Subcellular Location

```python
from biodbs.fetch import hpa_get_subcellular_location

location = hpa_get_subcellular_location("TP53")
```

## Pathology Data

```python
from biodbs.fetch import hpa_get_pathology

pathology = hpa_get_pathology("TP53")
```

## Protein Classes

```python
from biodbs.fetch import hpa_get_protein_class

classes = hpa_get_protein_class("TP53")
```

## Using the Fetcher Class

```python
from biodbs.fetch.HPA import HPA_Fetcher

fetcher = HPA_Fetcher()
gene = fetcher.get_gene("TP53")
```

## Related Resources

- **[UniProt](uniprot.md)** - Get detailed protein information, including subcellular localization annotations.
- **[Ensembl](ensembl.md)** - Get genomic context and transcript information for genes.
- **[ID Translation](../translate/genes.md)** - Translate between gene symbols and other identifiers for use with HPA.
