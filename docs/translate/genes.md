# Gene ID Translation

Translate between different gene identifier systems using `translate_gene_ids`.

## Quick Start

```python
from biodbs.translate import translate_gene_ids

# Gene symbols → Ensembl IDs (using universal aliases)
result = translate_gene_ids(
    ["TP53", "BRCA1", "EGFR"],
    from_type="gene_symbol",
    to_type="ensembl_gene_id",
)

# Gene symbols → Entrez IDs
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",
    to_type="entrez_id",
    database="ncbi",      # default
)
```

## Universal ID Type Aliases

Every database has its own field names for the same concept. biodbs provides a set of
**universal aliases** that work regardless of which backend you choose — the correct
native name is resolved automatically.

### `GeneIDType` enum

```python
from biodbs.translate import GeneIDType

# Use enum members as from_type / to_type
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type=GeneIDType.GENE_SYMBOL,
    to_type=GeneIDType.ENSEMBL_GENE_ID,
)

# Plain strings with the same values work identically
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",   # same as GeneIDType.GENE_SYMBOL
    to_type="ensembl_gene_id", # same as GeneIDType.ENSEMBL_GENE_ID
)
```

### Universal aliases and their values

| `GeneIDType` member | String value | Description | Example |
|---------------------|-------------|-------------|---------|
| `GENE_SYMBOL` | `"gene_symbol"` | Approved gene symbol | `"TP53"` |
| `ENSEMBL_GENE_ID` | `"ensembl_gene_id"` | Ensembl stable gene ID | `"ENSG00000141510"` |
| `ENSEMBL_TRANSCRIPT_ID` | `"ensembl_transcript_id"` | Ensembl transcript ID | `"ENST00000269305"` |
| `ENSEMBL_PROTEIN_ID` | `"ensembl_protein_id"` | Ensembl protein ID | `"ENSP00000269305"` |
| `ENTREZ_ID` | `"entrez_id"` | NCBI Entrez Gene ID | `"7157"` |
| `HGNC_ID` | `"hgnc_id"` | HGNC identifier | `"HGNC:11998"` |
| `HGNC_SYMBOL` | `"hgnc_symbol"` | HGNC-curated symbol | `"TP53"` |
| `UNIPROT_ID` | `"uniprot_id"` | UniProt accession | `"P04637"` |
| `REFSEQ_MRNA` | `"refseq_mrna"` | RefSeq mRNA accession | `"NM_000546"` |
| `REFSEQ_PROTEIN` | `"refseq_protein"` | RefSeq protein accession | `"NP_000537"` |
| `PDB_ID` | `"pdb_id"` | PDB structure ID | `"2OCJ"` |

### How aliases resolve per database

When you pass a universal alias, it is automatically mapped to the native field name
required by the chosen backend. Native field names are also accepted and passed through
unchanged — so existing code keeps working.

| Universal alias | BioMart | NCBI | UniProt | Ensembl REST | HGNC |
|-----------------|---------|------|---------|--------------|------|
| `gene_symbol` | `external_gene_name` | `symbol` | `Gene_Name` | `HGNC` | `symbol` |
| `ensembl_gene_id` | `ensembl_gene_id` | `ensembl_gene_id` | `Ensembl` | `ensembl_gene_id` | `ensembl_gene_id` |
| `ensembl_transcript_id` | `ensembl_transcript_id` | — | — | — | — |
| `ensembl_protein_id` | `ensembl_peptide_id` | — | — | — | — |
| `entrez_id` | `entrezgene_id` | `gene_id` | `GeneID` | `EntrezGene` | `entrez_id` |
| `hgnc_id` | `hgnc_id` | — | — | — | `hgnc_id` |
| `hgnc_symbol` | `hgnc_symbol` | — | — | — | `symbol` |
| `uniprot_id` | `uniprot_gn_id` | `uniprot` | `UniProtKB_AC-ID` | `Uniprot_gn` | `uniprot_ids` |
| `refseq_mrna` | `refseq_mrna` | `refseq_accession` | — | `RefSeq_mRNA` | `refseq_accession` |
| `refseq_protein` | `refseq_peptide` | `refseq_accession` | `RefSeq_Protein` | `RefSeq_peptide` | `refseq_accession` |
| `pdb_id` | — | — | `PDB` | — | — |

