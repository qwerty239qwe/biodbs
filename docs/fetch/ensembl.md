# Ensembl REST API

Access genomic data via the [Ensembl REST API](https://rest.ensembl.org/).

## Overview

The Ensembl REST API provides access to:

- **Gene/Transcript Lookup** - Retrieve annotations by ID or symbol
- **Sequences** - DNA, cDNA, CDS, and protein sequences
- **Variants** - VEP (Variant Effect Predictor)
- **Homology** - Orthologs and paralogs
- **Cross-references** - Links to external databases

## Quick Start

```python
from biodbs.fetch import (
    ensembl_lookup,
    ensembl_lookup_symbol,
    ensembl_get_sequence,
    ensembl_get_xrefs,
    ensembl_vep_hgvs,
)

# Lookup gene by Ensembl ID
gene = ensembl_lookup("ENSG00000141510")  # TP53

# Lookup by symbol
gene = ensembl_lookup_symbol("human", "TP53")
```

## Gene/Transcript Lookup

### By Ensembl ID

```python
from biodbs.fetch import ensembl_lookup, ensembl_lookup_batch

# Single lookup
gene = ensembl_lookup("ENSG00000141510", expand=True)

# Batch lookup
genes = ensembl_lookup_batch(["ENSG00000141510", "ENSG00000012048"])
```

### By Symbol

```python
from biodbs.fetch import ensembl_lookup_symbol

gene = ensembl_lookup_symbol("human", "TP53")
gene = ensembl_lookup_symbol("mouse", "Trp53")
```

## Sequences

### Get Sequence

```python
from biodbs.fetch import ensembl_get_sequence, ensembl_get_sequence_batch

# CDS sequence
cds = ensembl_get_sequence("ENST00000269305", sequence_type="cds")

# Protein sequence
protein = ensembl_get_sequence("ENSP00000269305", sequence_type="protein")

# Batch retrieval
sequences = ensembl_get_sequence_batch(
    ["ENST00000269305", "ENST00000357654"],
    sequence_type="cds"
)
```

### Genomic Region

```python
from biodbs.fetch import ensembl_get_sequence_region

seq = ensembl_get_sequence_region(
    "human",
    region="17:7661779-7687550",
    strand=1
)
```

## Cross-References

```python
from biodbs.fetch import ensembl_get_xrefs, ensembl_get_xrefs_symbol

# Get xrefs by Ensembl ID
xrefs = ensembl_get_xrefs("ENSG00000141510", external_db="HGNC")

# Get Ensembl ID by symbol
xrefs = ensembl_get_xrefs_symbol("human", "TP53")
```

## Homology

```python
from biodbs.fetch import ensembl_get_homology, ensembl_get_homology_symbol

# By Ensembl ID
homologs = ensembl_get_homology(
    "human",
    "ENSG00000141510",
    target_species="mouse"
)

# By symbol
homologs = ensembl_get_homology_symbol(
    "human",
    "TP53",
    target_species="mouse"
)
```

## Variant Effect Predictor (VEP)

```python
from biodbs.fetch import ensembl_vep_hgvs, ensembl_vep_id, ensembl_vep_region

# By HGVS notation
vep = ensembl_vep_hgvs("human", "ENST00000366667:c.803C>T")

# By variant ID
vep = ensembl_vep_id("human", "rs699")

# By region
vep = ensembl_vep_region("human", "17:7676154-7676154:1/A")
```

## Other Endpoints

### Overlap

```python
from biodbs.fetch import ensembl_get_overlap_id, ensembl_get_overlap_region

# Features overlapping a gene
overlap = ensembl_get_overlap_id("ENSG00000141510", feature="transcript")

# Features in region
overlap = ensembl_get_overlap_region(
    "human",
    "17:7661779-7687550",
    feature="gene"
)
```

### Assembly Mapping

```python
from biodbs.fetch import ensembl_map_assembly

# Convert coordinates between assemblies
mapped = ensembl_map_assembly(
    "human",
    "GRCh37",
    "17:7661779-7687550",
    "GRCh38"
)
```

### Ontology

```python
from biodbs.fetch import (
    ensembl_get_ontology_term,
    ensembl_get_ontology_ancestors,
    ensembl_get_ontology_descendants,
)

term = ensembl_get_ontology_term("GO:0006915")
ancestors = ensembl_get_ontology_ancestors("GO:0006915")
descendants = ensembl_get_ontology_descendants("GO:0006915")
```

## Using the Fetcher Class

```python
from biodbs.fetch.ensembl import Ensembl_Fetcher

fetcher = Ensembl_Fetcher()
gene = fetcher.lookup("ENSG00000141510", expand=True)
```
