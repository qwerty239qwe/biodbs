# biodbs

**biodbs** (Biological Database Services) is a Python library providing unified access to major biological and chemical databases with built-in support for ID translation and enrichment analysis.

## Features

- **Unified API** - Consistent interface across all supported databases
- **Four Namespaces** - Clear separation of concerns:
    - `biodbs.fetch` - Data retrieval from external databases
    - `biodbs.translate` - ID mapping between databases
    - `biodbs.analysis` - Statistical analysis (ORA, enrichment)
    - `biodbs.graph` - Knowledge graph building and export
- **Multiple Output Formats** - pandas/Polars DataFrames, CSV, JSON, SQLite
- **Enrichment Analysis** - Over-representation analysis with KEGG, GO, and EnrichR
- **Batch Processing** - Efficient handling of large queries with rate limiting
- **Type Safety** - Pydantic models for request/response validation

## Supported Databases

| Database | Description | Module |
|----------|-------------|--------|
| **UniProt** | Protein sequences, annotations, and ID mapping | `biodbs.fetch.uniprot` |
| **PubChem** | Chemical compounds, properties, and bioassays | `biodbs.fetch.pubchem` |
| **Ensembl REST** | Sequences, variants, homology, VEP, genomic features | `biodbs.fetch.ensembl` |
| **BioMart** | Gene annotations via Ensembl BioMart | `biodbs.fetch.biomart` |
| **KEGG** | Pathways, genes, compounds, biological systems | `biodbs.fetch.KEGG` |
| **ChEMBL** | Bioactive molecules, drug targets, pharmacology | `biodbs.fetch.ChEMBL` |
| **QuickGO** | Gene Ontology annotations and relationships | `biodbs.fetch.QuickGO` |
| **HPA** | Human Protein Atlas - protein expression | `biodbs.fetch.HPA` |
| **NCBI** | Gene information, taxonomy, and genome assemblies | `biodbs.fetch.NCBI` |
| **FDA** | Drug events, labels, recalls, device data | `biodbs.fetch.FDA` |
| **Reactome** | Pathway analysis and biological reactions | `biodbs.fetch.Reactome` |
| **Disease Ontology** | Disease terms and cross-references | `biodbs.fetch.DiseaseOntology` |

## Quick Example

```python
from biodbs.fetch import uniprot_get_entry, pubchem_get_compound
from biodbs.translate import translate_gene_to_uniprot
from biodbs.analysis import ora_kegg

# Fetch protein data
protein = uniprot_get_entry("P04637")  # TP53
print(protein.entries[0].protein_name)

# Translate gene names to UniProt
mapping = translate_gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}

# Perform pathway enrichment
result = ora_kegg(
    gene_list=["TP53", "BRCA1", "BRCA2", "ATM"],
    organism="hsa",
    id_type="symbol"
)
```

## Installation

```bash
pip install biodbs
```

Or with optional dependencies for the graph module:

```bash
pip install biodbs[graph]  # For NetworkX and RDF export support
```

## Getting Help

- [Getting Started Guide](getting-started/quickstart.md)
- [API Reference](api/fetch.md)
- [GitHub Issues](https://github.com/qwerty239qwe/biodbs/issues)

## License

MIT License
