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
| [Protein IDs](proteins.md) | `translate_protein_ids` | UniProt-based protein mapping |
| [Chemical IDs](chemicals.md) | `translate_chemical_ids` | Map between chemical identifiers |
| [Taxonomic names](../taxonomy/mapping.md) | `translate_taxon_names` | Resolve names to NCBI taxids and canonical-name metadata |

## Quick Start

```python
from biodbs.translate import (
    translate_gene_ids,
    translate_protein_ids,
    translate_chemical_ids,
)

# Gene symbols to Ensembl IDs
genes = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",
    to_type="ensembl_gene_id",
    return_dict=True
)
# {'TP53': 'ENSG00000141510', 'BRCA1': 'ENSG00000012048'}

# Gene symbols to UniProt accessions
proteins = translate_protein_ids(
    ["TP53", "BRCA1", "EGFR"], "Gene_Name", "UniProtKB_AC-ID", return_dict=True
)
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

## Taxonomic Names

Without a mapper, taxonomic names use online NCBI name-to-taxid resolution:

```python
from biodbs.translate import translate_taxon_names

taxa = translate_taxon_names(["Escherichia coli"])
```

This requires network access and only supplies the taxid and match provenance;
canonical names, rank, lineage, and accepted/synonym status require a configured
taxdump/GBIF mapper. For offline resolution:

```python
from biodbs.taxonomy import TaxonomyMapper, load_taxdump
from biodbs.translate import translate_taxon_names

mapper = TaxonomyMapper(taxdump=load_taxdump("data/ncbi/new_taxdump.tar.gz"))
taxa = translate_taxon_names(
    ["Escherichia coli", "Bacillus coli", "Not A Taxon"],
    mapper=mapper,
)
# hub_taxid: 562, 562, missing
# name_status: accepted, synonym, unmatched
```

This is a thin wrapper over `mapper.map_names`: it preserves input order,
duplicates, and unresolved rows. A taxdump is never downloaded automatically.
Configure NCBI/GBIF fetchers on the mapper for online resolution/enrichment. Fetcher errors propagate
unchanged. For lineage strings and cross-database joins, continue using
`biodbs.taxonomy`; see the [taxonomy guide](../taxonomy/mapping.md).

## Multiple Target Types

Gene, protein, and chemical translators can return multiple target ID types in a
single call, except the KEGG backend, which currently accepts one target type:

```python
# Get multiple ID types at once (more efficient than separate calls)
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="external_gene_name",
    to_type=["ensembl_gene_id", "entrezgene_id", "hgnc_id"],
)
#   external_gene_name    ensembl_gene_id  entrezgene_id     hgnc_id
# 0               TP53  ENSG00000141510           7157  HGNC:11998
# 1              BRCA1  ENSG00000012048            672   HGNC:1100

# Chemical IDs
result = translate_chemical_ids(
    ["aspirin"],
    from_type="name",
    to_type=["cid", "smiles", "inchikey"],
)

# Protein IDs
result = translate_protein_ids(
    ["P04637"],
    from_type="UniProtKB_AC-ID",
    to_type=["GeneID", "Ensembl", "Gene_Name"],
)
```

## Output Formats

Gene, protein, and chemical translators support two output formats.
`translate_taxon_names` always returns the taxonomy mapping DataFrame described above.

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
# Using BioMart (NCBI remains the default)
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

## Optional Reusable Mappers

Ordinary function calls do not require mapper objects. Defaults remain NCBI/human
for genes, UniProt/human/reviewed-only for proteins, and PubChem for existing
chemical ID types. Explicit `chembl_id` or KEGG chemical namespaces select the
appropriate route; unsupported pairs raise rather than falling back to another
database. The gene KEGG route requires `database="kegg"`.

Advanced callers can reuse configuration:

```python
from biodbs.translate import GeneMapper, translate_gene_ids

mapper = GeneMapper(database="hgnc", species="human")
result = translate_gene_ids(
    ["TP53"], "gene_symbol", "entrez_id", mapper=mapper, return_dict=True
)
# Equivalent: mapper.map(["TP53"], "gene_symbol", "entrez_id", return_dict=True)
```

`ChemicalMapper(database="auto")` and `ProteinMapper(organism=9606,
reviewed_only=True)` offer the same optional pattern. These are immutable
configuration objects, not result caches or new HTTP clients. Passing explicit
backend/species/organism/review settings conflicting with the mapper raises
`ValueError`, including explicit values equal to the normal defaults. `None`
marks an omitted setting; effective defaults are unchanged.

Existing helper functions remain supported without deprecation warnings. They
share the main translation logic while retaining their historical positional
arguments, dictionary defaults, column names, scalar/list outputs, and KEGG
whole-database behavior for empty input. The main KEGG APIs return prefixed
`source_id`/`target_id` columns, accept only one target type, and require `bulk=True`
for whole-database conversion. An empty list without `bulk=True` makes no request.

## Error Handling

Missing or unmappable IDs return `None` or `NaN`:

Ensembl and ChEMBL/PubChem translators also return missing mappings for expected
API/network failures. Use the fetcher APIs directly when you need to distinguish
an unavailable service from an unmappable ID. Live accuracy tests guard these
fetchers so confirmed outages are reported as skips; successful responses with
missing or incorrect reference IDs still fail their exact-ID assertions.

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
- [Taxonomy Mapping](../taxonomy/mapping.md) - Taxonomic names, lineages, and joins
- [ORA Analysis](../analysis/ora.md) - Use translated IDs in enrichment analysis
