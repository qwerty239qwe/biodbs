# BioMart

Query gene annotations via [Ensembl BioMart](https://www.ensembl.org/biomart/).

## Overview

BioMart is a query-oriented data management system for large biological datasets. It excels at:

- **Batch Queries** - Retrieve data for many genes at once
- **ID Conversion** - Map between identifier systems
- **Annotations** - GO terms, descriptions, homologs
- **Filtering** - Complex queries with multiple filters

## Quick Start

```python
from biodbs.fetch import (
    biomart_get_genes,
    biomart_get_genes_by_name,
    biomart_convert_ids,
    biomart_get_go_annotations,
)

# Get genes by Ensembl ID
genes = biomart_get_genes(["ENSG00000141510", "ENSG00000012048"])
df = genes.as_dataframe()
```

## Gene Retrieval

### By Ensembl ID

```python
from biodbs.fetch import biomart_get_genes

genes = biomart_get_genes(
    ["ENSG00000141510", "ENSG00000012048"],
    dataset="hsapiens_gene_ensembl"
)
```

### By Gene Name

```python
from biodbs.fetch import biomart_get_genes_by_name

genes = biomart_get_genes_by_name(["TP53", "BRCA1"])
```

### By Region

```python
from biodbs.fetch import biomart_get_genes_by_region

genes = biomart_get_genes_by_region(
    chromosome="17",
    start=7661779,
    end=7687550
)
```

## ID Conversion

```python
from biodbs.fetch import biomart_convert_ids

# Gene symbols to Ensembl IDs
converted = biomart_convert_ids(
    ["TP53", "BRCA1", "EGFR"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id"
)

# Ensembl to Entrez
converted = biomart_convert_ids(
    ["ENSG00000141510"],
    from_type="ensembl_gene_id",
    to_type="entrezgene_id"
)
```

### Supported ID Types

| ID Type | Description |
|---------|-------------|
| `ensembl_gene_id` | Ensembl gene ID |
| `ensembl_transcript_id` | Ensembl transcript ID |
| `external_gene_name` | Gene symbol |
| `hgnc_symbol` | HGNC symbol |
| `hgnc_id` | HGNC ID |
| `entrezgene_id` | NCBI Entrez ID |
| `uniprot_gn_id` | UniProt gene name |
| `refseq_mrna` | RefSeq mRNA ID |

## Annotations

### GO Annotations

```python
from biodbs.fetch import biomart_get_go_annotations

go = biomart_get_go_annotations(["ENSG00000141510"])
df = go.as_dataframe()
```

### Transcripts

```python
from biodbs.fetch import biomart_get_transcripts

transcripts = biomart_get_transcripts(["ENSG00000141510"])
```

### Homologs

```python
from biodbs.fetch import biomart_get_homologs

homologs = biomart_get_homologs(
    ["ENSG00000141510"],
    target_species="mmusculus"
)
```

## Custom Queries

```python
from biodbs.fetch import biomart_query

data = biomart_query(
    dataset="hsapiens_gene_ensembl",
    attributes=[
        "ensembl_gene_id",
        "external_gene_name",
        "description",
        "chromosome_name",
        "start_position",
        "end_position"
    ],
    filters={"ensembl_gene_id": ["ENSG00000141510", "ENSG00000012048"]}
)
```

## List Available Options

```python
from biodbs.fetch import biomart_list_datasets, biomart_list_attributes, biomart_list_filters

# List datasets
datasets = biomart_list_datasets()

# List attributes for a dataset
attributes = biomart_list_attributes("hsapiens_gene_ensembl")

# List filters
filters = biomart_list_filters("hsapiens_gene_ensembl")
```

## Using the Fetcher Class

```python
from biodbs.fetch.biomart import BioMart_Fetcher

fetcher = BioMart_Fetcher()
data = fetcher.query(
    dataset="hsapiens_gene_ensembl",
    attributes=["ensembl_gene_id", "external_gene_name"],
    filters={"chromosome_name": "17"}
)
```
