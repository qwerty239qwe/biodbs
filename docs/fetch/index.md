# Data Fetching Overview

The `biodbs.fetch` module provides unified access to biological and chemical databases.

**Related sections:**

- [API Reference](../api/fetch.md) - Complete function and class documentation
- [ID Translation](../translate/index.md) - Convert between identifier systems
- [Analysis](../analysis/index.md) - Statistical analysis of fetched data
- [Knowledge Graph](../graph/index.md) - Build graphs from fetched data

## Available Databases

| Database | Description | Key Functions |
|----------|-------------|---------------|
| [UniProt](uniprot.md) | Protein sequences and annotations | `uniprot_get_entry`, `uniprot_search` |
| [PubChem](pubchem.md) | Chemical compounds and properties | `pubchem_get_compound`, `pubchem_search_by_name` |
| [Ensembl](ensembl.md) | Genomic data and sequences | `ensembl_lookup`, `ensembl_get_sequence` |
| [BioMart](biomart.md) | Gene annotations and queries | `biomart_get_genes`, `biomart_convert_ids` |
| [KEGG](kegg.md) | Pathways and biological systems | `kegg_get`, `kegg_find`, `kegg_link` |
| [ChEMBL](chembl.md) | Bioactive molecules and targets | `chembl_get_molecule`, `chembl_get_target` |
| [QuickGO](quickgo.md) | Gene Ontology annotations | `quickgo_search_terms`, `quickgo_get_terms` |
| [HPA](hpa.md) | Protein expression data | `hpa_get_gene`, `hpa_get_tissue_expression` |
| [NCBI](ncbi.md) | Gene and taxonomy data | `ncbi_get_gene`, `ncbi_symbol_to_id` |
| [FDA](fda.md) | Drug and device data | `fda_drug_events`, `fda_drug_labels` |
| [Reactome](reactome.md) | Pathway data and analysis | `reactome_analyze`, `reactome_get_pathway_genes` |
| [EnrichR](enrichr.md) | Gene set enrichment | `enrichr_analyze`, `enrichr_get_libraries` |
| [Disease Ontology](disease-ontology.md) | Disease terms | `do_get_term`, `do_search` |

## Quick Start

### Import Convention

```python
# Import specific functions
from biodbs.fetch import uniprot_get_entry, pubchem_get_compound

# Or import fetcher classes
from biodbs.fetch.uniprot import UniProt_Fetcher
from biodbs.fetch.pubchem import PubChem_Fetcher
```

### Basic Usage Pattern

All fetch functions follow a similar pattern:

```python
from biodbs.fetch import uniprot_get_entry

# Fetch data
data = uniprot_get_entry("P04637")

# Access results
for entry in data.entries:
    print(entry.primaryAccession)
    print(entry.protein_name)

# Convert to DataFrame
df = data.as_dataframe()

# Get as dictionary
records = data.as_dict()
```

### Batch Operations

Fetch multiple items efficiently:

```python
from biodbs.fetch import uniprot_get_entries

# Batch retrieval
entries = uniprot_get_entries(["P04637", "P00533", "P38398"])

# Results combined in single response
print(f"Found {len(entries)} entries")
df = entries.as_dataframe()
```

### Search Operations

Most databases support search:

```python
from biodbs.fetch import uniprot_search, pubchem_search_by_name

# UniProt search with query syntax
results = uniprot_search(
    "gene:BRCA1 AND organism_id:9606 AND reviewed:true",
    size=100
)

# PubChem search by name
compounds = pubchem_search_by_name("aspirin")
```

## Output Formats

All data containers support multiple output formats:

=== "pandas"

    ```python
    df = data.as_dataframe(engine="pandas")
    ```

=== "Polars"

    ```python
    df = data.as_dataframe(engine="polars")
    ```

=== "Dictionary"

    ```python
    records = data.as_dict()
    ```

=== "JSON"

    ```python
    import json
    json_str = json.dumps(data.as_dict())
    ```

## Error Handling

```python
from biodbs.fetch import uniprot_get_entry

try:
    entry = uniprot_get_entry("P04637")
except ConnectionError as e:
    # API unavailable or rate limited
    print(f"Connection error: {e}")
except ValueError as e:
    # Invalid input
    print(f"Invalid input: {e}")
```

## Rate Limiting

All fetchers automatically handle rate limiting:

- Requests are throttled to respect API limits
- Automatic retry with exponential backoff on 429 errors
- Configurable via the `RateLimiter` class

```python
from biodbs.fetch._rate_limit import get_rate_limiter

limiter = get_rate_limiter()
# Rate limits are set per-host automatically
```

## Using Fetcher Classes

For more control, use [fetcher classes](../api/fetch.md#fetcher-classes) directly:

```python
from biodbs.fetch.uniprot import UniProt_Fetcher

# Create fetcher
fetcher = UniProt_Fetcher()

# Access all methods
entry = fetcher.get_entry("P04637")
results = fetcher.search("gene:TP53")
mapping = fetcher.gene_to_uniprot(["TP53", "BRCA1"])

# Batch operations with concurrency
sequences = fetcher.get_sequences(["P04637", "P00533"])
```

## Next Steps

- [UniProt Guide](uniprot.md) - Detailed UniProt fetching examples
- [PubChem Guide](pubchem.md) - Chemical compound data
- [ID Translation](../translate/index.md) - Map between identifier systems
- [ORA Analysis](../analysis/ora.md) - Pathway enrichment analysis
