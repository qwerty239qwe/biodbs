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

Use [`uniprot_get_entry`](../api/fetch.md#uniprot_get_entry) to fetch protein data, [`uniprot_search_by_gene`](../api/fetch.md#uniprot_search_by_gene) to search by gene name, and [`gene_to_uniprot`](../api/fetch.md#gene_to_uniprot) to map gene symbols.

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

For more control, use the [`UniProt_Fetcher`](../api/fetch.md#uniprot_fetcher) class directly.

### Chemical Data (PubChem)

Use [`pubchem_get_compound`](../api/fetch.md#pubchem_get_compound) to get compound data, [`pubchem_search_by_name`](../api/fetch.md#pubchem_search_by_name) to search by name, and [`pubchem_get_properties`](../api/fetch.md#pubchem_get_properties) to get specific properties.

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

For more control, use the [`PubChem_Fetcher`](../api/fetch.md#pubchem_fetcher) class directly.

### Gene Data (Ensembl/BioMart)

Use [`ensembl_lookup`](../api/fetch.md#ensembl_lookup) for gene lookups, [`biomart_get_genes`](../api/fetch.md#biomart_get_genes) for batch queries, and [`biomart_convert_ids`](../api/fetch.md#biomart_convert_ids) for ID conversion.

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

For more control, use the [`Ensembl_Fetcher`](../api/fetch.md#ensembl_fetcher) or [`BioMart_Fetcher`](../api/fetch.md#biomart_fetcher) classes directly.

## ID Translation

Translate between different identifier systems using functions from the [`translate`](../api/translate.md) module:

- [`translate_gene_ids`](../api/translate.md#translate_gene_ids) - Gene ID conversion via BioMart
- [`translate_protein_ids`](../api/translate.md#translate_protein_ids) - Protein ID mapping via UniProt
- [`translate_chemical_ids`](../api/translate.md#translate_chemical_ids) - Chemical ID translation via PubChem
- [`translate_gene_to_uniprot`](../api/translate.md#translate_gene_to_uniprot) - Gene symbols to UniProt accessions

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

Perform over-representation analysis using the [`analysis`](../api/analysis.md) module:

- [`ora_kegg`](../api/analysis.md#ora_kegg) - KEGG pathway enrichment
- [`ora_go`](../api/analysis.md#ora_go) - Gene Ontology enrichment
- [`ora_reactome`](../api/analysis.md#ora_reactome) - Reactome pathway enrichment
- [`ORAResult`](../api/analysis.md#oraresult) - Result container with filtering and export methods

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
- Build knowledge graphs in [Graph module](../graph/index.md)
