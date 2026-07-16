# NCBI

Access gene and taxonomy data via the [NCBI Datasets API](https://www.ncbi.nlm.nih.gov/datasets/).

## Overview

NCBI provides:

- **Gene Data** - Gene information and annotations
- **Taxonomy** - Organism classification
- **Genome Assemblies** - Reference genome data

## Quick Start

```python
from biodbs.fetch import (
    ncbi_get_gene,
    ncbi_symbol_to_id,
    ncbi_get_taxonomy,
)

# Get gene by Entrez ID
genes = ncbi_get_gene([7157, 672])
```

## Gene Data

### Get Genes

```python
from biodbs.fetch import ncbi_get_gene

# By Entrez Gene ID
genes = ncbi_get_gene([7157, 672])

# Access gene data
for gene in genes.genes:
    print(f"{gene.gene_id}: {gene.symbol}")
```

### Symbol to ID

```python
from biodbs.fetch import ncbi_symbol_to_id

mapping = ncbi_symbol_to_id(["TP53", "BRCA1"])
# {'TP53': 7157, 'BRCA1': 672}
```

### ID to Symbol

```python
from biodbs.fetch import ncbi_id_to_symbol

mapping = ncbi_id_to_symbol([7157, 672])
# {7157: 'TP53', 672: 'BRCA1'}
```

### Translate Gene IDs

```python
from biodbs.fetch import ncbi_translate_gene_ids

result = ncbi_translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="symbol",
    to_type="entrez_id",
    taxon="human"
)
```

## Taxonomy

```python
from biodbs.fetch import ncbi_get_taxonomy

# By taxonomy ID
tax = ncbi_get_taxonomy([9606, 10090])

# Access taxonomy data
human = tax.get_taxon(9606)
print(human.organism_name)  # "Homo sapiens"
```

## Using the Fetcher Class

```python
from biodbs.fetch.NCBI import NCBI_Fetcher

fetcher = NCBI_Fetcher()
genes = fetcher.get_genes_by_id([7157, 672])
```

## Static Reference Downloads

Download preformatted BLAST databases and the NCBI taxonomy dump directly from
NCBI's FTP. Both are verified against NCBI's published `.md5` sidecars and streamed
atomically (an interrupted download is never left in place).

```python
from biodbs.fetch import ncbi_download_blast_database, ncbi_download_taxdump

blast_db = ncbi_download_blast_database("16S_ribosomal_RNA", "data/ncbi")
taxdump = ncbi_download_taxdump("data/ncbi")
```

`dest` may be a directory (the archive filename is appended) or an explicit file
path. These are large archives — extraction and indexing are left to your pipeline.

## Related Resources

- **[Ensembl](ensembl.md)** - Alternative gene resource with genomic coordinates and VEP.
- **[UniProt](uniprot.md)** - Protein information for gene products.
- **[ID Translation](../translate/genes.md)** - Translate between Entrez Gene IDs and other identifiers using `translate_gene_ids(..., database="ncbi")`.