!!! note "Native strings are always accepted"
    If you pass a value that is **not** in the alias map (e.g. `"external_gene_name"` or
    `"Gene_Name"`), it is forwarded to the database unchanged. This means database-native
    field names still work, but universal aliases are preferred for portability.

## Choosing a Database

```python
from biodbs.translate import TranslationDatabase

result = translate_gene_ids(ids, from_type=..., to_type=...,
                             database=TranslationDatabase.NCBI)   # or "ncbi"
```

| Database | String | Best for | Human only? |
|----------|--------|----------|-------------|
| **NCBI** *(default)* | `"ncbi"` | symbol ↔ Entrez ↔ Ensembl; most stable | No |
| **Ensembl REST** | `"ensembl"` | Ensembl ID lookups; more stable than BioMart | No |
| **UniProt** | `"uniprot"` | UniProt accession, PDB, RefSeq protein | No |
| **BioMart** | `"biomart"` | Widest range of ID types; batch queries | No |
| **HGNC** | `"hgnc"` | HGNC IDs, approved symbols, aliases | **Yes** |

## Per-Database Details

### NCBI (default)

Queries the NCBI Datasets API. Best starting point for most symbol ↔ ID translations.

```python
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",   # resolves to "symbol"
    to_type="entrez_id",       # resolves to "gene_id"
    database="ncbi",
)
```

Supported ID types (universal alias → native):

| Universal alias | Native field |
|-----------------|-------------|
| `gene_symbol` | `symbol` |
| `ensembl_gene_id` | `ensembl_gene_id` |
| `entrez_id` | `gene_id` |
| `uniprot_id` | `uniprot` |
| `refseq_mrna` / `refseq_protein` | `refseq_accession` |

### Ensembl REST

Uses the Ensembl `/xrefs` endpoint. Natural choice when starting from Ensembl IDs.

```python
result = translate_gene_ids(
    ["ENSG00000141510", "ENSG00000012048"],
    from_type="ensembl_gene_id",
    to_type="entrez_id",        # resolves to "EntrezGene"
    database="ensembl",
)
```

Supported ID types (universal alias → native):

| Universal alias | Native field |
|-----------------|-------------|
| `gene_symbol` | `HGNC` |
| `ensembl_gene_id` | `ensembl_gene_id` |
| `entrez_id` | `EntrezGene` |
| `uniprot_id` | `Uniprot_gn` |
| `refseq_mrna` | `RefSeq_mRNA` |
| `refseq_protein` | `RefSeq_peptide` |

### UniProt

Uses the UniProt ID-mapping API. Best for anything involving UniProt accessions, PDB
IDs, or RefSeq protein IDs.

```python
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",   # resolves to "Gene_Name"
    to_type="uniprot_id",      # resolves to "UniProtKB_AC-ID"
    database="uniprot",
)
```

Supported ID types (universal alias → native):

| Universal alias | Native field |
|-----------------|-------------|
| `gene_symbol` | `Gene_Name` |
| `ensembl_gene_id` | `Ensembl` |
| `entrez_id` | `GeneID` |
| `uniprot_id` | `UniProtKB_AC-ID` |
| `refseq_protein` | `RefSeq_Protein` |
| `pdb_id` | `PDB` |

### BioMart

Uses Ensembl BioMart. Supports the widest variety of ID types but is slower and less
reliable than the other options for simple symbol translations.

```python
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",        # resolves to "external_gene_name"
    to_type="ensembl_transcript_id", # unique to BioMart
    database="biomart",
)
```

Supported ID types (universal alias → native):

| Universal alias | Native field |
|-----------------|-------------|
| `gene_symbol` | `external_gene_name` |
| `ensembl_gene_id` | `ensembl_gene_id` |
| `ensembl_transcript_id` | `ensembl_transcript_id` |
| `ensembl_protein_id` | `ensembl_peptide_id` |
| `entrez_id` | `entrezgene_id` |
| `hgnc_id` | `hgnc_id` |
| `hgnc_symbol` | `hgnc_symbol` |
| `uniprot_id` | `uniprot_gn_id` |
| `refseq_mrna` | `refseq_mrna` |
| `refseq_protein` | `refseq_peptide` |

### HGNC

Uses the HGNC REST API. Authoritative source for approved human gene symbols, HGNC IDs,
and aliases. **Human genes only.**

```python
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",   # resolves to "symbol"
    to_type="hgnc_id",         # resolves to "hgnc_id"
    database="hgnc",
)

result = translate_gene_ids(
    ["HGNC:11998", "HGNC:1100"],
    from_type="hgnc_id",
    to_type="ensembl_gene_id",
    database="hgnc",
)
```

