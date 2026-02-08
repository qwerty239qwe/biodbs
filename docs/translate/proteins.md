# Protein ID Translation

Translate between protein identifiers using UniProt ID mapping.

## Quick Start

```python
from biodbs.translate import (
    translate_protein_ids,
    translate_gene_to_uniprot,
    translate_uniprot_to_gene,
)

# Gene symbols to UniProt
mapping = translate_gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}
```

## translate_gene_to_uniprot

Map gene names to UniProt accessions.

```python
from biodbs.translate import translate_gene_to_uniprot

mapping = translate_gene_to_uniprot(
    gene_names=["TP53", "BRCA1", "EGFR"],
    organism=9606,          # Human (NCBI taxonomy ID)
    reviewed_only=True,     # Swiss-Prot entries only
    return_dict=True
)
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gene_names` | List[str] | required | Gene names/symbols |
| `organism` | int | 9606 | NCBI taxonomy ID |
| `reviewed_only` | bool | True | Only Swiss-Prot entries |
| `return_dict` | bool | True | Return dict or DataFrame |

## translate_uniprot_to_gene

Map UniProt accessions to gene names.

```python
from biodbs.translate import translate_uniprot_to_gene

mapping = translate_uniprot_to_gene(
    accessions=["P04637", "P38398", "P00533"],
    return_dict=True
)
# {'P04637': 'TP53', 'P38398': 'BRCA1', 'P00533': 'EGFR'}
```

## translate_protein_ids

General-purpose protein ID translation via UniProt ID mapping.

```python
from biodbs.translate import translate_protein_ids

# UniProt to NCBI Gene ID
result = translate_protein_ids(
    ids=["P04637", "P00533"],
    from_type="UniProtKB_AC-ID",
    to_type="GeneID",
    return_dict=True
)
# {'P04637': '7157', 'P00533': '1956'}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ids` | List[str] | required | IDs to translate |
| `from_type` | str | required | Source ID type |
| `to_type` | str or List[str] | required | Target ID type(s). Pass a list for multiple targets. |
| `organism` | int | 9606 | NCBI taxonomy ID (for Gene_Name mapping) |
| `return_dict` | bool | False | Return dict instead of DataFrame |

### Multiple Target Types

Get multiple ID types in one call:

```python
result = translate_protein_ids(
    ["P04637", "P00533"],
    from_type="UniProtKB_AC-ID",
    to_type=["GeneID", "Ensembl", "Gene_Name"],
)
#      from  GeneID           Ensembl Gene_Name
# 0  P04637    7157  ENSG00000141510      TP53
# 1  P00533    1956  ENSG00000146648      EGFR

# As dict with nested structure
result_dict = translate_protein_ids(
    ["P04637", "P00533"],
    from_type="UniProtKB_AC-ID",
    to_type=["GeneID", "Ensembl"],
    return_dict=True
)
# {'P04637': {'GeneID': '7157', 'Ensembl': 'ENSG00000141510'}, ...}
```

### Supported ID Types

| ID Type | Description | Example |
|---------|-------------|---------|
| `UniProtKB_AC-ID` | UniProt accession | P04637 |
| `Gene_Name` | Gene symbol | TP53 |
| `GeneID` | NCBI Gene ID | 7157 |
| `Ensembl` | Ensembl gene ID | ENSG00000141510 |
| `Ensembl_Protein` | Ensembl protein ID | ENSP00000269305 |
| `RefSeq_Protein` | RefSeq protein ID | NP_000537.3 |
| `PDB` | PDB structure ID | 1TUP |
| `STRING` | STRING database ID | 9606.ENSP00000269305 |
| `ChEMBL` | ChEMBL target ID | CHEMBL3927 |

### Examples

```python
# Gene names to UniProt
result = translate_protein_ids(
    ["TP53", "EGFR"],
    from_type="Gene_Name",
    to_type="UniProtKB"
)

# UniProt to Ensembl
result = translate_protein_ids(
    ["P04637", "P00533"],
    from_type="UniProtKB_AC-ID",
    to_type="Ensembl"
)

# UniProt to PDB
result = translate_protein_ids(
    ["P04637"],
    from_type="UniProtKB_AC-ID",
    to_type="PDB"
)
```

