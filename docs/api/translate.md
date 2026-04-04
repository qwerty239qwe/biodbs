# Translate Module API Reference

Complete reference for `biodbs.translate` module.

## Key Features

- **Universal ID aliases**: Use `GeneIDType` enum values (e.g. `"gene_symbol"`, `"entrez_id"`)
  instead of database-native field names — the correct name is resolved per backend automatically.
- **Multiple Target Types**: All main translation functions accept either a single target type
  or a list. When a list is provided, all target IDs are returned in one call.

```python
from biodbs.translate import translate_gene_ids, GeneIDType

# Universal alias (works with any database)
result = translate_gene_ids(["TP53"], from_type="gene_symbol", to_type="ensembl_gene_id")

# Enum members are equivalent
result = translate_gene_ids(["TP53"], from_type=GeneIDType.GENE_SYMBOL,
                             to_type=GeneIDType.ENSEMBL_GENE_ID)

# Multiple target types — more efficient than multiple calls
result = translate_gene_ids(
    ["TP53"],
    from_type="gene_symbol",
    to_type=["ensembl_gene_id", "entrez_id", "hgnc_id"]
)
```

## Enums

### GeneIDType

::: biodbs._funcs.translate._id_types.GeneIDType
    options:
      show_root_heading: true
      show_source: false
      members_order: source

### TranslationDatabase

::: biodbs._funcs.translate._id_types.TranslationDatabase
    options:
      show_root_heading: true
      show_source: false
      members_order: source

---

## Functions Summary

### Gene Translation

| Function | Description |
|----------|-------------|
| [`translate_gene_ids`](#translate_gene_ids) | Translate gene IDs between databases |
| [`translate_gene_ids_kegg`](#translate_gene_ids_kegg) | Translate gene IDs using KEGG API |

### Chemical Translation

| Function | Description |
|----------|-------------|
| [`translate_chemical_ids`](#translate_chemical_ids) | Translate chemical IDs via PubChem |
| [`translate_chemical_ids_kegg`](#translate_chemical_ids_kegg) | Translate chemical IDs using KEGG API |
| [`translate_chembl_to_pubchem`](#translate_chembl_to_pubchem) | Map ChEMBL IDs to PubChem CIDs |
| [`translate_pubchem_to_chembl`](#translate_pubchem_to_chembl) | Map PubChem CIDs to ChEMBL IDs |

### Protein Translation

| Function | Description |
|----------|-------------|
| [`translate_protein_ids`](#translate_protein_ids) | Translate protein IDs via UniProt ID mapping |
| [`translate_gene_to_uniprot`](#translate_gene_to_uniprot) | Map gene symbols to UniProt accessions |
| [`translate_uniprot_to_gene`](#translate_uniprot_to_gene) | Map UniProt accessions to gene symbols |
| [`translate_uniprot_to_pdb`](#translate_uniprot_to_pdb) | Map UniProt accessions to PDB IDs |
| [`translate_uniprot_to_ensembl`](#translate_uniprot_to_ensembl) | Map UniProt accessions to Ensembl gene IDs |
| [`translate_uniprot_to_refseq`](#translate_uniprot_to_refseq) | Map UniProt accessions to RefSeq protein IDs |

---

## Gene Translation

### translate_gene_ids

::: biodbs._funcs.translate.genes.translate_gene_ids
    options:
      show_root_heading: true
      show_source: false

### translate_gene_ids_kegg

::: biodbs._funcs.translate.genes.translate_gene_ids_kegg
    options:
      show_root_heading: true
      show_source: false

---

## Chemical Translation

### translate_chemical_ids

::: biodbs._funcs.translate.chem.translate_chemical_ids
    options:
      show_root_heading: true
      show_source: false

### translate_chemical_ids_kegg

::: biodbs._funcs.translate.chem.translate_chemical_ids_kegg
    options:
      show_root_heading: true
      show_source: false

### translate_chembl_to_pubchem

::: biodbs._funcs.translate.chem.translate_chembl_to_pubchem
    options:
      show_root_heading: true
      show_source: false

### translate_pubchem_to_chembl

::: biodbs._funcs.translate.chem.translate_pubchem_to_chembl
    options:
      show_root_heading: true
      show_source: false

---

## Protein Translation

### translate_protein_ids

::: biodbs._funcs.translate.proteins.translate_protein_ids
    options:
      show_root_heading: true
      show_source: false

### translate_gene_to_uniprot

::: biodbs._funcs.translate.proteins.translate_gene_to_uniprot
    options:
      show_root_heading: true
      show_source: false

### translate_uniprot_to_gene

::: biodbs._funcs.translate.proteins.translate_uniprot_to_gene
    options:
      show_root_heading: true
      show_source: false

### translate_uniprot_to_pdb

::: biodbs._funcs.translate.proteins.translate_uniprot_to_pdb
    options:
      show_root_heading: true
      show_source: false

### translate_uniprot_to_ensembl

::: biodbs._funcs.translate.proteins.translate_uniprot_to_ensembl
    options:
      show_root_heading: true
      show_source: false

### translate_uniprot_to_refseq

::: biodbs._funcs.translate.proteins.translate_uniprot_to_refseq
    options:
      show_root_heading: true
      show_source: false

---

## ID Type Reference

### Universal Gene ID Aliases

Use these values for `from_type` / `to_type` in `translate_gene_ids`. The correct
database-native name is resolved automatically per backend.

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

Native database strings (e.g. `"external_gene_name"`) are also accepted and passed through unchanged.

### Protein ID Types (UniProt mapping)

| ID Type | Description |
|---------|-------------|
| `UniProtKB_AC-ID` | UniProt accession |
| `Gene_Name` | Gene symbol |
| `GeneID` | NCBI Gene ID |
| `Ensembl` | Ensembl gene ID |
| `RefSeq_Protein` | RefSeq protein ID |
| `PDB` | PDB structure ID |

### Chemical ID Types (PubChem)

| ID Type | Description |
|---------|-------------|
| `name` | Compound name |
| `cid` | PubChem CID |
| `smiles` | SMILES string |
| `inchikey` | InChIKey |
| `formula` | Molecular formula |
