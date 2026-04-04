# HGNC

Access authoritative human gene nomenclature via the [HGNC REST API](https://www.genenames.org/help/rest/).

## Overview

The HUGO Gene Nomenclature Committee (HGNC) is the authority for approved human gene symbols and names. biodbs provides:

- **Exact lookups** by symbol, HGNC ID, Entrez ID, Ensembl ID, UniProt accession, or RefSeq accession
- **Wildcard search** across any HGNC field
- **Cross-reference retrieval** — get Ensembl, Entrez, UniProt IDs for any gene in one call

## Quick Start

```python
from biodbs.fetch import hgnc_fetch_by_symbol, hgnc_search_symbol

# Fetch a gene by symbol
data = hgnc_fetch_by_symbol("TP53")
entry = data[0]
print(entry.hgnc_id)         # "HGNC:11998"
print(entry.entrez_id)       # "7157"
print(entry.ensembl_gene_id) # "ENSG00000141510"

# Wildcard search
hits = hgnc_search_symbol("BRCA*")
print(hits.symbols())  # ['BRCA1', 'BRCA2', ...]
```

## Fetch by Identifier

### By Gene Symbol

```python
from biodbs.fetch import hgnc_fetch_by_symbol

data = hgnc_fetch_by_symbol("EGFR")
entry = data[0]
print(entry.name)   # "epidermal growth factor receptor"
print(entry.locus_type)
```

### By HGNC ID

```python
from biodbs.fetch import hgnc_fetch_by_hgnc_id

data = hgnc_fetch_by_hgnc_id("HGNC:11998")
print(data[0].symbol)  # "TP53"
```

### By Entrez Gene ID

```python
from biodbs.fetch import hgnc_fetch_by_entrez_id

data = hgnc_fetch_by_entrez_id("7157")
print(data[0].symbol)  # "TP53"
```

### By Ensembl Gene ID

```python
from biodbs.fetch import hgnc_fetch_by_ensembl_id

data = hgnc_fetch_by_ensembl_id("ENSG00000141510")
print(data[0].symbol)  # "TP53"
```

### By UniProt Accession

```python
from biodbs.fetch import hgnc_fetch_by_uniprot_id

data = hgnc_fetch_by_uniprot_id("P04637")
print(data[0].symbol)  # "TP53"
```

### By RefSeq Accession

```python
from biodbs.fetch import hgnc_fetch_by_refseq

data = hgnc_fetch_by_refseq("NM_000546")
print(data[0].symbol)  # "TP53"
```

## Search

### Symbol Wildcard Search

```python
from biodbs.fetch import hgnc_search_symbol

# All ZNF family members
hits = hgnc_search_symbol("ZNF*")
print(len(hits))

# Single character wildcard
hits = hgnc_search_symbol("BRCA?")
print(hits.symbols())  # ['BRCA1', 'BRCA2']
```

### General Field Search

```python
from biodbs.fetch import hgnc_search

# Boolean / Solr query
hits = hgnc_search("status:Approved AND locus_group:non-coding+RNA")

# Field + term
hits = hgnc_search("locus_type", "RNA*")
```

## Low-Level Fetch

```python
from biodbs.fetch import hgnc_fetch

# Exact-match on any HGNC stored field
data = hgnc_fetch("alias_symbol", "p53")
```

## Service Info

```python
from biodbs.fetch import hgnc_info

info = hgnc_info()
print(info["response"]["numDoc"])          # total gene count
print(info["response"]["lastModified"])    # last DB update
```

## Working with Results

```python
data = hgnc_fetch_by_symbol("TP53")
entry = data[0]

# Key fields on HGNCEntry
entry.hgnc_id          # "HGNC:11998"
entry.symbol           # "TP53"
entry.name             # "tumor protein p53"
entry.locus_group      # "protein-coding gene"
entry.locus_type       # "gene with protein product"
entry.entrez_id        # "7157"
entry.ensembl_gene_id  # "ENSG00000141510"
entry.uniprot_ids      # ["P04637"]
entry.refseq_accession # ["NM_000546"]
entry.status           # "Approved"

# Convert to DataFrame
df = data.as_dataframe()
```

## Using the Fetcher Class

```python
from biodbs.fetch.HGNC import HGNC_Fetcher

fetcher = HGNC_Fetcher()
data = fetcher.fetch("symbol", "TP53")
data = fetcher.search("symbol", "TP53*")
```

## Related Resources

- **[ID Translation](../translate/genes.md)** — HGNC powers the `"hgnc"` translation database in `translate_gene_ids()`.
- **[NCBI](ncbi.md)** — Complementary gene information including gene summaries and genomic location.
- **[UniProt](uniprot.md)** — Fetch protein data for genes identified via HGNC.