Supported ID types (universal alias → native):

| Universal alias | Native field |
|-----------------|-------------|
| `gene_symbol` / `hgnc_symbol` | `symbol` |
| `hgnc_id` | `hgnc_id` |
| `entrez_id` | `entrez_id` |
| `ensembl_gene_id` | `ensembl_gene_id` |
| `uniprot_id` | `uniprot_ids` |
| `refseq_mrna` / `refseq_protein` | `refseq_accession` |

## Multiple Target Types

Pass a list to `to_type` to retrieve several ID types in one call:

```python
result = translate_gene_ids(
    ["TP53", "BRCA1", "EGFR"],
    from_type="gene_symbol",
    to_type=["ensembl_gene_id", "entrez_id", "hgnc_id"],
    database="biomart",
)
#   gene_symbol    ensembl_gene_id  entrez_id     hgnc_id
# 0        TP53  ENSG00000141510       7157  HGNC:11998
# 1       BRCA1  ENSG00000012048        672   HGNC:1100
# 2        EGFR  ENSG00000146648       1956   HGNC:3236

# As nested dict
result = translate_gene_ids(
    ["TP53", "BRCA1"],
    from_type="gene_symbol",
    to_type=["ensembl_gene_id", "entrez_id"],
    return_dict=True,
)
# {'TP53': {'ensembl_gene_id': 'ENSG00000141510', 'entrez_id': '7157'}, ...}
```

## KEGG Translation

`translate_gene_ids_kegg` uses KEGG's `conv` endpoint, which maps between KEGG
organism-specific gene IDs and external databases.

```python
from biodbs.translate import translate_gene_ids_kegg

# KEGG IDs → Entrez Gene IDs
result = translate_gene_ids_kegg(
    ["hsa:7157", "hsa:672"],
    from_db="hsa",
    to_db="ncbi-geneid",
)

# KEGG IDs → UniProt accessions
result = translate_gene_ids_kegg(
    ["hsa:7157"],
    from_db="hsa",
    to_db="uniprot",
)
```

### KEGG database codes

| Code | Description |
|------|-------------|
| `hsa` | Human genes |
| `mmu` | Mouse genes |
| `rno` | Rat genes |
| `ncbi-geneid` | NCBI Entrez Gene ID |
| `ncbi-proteinid` | NCBI Protein ID |
| `uniprot` | UniProt accession |

## Species Support

All databases except HGNC support multiple species:

```python
result = translate_gene_ids(ids, from_type="gene_symbol",
                             to_type="ensembl_gene_id", species="mouse")
```

Accepted values for `species`: `"human"` (default), `"mouse"`, `"rat"`,
`"zebrafish"`, `"fly"`, `"worm"`, `"yeast"` — or a `Species` enum member.

## Return Formats

```python
# DataFrame (default) — one row per input ID
df = translate_gene_ids(ids, from_type="gene_symbol", to_type="entrez_id")

# Dict — {input_id: translated_id} for single target
mapping = translate_gene_ids(ids, from_type="gene_symbol",
                              to_type="entrez_id", return_dict=True)
# {'TP53': '7157', 'BRCA1': '672', ...}

# Dict — {input_id: {target: value, ...}} for multiple targets
mapping = translate_gene_ids(ids, from_type="gene_symbol",
                              to_type=["entrez_id", "ensembl_gene_id"],
                              return_dict=True)
# {'TP53': {'entrez_id': '7157', 'ensembl_gene_id': 'ENSG00000141510'}, ...}
```

## Related Resources

- **[HGNC](../fetch/hgnc.md)** — Direct HGNC API access (symbol search, cross-reference lookup).
- **[BioMart](../fetch/biomart.md)** — Batch gene annotation queries.
- **[Ensembl](../fetch/ensembl.md)** — REST API for detailed gene lookups.
- **[NCBI](../fetch/ncbi.md)** — NCBI Gene database.
- **[UniProt](../fetch/uniprot.md)** — Protein-centric ID mapping.
- **[KEGG](../fetch/kegg.md)** — KEGG gene identifiers.
- **[Protein ID Translation](proteins.md)** — Gene ↔ UniProt mapping convenience functions.
- **[Over-Representation Analysis](../analysis/ora.md)** — Translate IDs before pathway enrichment.
