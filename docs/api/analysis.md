# Analysis Module API Reference

Complete reference for `biodbs.analysis` module.

## Quick Import

```python
from biodbs.analysis import (
    # Core ORA functions
    ora,
    ora_kegg,
    ora_go,
    ora_enrichr,
    ora_reactome,
    ora_reactome_local,
    # Result classes
    ORAResult,
    ORATermResult,
    Pathway,
    # Enums
    Species,
    GOAspect,
    CorrectionMethod,
    TranslationDatabase,
    PathwayDatabase,
    # Utility functions
    hypergeometric_test,
    multiple_test_correction,
)
```

---

## Enums

### Species

::: biodbs._funcs.analysis.ora.Species
    options:
      show_root_heading: true
      members_order: source

### GOAspect

::: biodbs._funcs.analysis.ora.GOAspect
    options:
      show_root_heading: true
      members_order: source

### CorrectionMethod

::: biodbs._funcs.analysis.ora.CorrectionMethod
    options:
      show_root_heading: true
      members_order: source

### TranslationDatabase

::: biodbs._funcs.analysis.ora.TranslationDatabase
    options:
      show_root_heading: true
      members_order: source

### PathwayDatabase

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