## Convenience Functions

### UniProt to PDB

```python
from biodbs.translate import translate_uniprot_to_pdb

mapping = translate_uniprot_to_pdb(["P04637"])
# {'P04637': ['1A1U', '1AIE', '1C26', ...]}
```

### UniProt to Ensembl

```python
from biodbs.translate import translate_uniprot_to_ensembl

mapping = translate_uniprot_to_ensembl(["P04637", "P00533"])
# {'P04637': 'ENSG00000141510', 'P00533': 'ENSG00000146648'}
```

### UniProt to RefSeq

```python
from biodbs.translate import translate_uniprot_to_refseq

mapping = translate_uniprot_to_refseq(["P04637"])
# {'P04637': ['NP_000537.3', ...]}
```

## Organism Support

Specify organism for gene name to UniProt mapping:

```python
# Human (default)
mapping = translate_gene_to_uniprot(["TP53"], organism=9606)

# Mouse
mapping = translate_gene_to_uniprot(["Trp53"], organism=10090)

# Common taxonomy IDs
organisms = {
    "human": 9606,
    "mouse": 10090,
    "rat": 10116,
    "zebrafish": 7955,
    "fly": 7227,
    "yeast": 559292,
}
```

## Examples

### Build Protein Annotation Table

```python
from biodbs.translate import (
    translate_gene_to_uniprot,
    translate_uniprot_to_ensembl,
    translate_uniprot_to_pdb,
)
import pandas as pd

genes = ["TP53", "BRCA1", "EGFR", "MYC"]

# Get UniProt accessions
uniprot = translate_gene_to_uniprot(genes)

# Get Ensembl IDs
accessions = list(uniprot.values())
ensembl = translate_uniprot_to_ensembl(accessions)

# Get PDB structures
pdb = translate_uniprot_to_pdb(accessions)

# Build table
data = []
for gene in genes:
    acc = uniprot.get(gene)
    if acc:
        data.append({
            "gene": gene,
            "uniprot": acc,
            "ensembl": ensembl.get(acc),
            "pdb_count": len(pdb.get(acc, [])),
        })

df = pd.DataFrame(data)
```

### Cross-Database ID Mapping

```python
from biodbs.translate import translate_protein_ids

proteins = ["P04637", "P00533", "P38398"]

# Get all target types in one call (recommended)
result = translate_protein_ids(
    proteins,
    from_type="UniProtKB_AC-ID",
    to_type=["GeneID", "Ensembl", "RefSeq_Protein", "Gene_Name"],
)
#      from  GeneID           Ensembl  RefSeq_Protein Gene_Name
# 0  P04637    7157  ENSG00000141510     NP_000537.3      TP53
# 1  P00533    1956  ENSG00000146648     NP_005219.2      EGFR
# 2  P38398     672  ENSG00000012048     NP_009225.1     BRCA1

# Or make separate calls (less efficient)
gene_ids = translate_protein_ids(
    proteins, "UniProtKB_AC-ID", "GeneID", return_dict=True
)
ensembl_ids = translate_protein_ids(
    proteins, "UniProtKB_AC-ID", "Ensembl", return_dict=True
)
```

## Related Resources

### Backend Data Source

- **[UniProt](../fetch/uniprot.md)** - Full UniProt API access, including `uniprot_map_ids()` for ID mapping.

### Other Translation

- **[Gene Translation](genes.md)** - Translate gene symbols to Ensembl, Entrez, etc.
- **[Chemical Translation](chemicals.md)** - Translate chemical identifiers.

### Use Cases

- **[ChEMBL](../fetch/chembl.md)** - Use ChEMBL target IDs from `translate_protein_ids()`.
- **[QuickGO](../fetch/quickgo.md)** - Use UniProt accessions for GO annotation lookups.
- **[Over-Representation Analysis](../analysis/ora.md)** - Translate protein IDs before enrichment.
