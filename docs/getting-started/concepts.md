# Core Concepts

This page explains the key concepts and design patterns used in biodbs.

## Architecture Overview

biodbs follows a layered architecture:

```
┌──────────────────────────────────────────────────────────────────────┐
│                          User Interface                               │
│   biodbs.fetch  │  biodbs.translate  │  biodbs.analysis │ biodbs.graph │
├──────────────────────────────────────────────────────────────────────┤
│                     Convenience Functions                             │
│           uniprot_get_entry(), translate_gene_ids()                  │
├──────────────────────────────────────────────────────────────────────┤
│                       Fetcher Classes                                 │
│       UniProt_Fetcher, PubChem_Fetcher, Ensembl_Fetcher              │
├──────────────────────────────────────────────────────────────────────┤
│                      Data Models (Pydantic)                           │
│           UniProtEntry, CompoundData, GeneData                       │
├──────────────────────────────────────────────────────────────────────┤
│                 Rate Limiting & Retry Logic                           │
│                     request_with_retry()                              │
└──────────────────────────────────────────────────────────────────────┘
```

## Fetcher Classes vs Convenience Functions

biodbs provides two ways to access each database:

### Convenience Functions (Recommended)

Simple, stateless functions for common operations:

```python
from biodbs.fetch import uniprot_get_entry, uniprot_search

# Simple and direct
entry = uniprot_get_entry("P04637")
results = uniprot_search("gene:TP53 AND organism_id:9606")
```

### Fetcher Classes

Object-oriented interface for more control:

```python
from biodbs.fetch.uniprot import UniProt_Fetcher

# Create fetcher instance
fetcher = UniProt_Fetcher()

# Use methods
entry = fetcher.get_entry("P04637")
results = fetcher.search_by_gene("TP53", organism=9606)

# Batch operations with rate limiting
mapping = fetcher.gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
```

## Data Containers

All fetch operations return typed data containers that provide:

### Common Methods

```python
# Get raw results
data.results          # List of result objects

# Convert to different formats
data.as_dict()        # List of dictionaries
data.as_dataframe()   # pandas DataFrame
data.as_dataframe(engine="polars")  # Polars DataFrame

# Metadata
len(data)             # Number of results
data.summary()        # Text summary
```

### Database-Specific Methods

Each data container has specialized methods:

```python
# UniProtFetchedData
data.get_accessions()
data.get_gene_names()
data.get_sequences()
data.filter_reviewed()
data.to_fasta()

# PubChemFetchedData
data.get_cids()
data.get_smiles()
data.get_properties()
```

## Rate Limiting

biodbs automatically handles rate limiting for all APIs:

```python
from biodbs.fetch._rate_limit import get_rate_limiter

# View current rate limits
limiter = get_rate_limiter()
print(limiter.get_rate("rest.uniprot.org"))  # 10 requests/sec
```

### Per-Database Limits

| Database | Rate Limit | Notes |
|----------|------------|-------|
| UniProt | 10 req/s | Generous for programmatic access |
| PubChem | 5 req/s | Throttled for heavy usage |
| Ensembl | 15 req/s | Higher for registered users |
| NCBI | 3-10 req/s | Depends on API key |
| ChEMBL | 10 req/s | |
| KEGG | 10 req/s | |

## Error Handling

biodbs uses standard Python exceptions:

```python
from biodbs.fetch import uniprot_get_entry

try:
    entry = uniprot_get_entry("INVALID_ID")
except ConnectionError as e:
    print(f"API error: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
```

### Automatic Retries

API calls automatically retry on transient failures:

- **429 Too Many Requests** - Waits and retries with backoff
- **500-504 Server Errors** - Retries up to 3 times
- **Timeouts** - Retries with increased timeout

## Pydantic Models

All data is validated using Pydantic models:

```python
from biodbs.data.uniprot import UniProtEntry

# Models provide type hints and validation
entry: UniProtEntry = data.entries[0]

# Access properties
print(entry.primaryAccession)  # str
print(entry.gene_name)         # Optional[str]
print(entry.tax_id)            # Optional[int]

# Models are serializable
entry.model_dump()             # Dict
entry.model_dump_json()        # JSON string
```

## Batch Processing

For large queries, use batch methods:

```python
from biodbs.fetch.uniprot import UniProt_Fetcher

fetcher = UniProt_Fetcher()

# Batch retrieval (uses search with OR query)
entries = fetcher.get_entries(["P04637", "P00533", "P38398", ...])

# Concurrent gene mapping (uses schedule_process)
mapping = fetcher.gene_to_uniprot(large_gene_list)

# Paginated search
all_results = fetcher.search_all(
    query="organism_id:9606 AND reviewed:true",
    max_results=10000
)
```

## Caching

biodbs supports optional caching for expensive operations:

```python
from biodbs.data.uniprot import UniProtDataManager

# Create data manager with caching
manager = UniProtDataManager(
    storage_path="./cache",
    cache_expiry_days=7
)

# Save fetched data
manager.save_protein_data(data, "proteins.json")

# Load cached data
cached = manager.load("proteins.json")
```

## Next Steps

- Explore specific databases: [Data Fetching](../fetch/index.md)
- Learn about ID translation: [ID Translation](../translate/index.md)
- Perform enrichment analysis: [Analysis](../analysis/index.md)
- Build knowledge graphs: [Knowledge Graph](../graph/index.md)
