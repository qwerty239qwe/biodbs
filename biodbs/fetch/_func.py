"""Convenience functions for fetching data from biological databases.

This module provides easy-to-use functions for common data fetching operations
without needing to instantiate fetcher classes directly.

Usage:
    from biodbs.fetch import funcs

    # PubChem
    compound = funcs.pubchem_get_compound(2244)  # Aspirin

    # BioMart/Ensembl
    genes = funcs.biomart_get_genes(["ENSG00000141510", "ENSG00000012048"])

    # HPA
    expression = funcs.hpa_get_tissue_expression("TP53")

    # ChEMBL
    molecule = funcs.chembl_get_molecule("CHEMBL25")

    # KEGG
    pathway = funcs.kegg_get("hsa00010")

    # QuickGO
    terms = funcs.quickgo_search_terms("apoptosis")

    # FDA
    events = funcs.fda_drug_events(search="aspirin", limit=10)

For ID translation functions, use biodbs._funcs:
    from biodbs._funcs import translate_gene_ids, translate_chemical_ids
"""

# =============================================================================
# PubChem functions
# =============================================================================
from biodbs.fetch.pubchem.funcs import (
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

# =============================================================================
# BioMart/Ensembl functions
# =============================================================================
from biodbs.fetch.biomart.funcs import (
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

# =============================================================================
# Human Protein Atlas (HPA) functions
# =============================================================================
from biodbs.fetch.HPA.funcs import (
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

# =============================================================================
# ChEMBL functions
# =============================================================================
from biodbs.fetch.ChEMBL.funcs import (
    chembl_get_molecule,
    chembl_get_target,
    chembl_search_molecules,
    chembl_get_activities_for_target,
    chembl_get_activities_for_molecule,
    chembl_get_approved_drugs,
    chembl_get_drug_indications,
    chembl_get_mechanisms,
)

# =============================================================================
# KEGG functions
# =============================================================================
from biodbs.fetch.KEGG.funcs import (
    kegg_info,
    kegg_list,
    kegg_find,
    kegg_get,
    kegg_get_batch,
    kegg_conv,
    kegg_link,
    kegg_ddi,
)

# =============================================================================
# QuickGO functions
# =============================================================================
from biodbs.fetch.QuickGO.funcs import (
    quickgo_search_terms,
    quickgo_get_terms,
    quickgo_get_term_children,
    quickgo_get_term_ancestors,
    quickgo_search_annotations,
    quickgo_search_annotations_all,
    quickgo_download_annotations,
    quickgo_get_gene_product,
)

# =============================================================================
# FDA functions
# =============================================================================
from biodbs.fetch.FDA.funcs import (
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

__all__ = [
    # PubChem
    "pubchem_get_compound",
    "pubchem_get_compounds",
    "pubchem_search_by_name",
    "pubchem_search_by_smiles",
    "pubchem_search_by_inchikey",
    "pubchem_search_by_formula",
    "pubchem_get_properties",
    "pubchem_get_synonyms",
    "pubchem_get_description",
    "pubchem_get_safety",
    "pubchem_get_pharmacology",
    "pubchem_get_drug_info",
    # BioMart/Ensembl
    "biomart_get_genes",
    "biomart_get_genes_by_name",
    "biomart_get_genes_by_region",
    "biomart_get_transcripts",
    "biomart_get_go_annotations",
    "biomart_get_homologs",
    "biomart_convert_ids",
    "biomart_query",
    "biomart_list_datasets",
    "biomart_list_attributes",
    "biomart_list_filters",
    # HPA
    "hpa_get_gene",
    "hpa_get_genes",
    "hpa_get_tissue_expression",
    "hpa_get_blood_expression",
    "hpa_get_brain_expression",
    "hpa_get_subcellular_location",
    "hpa_get_pathology",
    "hpa_get_protein_class",
    "hpa_search",
    # ChEMBL
    "chembl_get_molecule",
    "chembl_get_target",
    "chembl_search_molecules",
    "chembl_get_activities_for_target",
    "chembl_get_activities_for_molecule",
    "chembl_get_approved_drugs",
    "chembl_get_drug_indications",
    "chembl_get_mechanisms",
    # KEGG
    "kegg_info",
    "kegg_list",
    "kegg_find",
    "kegg_get",
    "kegg_get_batch",
    "kegg_conv",
    "kegg_link",
    "kegg_ddi",
    # QuickGO
    "quickgo_search_terms",
    "quickgo_get_terms",
    "quickgo_get_term_children",
    "quickgo_get_term_ancestors",
    "quickgo_search_annotations",
    "quickgo_search_annotations_all",
    "quickgo_download_annotations",
    "quickgo_get_gene_product",
    # FDA
    "fda_search",
    "fda_search_all",
    "fda_drug_events",
    "fda_drug_labels",
    "fda_drug_enforcement",
    "fda_drug_ndc",
    "fda_drug_drugsfda",
    "fda_device_events",
    "fda_device_classification",
    "fda_device_510k",
    "fda_device_pma",
    "fda_device_recall",
    "fda_device_udi",
    "fda_food_events",
    "fda_food_enforcement",
    "fda_animalandveterinary_events",
    "fda_tobacco_problem",
]
