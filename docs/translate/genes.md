# Gene ID Translation

Translate between different gene identifier systems.

## Quick Start

```python
from biodbs.translate import translate_gene_ids, translate_gene_ids_kegg

# Gene symbols to Ensembl IDs
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id"
)
```

## translate_gene_ids

The main function for gene ID translation with multiple backend databases.

```python
from biodbs.translate import translate_gene_ids

result = translate_gene_ids(
    ids=["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    species="human",
    database="biomart",
    return_dict=False
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ids` | List[str] | required | IDs to translate |
| `from_type` | str | required | Source ID type |
| `to_type` | str | required | Target ID type |
| `species` | str | "human" | Species name |
| `database` | str | "biomart" | Backend database |
| `return_dict` | bool | False | Return dict instead of DataFrame |

### Supported Databases

#### BioMart (default)

Best for batch queries with many ID types.

```python
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    database="biomart"
)
```

**Supported ID types:**

| ID Type | Description | Example |
|---------|-------------|---------|
| `ensembl_gene_id` | Ensembl gene ID | ENSG00000141510 |
| `ensembl_transcript_id` | Ensembl transcript | ENST00000269305 |
| `external_gene_name` | Gene symbol | TP53 |
| `hgnc_symbol` | HGNC symbol | TP53 |
| `hgnc_id` | HGNC ID | HGNC:11998 |
| `entrezgene_id` | NCBI Entrez ID | 7157 |
| `uniprot_gn_id` | UniProt gene name | P04637 |
| `refseq_mrna` | RefSeq mRNA | NM_000546 |

#### Ensembl REST API

Better for single ID lookups with more cross-references.

```python
result = translate_gene_ids(
    ["ENSG00000141510"],
    from_type="ensembl_gene_id",
    to_type="HGNC",
    database="ensembl"
)
```

#### NCBI

Best for NCBI Gene IDs and RefSeq.

```python
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="symbol",
    to_type="entrez_id",
    database="ncbi"
)
```

**Supported ID types:**

| ID Type | Description |
|---------|-------------|
| `symbol` / `gene_symbol` | Gene symbol |
| `entrez_id` / `gene_id` | NCBI Gene ID |
| `refseq_accession` | RefSeq accession |

#### UniProt

Best for protein-centric translations.

```python
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="Gene_Name",
    to_type="UniProtKB",
    database="uniprot"
)
```

**Supported ID types:**

| ID Type | Description |
|---------|-------------|
| `UniProtKB_AC-ID` | UniProt accession |
| `Gene_Name` | Gene symbol |
| `GeneID` | NCBI Gene ID |
| `Ensembl` | Ensembl gene ID |

## translate_gene_ids_kegg

Translate using KEGG database.

```python
from biodbs.translate import translate_gene_ids_kegg

# KEGG to NCBI Gene ID
result = translate_gene_ids_kegg(
    ["hsa:7157", "hsa:672"],
    from_db="hsa",
    to_db="ncbi-geneid"
)

# KEGG to UniProt
result = translate_gene_ids_kegg(
    ["hsa:7157"],
    from_db="hsa",
    to_db="uniprot"
)
```

### KEGG Database Codes

| Code | Description |
|------|-------------|
| `hsa` | Human genes |
| `mmu` | Mouse genes |
| `ncbi-geneid` | NCBI Gene ID |
| `ncbi-proteinid` | NCBI Protein ID |
| `uniprot` | UniProt accession |

## Species Support

```python
# Human (default)
result = translate_gene_ids(ids, species="human")

# Mouse
result = translate_gene_ids(ids, species="mouse")

# Supported species
species_list = ["human", "mouse", "rat", "zebrafish", "fly", "worm", "yeast"]
```

## Examples

### Gene Symbols to Multiple IDs

```python
from biodbs.translate import translate_gene_ids

genes = ["TP53", "BRCA1", "EGFR"]

# To Ensembl
ensembl = translate_gene_ids(
    genes,
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    return_dict=True
)

# To Entrez
entrez = translate_gene_ids(
    genes,
    from_type="external_gene_name",
    to_type="entrezgene_id",
    return_dict=True
)
```

### Ensembl to Multiple Databases

```python
ensembl_ids = ["ENSG00000141510", "ENSG00000012048"]

# To HGNC via Ensembl REST
hgnc = translate_gene_ids(
    ensembl_ids,
    from_type="ensembl_gene_id",
    to_type="HGNC",
    database="ensembl"
)

# To Entrez via BioMart
entrez = translate_gene_ids(
    ensembl_ids,
    from_type="ensembl_gene_id",
    to_type="entrezgene_id",
    database="biomart"
)
```
