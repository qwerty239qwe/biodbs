# Fetch Module API Reference

Complete reference for `biodbs.fetch` module.

## Summary

### Fetcher Classes

| Class | Description |
|-------|-------------|
| [`UniProt_Fetcher`](#uniprot_fetcher) | Fetch protein data from UniProt REST API |
| [`PubChem_Fetcher`](#pubchem_fetcher) | Fetch chemical data from PubChem PUG REST/View APIs |
| [`Ensembl_Fetcher`](#ensembl_fetcher) | Fetch genomic data from Ensembl REST API |
| [`BioMart_Fetcher`](#biomart_fetcher) | Query Ensembl BioMart for gene annotations |
| [`KEGG_Fetcher`](#kegg_fetcher) | Fetch pathway and gene data from KEGG API |
| [`ChEMBL_Fetcher`](#chembl_fetcher) | Fetch bioactivity data from ChEMBL API |
| [`QuickGO_Fetcher`](#quickgo_fetcher) | Fetch GO annotations from QuickGO API |
| [`HPA_Fetcher`](#hpa_fetcher) | Fetch protein expression from Human Protein Atlas |
| [`NCBI_Fetcher`](#ncbi_fetcher) | Fetch gene data from NCBI Entrez |
| [`FDA_Fetcher`](#fda_fetcher) | Fetch drug/device data from openFDA |
| [`Reactome_Fetcher`](#reactome_fetcher) | Fetch pathway data from Reactome |
| [`DO_Fetcher`](#do_fetcher) | Fetch disease terms from Disease Ontology |
| [`EnrichR_Fetcher`](#enrichr_fetcher) | Perform gene set enrichment via EnrichR |
| [`HGNC_Fetcher`](#hgnc_fetcher) | Fetch gene nomenclature from HGNC |
| [`ClinVar_Fetcher`](#clinvar_fetcher) | Fetch clinical variant data from ClinVar |
| [`LPSN_Fetcher`](#lpsn_fetcher) | Fetch prokaryotic nomenclature records from LPSN |

### UniProt Functions

| Function | Description |
|----------|-------------|
| [`uniprot_get_entry`](#uniprot_get_entry) | Get a single UniProt entry by accession |
| [`uniprot_search`](#uniprot_search) | Search UniProtKB with query |
| [`uniprot_search_by_gene`](#uniprot_search_by_gene) | Search by gene name |
| [`gene_to_uniprot`](#gene_to_uniprot) | Map gene symbols to UniProt accessions |
| [`uniprot_map_ids`](#uniprot_map_ids) | Map IDs between databases |

### PubChem Functions

| Function | Description |
|----------|-------------|
| [`pubchem_get_compound`](#pubchem_get_compound) | Get compound record by CID |
| [`pubchem_search_by_name`](#pubchem_search_by_name) | Search compounds by name |
| [`pubchem_get_properties`](#pubchem_get_properties) | Get compound properties |

### LPSN Functions

| Function | Description |
|----------|-------------|
| [`lpsn_fetch`](#lpsn_fetch) | Fetch LPSN records by ID |
| [`lpsn_advanced_search`](#lpsn_advanced_search) | Search LPSN with documented parameters |
| [`lpsn_flexible_search`](#lpsn_flexible_search) | Search LPSN by JSON field matches |
| [`lpsn_search_and_fetch`](#lpsn_search_and_fetch) | Search IDs and fetch full records |

### Ensembl Functions

| Function | Description |
|----------|-------------|
| [`ensembl_lookup`](#ensembl_lookup) | Lookup entity by Ensembl ID |
| [`ensembl_lookup_symbol`](#ensembl_lookup_symbol) | Lookup by gene symbol |
| [`ensembl_get_sequence`](#ensembl_get_sequence) | Get nucleotide/protein sequence |
| [`ensembl_get_xrefs`](#ensembl_get_xrefs) | Get cross-references |

### BioMart Functions

| Function | Description |
|----------|-------------|
| [`biomart_get_genes`](#biomart_get_genes) | Get gene annotations by Ensembl IDs |
| [`biomart_convert_ids`](#biomart_convert_ids) | Convert between gene ID types |
| [`biomart_query`](#biomart_query) | Custom BioMart query |

### KEGG Functions

| Function | Description |
|----------|-------------|
| [`kegg_list`](#kegg_list) | List entries in a KEGG database |
| [`kegg_get`](#kegg_get) | Get KEGG entry by ID |
| [`kegg_link`](#kegg_link) | Get cross-references between databases |
| [`kegg_conv`](#kegg_conv) | Convert between KEGG and external IDs |

### ChEMBL Functions

| Function | Description |
|----------|-------------|
| [`chembl_get_molecule`](#chembl_get_molecule) | Get molecule by ChEMBL ID |
| [`chembl_search_molecules`](#chembl_search_molecules) | Search molecules by name |
| [`chembl_get_approved_drugs`](#chembl_get_approved_drugs) | Get approved drugs list |

### QuickGO Functions

| Function | Description |
|----------|-------------|
| [`quickgo_search_annotations`](#quickgo_search_annotations) | Search GO annotations |
| [`quickgo_get_terms`](#quickgo_get_terms) | Get GO term details |

### HPA Functions

| Function | Description |
|----------|-------------|
| [`hpa_get_gene`](#hpa_get_gene) | Get gene expression data |
| [`hpa_get_tissue_expression`](#hpa_get_tissue_expression) | Get tissue-level expression |

### NCBI Functions

| Function | Description |
|----------|-------------|
| [`ncbi_get_gene`](#ncbi_get_gene) | Get gene info by Entrez ID |
| [`ncbi_symbol_to_id`](#ncbi_symbol_to_id) | Convert gene symbol to Entrez ID |

### FDA Functions

| Function | Description |
|----------|-------------|
| [`fda_search`](#fda_search) | Search openFDA endpoints |
| [`fda_drug_events`](#fda_drug_events) | Search drug adverse events |

### Reactome Functions

| Function | Description |
|----------|-------------|
| [`reactome_analyze`](#reactome_analyze) | Analyze gene list against Reactome |

### Disease Ontology Functions

| Function | Description |
|----------|-------------|
| [`do_get_term`](#do_get_term) | Get disease term by DOID |
| [`do_get_children`](#do_get_children) | Get child terms |

### EnrichR Functions

| Function | Description |
|----------|-------------|
| [`enrichr_enrich`](#enrichr_enrich) | Perform enrichment analysis |
| [`enrichr_get_libraries`](#enrichr_get_libraries) | List available gene set libraries |

### HGNC Functions

| Function | Description |
|----------|-------------|
| [`hgnc_fetch`](#hgnc_fetch) | Exact-match lookup by any HGNC field |
| [`hgnc_search`](#hgnc_search) | Wildcard / boolean search across HGNC |
| [`hgnc_fetch_by_symbol`](#hgnc_fetch_by_symbol) | Fetch gene by approved symbol |
| [`hgnc_fetch_by_hgnc_id`](#hgnc_fetch_by_hgnc_id) | Fetch gene by HGNC ID |
| [`hgnc_fetch_by_entrez_id`](#hgnc_fetch_by_entrez_id) | Fetch gene by Entrez Gene ID |
| [`hgnc_fetch_by_ensembl_id`](#hgnc_fetch_by_ensembl_id) | Fetch gene by Ensembl gene ID |
| [`hgnc_fetch_by_uniprot_id`](#hgnc_fetch_by_uniprot_id) | Fetch gene by UniProt accession |
| [`hgnc_fetch_by_refseq`](#hgnc_fetch_by_refseq) | Fetch gene by RefSeq accession |
| [`hgnc_search_symbol`](#hgnc_search_symbol) | Wildcard search on gene symbols |
| [`hgnc_info`](#hgnc_info) | Return HGNC service metadata |

### ClinVar Functions

| Function | Description |
|----------|-------------|
| [`clinvar_search`](#clinvar_search) | Search ClinVar with an Entrez query string |
| [`clinvar_count`](#clinvar_count) | Count ClinVar records matching a query |
| [`clinvar_fetch_by_id`](#clinvar_fetch_by_id) | Fetch variant summaries by variation UID |
| [`clinvar_search_gene`](#clinvar_search_gene) | Search and fetch variants for a gene |
| [`clinvar_search_condition`](#clinvar_search_condition) | Search and fetch variants for a condition |
| [`clinvar_fetch_vcv`](#clinvar_fetch_vcv) | Fetch full VCV XML record |
| [`clinvar_fetch_rcv`](#clinvar_fetch_rcv) | Fetch full RCV XML record |
| [`clinvar_link_pubmed`](#clinvar_link_pubmed) | Get PubMed IDs linked to a variation |

---

## Fetcher Classes

### UniProt_Fetcher

::: biodbs.fetch.uniprot.uniprot_fetcher.UniProt_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### PubChem_Fetcher

::: biodbs.fetch.pubchem.pubchem_fetcher.PubChem_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### Ensembl_Fetcher

::: biodbs.fetch.ensembl.ensembl_fetcher.Ensembl_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### BioMart_Fetcher

::: biodbs.fetch.biomart.biomart_fetcher.BioMart_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### KEGG_Fetcher

::: biodbs.fetch.KEGG.kegg_fetcher.KEGG_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### ChEMBL_Fetcher

::: biodbs.fetch.ChEMBL.chembl_fetcher.ChEMBL_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### QuickGO_Fetcher

::: biodbs.fetch.QuickGO.quickgo_fetcher.QuickGO_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### HPA_Fetcher

::: biodbs.fetch.HPA.hpa_fetcher.HPA_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### NCBI_Fetcher

::: biodbs.fetch.NCBI.ncbi_fetcher.NCBI_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### FDA_Fetcher

::: biodbs.fetch.FDA.fda_fetcher.FDA_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### Reactome_Fetcher

::: biodbs.fetch.Reactome.reactome_fetcher.Reactome_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### DO_Fetcher

::: biodbs.fetch.DiseaseOntology.do_fetcher.DO_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### EnrichR_Fetcher

::: biodbs.fetch.EnrichR.enrichr_fetcher.EnrichR_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### HGNC_Fetcher

::: biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

### ClinVar_Fetcher

::: biodbs.fetch.ClinVar.clinvar_fetcher.ClinVar_Fetcher
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_bases: false

---

## UniProt

### uniprot_get_entry

::: biodbs.fetch.uniprot.funcs.uniprot_get_entry
    options:
      show_root_heading: true
      show_source: false

### uniprot_search

::: biodbs.fetch.uniprot.funcs.uniprot_search
    options:
      show_root_heading: true
      show_source: false

### uniprot_search_by_gene

::: biodbs.fetch.uniprot.funcs.uniprot_search_by_gene
    options:
      show_root_heading: true
      show_source: false

### gene_to_uniprot

::: biodbs.fetch.uniprot.funcs.gene_to_uniprot
    options:
      show_root_heading: true
      show_source: false

### uniprot_map_ids

::: biodbs.fetch.uniprot.funcs.uniprot_map_ids
    options:
      show_root_heading: true
      show_source: false

---

## PubChem

### pubchem_get_compound

::: biodbs.fetch.pubchem.funcs.pubchem_get_compound
    options:
      show_root_heading: true
      show_source: false

### pubchem_search_by_name

::: biodbs.fetch.pubchem.funcs.pubchem_search_by_name
    options:
      show_root_heading: true
      show_source: false

### pubchem_get_properties

::: biodbs.fetch.pubchem.funcs.pubchem_get_properties
    options:
      show_root_heading: true
      show_source: false

---

## Ensembl

### ensembl_lookup

::: biodbs.fetch.ensembl.funcs.ensembl_lookup
    options:
      show_root_heading: true
      show_source: false

### ensembl_lookup_symbol

::: biodbs.fetch.ensembl.funcs.ensembl_lookup_symbol
    options:
      show_root_heading: true
      show_source: false

### ensembl_get_sequence

::: biodbs.fetch.ensembl.funcs.ensembl_get_sequence
    options:
      show_root_heading: true
      show_source: false

### ensembl_get_xrefs

::: biodbs.fetch.ensembl.funcs.ensembl_get_xrefs
    options:
      show_root_heading: true
      show_source: false

---

## BioMart

### biomart_get_genes

::: biodbs.fetch.biomart.funcs.biomart_get_genes
    options:
      show_root_heading: true
      show_source: false

### biomart_convert_ids

::: biodbs.fetch.biomart.funcs.biomart_convert_ids
    options:
      show_root_heading: true
      show_source: false

### biomart_query

::: biodbs.fetch.biomart.funcs.biomart_query
    options:
      show_root_heading: true
      show_source: false

---

## KEGG

### kegg_list

::: biodbs.fetch.KEGG.funcs.kegg_list
    options:
      show_root_heading: true
      show_source: false

### kegg_get

::: biodbs.fetch.KEGG.funcs.kegg_get
    options:
      show_root_heading: true
      show_source: false

### kegg_link

::: biodbs.fetch.KEGG.funcs.kegg_link
    options:
      show_root_heading: true
      show_source: false

### kegg_conv

::: biodbs.fetch.KEGG.funcs.kegg_conv
    options:
      show_root_heading: true
      show_source: false

---

## ChEMBL

### chembl_get_molecule

::: biodbs.fetch.ChEMBL.funcs.chembl_get_molecule
    options:
      show_root_heading: true
      show_source: false

### chembl_search_molecules

::: biodbs.fetch.ChEMBL.funcs.chembl_search_molecules
    options:
      show_root_heading: true
      show_source: false

### chembl_get_approved_drugs

::: biodbs.fetch.ChEMBL.funcs.chembl_get_approved_drugs
    options:
      show_root_heading: true
      show_source: false

---

## QuickGO

### quickgo_search_annotations

::: biodbs.fetch.QuickGO.funcs.quickgo_search_annotations
    options:
      show_root_heading: true
      show_source: false

### quickgo_get_terms

::: biodbs.fetch.QuickGO.funcs.quickgo_get_terms
    options:
      show_root_heading: true
      show_source: false

---

## HPA (Human Protein Atlas)

### hpa_get_gene

::: biodbs.fetch.HPA.funcs.hpa_get_gene
    options:
      show_root_heading: true
      show_source: false

### hpa_get_tissue_expression

::: biodbs.fetch.HPA.funcs.hpa_get_tissue_expression
    options:
      show_root_heading: true
      show_source: false

---

## NCBI

### ncbi_get_gene

::: biodbs.fetch.NCBI.funcs.ncbi_get_gene
    options:
      show_root_heading: true
      show_source: false

### ncbi_symbol_to_id

::: biodbs.fetch.NCBI.funcs.ncbi_symbol_to_id
    options:
      show_root_heading: true
      show_source: false

---

## FDA

### fda_search

::: biodbs.fetch.FDA.funcs.fda_search
    options:
      show_root_heading: true
      show_source: false

### fda_drug_events

::: biodbs.fetch.FDA.funcs.fda_drug_events
    options:
      show_root_heading: true
      show_source: false

---

## Reactome

### reactome_analyze

::: biodbs.fetch.Reactome.funcs.reactome_analyze
    options:
      show_root_heading: true
      show_source: false

---

## Disease Ontology

### do_get_term

::: biodbs.fetch.DiseaseOntology.funcs.do_get_term
    options:
      show_root_heading: true
      show_source: false

### do_get_children

::: biodbs.fetch.DiseaseOntology.funcs.do_get_children
    options:
      show_root_heading: true
      show_source: false

---

## EnrichR

### enrichr_enrich

::: biodbs.fetch.EnrichR.funcs.enrichr_enrich
    options:
      show_root_heading: true
      show_source: false

### enrichr_get_libraries

::: biodbs.fetch.EnrichR.funcs.enrichr_get_libraries
    options:
      show_root_heading: true
      show_source: false

---

## HGNC

### hgnc_fetch

::: biodbs.fetch.HGNC.funcs.hgnc_fetch
    options:
      show_root_heading: true
      show_source: false

### hgnc_search

::: biodbs.fetch.HGNC.funcs.hgnc_search
    options:
      show_root_heading: true
      show_source: false

### hgnc_fetch_by_symbol

::: biodbs.fetch.HGNC.funcs.hgnc_fetch_by_symbol
    options:
      show_root_heading: true
      show_source: false

### hgnc_fetch_by_hgnc_id

::: biodbs.fetch.HGNC.funcs.hgnc_fetch_by_hgnc_id
    options:
      show_root_heading: true
      show_source: false

### hgnc_fetch_by_entrez_id

::: biodbs.fetch.HGNC.funcs.hgnc_fetch_by_entrez_id
    options:
      show_root_heading: true
      show_source: false

### hgnc_fetch_by_ensembl_id

::: biodbs.fetch.HGNC.funcs.hgnc_fetch_by_ensembl_id
    options:
      show_root_heading: true
      show_source: false

### hgnc_fetch_by_uniprot_id

::: biodbs.fetch.HGNC.funcs.hgnc_fetch_by_uniprot_id
    options:
      show_root_heading: true
      show_source: false

### hgnc_fetch_by_refseq

::: biodbs.fetch.HGNC.funcs.hgnc_fetch_by_refseq
    options:
      show_root_heading: true
      show_source: false

### hgnc_search_symbol

::: biodbs.fetch.HGNC.funcs.hgnc_search_symbol
    options:
      show_root_heading: true
      show_source: false

### hgnc_info

::: biodbs.fetch.HGNC.funcs.hgnc_info
    options:
      show_root_heading: true
      show_source: false

---

## ClinVar

### clinvar_search

::: biodbs.fetch.ClinVar.funcs.clinvar_search
    options:
      show_root_heading: true
      show_source: false

### clinvar_count

::: biodbs.fetch.ClinVar.funcs.clinvar_count
    options:
      show_root_heading: true
      show_source: false

### clinvar_fetch_by_id

::: biodbs.fetch.ClinVar.funcs.clinvar_fetch_by_id
    options:
      show_root_heading: true
      show_source: false

### clinvar_search_gene

::: biodbs.fetch.ClinVar.funcs.clinvar_search_gene
    options:
      show_root_heading: true
      show_source: false

### clinvar_search_condition

::: biodbs.fetch.ClinVar.funcs.clinvar_search_condition
    options:
      show_root_heading: true
      show_source: false

### clinvar_fetch_vcv

::: biodbs.fetch.ClinVar.funcs.clinvar_fetch_vcv
    options:
      show_root_heading: true
      show_source: false

### clinvar_fetch_rcv

::: biodbs.fetch.ClinVar.funcs.clinvar_fetch_rcv
    options:
      show_root_heading: true
      show_source: false

### clinvar_link_pubmed

::: biodbs.fetch.ClinVar.funcs.clinvar_link_pubmed
    options:
      show_root_heading: true
      show_source: false

---

## LPSN

### LPSN_Fetcher

::: biodbs.fetch.LPSN.lpsn_fetcher.LPSN_Fetcher
    options:
      show_root_heading: true
      show_source: false

### lpsn_fetch

::: biodbs.fetch.LPSN.funcs.lpsn_fetch
    options:
      show_root_heading: true
      show_source: false

### lpsn_advanced_search

::: biodbs.fetch.LPSN.funcs.lpsn_advanced_search
    options:
      show_root_heading: true
      show_source: false

### lpsn_flexible_search

::: biodbs.fetch.LPSN.funcs.lpsn_flexible_search
    options:
      show_root_heading: true
      show_source: false

### lpsn_search_and_fetch

::: biodbs.fetch.LPSN.funcs.lpsn_search_and_fetch
    options:
      show_root_heading: true
      show_source: false

---

## Rate Limiting

| Function/Class | Description |
|----------------|-------------|
| `RateLimiter` | Global rate limiter for API calls |
| `get_rate_limiter` | Get the singleton rate limiter instance |
| `request_with_retry` | Make HTTP request with retry logic |
