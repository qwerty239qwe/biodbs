# Over-Representation Analysis (ORA)

Perform pathway and gene set enrichment analysis.

## Overview

ORA tests whether your gene list is enriched for genes from specific pathways or functional categories compared to a background.

## KEGG Pathway Enrichment

```python
from biodbs.analysis import ora_kegg

# Using Entrez IDs (default)
result = ora_kegg(
    genes=["7157", "672", "675", "580", "581"],  # Entrez IDs
    organism="hsa"
)

# View significant pathways
significant = result.significant_terms(alpha=0.05)
df = significant.as_dataframe()
print(df[["term_id", "term_name", "p_value", "adjusted_p_value"]])
```

### Using Different ID Types

The `from_id_type` parameter enables automatic ID translation:

```python
from biodbs.analysis import ora_kegg

# Using gene symbols - automatic translation to Entrez
result = ora_kegg(
    genes=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    organism="hsa",
    from_id_type="symbol"
)

# Using Ensembl IDs
result = ora_kegg(
    genes=["ENSG00000141510", "ENSG00000012048"],
    organism="hsa",
    from_id_type="ensembl"
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genes` | List[str] | required | Genes to analyze |
| `organism` | str | required | KEGG organism code (e.g., "hsa") |
| `from_id_type` | str | "entrez" | Input ID type (see below) |
| `background` | Set[str] | None | Background gene set |
| `min_overlap` | int | 3 | Minimum overlap required |
| `correction_method` | str | "bh" | Multiple testing correction |

### Supported ID Types

| ID Type | Aliases | Example |
|---------|---------|---------|
| `entrez` | entrezgene, ncbi_gene, gene_id | "7157" |
| `symbol` | gene_symbol, gene_name | "TP53" |
| `ensembl` | ensembl_gene_id | "ENSG00000141510" |
| `uniprot` | uniprot_id, swissprot | "P04637" |

### Organism Codes

| Code | Organism |
|------|----------|
| `hsa` | Human |
| `mmu` | Mouse |
| `rno` | Rat |
| `dme` | Fruit fly |
| `sce` | Yeast |

## Gene Ontology Enrichment

```python
from biodbs.analysis import ora_go

# Using UniProt IDs (default)
result = ora_go(
    genes=["P04637", "P38398", "P51587"],  # UniProt IDs
    taxon_id=9606,  # Human
    aspect="biological_process"
)

# Using gene symbols - automatic translation
result = ora_go(
    genes=["TP53", "BRCA1", "BRCA2"],
    taxon_id=9606,
    from_id_type="symbol"
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genes` | List[str] | required | Genes to analyze |
| `taxon_id` | int | required | NCBI taxonomy ID |
| `from_id_type` | str | "uniprot" | Input ID type |
| `aspect` | str | "biological_process" | GO aspect |

### GO Aspects

| Aspect | Description |
|--------|-------------|
| `biological_process` | BP - What the gene does |
| `molecular_function` | MF - Biochemical activity |
| `cellular_component` | CC - Where in the cell |

## Reactome Pathway Enrichment

Reactome provides curated, peer-reviewed pathway analysis. Two methods are available:

- **`ora_reactome`** - Uses Reactome's Analysis Service API (recommended for most cases)
- **`ora_reactome_local`** - Performs local ORA with custom backgrounds

### API-Based Analysis (ora_reactome)

```python
from biodbs.analysis import ora_reactome

result = ora_reactome(
    genes=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    species="Homo sapiens"
)

# View results - __repr__ shows summary
print(result)
# ReactomeFetchedData(847 pathways, 52 significant (FDR≤0.05), query=5 ids)
#   Top: R-HSA-69620 'Cell Cycle Checkpoints' (FDR=1.23e-08)

# Detailed summary
print(result.summary())

# Get significant pathways
significant = result.significant_pathways(fdr_threshold=0.05)
df = significant.as_dataframe()
```

