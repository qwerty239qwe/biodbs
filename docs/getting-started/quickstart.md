# Quick Start

This guide will help you get started with biodbs in just a few minutes.

## The Four Namespaces

biodbs is organized into four main namespaces:

```python
# Data fetching - retrieve data from databases
from biodbs.fetch import uniprot_get_entry, pubchem_get_compound

# ID translation - map between identifier systems
from biodbs.translate import translate_gene_ids, translate_protein_ids

# Analysis - enrichment and statistics
from biodbs.analysis import ora_kegg, ora_go

# Knowledge graph - build and export graphs (requires optional dependencies)
from biodbs.graph import build_disease_graph, to_networkx
```

## Fetching Data

### Protein Data (UniProt)

```python
from biodbs.fetch import (
    uniprot_get_entry,
    uniprot_search_by_gene,
    gene_to_uniprot,
)

# Get a protein by UniProt accession
protein = uniprot_get_entry("P04637")  # TP53
print(f"Name: {protein.entries[0].protein_name}")
print(f"Gene: {protein.entries[0].gene_name}")
print(f"Organism: {protein.entries[0].organism_name}")

# Search by gene name
results = uniprot_search_by_gene("BRCA1", organism=9606)
for entry in results.entries:
    print(f"{entry.primaryAccession}: {entry.protein_name}")

# Map gene names to UniProt accessions
mapping = gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
print(mapping)
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}
```

### Chemical Data (PubChem)

```python
from biodbs.fetch import (
    pubchem_get_compound,
    pubchem_search_by_name,
    pubchem_get_properties,
)

# Get compound by CID
compound = pubchem_get_compound(2244)  # Aspirin
print(compound.results)

# Search by name
results = pubchem_search_by_name("caffeine")
cids = results.get_cids()

# Get specific properties
props = pubchem_get_properties(
    2244,
    properties=["MolecularWeight", "MolecularFormula", "CanonicalSMILES"]
)
```

### Gene Data (Ensembl/BioMart)

```python
from biodbs.fetch import (
    ensembl_lookup,
    biomart_get_genes,
    biomart_convert_ids,
)

# Lookup gene in Ensembl
gene = ensembl_lookup("ENSG00000141510")  # TP53

# Get genes via BioMart
genes = biomart_get_genes(["ENSG00000141510", "ENSG00000012048"])
df = genes.as_dataframe()

# Convert IDs
converted = biomart_convert_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id"
)
```

## ID Translation

Translate between different identifier systems:

```python
from biodbs.translate import (
    translate_gene_ids,
    translate_protein_ids,
    translate_chemical_ids,
    translate_gene_to_uniprot,
)

# Gene symbols to Ensembl IDs
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    return_dict=True
)
# {'TP53': 'ENSG00000141510', 'BRCA1': 'ENSG00000012048'}

# Gene symbols to UniProt accessions
mapping = translate_gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}

# UniProt to NCBI Gene IDs
result = translate_protein_ids(
    ["P04637", "P00533"],
    from_type="UniProtKB_AC-ID",
    to_type="GeneID",
    return_dict=True
)
# {'P04637': '7157', 'P00533': '1956'}

# Chemical name to PubChem CID
result = translate_chemical_ids(
    ["aspirin", "caffeine"],
    from_type="name",
    to_type="cid"
)
```

## Enrichment Analysis

Perform over-representation analysis:

```python
from biodbs.analysis import ora_kegg, ora_go

# KEGG pathway enrichment
result = ora_kegg(
    gene_list=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    organism="hsa",
    id_type="symbol"  # Auto-converts to Entrez IDs
)

# View results
print(result.summary())
df = result.as_dataframe()
print(df[["term_id", "term_name", "p_value", "overlap_genes"]])

# Get significant terms
significant = result.significant_terms(alpha=0.05)
```

## Output Formats

All fetch operations return data objects with multiple export options:

```python
from biodbs.fetch import uniprot_get_entries

data = uniprot_get_entries(["P04637", "P00533", "P38398"])

# As dictionary
records = data.as_dict()

# As pandas DataFrame
df = data.as_dataframe(engine="pandas")

# As Polars DataFrame
df = data.as_dataframe(engine="polars")

# Filter and transform
reviewed = data.filter_reviewed()
human_only = data.filter_by_organism(9606)

# Get specific data
accessions = data.get_accessions()
gene_names = data.get_gene_names()
sequences = data.get_sequences()
```

## Next Steps

- Learn about [core concepts](concepts.md)
- Explore specific databases in [Data Fetching](../fetch/index.md)
- See all [ID translation options](../translate/index.md)
- Perform [enrichment analysis](../analysis/index.md)
