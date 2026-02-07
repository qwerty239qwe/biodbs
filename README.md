# biodbs

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

## Quick Start

### Namespace Overview

```python
# Data fetching - low-level API wrappers
from biodbs.fetch import pubchem_get_compound, kegg_get, ensembl_lookup, uniprot_get_entry

# ID translation - mapping between databases
from biodbs.translate import translate_gene_ids, translate_chemical_ids, translate_protein_ids

# Analysis - enrichment and statistics
from biodbs.analysis import ora_kegg, ora_go, ora_enrichr
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

# BioMart - Get gene information
genes = biomart_get_genes(["ENSG00000141510", "ENSG00000012048"])
df = genes.as_dataframe()

# ChEMBL - Search for molecules
molecules = chembl_search_molecules("aspirin")

# KEGG - Get pathway information
pathway = kegg_get("hsa00010")  # Glycolysis pathway

# QuickGO - Search GO terms
terms = quickgo_search_terms("apoptosis")

# HPA - Get tissue expression
expression = hpa_get_tissue_expression("TP53")

# FDA - Search drug adverse events
events = fda_drug_events(search="aspirin", limit=10)

# Ensembl - Lookup gene and get sequence
gene = ensembl_lookup("ENSG00000141510")  # TP53

# UniProt - Get protein entry
protein = uniprot_get_entry("P04637")  # TP53 protein
print(protein.entries[0].protein_name)

# UniProt - Search by gene name
results = uniprot_search_by_gene("BRCA1", organism=9606)
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

# Compound names to PubChem CIDs
result = translate_chemical_ids(
    ["aspirin", "ibuprofen"],
    from_type="name",
    to_type="cid"
)

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
pubchem_to_chembl = translate_pubchem_to_chembl([2244, 2519])
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

# View significant pathways
significant = result.significant_terms(alpha=0.05)
df = significant.as_dataframe()
print(df[["term_id", "term_name", "p_value", "q_value", "overlap_genes"]])

# GO enrichment (requires UniProt IDs)
result = ora_go(
    gene_list=["P04637", "P38398", "P51587"],  # UniProt accessions
    taxon_id=9606,  # Human
    aspect="biological_process"
)

# Gene symbols with automatic ID mapping
result = ora_kegg(
    gene_list=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
    organism="hsa",
    id_type="symbol"  # Auto-converts to Entrez IDs
)

# EnrichR (uses external web service)
result = ora_enrichr(
    genes=["TP53", "BRCA1", "BRCA2", "ATM"],
    gene_set_library="KEGG_2021_Human"
)
```

## Output Formats

All fetch operations return data objects with multiple export options:

```python
from biodbs.fetch import pubchem_get_compound

data = pubchem_get_compound(2244)

# As dictionary
records = data.as_dict()

# As pandas DataFrame
df = data.as_dataframe(engine="pandas")

# As Polars DataFrame
df = data.as_dataframe(engine="polars")

# Save to file
data.to_csv("aspirin.csv")
data.to_json("aspirin.json")
data.to_sqlite("compounds.db", table_name="aspirin")
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
results = pubchem_search_by_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C")

# Get compound properties
props = pubchem_get_properties(
    2244,
    properties=["MolecularWeight", "MolecularFormula", "CanonicalSMILES"]
)

# Get additional data
synonyms = pubchem_get_synonyms(2244)
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
genes = biomart_get_genes_by_name(["TP53", "BRCA1"])

# Get transcripts and GO annotations
transcripts = biomart_get_transcripts(["ENSG00000141510"])
go_terms = biomart_get_go_annotations(["ENSG00000141510"])

# Convert IDs
converted = biomart_convert_ids(
    ["ENSG00000141510"],
    from_type="ensembl_gene_id",
    to_type="hgnc_symbol"
)
```

### KEGG

```python
from biodbs.fetch import kegg_info, kegg_list, kegg_find, kegg_get, kegg_conv, kegg_link

# Database information and listing
info = kegg_info("pathway")
pathways = kegg_list("pathway", organism="hsa")

# Search and retrieve
results = kegg_find("genes", "shiga toxin")
entry = kegg_get("hsa:7157")  # TP53 gene

# ID conversion and cross-references
converted = kegg_conv("ncbi-geneid", ["hsa:7157", "hsa:672"])
links = kegg_link("pathway", ["hsa:7157"])
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
term = quickgo_get_terms(["GO:0006915"])
children = quickgo_get_term_children("GO:0008150")

# Search annotations
annotations = quickgo_search_annotations(gene_product_id="UniProtKB:P04637")
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
gene = ensembl_lookup_symbol("human", "TP53")

# Get sequences
cds = ensembl_get_sequence("ENST00000269305", sequence_type="cds")
protein = ensembl_get_sequence("ENSP00000269305", sequence_type="protein")

# Cross-references and homology
xrefs = ensembl_get_xrefs("ENSG00000141510", external_db="HGNC")
homologs = ensembl_get_homology("human", "ENSG00000141510", target_species="mouse")

# Variant Effect Predictor
vep = ensembl_vep_hgvs("human", "ENST00000366667:c.803C>T")
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
target = chembl_get_target("CHEMBL1862")

# Search and get activities
results = chembl_search_molecules("aspirin")
activities = chembl_get_activities_for_target("CHEMBL1862")
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
tissue_expr = hpa_get_tissue_expression("TP53")
location = hpa_get_subcellular_location("TP53")
```

### FDA

```python
from biodbs.fetch import fda_drug_events, fda_drug_labels, fda_search_all

# Drug data
events = fda_drug_events(search="aspirin", limit=10)
labels = fda_drug_labels(search="aspirin")

# Paginated search
all_results = fda_search_all(endpoint="drug/event", search="aspirin", max_results=500)
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

# Search UniProtKB
results = uniprot_search("gene:BRCA1 AND organism_id:9606 AND reviewed:true")

# Search by gene name
results = uniprot_search_by_gene("TP53", organism=9606, reviewed_only=True)

# Map gene names to UniProt accessions
mapping = gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}

# Map UniProt to gene names
mapping = uniprot_to_gene(["P04637", "P00533"])
# {'P04637': 'TP53', 'P00533': 'EGFR'}

# Get protein sequences
sequences = uniprot_get_sequences(["P04637", "P00533"])

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

# BioMart
fetcher = BioMart_Fetcher()
data = fetcher.query(
    dataset="hsapiens_gene_ensembl",
    attributes=["ensembl_gene_id", "external_gene_name"],
    filters={"ensembl_gene_id": ["ENSG00000141510"]}
)

# Ensembl REST
fetcher = Ensembl_Fetcher()
data = fetcher.lookup("ENSG00000141510", expand=True)

# UniProt
fetcher = UniProt_Fetcher()
data = fetcher.get_entry("P04637")
results = fetcher.search_by_gene("TP53", organism=9606)
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
