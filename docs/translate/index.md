# ID Translation Overview

The `biodbs.translate` module provides functions for mapping between different biological identifier systems.

**Related sections:**

- [API Reference](../api/translate.md) - Complete function documentation
- [Data Fetching](../fetch/index.md) - Fetch data using translated IDs
- [Analysis](../analysis/index.md) - Use translated IDs in ORA analysis
- [Knowledge Graph](../graph/index.md) - Build graphs with cross-referenced entities

## Available Translators

| Category | Functions | Description |
|----------|-----------|-------------|
| [Gene IDs](genes.md) | `translate_gene_ids` | Map between gene identifier systems |
| [Protein IDs](proteins.md) | `translate_protein_ids`, `translate_gene_to_uniprot` | UniProt-based protein mapping |
| [Chemical IDs](chemicals.md) | `translate_chemical_ids` | Map between chemical identifiers |

## Quick Start

```python
from biodbs.translate import (
    translate_gene_ids,
    translate_protein_ids,
    translate_chemical_ids,
    translate_gene_to_uniprot,
)

# Gene symbols to Ensembl IDs
genes = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    return_dict=True
)
# {'TP53': 'ENSG00000141510', 'BRCA1': 'ENSG00000012048'}

# Gene symbols to UniProt accessions
proteins = translate_gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
# {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}

# UniProt to NCBI Gene ID
mapping = translate_protein_ids(
    ["P04637", "P00533"],
    from_type="UniProtKB_AC-ID",
    to_type="GeneID",
    return_dict=True
)
# {'P04637': '7157', 'P00533': '1956'}

# Chemical names to PubChem CIDs
chemicals = translate_chemical_ids(
    ["aspirin", "caffeine"],
    from_type="name",
    to_type="cid"
)
```

## Output Formats

All translation functions support two output formats:

### Dictionary (return_dict=True)

```python
mapping = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    return_dict=True
)
# {'TP53': 'ENSG00000141510', 'BRCA1': 'ENSG00000012048'}
```

### DataFrame (return_dict=False, default)

```python
df = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id"
)
#   external_gene_name    ensembl_gene_id
# 0               TP53  ENSG00000141510
# 1              BRCA1  ENSG00000012048
```

## Database Selection

Many translators support multiple backend databases:

```python
# Using BioMart (default)
result = translate_gene_ids(
    ["TP53"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    database="biomart"
)

# Using Ensembl REST API
result = translate_gene_ids(
    ["ENSG00000141510"],
    from_type="ensembl_gene_id",
    to_type="HGNC",
    database="ensembl"
)

# Using NCBI
result = translate_gene_ids(
    ["TP53"],
    from_type="symbol",
    to_type="entrez_id",
    database="ncbi"
)

# Using UniProt
result = translate_gene_ids(
    ["TP53"],
    from_type="Gene_Name",
    to_type="UniProtKB",
    database="uniprot"
)
```

## Species Support

Specify species for organism-specific translations:

```python
# Human (default)
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    species="human"
)

# Mouse
result = translate_gene_ids(
    ["Trp53", "Brca1"],
    from_type="external_gene_name",
    to_type="ensembl_gene_id",
    species="mouse"
)
```

## Error Handling

Missing or unmappable IDs return `None` or `NaN`:

```python
mapping = translate_gene_to_uniprot(
    ["TP53", "NOT_A_GENE", "BRCA1"]
)
# {'TP53': 'P04637', 'BRCA1': 'P38398'}
# Note: 'NOT_A_GENE' is not in the result
```

## Next Steps

- [Gene ID Translation](genes.md) - Detailed gene ID mapping guide
- [Protein ID Translation](proteins.md) - UniProt-based protein mapping
- [Chemical ID Translation](chemicals.md) - Chemical identifier mapping
- [ORA Analysis](../analysis/ora.md) - Use translated IDs in enrichment analysis
