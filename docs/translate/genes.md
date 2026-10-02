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
| `ensembl_transcript_id` | `ensembl_transcript_id` | — | — | `ensembl_transcript_id` | — |
| `ensembl_protein_id` | `ensembl_peptide_id` | — | — | `ensembl_protein_id` | — |
| `entrez_id` | `entrezgene_id` | `gene_id` | `GeneID` | `EntrezGene` | `entrez_id` |
| `hgnc_id` | `hgnc_id` | — | — | — | `hgnc_id` |
| `hgnc_symbol` | `hgnc_symbol` | — | — | — | `symbol` |
| `uniprot_id` | `uniprot_gn_id` | `uniprot` | `UniProtKB_AC-ID` | `Uniprot_gn` | `uniprot_ids` |
| `refseq_mrna` | `refseq_mrna` | `refseq_accession` | — | `RefSeq_mRNA` | `refseq_accession` |
| `refseq_protein` | `refseq_peptide` | `refseq_protein` | `RefSeq_Protein` | `RefSeq_peptide` | — |
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
| `refseq_mrna` | `refseq_accession` |
| `refseq_protein` | `refseq_protein` |

Explicit-ID queries follow all result pages. RefSeq inputs are queried separately
per unique accession because batched Datasets reports do not identify which
accession matched each gene. This avoids guessing associations, but costs more
requests than a symbol/Entrez batch.

Current Datasets gene reports provide transcript/protein counts, not their
accessions; RefSeq **output** mappings can therefore be missing. Use UniProt for
RefSeq protein output, or BioMart/Ensembl for transcript output.

### Ensembl REST

Uses the Ensembl `/xrefs` endpoint. Natural choice when starting from Ensembl IDs.

Symbol inputs are resolved to a gene, then translated to the requested target
namespace. Transcript/protein output follows the canonical transcript when
available, otherwise the first transcript. Same-type stable-ID conversions return
the input unchanged without a request; this does not validate that the ID exists.
Repeated inputs share one lookup within a single-target call.

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
    to_type="ensembl_transcript_id",
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
| `refseq_mrna` | `refseq_accession` |

HGNC does not provide RefSeq protein identifiers. Requesting the universal
`refseq_protein` alias raises `ValueError`; use `database="uniprot"` instead.

## Multiple Target Types

Pass a list to `to_type` to retrieve several ID types in one call:

```python
result = translate_gene_ids(
    ["TP53", "BRCA1", "EGFR"],
    from_type="gene_symbol",
    to_type=["ensembl_gene_id", "entrez_id", "hgnc_id"],
    database="biomart",
)
#   external_gene_name    ensembl_gene_id  entrezgene_id     hgnc_id
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
# {'TP53': {'ensembl_gene_id': 'ENSG00000141510', 'gene_id': '7157'}, ...}
```

Output columns and nested dictionary keys use database-native names, not the
universal aliases. Multiple-target DataFrames preserve input order and duplicate
rows, with missing mappings represented as empty values. Dictionaries necessarily
collapse duplicate input keys.

HGNC fetches each unique input once and extracts all targets from that record.
Other gene backends currently execute a separate conversion for each target.

## Accuracy and Performance Checks

`tests/test_translate/test_quality.py` checks exact reference IDs, namespaces,
input-key association, missing values, duplicate rows, and pagination. Its live
tests cover human/mouse genes, RefSeq input mapping, protein accessions, aspirin,
caffeine, and the ChEMBL–PubChem aspirin round trip. These are reference checks,
not an estimate of accuracy for every organism or ambiguous identifier.

Offline performance checks assert request counts rather than flaky time limits.
For two unique HGNC inputs repeated in a batch, with two target types:

| Input rows | Lookups before | Lookups after | Median offline processing after |
|------------|----------------|---------------|---------------------------------|
| 20 | 40 | 2 | 0.22 ms |
| 200 | 400 | 2 | 0.43 ms |
| 2,000 | 4,000 | 2 | 0.69 ms |

Measurements are five-run medians on the development machine, using mocked
responses with no network delay. The optimized output also retains every input
row; the previous multi-target output collapsed duplicates. Fully unique HGNC
inputs still require one lookup each. No persistent cache or new dependency was
added.

In the 2026-10-03 nine-case live reference run, Ensembl took 121.6 seconds; the
other eight cases took 0.8–6.6 seconds each. These are individual observations, not latency
guarantees or a throughput benchmark. Service latency, retries, and rate limits
can dominate large online jobs.

Scalar dictionaries and multi-target output can select one ID from a one-to-many
mapping. BioMart dictionaries retain the last non-missing match; most other
backends select the first. Use full mapping tables or the list-valued UniProt
fetch helpers when all isoforms/cross-references matter. Pin source releases for
reproducible analyses.

Run the offline checks without network access:

```bash
python -m pytest tests/test_translate tests/test_taxonomy -m "not integration" -q
```

Run the reference checks against live APIs:

```bash
python -m pytest tests/test_translate/test_quality.py -m integration -q --durations=20
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
