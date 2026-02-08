# EnrichR

Access gene set enrichment analysis via the [EnrichR API](https://maayanlab.cloud/Enrichr/).

## Overview

EnrichR provides:

- **100+ Gene Set Libraries** - KEGG, GO, Reactome, WikiPathways, and more
- **Enrichment Analysis** - Statistical enrichment testing
- **Combined Scores** - Integrated p-value and z-score metrics

## Quick Start

```python
from biodbs.fetch import enrichr_analyze, enrichr_get_libraries

# Analyze gene list against a library
result = enrichr_analyze(
    genes=["TP53", "BRCA1", "BRCA2", "ATM"],
    gene_set_library="KEGG_2021_Human"
)

# View results
df = result.as_dataframe()
print(df[["term_name", "adjusted_p_value", "combined_score"]])
```

## Gene Set Libraries

### List Available Libraries

```python
from biodbs.fetch import enrichr_get_libraries

libraries = enrichr_get_libraries()
print(f"Available libraries: {len(libraries)}")

# Search for specific libraries
kegg_libs = [lib for lib in libraries.get_library_names() if "KEGG" in lib]
```

### Popular Libraries

| Library | Description |
|---------|-------------|
| `KEGG_2021_Human` | KEGG metabolic pathways |
| `GO_Biological_Process_2021` | GO biological processes |
| `GO_Molecular_Function_2021` | GO molecular functions |
| `GO_Cellular_Component_2021` | GO cellular components |
| `Reactome_2022` | Reactome pathways |
| `WikiPathways_2019_Human` | WikiPathways |
| `MSigDB_Hallmark_2020` | MSigDB hallmark gene sets |
| `GWAS_Catalog_2019` | GWAS associations |
| `OMIM_Disease` | Disease associations |

## Enrichment Analysis

### Basic Analysis

```python
from biodbs.fetch import enrichr_analyze

result = enrichr_analyze(
    genes=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    gene_set_library="KEGG_2021_Human"
)

# Get significant terms
significant = result.significant_terms(p_threshold=0.05)
print(f"Significant pathways: {len(significant)}")
```

### Multiple Libraries

```python
from biodbs.fetch import enrichr_analyze

genes = ["TP53", "BRCA1", "BRCA2"]

# Analyze against multiple libraries
libraries = ["KEGG_2021_Human", "Reactome_2022", "GO_Biological_Process_2021"]
for lib in libraries:
    result = enrichr_analyze(genes, gene_set_library=lib)
    sig = result.significant_terms(p_threshold=0.05)
    print(f"{lib}: {len(sig)} significant terms")
```

## Working with Results

### EnrichRFetchedData

```python
result = enrichr_analyze(genes, gene_set_library="KEGG_2021_Human")

# Number of terms
print(f"Terms tested: {len(result)}")

# As DataFrame
df = result.as_dataframe()

# Get top terms by combined score
top = result.top_terms(n=10)

# Filter significant
significant = result.significant_terms(p_threshold=0.05, use_adjusted=True)
```

### Result Columns

| Column | Description |
|--------|-------------|
| `term_name` | Gene set name |
| `p_value` | Raw p-value |
| `adjusted_p_value` | FDR-adjusted p-value |
| `z_score` | Z-score |
| `combined_score` | Combined score (log(p) * z) |
| `overlapping_genes` | Genes in overlap |
| `odds_ratio` | Odds ratio |

### Get Overlap Genes

```python
result = enrichr_analyze(genes, gene_set_library="KEGG_2021_Human")

# Get genes for a specific term
overlap = result.get_genes_for_term("Cell cycle")
print(f"Overlapping genes: {overlap}")
```

## Using the Fetcher Class

```python
from biodbs.fetch.EnrichR import EnrichR_Fetcher

fetcher = EnrichR_Fetcher()

# Submit gene list
user_list_id = fetcher.add_list(["TP53", "BRCA1", "BRCA2"])

# Run enrichment
result = fetcher.enrich(
    user_list_id=user_list_id,
    gene_set_library="KEGG_2021_Human"
)
```

## Example Workflow

```python
from biodbs.fetch import enrichr_analyze, enrichr_get_libraries

# Define genes of interest
genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2", "RAD51", "PALB2"]

# KEGG pathway enrichment
kegg_result = enrichr_analyze(genes, "KEGG_2021_Human")
print("KEGG Results:")
print(kegg_result)  # Shows summary with significant count

# Get significant pathways
significant = kegg_result.significant_terms(p_threshold=0.05)
df = significant.as_dataframe()
print(df[["term_name", "adjusted_p_value", "combined_score"]].head(10))

# Export results
df.to_csv("enrichr_results.csv", index=False)
```

## Related Resources

- **[Over-Representation Analysis](../analysis/ora.md)** - Use EnrichR via the unified ORA interface with `ora_enrichr()`.
- **[KEGG](kegg.md)** - Direct access to KEGG pathway data.
- **[Reactome](reactome.md)** - Alternative pathway analysis with Reactome's dedicated API.
- **[QuickGO](quickgo.md)** - Direct access to Gene Ontology annotations.
