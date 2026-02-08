# biodbs

[![PyPI version](https://img.shields.io/pypi/v/biodbs)](https://pypi.org/project/biodbs/)
[![Python versions](https://img.shields.io/pypi/pyversions/biodbs)](https://pypi.org/project/biodbs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/qwerty239qwe/biodbs/graph/badge.svg?token=ZQNWLVJV35)](https://codecov.io/gh/qwerty239qwe/biodbs)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://qwerty239qwe.github.io/biodbs/)

**biodbs** (Biological Database Services) is a Python library providing unified access to major biological and chemical databases with built-in support for ID translation and enrichment analysis.

## Features

- **Unified API**: Consistent interface across all supported databases
- **Four Namespaces**: Clear separation of concerns
  - `biodbs.fetch` - Data retrieval from external databases
  - `biodbs.translate` - ID mapping between databases
  - `biodbs.analysis` - Statistical analysis (ORA, enrichment)
  - `biodbs.graph` - Knowledge graph building and export
- **Multiple Output Formats**: pandas/Polars DataFrames, CSV, JSON, SQLite
- **Enrichment Analysis**: Over-representation analysis with KEGG, GO, and EnrichR
- **Batch Processing**: Efficient handling of large queries
- **Type Safety**: Pydantic models for request/response validation

## Supported Databases

| Database | Description |
|----------|-------------|
| **PubChem** | Chemical compounds, properties, and bioassays |
| **BioMart** | Gene annotations via Ensembl BioMart |
| **Ensembl REST** | Sequences, variants, homology, VEP, genomic features |
| **ChEMBL** | Bioactive molecules, drug targets, pharmacology |
| **KEGG** | Pathways, genes, compounds, biological systems |
| **QuickGO** | Gene Ontology annotations and relationships |
| **HPA** | Human Protein Atlas - protein expression |
| **FDA** | Drug events, labels, recalls, device data |
| **UniProt** | Protein sequences, annotations, and ID mapping |
| **NCBI** | Gene information, taxonomy, and genome assemblies |
| **Reactome** | Pathway analysis and biological reactions |
| **Disease Ontology** | Disease terms and cross-references |

## Installation

```bash
pip install biodbs
```

or with [uv](https://docs.astral.sh/uv/):

```bash
uv add biodbs
```

## Quick Start

### Namespace Overview

```python
# Data fetching - low-level API wrappers
from biodbs.fetch import pubchem_get_compound, kegg_get, ensembl_lookup, uniprot_get_entry

# ID translation - mapping between databases
from biodbs.translate import translate_gene_ids, translate_chemical_ids, translate_protein_ids

# Analysis - enrichment and statistics
from biodbs.analysis import ora_kegg, ora_go, ora_enrichr

# Knowledge graph - building and exporting biological knowledge graphs
from biodbs.graph import build_disease_graph, build_go_graph, to_networkx, to_json_ld
```

### Fetching Data

```python
from biodbs.fetch import (
    pubchem_get_compound,
    biomart_get_genes,
    chembl_search_molecules,
    kegg_get,
    quickgo_search_terms,
    hpa_get_tissue_expression,
    fda_drug_events,
    ensembl_lookup,
    uniprot_get_entry,
    uniprot_search_by_gene,
)

# PubChem - Get compound information
compound = pubchem_get_compound(2244)  # Aspirin
print(compound.results)
# [{'CID': 2244, 'MolecularFormula': 'C9H8O4', 'MolecularWeight': '180.16', ...}]

# BioMart - Get gene information
genes = biomart_get_genes(["ENSG00000141510", "ENSG00000012048"])
df = genes.as_dataframe()
#   ensembl_gene_id  external_gene_name chromosome_name  ...
# 0  ENSG00000141510               TP53              17  ...
# 1  ENSG00000012048              BRCA1              17  ...

# ChEMBL - Search for molecules
molecules = chembl_search_molecules("aspirin")
# FetchedData(source='chembl', total_results=1, ...)

# KEGG - Get pathway information
pathway = kegg_get("hsa00010")  # Glycolysis pathway
# FetchedData(source='kegg', total_results=1, ...)

# QuickGO - Search GO terms
terms = quickgo_search_terms("apoptosis")
# FetchedData(source='quickgo', total_results=25, ...)

# HPA - Get tissue expression
expression = hpa_get_tissue_expression("TP53")
# FetchedData(source='hpa', total_results=1, ...)

# FDA - Search drug adverse events
events = fda_drug_events(search="aspirin", limit=10)
# FetchedData(source='fda', total_results=10, ...)

# Ensembl - Lookup gene and get sequence
gene = ensembl_lookup("ENSG00000141510")  # TP53
# FetchedData(source='ensembl', total_results=1, ...)

# UniProt - Get protein entry
protein = uniprot_get_entry("P04637")  # TP53 protein
print(protein.entries[0].protein_name)
# "Cellular tumor antigen p53"

# UniProt - Search by gene name
results = uniprot_search_by_gene("BRCA1", organism=9606)
# FetchedData(source='uniprot', total_results=1, ...)
```

### ID Translation

```python
from biodbs.translate import (
    translate_gene_ids,
    translate_chemical_ids,
    translate_protein_ids,
    translate_gene_to_uniprot,
    translate_uniprot_to_gene,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
)

# Gene symbols to Ensembl IDs
result = translate_gene_ids(
    ["TP53", "BRCA1", "EGFR"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id"
)
# FetchedData with columns: external_gene_name, ensembl_gene_id

# Compound names to PubChem CIDs
result = translate_chemical_ids(
    ["aspirin", "ibuprofen"],
    from_type="name",
    to_type="cid"
)
# FetchedData with columns: name, cid

# Gene symbols to UniProt accessions
mapping = translate_gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}

# UniProt to NCBI Gene IDs
mapping = translate_protein_ids(
    ["P04637", "P00533"],
    from_type="UniProtKB_AC-ID",
    to_type="GeneID",
    return_dict=True
)
# {'P04637': '7157', 'P00533': '1956'}

# Get as dictionary
mapping = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    return_dict=True
)
# {'TP53': 'ENSG00000141510', 'BRCA1': 'ENSG00000012048'}

# Cross-database translation
chembl_to_pubchem = translate_chembl_to_pubchem(["CHEMBL25", "CHEMBL521"])
# {'CHEMBL25': 2244, 'CHEMBL521': 2519}
pubchem_to_chembl = translate_pubchem_to_chembl([2244, 2519])
# {2244: 'CHEMBL25', 2519: 'CHEMBL521'}
```

### Over-Representation Analysis (ORA)

Perform pathway and gene set enrichment analysis:

```python
from biodbs.analysis import ora_kegg, ora_go, ora_enrichr, ORAResult

# KEGG pathway enrichment
result = ora_kegg(
    gene_list=["7157", "672", "675", "580", "581"],  # Entrez IDs
    organism="hsa",
    id_type="entrez"
)
print(result.summary())
# ORA Results: 5 terms tested, 3 significant (q < 0.05)

# View significant pathways
significant = result.significant_terms(alpha=0.05)
df = significant.as_dataframe()
print(df[["term_id", "term_name", "p_value", "q_value", "overlap_genes"]])
#      term_id              term_name    p_value    q_value overlap_genes
# 0  hsa05200        Pathways in cancer  0.00012    0.003    [7157, 672]
# 1  hsa04115  p53 signaling pathway    0.00045    0.008    [7157]

# GO enrichment (requires UniProt IDs)
result = ora_go(
    gene_list=["P04637", "P38398", "P51587"],  # UniProt accessions
    taxon_id=9606,  # Human
    aspect="biological_process"
)
# ORAResult(tested=120, significant=15, ...)

# Gene symbols with automatic ID mapping
result = ora_kegg(
    gene_list=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    organism="hsa",
    id_type="symbol"  # Auto-converts to Entrez IDs
)
# ORAResult(tested=10, significant=4, ...)

# EnrichR (uses external web service)
result = ora_enrichr(
    genes=["TP53", "BRCA1", "BRCA2", "ATM"],
    gene_set_library="KEGG_2021_Human"
)
# ORAResult(tested=50, significant=8, ...)
```

### Knowledge Graph

Build and export biological knowledge graphs from fetched data:

```python
from biodbs.fetch import DO_Fetcher, quickgo_search_annotations
from biodbs.graph import (
    build_disease_graph,
    build_go_graph,
    merge_graphs,
    to_networkx,
    to_json_ld,
    to_neo4j_csv,
    to_cypher,
    get_graph_statistics,
    find_hub_nodes,
    find_shortest_path,
)

# Build a disease ontology graph
fetcher = DO_Fetcher()
disease_data = fetcher.get_children("DOID:162")  # Cancer subtypes
disease_graph = build_disease_graph(disease_data)
print(disease_graph)
# KnowledgeGraph(name='DiseaseOntologyGraph', nodes=47, edges=0)

# Build with hierarchy (parent → children edges)
parent_data = fetcher.get_by_id("DOID:162")
children_data = fetcher.get_children("DOID:162")
from biodbs.graph import build_disease_graph_with_hierarchy
hierarchy_graph = build_disease_graph_with_hierarchy(parent_data, children_data)
print(hierarchy_graph.summary())
# KnowledgeGraph: DiseaseOntologyGraph
# Nodes: 48
# Edges: 47
#
# Node types:
#   disease: 48
#
# Edge types:
#   is_a: 47

# Build a GO annotation graph
annotations = quickgo_search_annotations(gene_product_id="UniProtKB:P04637")
go_graph = build_go_graph(annotations)
# KnowledgeGraph(name='GeneOntologyGraph', nodes=25, edges=24)

# Merge multiple graphs
merged = merge_graphs(disease_graph, go_graph, name="BioGraph")
# KnowledgeGraph(name='BioGraph', nodes=72, edges=24)

# Analyze the graph
stats = get_graph_statistics(hierarchy_graph)
# {'num_nodes': 48, 'num_edges': 47, 'density': 0.021, ...}

hubs = find_hub_nodes(hierarchy_graph, top_n=3)
# [('DOID:162', 47), ('DOID:0050687', 12), ...]

path = find_shortest_path(hierarchy_graph, "DOID:1612", "DOID:162")
# ['DOID:1612', 'DOID:162']

# Export to NetworkX
nx_graph = to_networkx(hierarchy_graph)
# <networkx.classes.digraph.DiGraph with 48 nodes and 47 edges>

# Export to JSON-LD (ideal for KG-RAG applications)
json_ld = to_json_ld(hierarchy_graph)
# {'@context': {...}, '@type': 'schema:Dataset', '@graph': [...]}

# Export to Neo4j CSV
nodes_path, edges_path = to_neo4j_csv(hierarchy_graph, "./neo4j_import/")
# (Path('neo4j_import/nodes.csv'), Path('neo4j_import/relationships.csv'))

# Export to Cypher script
cypher_script = to_cypher(hierarchy_graph)
# "// Cypher script generated from KnowledgeGraph: DiseaseOntologyGraph\n..."
```

## Output Formats

All fetch operations return data objects with multiple export options:

```python
from biodbs.fetch import pubchem_get_compound

data = pubchem_get_compound(2244)

# As dictionary
records = data.as_dict()
# [{'CID': 2244, 'MolecularFormula': 'C9H8O4', ...}]

# As pandas DataFrame
df = data.as_dataframe(engine="pandas")
# pandas.DataFrame with compound properties as columns

# As Polars DataFrame
df = data.as_dataframe(engine="polars")
# polars.DataFrame with compound properties as columns

# Save to file
data.to_csv("aspirin.csv")       # writes aspirin.csv
data.to_json("aspirin.json")     # writes aspirin.json
data.to_sqlite("compounds.db", table_name="aspirin")  # writes to SQLite database
```

## Detailed Usage

### PubChem

```python
from biodbs.fetch import (
    pubchem_get_compound,
    pubchem_search_by_name,
    pubchem_search_by_smiles,
    pubchem_get_properties,
    pubchem_get_synonyms,
)

# Search compounds
results = pubchem_search_by_name("caffeine")
# FetchedData(source='pubchem', total_results=1, ...)
results = pubchem_search_by_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C")
# FetchedData(source='pubchem', total_results=1, ...)

# Get compound properties
props = pubchem_get_properties(
    2244,
    properties=["MolecularWeight", "MolecularFormula", "CanonicalSMILES"]
)
# FetchedData with columns: CID, MolecularWeight, MolecularFormula, CanonicalSMILES

# Get additional data
synonyms = pubchem_get_synonyms(2244)
# FetchedData(source='pubchem', total_results=1, ...)
```

### BioMart/Ensembl

```python
from biodbs.fetch import (
    biomart_get_genes,
    biomart_get_genes_by_name,
    biomart_get_transcripts,
    biomart_get_go_annotations,
    biomart_convert_ids,
)

# Get genes by Ensembl ID or symbol
genes = biomart_get_genes(["ENSG00000141510", "ENSG00000012048"])
# FetchedData(source='biomart', total_results=2, ...)
genes = biomart_get_genes_by_name(["TP53", "BRCA1"])
# FetchedData(source='biomart', total_results=2, ...)

# Get transcripts and GO annotations
transcripts = biomart_get_transcripts(["ENSG00000141510"])
# FetchedData with columns: ensembl_gene_id, ensembl_transcript_id, ...
go_terms = biomart_get_go_annotations(["ENSG00000141510"])
# FetchedData with columns: ensembl_gene_id, go_id, name_1006, namespace_1003

# Convert IDs
converted = biomart_convert_ids(
    ["ENSG00000141510"],
    from_type="ensembl_gene_id",
    to_type="hgnc_symbol"
)
# FetchedData with columns: ensembl_gene_id, hgnc_symbol
```

### KEGG

```python
from biodbs.fetch import kegg_info, kegg_list, kegg_find, kegg_get, kegg_conv, kegg_link

# Database information and listing
info = kegg_info("pathway")
# FetchedData(source='kegg', total_results=1, ...)
pathways = kegg_list("pathway", organism="hsa")
# FetchedData with columns: entry_id, definition

# Search and retrieve
results = kegg_find("genes", "shiga toxin")
# FetchedData with columns: entry_id, definition
entry = kegg_get("hsa:7157")  # TP53 gene
# FetchedData(source='kegg', total_results=1, ...)

# ID conversion and cross-references
converted = kegg_conv("ncbi-geneid", ["hsa:7157", "hsa:672"])
# FetchedData with columns: source_id, target_id
links = kegg_link("pathway", ["hsa:7157"])
# FetchedData with columns: source_id, target_id
```

### QuickGO

```python
from biodbs.fetch import (
    quickgo_search_terms,
    quickgo_get_terms,
    quickgo_get_term_children,
    quickgo_search_annotations,
)

# Search and retrieve GO terms
terms = quickgo_search_terms("apoptosis")
# FetchedData(source='quickgo', total_results=25, ...)
term = quickgo_get_terms(["GO:0006915"])
# FetchedData(source='quickgo', total_results=1, ...)
children = quickgo_get_term_children("GO:0008150")
# FetchedData(source='quickgo', total_results=30, ...)

# Search annotations
annotations = quickgo_search_annotations(gene_product_id="UniProtKB:P04637")
# FetchedData(source='quickgo', total_results=50, ...)
```

### Ensembl REST API

```python
from biodbs.fetch import (
    ensembl_lookup,
    ensembl_lookup_symbol,
    ensembl_get_sequence,
    ensembl_get_xrefs,
    ensembl_get_homology,
    ensembl_vep_hgvs,
)

# Lookup genes
gene = ensembl_lookup("ENSG00000141510", expand=True)
# FetchedData(source='ensembl', total_results=1, ...)
gene = ensembl_lookup_symbol("human", "TP53")
# FetchedData(source='ensembl', total_results=1, ...)

# Get sequences
cds = ensembl_get_sequence("ENST00000269305", sequence_type="cds")
# FetchedData with sequence string in results
protein = ensembl_get_sequence("ENSP00000269305", sequence_type="protein")
# FetchedData with protein sequence string in results

# Cross-references and homology
xrefs = ensembl_get_xrefs("ENSG00000141510", external_db="HGNC")
# FetchedData(source='ensembl', total_results=1, ...)
homologs = ensembl_get_homology("human", "ENSG00000141510", target_species="mouse")
# FetchedData with homology records including target species info

# Variant Effect Predictor
vep = ensembl_vep_hgvs("human", "ENST00000366667:c.803C>T")
# FetchedData with variant consequence predictions
```

### ChEMBL

```python
from biodbs.fetch import (
    chembl_get_molecule,
    chembl_search_molecules,
    chembl_get_target,
    chembl_get_activities_for_target,
)

# Get molecule and target data
molecule = chembl_get_molecule("CHEMBL25")
# FetchedData(source='chembl', total_results=1, ...)
target = chembl_get_target("CHEMBL1862")
# FetchedData(source='chembl', total_results=1, ...)

# Search and get activities
results = chembl_search_molecules("aspirin")
# FetchedData(source='chembl', total_results=1, ...)
activities = chembl_get_activities_for_target("CHEMBL1862")
# FetchedData(source='chembl', total_results=25, ...)
```

### Human Protein Atlas (HPA)

```python
from biodbs.fetch import (
    hpa_get_gene,
    hpa_get_tissue_expression,
    hpa_get_subcellular_location,
)

# Get gene and expression data
gene = hpa_get_gene("TP53")
# FetchedData(source='hpa', total_results=1, ...)
tissue_expr = hpa_get_tissue_expression("TP53")
# FetchedData(source='hpa', total_results=1, ...)
location = hpa_get_subcellular_location("TP53")
# FetchedData(source='hpa', total_results=1, ...)
```

### FDA

```python
from biodbs.fetch import fda_drug_events, fda_drug_labels, fda_search_all

# Drug data
events = fda_drug_events(search="aspirin", limit=10)
# FetchedData(source='fda', total_results=10, ...)
labels = fda_drug_labels(search="aspirin")
# FetchedData(source='fda', total_results=1, ...)

# Paginated search
all_results = fda_search_all(endpoint="drug/event", search="aspirin", max_results=500)
# FetchedData(source='fda', total_results=500, ...)
```

### UniProt

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

# Get protein entry by accession
entry = uniprot_get_entry("P04637")  # TP53
print(entry.entries[0].protein_name)  # "Cellular tumor antigen p53"
print(entry.entries[0].gene_name)     # "TP53"

# Get multiple entries
entries = uniprot_get_entries(["P04637", "P00533", "P38398"])
df = entries.as_dataframe()
#   accession        protein_name gene_name organism  ...
# 0    P04637  Cellular tumor...      TP53    Human  ...
# 1    P00533  Epidermal grow...      EGFR    Human  ...
# 2    P38398  BRCA1 DNA repa...     BRCA1    Human  ...

# Search UniProtKB
results = uniprot_search("gene:BRCA1 AND organism_id:9606 AND reviewed:true")
# FetchedData(source='uniprot', total_results=1, ...)

# Search by gene name
results = uniprot_search_by_gene("TP53", organism=9606, reviewed_only=True)
# FetchedData(source='uniprot', total_results=1, ...)

# Map gene names to UniProt accessions
mapping = gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}

# Map UniProt to gene names
mapping = uniprot_to_gene(["P04637", "P00533"])
# {'P04637': 'TP53', 'P00533': 'EGFR'}

# Get protein sequences
sequences = uniprot_get_sequences(["P04637", "P00533"])
# {'P04637': 'MEEPQSDPSVEPPLSQETFSDLWK...', 'P00533': 'MRPSGTAGAALLALL...'}

# ID mapping between databases
mapping = uniprot_map_ids(
    ["P04637", "P00533"],
    from_db="UniProtKB_AC-ID",
    to_db="GeneID"
)
# {'P04637': ['7157'], 'P00533': ['1956']}
```

## Using Fetcher Classes

For more control, use the fetcher classes directly:

```python
from biodbs.fetch.pubchem import PubChem_Fetcher
from biodbs.fetch.biomart import BioMart_Fetcher
from biodbs.fetch.ensembl import Ensembl_Fetcher
from biodbs.fetch.uniprot import UniProt_Fetcher

# PubChem
fetcher = PubChem_Fetcher()
data = fetcher.get_compound(2244)
# FetchedData(source='pubchem', total_results=1, ...)

# BioMart
fetcher = BioMart_Fetcher()
data = fetcher.query(
    dataset="hsapiens_gene_ensembl",
    attributes=["ensembl_gene_id", "external_gene_name"],
    filters={"ensembl_gene_id": ["ENSG00000141510"]}
)
# FetchedData(source='biomart', total_results=1, ...)

# Ensembl REST
fetcher = Ensembl_Fetcher()
data = fetcher.lookup("ENSG00000141510", expand=True)
# FetchedData(source='ensembl', total_results=1, ...)

# UniProt
fetcher = UniProt_Fetcher()
data = fetcher.get_entry("P04637")
# FetchedData(source='uniprot', total_results=1, ...)
results = fetcher.search_by_gene("TP53", organism=9606)
# FetchedData(source='uniprot', total_results=1, ...)
```

## Supported ID Types

### Gene IDs (via BioMart)

| ID Type | Description | Example |
|---------|-------------|---------|
| `ensembl_gene_id` | Ensembl gene ID | ENSG00000141510 |
| `external_gene_name` | Gene symbol | TP53 |
| `hgnc_symbol` | HGNC symbol | TP53 |
| `entrezgene_id` | NCBI Entrez ID | 7157 |
| `uniprot_gn_id` | UniProt gene name | P04637 |

### Chemical IDs (via PubChem)

| ID Type | Description | Example |
|---------|-------------|---------|
| `cid` | PubChem Compound ID | 2244 |
| `name` | Compound name | aspirin |
| `smiles` | SMILES string | CC(=O)OC1=CC=CC=C1C(=O)O |
| `inchikey` | InChIKey | BSYNRYMUTXBXSQ-UHFFFAOYSA-N |

### Protein IDs (via UniProt)

| ID Type | Description | Example |
|---------|-------------|---------|
| `UniProtKB_AC-ID` | UniProt accession | P04637 |
| `Gene_Name` | Gene symbol | TP53 |
| `GeneID` | NCBI Gene ID | 7157 |
| `Ensembl` | Ensembl gene ID | ENSG00000141510 |
| `RefSeq_Protein` | RefSeq protein ID | NP_000537.3 |
| `PDB` | PDB structure ID | 1TUP |

## Requirements

**Core dependencies** (installed automatically):

- Python 3.10+
- pandas
- polars
- pydantic
- requests
- scipy

**Optional dependencies**:

- `networkx` and `rdflib` - for graph module exports (`pip install biodbs[graph]`)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