### Local Analysis with Custom Background (ora_reactome_local)

Use `ora_reactome_local` when you need:

- Custom background gene set (e.g., only expressed genes)
- Different multiple testing correction methods
- Offline analysis capability

```python
from biodbs.analysis import ora_reactome_local

# Define your gene list
genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]

# Define custom background (e.g., all expressed genes in your experiment)
background = load_expressed_genes()  # Your background set

result = ora_reactome_local(
    genes=genes,
    background=background,
    species="Homo sapiens",
    correction_method="fdr_bh",  # Benjamini-Hochberg
    min_size=5,
    max_size=500
)

print(result.summary())
df = result.significant_terms(alpha=0.05).as_dataframe()
```

### Parameters (ora_reactome)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genes` | List[str] | required | Genes to analyze |
| `species` | str | "Homo sapiens" | Species name |
| `from_id_type` | str | "symbol" | Input ID type (symbol, ensembl, entrez, uniprot) |
| `interactors` | bool | False | Include interactors in analysis |
| `include_disease` | bool | True | Include disease pathways |
| `min_entities` | int | None | Minimum pathway size |
| `max_entities` | int | None | Maximum pathway size |
| `fetch_overlap_genes` | bool | False | Fetch specific overlap genes (slower) |

### Parameters (ora_reactome_local)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genes` | List[str] | required | Genes to analyze |
| `species` | str | "Homo sapiens" | Species name |
| `from_id_type` | str | "symbol" | Input ID type (symbol, ensembl, entrez, uniprot) |
| `background` | Set[str] | None | Background gene set (None = all pathway genes) |
| `correction_method` | str | "fdr_bh" | Multiple testing correction |
| `min_size` | int | 5 | Minimum pathway size |
| `max_size` | int | 500 | Maximum pathway size |
| `use_cache` | bool | True | Cache pathway-gene mappings |

### Correction Methods

| Method | Description |
|--------|-------------|
| `fdr_bh` | Benjamini-Hochberg FDR (default) |
| `bonferroni` | Bonferroni correction |
| `holm` | Holm-Bonferroni |
| `fdr_by` | Benjamini-Yekutieli FDR |

### Supported Species

| Species | Description |
|---------|-------------|
| `Homo sapiens` | Human |
| `Mus musculus` | Mouse |
| `Rattus norvegicus` | Rat |
| `Danio rerio` | Zebrafish |
| `Drosophila melanogaster` | Fruit fly |
| `Saccharomyces cerevisiae` | Yeast |

### Example with Different Identifiers

```python
# Using gene symbols (default)
result = ora_reactome(["TP53", "BRCA1", "EGFR"])

# Using UniProt IDs
result = ora_reactome(["P04637", "P38398", "P00533"], from_id_type="uniprot")

# Using Ensembl IDs
result = ora_reactome(
    ["ENSG00000141510", "ENSG00000012048"],
    from_id_type="ensembl"
)

# Using Entrez IDs
result = ora_reactome(["7157", "672", "675"], from_id_type="entrez")

# Mouse genes
result = ora_reactome(
    ["Trp53", "Brca1", "Brca2"],
    species="Mus musculus"
)
```

### When to Use Local vs API

| Use Case | Recommended |
|----------|-------------|
| Standard enrichment | `ora_reactome` |
| Custom background | `ora_reactome_local` |
| RNA-seq DEG analysis | `ora_reactome_local` |
| Quick exploratory analysis | `ora_reactome` |
| Reproducible offline analysis | `ora_reactome_local` |

## EnrichR Analysis

EnrichR provides access to 100+ gene set libraries.

