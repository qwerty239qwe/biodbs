# Analysis Module API Reference

Complete reference for `biodbs.analysis` module.

## Summary

### Classes

| Class | Description |
|-------|-------------|
| [`ORAResult`](#oraresult) | Container for over-representation analysis results |
| [`ORATermResult`](#oratermresult) | Single term result from ORA |
| [`Pathway`](#pathway) | Represents a biological pathway with gene sets |

### Enums

| Enum | Description |
|------|-------------|
| [`Species`](#species) | Supported species for ORA (human, mouse, rat, etc.) |
| [`GOAspect`](#goaspect) | Gene Ontology aspects (BP, MF, CC) |
| [`CorrectionMethod`](#correctionmethod) | Multiple testing correction methods (FDR, Bonferroni) |
| [`TranslationDatabase`](#translationdatabase) | Databases for automatic ID translation |
| [`PathwayDatabase`](#pathwaydatabase) | Pathway database sources (KEGG, GO, Reactome) |

### Core ORA Functions

| Function | Description |
|----------|-------------|
| [`ora`](#ora) | Generic ORA against any pathway database |
| [`ora_kegg`](#ora_kegg) | ORA against KEGG pathways |
| [`ora_go`](#ora_go) | ORA against Gene Ontology terms |
| [`ora_reactome`](#ora_reactome) | ORA against Reactome pathways (via API) |
| [`ora_reactome_local`](#ora_reactome_local) | ORA against Reactome pathways (local calculation) |
| [`ora_enrichr`](#ora_enrichr) | ORA via EnrichR web service |

### Utility Functions

| Function | Description |
|----------|-------------|
| [`hypergeometric_test`](#hypergeometric_test) | Compute hypergeometric p-value |
| [`multiple_test_correction`](#multiple_test_correction) | Apply multiple testing correction |

---

## Enums

### Species

Supported species for ORA. Each member contains: `(taxon_id, common_name, kegg_code, scientific_name)`.

| Member | Taxon ID | KEGG Code | Scientific Name |
|--------|----------|-----------|-----------------|
| `HUMAN` | 9606 | `hsa` | Homo sapiens |
| `MOUSE` | 10090 | `mmu` | Mus musculus |
| `RAT` | 10116 | `rno` | Rattus norvegicus |
| `ZEBRAFISH` | 7955 | `dre` | Danio rerio |
| `FLY` | 7227 | `dme` | Drosophila melanogaster |
| `WORM` | 6239 | `cel` | Caenorhabditis elegans |
| `YEAST` | 559292 | `sce` | Saccharomyces cerevisiae |

::: biodbs._funcs.analysis.ora.Species
    options:
      show_root_heading: true
      members_order: source

### GOAspect

Gene Ontology aspects for filtering GO terms.

| Member | Value | Description |
|--------|-------|-------------|
| `BIOLOGICAL_PROCESS` | `"biological_process"` | BP - Biological processes |
| `MOLECULAR_FUNCTION` | `"molecular_function"` | MF - Molecular functions |
| `CELLULAR_COMPONENT` | `"cellular_component"` | CC - Cellular components |
| `ALL` | `"all"` | All GO aspects |

::: biodbs._funcs.analysis.ora.GOAspect
    options:
      show_root_heading: true
      members_order: source

### CorrectionMethod

Multiple testing correction methods.

| Member | Value | Description |
|--------|-------|-------------|
| `BONFERRONI` | `"bonferroni"` | Bonferroni correction (conservative) |
| `BH` | `"benjamini_hochberg"` | Benjamini-Hochberg FDR (recommended) |
| `BY` | `"benjamini_yekutieli"` | Benjamini-Yekutieli FDR |
| `HOLM` | `"holm"` | Holm-Bonferroni method |
| `NONE` | `"none"` | No correction |

::: biodbs._funcs.analysis.ora.CorrectionMethod
    options:
      show_root_heading: true
      members_order: source

### TranslationDatabase

Databases for automatic ID translation.

| Member | Value | Description |
|--------|-------|-------------|
| `BIOMART` | `"biomart"` | Ensembl BioMart |
| `UNIPROT` | `"uniprot"` | UniProt ID mapping |
| `NCBI` | `"ncbi"` | NCBI Gene database |

::: biodbs._funcs.analysis.ora.TranslationDatabase
    options:
      show_root_heading: true
      members_order: source

### PathwayDatabase

Pathway database sources.

| Member | Value | Description |
|--------|-------|-------------|
| `KEGG` | `"kegg"` | KEGG pathways |
| `GO` | `"go"` | Gene Ontology terms |
| `ENRICHR` | `"enrichr"` | EnrichR libraries |
| `REACTOME` | `"reactome"` | Reactome pathways |

::: biodbs._funcs.analysis.ora.PathwayDatabase
    options:
      show_root_heading: true
      members_order: source

---

## Result Classes

### ORAResult

::: biodbs._funcs.analysis.ora.ORAResult
    options:
      show_root_heading: true
      members_order: source
      show_source: false

### ORATermResult

::: biodbs._funcs.analysis.ora.ORATermResult
    options:
      show_root_heading: true
      members_order: source
      show_source: false

### Pathway

::: biodbs._funcs.analysis.ora.Pathway
    options:
      show_root_heading: true
      members_order: source
      show_source: false

---

## Core ORA Functions

### ora

::: biodbs._funcs.analysis.ora.ora
    options:
      show_root_heading: true
      show_source: false

### ora_kegg

::: biodbs._funcs.analysis.ora.ora_kegg
    options:
      show_root_heading: true
      show_source: false

### ora_go

::: biodbs._funcs.analysis.ora.ora_go
    options:
      show_root_heading: true
      show_source: false

### ora_reactome

::: biodbs._funcs.analysis.ora.ora_reactome
    options:
      show_root_heading: true
      show_source: false

### ora_reactome_local

::: biodbs._funcs.analysis.ora.ora_reactome_local
    options:
      show_root_heading: true
      show_source: false

### ora_enrichr

::: biodbs._funcs.analysis.ora.ora_enrichr
    options:
      show_root_heading: true
      show_source: false

---

## Utility Functions

### hypergeometric_test

::: biodbs._funcs.analysis.ora.hypergeometric_test
    options:
      show_root_heading: true
      show_source: false

### multiple_test_correction

::: biodbs._funcs.analysis.ora.multiple_test_correction
    options:
      show_root_heading: true
      show_source: false

---

## DataFrame Columns

When using `ORAResult.as_dataframe()`:

| Column | Type | Description |
|--------|------|-------------|
| `term_id` | str | Pathway/term ID |
| `term_name` | str | Pathway/term name |
| `p_value` | float | Raw p-value |
| `adjusted_p_value` | float | FDR-adjusted p-value |
| `overlap_count` | int | Overlapping genes |
| `term_size` | int | Total genes in term |
| `query_size` | int | Number of query genes |
| `background_size` | int | Universe size |
| `fold_enrichment` | float | Enrichment score |
| `odds_ratio` | float | Odds ratio |
| `overlap_genes` | str | Comma-separated gene IDs |
| `database` | str | Source database |

---

## EnrichR Libraries

Popular gene set libraries available in EnrichR:

| Library | Description |
|---------|-------------|
| `KEGG_2021_Human` | KEGG pathways |
| `GO_Biological_Process_2021` | GO biological process |
| `GO_Molecular_Function_2021` | GO molecular function |
| `GO_Cellular_Component_2021` | GO cellular component |
| `Reactome_2022` | Reactome pathways |
| `WikiPathways_2019_Human` | WikiPathways |
| `MSigDB_Hallmark_2020` | MSigDB Hallmark |
| `GWAS_Catalog_2019` | GWAS Catalog |
| `DisGeNET` | Disease-gene associations |
| `DrugMatrix` | Drug signatures |

Get all available libraries:

```python
from biodbs.fetch import enrichr_get_libraries
libraries = enrichr_get_libraries()
```
