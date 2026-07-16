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

    # Ensembl
    gene = funcs.ensembl_lookup("ENSG00000141510")
    seq = funcs.ensembl_get_sequence("ENST00000269305", sequence_type="cds")

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

# =============================================================================
# EnrichR functions
# =============================================================================
from biodbs.fetch.EnrichR.funcs import (
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

# =============================================================================
# Reactome functions
# =============================================================================
from biodbs.fetch.Reactome.funcs import (
    reactome_analyze,
    reactome_analyze_projection,
    reactome_get_pathways_top,
    reactome_get_species,
    reactome_get_found_entities,
    reactome_get_database_version,
)

# =============================================================================
# NCBI Datasets functions
# =============================================================================
from biodbs.fetch.NCBI.funcs import (
    ncbi_download_blast_database,
    ncbi_download_taxdump,
    ncbi_get_gene,
    ncbi_symbol_to_id,
    ncbi_id_to_symbol,
    ncbi_get_taxonomy,
    ncbi_translate_gene_ids,
)

# =============================================================================
# Ensembl REST API functions
# =============================================================================
from biodbs.fetch.ensembl.funcs import (
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

# =============================================================================
# Disease Ontology functions
# =============================================================================
from biodbs.fetch.DiseaseOntology.funcs import (
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

# =============================================================================
# HGNC functions
# =============================================================================
from biodbs.fetch.HGNC.funcs import (
    hgnc_info,
    hgnc_fetch,
    hgnc_search,
    hgnc_fetch_by_symbol,
    hgnc_fetch_by_hgnc_id,
    hgnc_fetch_by_entrez_id,
    hgnc_fetch_by_ensembl_id,
    hgnc_fetch_by_uniprot_id,
    hgnc_fetch_by_refseq,
    hgnc_search_symbol,
)

# =============================================================================
# LPSN functions
# =============================================================================
from biodbs.fetch.LPSN.funcs import (
    lpsn_fetch,
    lpsn_advanced_search,
    lpsn_flexible_search,
    lpsn_search_and_fetch,
)

# =============================================================================
# SILVA functions
# =============================================================================
from biodbs.fetch.SILVA.funcs import (
    silva_get_version,
    silva_list_current_files,
    silva_list_archive_releases,
    silva_get_readme,
    silva_get_citation,
    silva_download_file,
    silva_download_classifier,
)

# =============================================================================
# HOMD functions
# =============================================================================
from biodbs.fetch.HOMD.funcs import (
    homd_download_16s_refseq,
    homd_download_16s_taxonomy,
    homd_download_file,
    homd_get_crispr_table,
    homd_get_genome_metadata,
    homd_get_gtdb_taxonomy,
    homd_get_hmt_lineage,
    homd_get_phage_table,
    homd_get_table,
    homd_get_taxon_table,
    homd_get_taxonomic_hierarchy,
    homd_get_text,
    homd_list_16s_refseq,
    homd_list_downloads,
    homd_list_ftp,
)

# =============================================================================
# GTDB functions
# =============================================================================
from biodbs.fetch.GTDB.funcs import (
    gtdb_download_file,
    gtdb_download_metadata,
    gtdb_download_taxonomy,
    gtdb_download_tree,
    gtdb_get_file_descriptions,
    gtdb_get_md5sums,
    gtdb_get_metadata,
    gtdb_get_release_notes,
    gtdb_get_taxonomy,
    gtdb_get_tree,
    gtdb_get_version,
    gtdb_list_release_files,
    gtdb_list_releases,
)

# =============================================================================
# PR2 functions
# =============================================================================
from biodbs.fetch.PR2.funcs import (
    pr2_list_releases,
    pr2_list_assets,
    pr2_download_asset,
)

# =============================================================================
# GreenGenes functions
# =============================================================================
from biodbs.fetch.GreenGenes.funcs import (
    greengenes_list_releases,
    greengenes_list_files,
    greengenes_download_file,
)

# =============================================================================
# EUKARYOME functions
# =============================================================================
from biodbs.fetch.EUKARYOME.funcs import (
    eukaryome_build_url,
    eukaryome_download,
)

# =============================================================================
# MIDORI2 functions
# =============================================================================
from biodbs.fetch.MIDORI2.funcs import (
    midori2_build_url,
    midori2_download,
)

# =============================================================================
# UNITE functions
# =============================================================================
from biodbs.fetch.UNITE.funcs import (
    unite_resolve_doi,
    unite_get_download_url,
    unite_download,
)

# =============================================================================
# ClinVar functions
# =============================================================================
from biodbs.fetch.ClinVar.funcs import (
    clinvar_search,
    clinvar_count,
    clinvar_fetch_by_id,
    clinvar_search_gene,
    clinvar_search_condition,
    clinvar_fetch_vcv,
    clinvar_fetch_rcv,
    clinvar_link_pubmed,
)

# =============================================================================
# UniProt functions
# =============================================================================
from biodbs.fetch.uniprot.funcs import (
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
    # EnrichR
    "enrichr_get_libraries",
    "enrichr_enrich",
    "enrichr_enrich_multiple",
    "enrichr_enrich_with_background",
    "enrichr_kegg",
    "enrichr_go_bp",
    "enrichr_go_mf",
    "enrichr_go_cc",
    "enrichr_reactome",
    "enrichr_wikipathways",
    # Reactome
    "reactome_analyze",
    "reactome_analyze_projection",
    "reactome_get_pathways_top",
    "reactome_get_species",
    "reactome_get_found_entities",
    "reactome_get_database_version",
    # NCBI
    "ncbi_get_gene",
    "ncbi_symbol_to_id",
    "ncbi_id_to_symbol",
    "ncbi_get_taxonomy",
    "ncbi_translate_gene_ids",
    "ncbi_download_blast_database",
    "ncbi_download_taxdump",
    # Ensembl
    "ensembl_lookup",
    "ensembl_lookup_batch",
    "ensembl_lookup_symbol",
    "ensembl_get_sequence",
    "ensembl_get_sequence_batch",
    "ensembl_get_sequence_region",
    "ensembl_get_overlap_id",
    "ensembl_get_overlap_region",
    "ensembl_get_xrefs",
    "ensembl_get_xrefs_symbol",
    "ensembl_get_homology",
    "ensembl_get_homology_symbol",
    "ensembl_get_variation",
    "ensembl_vep_hgvs",
    "ensembl_vep_id",
    "ensembl_vep_region",
    "ensembl_map_assembly",
    "ensembl_get_phenotype_gene",
    "ensembl_get_phenotype_region",
    "ensembl_get_ontology_term",
    "ensembl_get_ontology_ancestors",
    "ensembl_get_ontology_descendants",
    "ensembl_get_genetree",
    "ensembl_get_genetree_member",
    "ensembl_get_assembly_info",
    "ensembl_get_species_info",
    # Disease Ontology
    "do_get_term",
    "do_get_terms",
    "do_search",
    "do_get_parents",
    "do_get_children",
    "do_get_ancestors",
    "do_get_descendants",
    "doid_to_mesh",
    "doid_to_umls",
    "doid_to_icd10",
    "do_xref_mapping",
    # HGNC
    "hgnc_info",
    "hgnc_fetch",
    "hgnc_search",
    "hgnc_fetch_by_symbol",
    "hgnc_fetch_by_hgnc_id",
    "hgnc_fetch_by_entrez_id",
    "hgnc_fetch_by_ensembl_id",
    "hgnc_fetch_by_uniprot_id",
    "hgnc_fetch_by_refseq",
    "hgnc_search_symbol",
    # LPSN
    "lpsn_fetch",
    "lpsn_advanced_search",
    "lpsn_flexible_search",
    "lpsn_search_and_fetch",
    # SILVA
    "silva_get_version",
    "silva_list_current_files",
    "silva_list_archive_releases",
    "silva_get_readme",
    "silva_get_citation",
    "silva_download_file",
    "silva_download_classifier",
    # HOMD
    "homd_list_ftp",
    "homd_list_downloads",
    "homd_download_file",
    "homd_get_table",
    "homd_get_text",
    "homd_get_taxon_table",
    "homd_get_taxonomic_hierarchy",
    "homd_get_hmt_lineage",
    "homd_get_genome_metadata",
    "homd_get_gtdb_taxonomy",
    "homd_get_phage_table",
    "homd_get_crispr_table",
    "homd_list_16s_refseq",
    "homd_download_16s_refseq",
    "homd_download_16s_taxonomy",
    # GTDB
    "gtdb_list_releases",
    "gtdb_list_release_files",
    "gtdb_get_version",
    "gtdb_get_release_notes",
    "gtdb_get_file_descriptions",
    "gtdb_get_md5sums",
    "gtdb_get_taxonomy",
    "gtdb_get_metadata",
    "gtdb_get_tree",
    "gtdb_download_file",
    "gtdb_download_taxonomy",
    "gtdb_download_metadata",
    "gtdb_download_tree",
    # PR2
    "pr2_list_releases",
    "pr2_list_assets",
    "pr2_download_asset",
    # GreenGenes
    "greengenes_list_releases",
    "greengenes_list_files",
    "greengenes_download_file",
    # EUKARYOME
    "eukaryome_build_url",
    "eukaryome_download",
    # MIDORI2
    "midori2_build_url",
    "midori2_download",
    # UNITE
    "unite_resolve_doi",
    "unite_get_download_url",
    "unite_download",
    # ClinVar
    "clinvar_search",
    "clinvar_count",
    "clinvar_fetch_by_id",
    "clinvar_search_gene",
    "clinvar_search_condition",
    "clinvar_fetch_vcv",
    "clinvar_fetch_rcv",
    "clinvar_link_pubmed",
    # UniProt
    "uniprot_get_entry",
    "uniprot_get_entries",
    "uniprot_search",
    "uniprot_search_by_gene",
    "uniprot_search_by_keyword",
    "gene_to_uniprot",
    "uniprot_to_gene",
    "uniprot_get_sequences",
    "uniprot_map_ids",
]
