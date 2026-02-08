# UniProt

Access protein sequences, annotations, and ID mapping via the [UniProt REST API](https://www.uniprot.org/help/api).

## Overview

UniProt (Universal Protein Resource) is the most comprehensive protein sequence and annotation database. biodbs provides full access to:

- **Entry Retrieval** - Get protein entries by accession
- **Search** - Query UniProtKB with powerful search syntax
- **ID Mapping** - Map between UniProt and other databases
- **Batch Operations** - Efficiently process large lists

## Quick Start

```python
from biodbs.fetch import (
    uniprot_get_entry,
    uniprot_get_entries,
    uniprot_search,
    uniprot_search_by_gene,
    gene_to_uniprot,
    uniprot_to_gene,
    uniprot_get_sequences,
    uniprot_map_ids,
)

# Get a single protein
entry = uniprot_get_entry("P04637")
print(entry.entries[0].protein_name)  # "Cellular tumor antigen p53"
```

## Entry Retrieval

### Get Single Entry

```python
from biodbs.fetch import uniprot_get_entry

entry = uniprot_get_entry("P04637")  # TP53

# Access entry data
protein = entry.entries[0]
print(f"Accession: {protein.primaryAccession}")
print(f"Entry Name: {protein.uniProtkbId}")
print(f"Protein: {protein.protein_name}")
print(f"Gene: {protein.gene_name}")
print(f"Organism: {protein.organism_name}")
print(f"Tax ID: {protein.tax_id}")
print(f"Sequence Length: {protein.sequence_length}")
print(f"Is Reviewed: {protein.is_reviewed}")
```

### Get Multiple Entries

```python
from biodbs.fetch import uniprot_get_entries

entries = uniprot_get_entries(["P04637", "P00533", "P38398"])

# Iterate over entries
for protein in entries.entries:
    print(f"{protein.primaryAccession}: {protein.gene_name}")

# Convert to DataFrame
df = entries.as_dataframe()
print(df[["accession", "gene_name", "protein_name", "organism"]])
```

## Searching UniProt

### Basic Search

```python
from biodbs.fetch import uniprot_search

# Search with UniProt query syntax
results = uniprot_search(
    "gene:TP53 AND organism_id:9606 AND reviewed:true",
    size=25
)

print(f"Found {len(results)} entries")
for entry in results.entries:
    print(f"{entry.primaryAccession}: {entry.protein_name}")
```

### Search by Gene Name

```python
from biodbs.fetch import uniprot_search_by_gene

# Search for human BRCA1
results = uniprot_search_by_gene(
    "BRCA1",
    organism=9606,      # Human (NCBI taxonomy ID)
    reviewed_only=True  # Only Swiss-Prot entries
)

print(results.entries[0].primaryAccession)  # P38398
```

### Search by Keyword

```python
from biodbs.fetch import uniprot_search_by_keyword

# Find kinases in human
results = uniprot_search_by_keyword(
    "kinase",
    organism=9606,
    reviewed_only=True,
    size=100
)
```

### Query Syntax

UniProt supports a powerful query syntax:

| Field | Example | Description |
|-------|---------|-------------|
| `gene` | `gene:TP53` | Gene name |
| `organism_id` | `organism_id:9606` | NCBI taxonomy ID |
| `reviewed` | `reviewed:true` | Swiss-Prot only |
| `keyword` | `keyword:kinase` | UniProt keyword |
| `accession` | `accession:P04637` | UniProt accession |
| `protein_name` | `protein_name:p53` | Protein name |
| `length` | `length:[1 TO 100]` | Sequence length range |

Combine with `AND`, `OR`, `NOT`:

```python
# Complex query
results = uniprot_search(
    "(gene:BRCA1 OR gene:BRCA2) AND organism_id:9606 AND reviewed:true"
)
```

## Gene to UniProt Mapping

### Map Gene Names to Accessions

```python
from biodbs.fetch import gene_to_uniprot

mapping = gene_to_uniprot(
    ["TP53", "BRCA1", "EGFR", "MYC"],
    organism=9606,        # Human
    reviewed_only=True    # Swiss-Prot entries only
)

print(mapping)
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533', 'MYC': 'P01106'}
```

### Map Accessions to Gene Names

```python
from biodbs.fetch import uniprot_to_gene

mapping = uniprot_to_gene(["P04637", "P00533", "P38398"])

print(mapping)
# {'P04637': 'TP53', 'P00533': 'EGFR', 'P38398': 'BRCA1'}
```

## ID Mapping

Map between UniProt and other databases:

```python
from biodbs.fetch import uniprot_map_ids

# UniProt to NCBI Gene ID
mapping = uniprot_map_ids(
    ["P04637", "P00533"],
    from_db="UniProtKB_AC-ID",
    to_db="GeneID"
)
print(mapping)
# {'P04637': ['7157'], 'P00533': ['1956']}

# UniProt to Ensembl
mapping = uniprot_map_ids(
    ["P04637"],
    from_db="UniProtKB_AC-ID",
    to_db="Ensembl"
)

# UniProt to PDB
mapping = uniprot_map_ids(
    ["P04637"],
    from_db="UniProtKB_AC-ID",
    to_db="PDB"
)
```

### Supported Databases

| Database Code | Description |
|---------------|-------------|
| `UniProtKB_AC-ID` | UniProt accession |
| `UniProtKB` | UniProt entry |
| `Gene_Name` | Gene symbol |
| `GeneID` | NCBI Gene ID |
| `Ensembl` | Ensembl gene ID |
| `Ensembl_Protein` | Ensembl protein ID |
| `RefSeq_Protein` | RefSeq protein ID |
| `PDB` | PDB structure ID |
| `STRING` | STRING database ID |
| `ChEMBL` | ChEMBL target ID |

## Sequences

### Get Protein Sequences

```python
from biodbs.fetch import uniprot_get_sequences

sequences = uniprot_get_sequences(["P04637", "P00533"])

for acc, seq in sequences.items():
    print(f"{acc}: {seq[:50]}...")
```

### Export as FASTA

```python
from biodbs.fetch import uniprot_get_entries

entries = uniprot_get_entries(["P04637", "P00533"])
fasta = entries.to_fasta()
print(fasta)
```

## Working with Results

### UniProtFetchedData Methods

```python
entries = uniprot_get_entries(["P04637", "P00533", "P38398"])

# Get lists
accessions = entries.get_accessions()
gene_names = entries.get_gene_names()
protein_names = entries.get_protein_names()

# Get specific entry
tp53 = entries.get_entry("P04637")
brca1 = entries.get_entry_by_gene("BRCA1")

# Filter
reviewed = entries.filter_reviewed()
human = entries.filter_by_organism(9606)

# Mappings
acc_to_gene = entries.to_gene_mapping()
gene_to_acc = entries.to_accession_mapping()
```

### Entry Properties

```python
entry = uniprot_get_entry("P04637").entries[0]

# Basic info
entry.primaryAccession      # "P04637"
entry.uniProtkbId          # "P53_HUMAN"
entry.protein_name         # "Cellular tumor antigen p53"
entry.gene_name            # "TP53"
entry.gene_names           # ["TP53", "P53"]

# Organism
entry.organism_name        # "Homo sapiens"
entry.tax_id               # 9606

# Sequence
entry.sequence_length      # 393
entry.sequence.value       # "MEEPQSDPSV..."

# Status
entry.is_reviewed          # True (Swiss-Prot)

# Annotations
entry.get_function()       # Function description
entry.get_subcellular_location()

# Cross-references
entry.pdb_ids              # ["1A1U", "1AIE", ...]
entry.ensembl_gene_id      # "ENSG00000141510"
entry.entrez_gene_id       # "7157"
entry.get_xref("GO")       # First GO term
entry.get_all_xrefs("GO")  # All GO terms
```

## Using the Fetcher Class

For more control, use the fetcher class directly:

```python
from biodbs.fetch.uniprot import UniProt_Fetcher

fetcher = UniProt_Fetcher()

# All convenience functions are available as methods
entry = fetcher.get_entry("P04637")
results = fetcher.search("gene:TP53")
results = fetcher.search_by_gene("BRCA1", organism=9606)

# Additional methods
results = fetcher.search_by_organism(9606, reviewed_only=True)
all_results = fetcher.search_all("organism_id:9606", max_results=10000)
```

## Rate Limiting

UniProt API has a rate limit of ~10 requests/second. biodbs handles this automatically:

```python
# Large batch operations are rate-limited
mapping = gene_to_uniprot(large_gene_list)  # Concurrent with rate limiting
```

## Examples

### Find All Human Kinases

```python
from biodbs.fetch import uniprot_search

kinases = uniprot_search(
    "keyword:kinase AND organism_id:9606 AND reviewed:true",
    size=500
)

df = kinases.as_dataframe()
print(f"Found {len(df)} human kinases")
```

### Get Protein Info for Gene List

```python
from biodbs.fetch import gene_to_uniprot, uniprot_get_entries

genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]

# Map to UniProt
mapping = gene_to_uniprot(genes)

# Get full entries
entries = uniprot_get_entries(list(mapping.values()))

# Export to DataFrame
df = entries.as_dataframe()
df.to_csv("proteins.csv", index=False)
```

### Cross-Reference Lookup

```python
from biodbs.fetch import uniprot_map_ids

proteins = ["P04637", "P00533", "P38398"]

# Get all PDB structures
pdb_mapping = uniprot_map_ids(proteins, "UniProtKB_AC-ID", "PDB")

for protein, pdb_ids in pdb_mapping.items():
    print(f"{protein}: {len(pdb_ids)} structures")
```

## Related Resources

- **[ChEMBL](chembl.md)** - Find bioactivity data and drug information for UniProt proteins. Use `uniprot_map_ids()` with `to_db="ChEMBL"` to get ChEMBL target IDs.
- **[Ensembl](ensembl.md)** - Get genomic information (transcripts, variants) for UniProt proteins.
- **[QuickGO](quickgo.md)** - Retrieve Gene Ontology annotations for UniProt accessions.
- **[Reactome](reactome.md)** - Find pathways and reactions involving UniProt proteins.
- **[ID Translation](../translate/proteins.md)** - Translate between UniProt accessions and other protein identifiers (Ensembl, RefSeq, PDB).
