# Fetch Module API Reference

Complete reference for `biodbs.fetch` module.

---

## UniProt

```python
from biodbs.fetch import (
    uniprot_get_entry,
    uniprot_get_entries,
    uniprot_search,
    uniprot_search_by_gene,
    uniprot_search_by_keyword,
    gene_to_uniprot,
    uniprot_to_gene,
    uniprot_get_sequences,
    uniprot_map_ids,
)
```

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

```python
from biodbs.fetch import (
    pubchem_get_compound,
    pubchem_get_compounds,
    pubchem_search_by_name,
    pubchem_search_by_smiles,
    pubchem_search_by_inchikey,
    pubchem_search_by_formula,
    pubchem_get_properties,
    pubchem_get_synonyms,
    pubchem_get_description,
    pubchem_get_safety,
    pubchem_get_pharmacology,
    pubchem_get_drug_info,
)
```

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

```python
from biodbs.fetch import (
    ensembl_lookup,
    ensembl_lookup_batch,
    ensembl_lookup_symbol,
    ensembl_get_sequence,
    ensembl_get_sequence_batch,
    ensembl_get_sequence_region,
    ensembl_get_overlap_id,
    ensembl_get_overlap_region,
    ensembl_get_xrefs,
    ensembl_get_xrefs_symbol,
    ensembl_get_homology,
    ensembl_get_homology_symbol,
    ensembl_get_variation,
    ensembl_vep_hgvs,
    ensembl_vep_id,
    ensembl_vep_region,
    ensembl_map_assembly,
    ensembl_get_phenotype_gene,
    ensembl_get_phenotype_region,
    ensembl_get_ontology_term,
    ensembl_get_ontology_ancestors,
    ensembl_get_ontology_descendants,
    ensembl_get_genetree,
    ensembl_get_genetree_member,
    ensembl_get_assembly_info,
    ensembl_get_species_info,
)
```

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

```python
from biodbs.fetch import (
    biomart_get_genes,
    biomart_get_genes_by_name,
    biomart_get_genes_by_region,
    biomart_get_transcripts,
    biomart_get_go_annotations,
    biomart_get_homologs,
    biomart_convert_ids,
    biomart_query,
    biomart_list_datasets,
    biomart_list_attributes,
    biomart_list_filters,
)
```

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

```python
from biodbs.fetch import (
    kegg_info,
    kegg_list,
    kegg_find,
    kegg_get,
    kegg_get_batch,
    kegg_conv,
    kegg_link,
    kegg_ddi,
)
```

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

```python
from biodbs.fetch import (
    chembl_get_molecule,
    chembl_get_target,
    chembl_search_molecules,
    chembl_get_activities_for_target,
    chembl_get_activities_for_molecule,
    chembl_get_approved_drugs,
    chembl_get_drug_indications,
    chembl_get_mechanisms,
)
```

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

```python
from biodbs.fetch import (
    quickgo_search_terms,
    quickgo_get_terms,
    quickgo_get_term_children,
    quickgo_get_term_ancestors,
    quickgo_search_annotations,
    quickgo_search_annotations_all,
    quickgo_download_annotations,
    quickgo_get_gene_product,
)
```

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

```python
from biodbs.fetch import (
    hpa_get_gene,
    hpa_get_genes,
    hpa_get_tissue_expression,
    hpa_get_blood_expression,
    hpa_get_brain_expression,
    hpa_get_subcellular_location,
    hpa_get_pathology,
    hpa_get_protein_class,
    hpa_search,
)
```

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

```python
from biodbs.fetch import (
    ncbi_get_gene,
    ncbi_symbol_to_id,
    ncbi_id_to_symbol,
    ncbi_get_taxonomy,
    ncbi_translate_gene_ids,
)
```

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

```python
from biodbs.fetch import (
    fda_search,
    fda_search_all,
    fda_drug_events,
    fda_drug_labels,
    fda_drug_enforcement,
    fda_drug_ndc,
    fda_drug_drugsfda,
    fda_device_events,
    fda_device_classification,
    fda_device_510k,
    fda_device_pma,
    fda_device_recall,
    fda_device_udi,
    fda_food_events,
    fda_food_enforcement,
    fda_animalandveterinary_events,
    fda_tobacco_problem,
)
```

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

```python
from biodbs.fetch import (
    reactome_analyze,
    reactome_analyze_projection,
    reactome_get_pathways_top,
    reactome_get_species,
    reactome_get_found_entities,
    reactome_get_database_version,
)
```

### reactome_analyze

::: biodbs.fetch.Reactome.funcs.reactome_analyze
    options:
      show_root_heading: true
      show_source: false

---

## Disease Ontology

```python
from biodbs.fetch import (
    do_get_term,
    do_get_terms,
    do_search,
    do_get_parents,
    do_get_children,
    do_get_ancestors,
    do_get_descendants,
    doid_to_mesh,
    doid_to_umls,
    doid_to_icd10,
    do_xref_mapping,
)
```

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

```python
from biodbs.fetch import (
    enrichr_get_libraries,
    enrichr_enrich,
    enrichr_enrich_multiple,
    enrichr_enrich_with_background,
    enrichr_kegg,
    enrichr_go_bp,
    enrichr_go_mf,
    enrichr_go_cc,
    enrichr_reactome,
    enrichr_wikipathways,
)
```

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

## Fetcher Classes

For more control, use the fetcher classes directly:

```python
from biodbs.fetch.uniprot import UniProt_Fetcher
from biodbs.fetch.pubchem import PubChem_Fetcher
from biodbs.fetch.ensembl import Ensembl_Fetcher
from biodbs.fetch.biomart import BioMart_Fetcher
from biodbs.fetch.KEGG import KEGG_Fetcher
from biodbs.fetch.ChEMBL import ChEMBL_Fetcher
from biodbs.fetch.QuickGO import QuickGO_Fetcher
from biodbs.fetch.HPA import HPA_Fetcher
from biodbs.fetch.NCBI import NCBI_Fetcher
from biodbs.fetch.FDA import FDA_Fetcher
from biodbs.fetch.Reactome import Reactome_Fetcher
from biodbs.fetch.DiseaseOntology import DiseaseOntology_Fetcher
```

---

## Rate Limiting

```python
from biodbs.fetch import (
    RateLimiter,
    get_rate_limiter,
    request_with_retry,
    retry_with_backoff,
)
```
