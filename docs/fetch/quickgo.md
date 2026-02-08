# QuickGO

Access Gene Ontology data via the [QuickGO API](https://www.ebi.ac.uk/QuickGO/).

## Overview

QuickGO provides fast access to Gene Ontology (GO) data:

- **GO Terms** - Term definitions and relationships
- **Annotations** - Gene-GO associations
- **Hierarchy** - Parent/child relationships

## Quick Start

```python
from biodbs.fetch import (
    quickgo_search_terms,
    quickgo_get_terms,
    quickgo_search_annotations,
)

# Search GO terms
terms = quickgo_search_terms("apoptosis")
```

## GO Terms

### Search Terms

```python
from biodbs.fetch import quickgo_search_terms

terms = quickgo_search_terms("apoptosis")
terms = quickgo_search_terms("kinase activity")
```

### Get Terms

```python
from biodbs.fetch import quickgo_get_terms

terms = quickgo_get_terms(["GO:0006915", "GO:0008150"])
```

### Term Hierarchy

```python
from biodbs.fetch import quickgo_get_term_children, quickgo_get_term_ancestors

children = quickgo_get_term_children("GO:0008150")
ancestors = quickgo_get_term_ancestors("GO:0006915")
```

## Annotations

### Search Annotations

```python
from biodbs.fetch import quickgo_search_annotations

# By gene product
annotations = quickgo_search_annotations(
    gene_product_id="UniProtKB:P04637"
)

# By GO term
annotations = quickgo_search_annotations(
    go_id="GO:0006915"
)
```

### Download Annotations

```python
from biodbs.fetch import quickgo_download_annotations, quickgo_search_annotations_all

# Download in different formats
annotations = quickgo_download_annotations(
    gene_product_id="UniProtKB:P04637",
    format="tsv"
)

# Get all annotations (paginated)
all_annotations = quickgo_search_annotations_all(
    taxon_id=9606,
    aspect="biological_process"
)
```

### Gene Product Info

```python
from biodbs.fetch import quickgo_get_gene_product

product = quickgo_get_gene_product("UniProtKB:P04637")
```

## Using the Fetcher Class

```python
from biodbs.fetch.QuickGO import QuickGO_Fetcher

fetcher = QuickGO_Fetcher()
terms = fetcher.search_terms("apoptosis")
```

## Related Resources

- **[UniProt](uniprot.md)** - Get detailed protein information for GO-annotated gene products. QuickGO uses UniProt accessions for queries.
- **[Over-Representation Analysis](../analysis/ora.md)** - Perform GO term enrichment analysis with `ora_go()`.
- **[Knowledge Graphs](../graph/building.md)** - Build knowledge graphs from GO data with `build_go_graph()`.
- **[ID Translation](../translate/genes.md)** - Translate gene identifiers to UniProt format for QuickGO annotation lookups.