```python
from biodbs.analysis import ora_enrichr

# Using gene symbols (default)
result = ora_enrichr(
    genes=["TP53", "BRCA1", "BRCA2", "ATM"],
    gene_set_library="KEGG_2021_Human"
)

# Using Ensembl IDs - automatic translation
result = ora_enrichr(
    genes=["ENSG00000141510", "ENSG00000012048"],
    gene_set_library="KEGG_2021_Human",
    from_id_type="ensembl"
)

# Using Entrez IDs
result = ora_enrichr(
    genes=["7157", "672", "675"],
    gene_set_library="GO_Biological_Process_2023",
    from_id_type="entrez"
)
```

### Convenience Functions

```python
from biodbs.analysis import (
    enrichr_kegg,
    enrichr_go_bp,
    enrichr_go_mf,
    enrichr_go_cc,
    enrichr_reactome,
    enrichr_wikipathways,
)

# KEGG
result = enrichr_kegg(["TP53", "BRCA1", "BRCA2"])

# GO Biological Process
result = enrichr_go_bp(["TP53", "BRCA1", "BRCA2"])

# Reactome
result = enrichr_reactome(["TP53", "BRCA1", "BRCA2"])
```

### Popular Libraries

| Library | Description |
|---------|-------------|
| `KEGG_2021_Human` | KEGG pathways |
| `GO_Biological_Process_2021` | GO BP |
| `GO_Molecular_Function_2021` | GO MF |
| `GO_Cellular_Component_2021` | GO CC |
| `Reactome_2022` | Reactome pathways |
| `WikiPathways_2019_Human` | WikiPathways |
| `MSigDB_Hallmark_2020` | Hallmark gene sets |

### List All Libraries

```python
from biodbs.fetch import enrichr_get_libraries

libraries = enrichr_get_libraries()
```

## Working with Results

### ORAResult Object

```python
result = ora_kegg(gene_list, organism="hsa")

# Summary statistics
print(result.summary())

# Total terms tested
print(f"Terms tested: {len(result)}")

# As DataFrame
df = result.as_dataframe()

# Significant terms only
significant = result.significant_terms(alpha=0.05)
significant = result.significant_terms(alpha=0.1, use_fdr=True)
```

### DataFrame Columns

```python
df = result.as_dataframe()

# Available columns
print(df.columns.tolist())
# ['term_id', 'term_name', 'p_value', 'q_value',
#  'overlap_count', 'term_size', 'overlap_genes', 'fold_enrichment']
```

## Examples

### Complete Workflow

```python
from biodbs.analysis import ora_kegg
from biodbs.translate import translate_gene_to_uniprot

# Your differentially expressed genes
deg_genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2", "RAD51", "PALB2"]

# KEGG enrichment
kegg_result = ora_kegg(
    gene_list=deg_genes,
    organism="hsa",
    id_type="symbol"
)

# View results
print(kegg_result.summary())

# Get significant pathways
significant = kegg_result.significant_terms(alpha=0.05)
df = significant.as_dataframe()

# Export
df.to_csv("kegg_enrichment.csv", index=False)
```

### Compare Multiple Gene Lists

```python
from biodbs.analysis import ora_kegg

gene_sets = {
    "upregulated": ["TP53", "BRCA1", "ATM"],
    "downregulated": ["MYC", "CCND1", "CDK4"],
}

results = {}
for name, genes in gene_sets.items():
    results[name] = ora_kegg(genes, organism="hsa", id_type="symbol")
    print(f"\n{name}:")
    print(results[name].summary())
```

### Multi-Database Enrichment

```python
from biodbs.analysis import ora_kegg, ora_reactome, ora_enrichr

genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]

# KEGG
kegg = ora_kegg(genes, organism="hsa", id_type="symbol")

# Reactome (direct API)
reactome = ora_reactome(genes, species="Homo sapiens")

# GO BP (via EnrichR)
go_bp = ora_enrichr(genes, gene_set_library="GO_Biological_Process_2021")

# Compare results
for name, result in [("KEGG", kegg), ("Reactome", reactome), ("GO_BP", go_bp)]:
    sig = result.significant_terms(p_threshold=0.05)
    print(f"{name}: {len(sig)} significant terms")
```
