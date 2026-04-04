# ClinVar

Access clinical variant data via the [NCBI ClinVar API](https://www.ncbi.nlm.nih.gov/clinvar/).

## Overview

ClinVar is NCBI's archive of relationships between genomic variation and human health. biodbs provides:

- **Gene and condition search** — find variants by gene symbol or disease name in one step
- **Batch fetch** — retrieve full variant summaries by variation UID
- **Clinical significance filtering** — easily isolate pathogenic variants
- **PubMed linking** — find publications associated with a variant
- **VCV / RCV XML access** — retrieve full structured records

## Quick Start

```python
from biodbs.fetch import clinvar_search_gene, clinvar_search_condition

# Pathogenic variants in BRCA1
data = clinvar_search_gene("BRCA1", clinical_significance="pathogenic")
df = data.as_dataframe()
print(df[["variation_id", "title", "clinical_significance"]])

# Variants linked to Lynch syndrome
data = clinvar_search_condition("Lynch syndrome", retmax=100)
print(len(data))
```

## Searching

### By Gene Symbol

```python
from biodbs.fetch import clinvar_search_gene

# All variants for TP53
data = clinvar_search_gene("TP53", retmax=500)

# Pathogenic only
data = clinvar_search_gene("TP53", clinical_significance="pathogenic")

# Include multi-gene variants
data = clinvar_search_gene("TP53", single_gene=False)
```

### By Condition / Disease

```python
from biodbs.fetch import clinvar_search_condition

data = clinvar_search_condition("Breast cancer", retmax=200)
data = clinvar_search_condition("Lynch syndrome",
                                 clinical_significance="pathogenic")
```

### Custom Entrez Query

```python
from biodbs.fetch import clinvar_search, clinvar_count, clinvar_fetch_by_id

# Count first
n = clinvar_count("BRCA2[gene] AND pathogenic[clnsig]")
print(f"{n} pathogenic BRCA2 variants")

# Then fetch
uids = clinvar_search("BRCA2[gene] AND pathogenic[clnsig]", retmax=50)
data = clinvar_fetch_by_id(uids)
```

## Fetching by ID

```python
from biodbs.fetch import clinvar_fetch_by_id

# By variation UID
data = clinvar_fetch_by_id([65533, 14206, 31124])
print(data.as_dataframe())
```

## Filtering Results

```python
data = clinvar_search_gene("BRCA1", retmax=1000)

# Keep only pathogenic / likely pathogenic variants
path = data.pathogenic()
print(f"{len(path)} pathogenic variants")

# Access individual variants
for variant in path:
    print(variant.variation_id, variant.title, variant.clinical_significance)
```

## Working with Results

### The `ClinVarFetchedData` container

Printing the container shows a brief summary:

```python
data = clinvar_search_gene("BRCA1", clinical_significance="pathogenic", retmax=50)
print(data)
# <ClinVarFetchedData: 50 variants (of 1243 found)>
```

It supports standard sequence operations:

```python
len(data)           # 50
data[0]             # first variant
data[-1]            # last variant
data[0:5]           # slice → list of ClinVarVariant

# Iterate
for variant in data:
    print(variant.accession, variant.clinical_significance)
```

### Lookup by identifier

Any of the standard ClinVar accession formats work as a key:

```python
data["65533"]           # by variation UID (string or int not accepted — must be str)
data["VCV000065533"]    # by VCV accession (with or without version suffix)
data["VCV000065533.5"]  # versioned VCV accession
data["RCV000031124"]    # by RCV accession
```

### The `ClinVarVariant` record

Printing a single variant shows its key details:

```python
v = data[0]
print(v)
# <ClinVarVariant VCV000065533 [BRCA1] single nucleotide variant — Pathogenic>
```

All available fields:

| Field | Type | Example |
|-------|------|---------|
| `variation_id` | `str` | `"65533"` |
| `accession` | `str` | `"VCV000065533"` |
| `accession_version` | `str` | `"VCV000065533.5"` |
| `title` | `str` | `"NM_007294.4(BRCA1):c.5266dupC (p.Gln1756ProfsTer25)"` |
| `variation_type` | `str \| None` | `"single nucleotide variant"` |
| `clinical_significance` | `str \| None` | `"Pathogenic"` |
| `review_status` | `str \| None` | `"reviewed by expert panel"` |
| `last_evaluated` | `str \| None` | `"2018-09-21"` |
| `gene_symbols` | `List[str]` | `["BRCA1"]` |
| `gene_ids` | `List[str]` | `["672"]` |
| `conditions` | `List[str]` | `["Hereditary breast ovarian cancer syndrome"]` |
| `rcv_accessions` | `List[str]` | `["RCV000031124"]` |
| `protein_change` | `str \| None` | `"Gln1756ProfsTer25"` |
| `chromosome` | `str \| None` | `"17"` |
| `start` | `int \| None` | `43045703` |
| `stop` | `int \| None` | `43045703` |
| `assembly` | `str \| None` | `"GRCh38"` |

Computed properties:

```python
v.is_pathogenic   # True if Pathogenic or Likely pathogenic
v.primary_gene    # first entry of gene_symbols, or None
```

### Collection-level accessors

```python
data.variation_ids()   # ["65533", "14206", ...]  — all variation UIDs
data.accessions()      # ["VCV000065533", ...]     — all VCV accessions
data.gene_symbols()    # ["BRCA1", "BRCA2", ...]  — unique symbols across all variants
data.total_count       # total hits from the original search (may exceed len(data))
```

### Convert to DataFrame

```python
df = data.as_dataframe()
print(df.columns.tolist())
# ['variation_id', 'accession', 'accession_version', 'title', 'variation_type',
#  'clinical_significance', 'review_status', 'last_evaluated', 'gene_symbols',
#  'gene_ids', 'conditions', 'rcv_accessions', 'protein_change',
#  'chromosome', 'start', 'stop', 'assembly']
```

List-valued fields (`gene_symbols`, `gene_ids`, `conditions`, `rcv_accessions`) are joined with `";"` in the DataFrame for easy CSV export.

```python
records = data.as_dict()   # list of plain dicts (lists remain as lists)
```

## XML Records

```python
from biodbs.fetch import clinvar_fetch_vcv, clinvar_fetch_rcv

# Full VCV XML (variation-centric record)
xml = clinvar_fetch_vcv("VCV000065533")

# Full RCV XML (variation-condition pair)
xml = clinvar_fetch_rcv("RCV000031124")
```

## PubMed Links

```python
from biodbs.fetch import clinvar_link_pubmed

pmids = clinvar_link_pubmed(65533)
print(f"Found {len(pmids)} linked PubMed articles")
```

## Using the Fetcher Class

```python
from biodbs.fetch.ClinVar import ClinVar_Fetcher

fetcher = ClinVar_Fetcher()
uids = fetcher.search("BRCA1[gene] AND pathogenic[clnsig]")
data = fetcher.fetch_summary(uids[:20])
```

## Related Resources

- **[NCBI](ncbi.md)** — Gene summaries, taxonomy, and genome assemblies from NCBI.
- **[Disease Ontology](disease-ontology.md)** — Structured disease terms to complement ClinVar condition names.
- **[UniProt](uniprot.md)** — Fetch protein-level functional data for genes identified in ClinVar.
