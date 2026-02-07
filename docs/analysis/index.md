# Analysis Overview

The `biodbs.analysis` module provides statistical analysis functions for biological data.

## Available Analyses

| Analysis | Function | Description |
|----------|----------|-------------|
| [ORA](ora.md) | `ora_kegg`, `ora_go`, `ora_enrichr` | Over-representation analysis |

## Quick Start

```python
from biodbs.analysis import ora_kegg, ora_go, ora_enrichr

# KEGG pathway enrichment
result = ora_kegg(
    gene_list=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    organism="hsa",
    id_type="symbol"
)

# View results
print(result.summary())
df = result.as_dataframe()
```

## Over-Representation Analysis

ORA (Over-Representation Analysis) tests whether a gene set is enriched for genes from specific pathways or functional categories.

### Supported Resources

| Function | Resource | Gene ID Type |
|----------|----------|--------------|
| `ora_kegg` | KEGG Pathways | Entrez ID, Symbol |
| `ora_go` | Gene Ontology (via QuickGO) | UniProt |
| `ora_enrichr` | EnrichR (100+ libraries) | Symbol |

### Basic Usage

```python
from biodbs.analysis import ora_kegg

result = ora_kegg(
    gene_list=["TP53", "BRCA1", "BRCA2", "ATM"],
    organism="hsa",
    id_type="symbol"  # Auto-converts to Entrez
)

# Get significant pathways
significant = result.significant_terms(alpha=0.05)
print(significant.as_dataframe())
```

## Working with Results

### ORAResult Object

```python
result = ora_kegg(gene_list, organism="hsa")

# Summary
print(result.summary())

# Number of terms tested
print(f"Tested: {len(result)} terms")

# As DataFrame
df = result.as_dataframe()

# Filter significant
significant = result.significant_terms(alpha=0.05)
significant = result.significant_terms(alpha=0.1, use_fdr=True)
```

### Result Columns

| Column | Description |
|--------|-------------|
| `term_id` | Pathway/term identifier |
| `term_name` | Pathway/term name |
| `p_value` | Raw p-value |
| `q_value` | FDR-adjusted p-value |
| `overlap_count` | Number of genes overlapping |
| `term_size` | Total genes in term |
| `overlap_genes` | List of overlapping genes |
| `fold_enrichment` | Enrichment score |

## Next Steps

- [Detailed ORA documentation](ora.md)
- [UniProt ID translation](../translate/proteins.md) (for GO analysis)
- [KEGG pathway data](../fetch/kegg.md)
