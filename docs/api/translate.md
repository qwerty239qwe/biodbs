# Translate Module API Reference

Complete reference for `biodbs.translate` module.

## Quick Import

```python
from biodbs.translate import (
    # Gene translation
    translate_gene_ids,
    translate_gene_ids_kegg,
    # Chemical translation
    translate_chemical_ids,
    translate_chemical_ids_kegg,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
    # Protein translation
    translate_protein_ids,
    translate_gene_to_uniprot,
    translate_uniprot_to_gene,
    translate_uniprot_to_pdb,
    translate_uniprot_to_ensembl,
    translate_uniprot_to_refseq,
)
```

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

### Gene ID Types (BioMart)

| ID Type | Description |
|---------|-------------|
| `ensembl_gene_id` | Ensembl gene ID |
| `ensembl_transcript_id` | Ensembl transcript ID |
| `external_gene_name` | Gene symbol |
| `hgnc_symbol` | HGNC symbol |
| `hgnc_id` | HGNC ID |
| `entrezgene_id` | NCBI Entrez ID |
| `uniprot_gn_id` | UniProt gene name |
| `refseq_mrna` | RefSeq mRNA ID |

### Protein ID Types (UniProt)

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
