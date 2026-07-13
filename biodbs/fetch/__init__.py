"""Fetch module for biological database APIs.

This module provides fetcher classes and convenience functions for accessing
various biological databases.

Usage:
    # Using fetcher classes (OOP style)
    from biodbs.fetch.pubchem import PubChem_Fetcher
    fetcher = PubChem_Fetcher()
    data = fetcher.get_compound(2244)

    # Using convenience functions (functional style)
    from biodbs.fetch import pubchem_get_compound
    data = pubchem_get_compound(2244)

    # Or import all fetch functions
    from biodbs.fetch import *

For ID translation, use biodbs.translate:
    from biodbs.translate import translate_gene_ids, translate_chemical_ids

For analysis functions, use biodbs.analysis:
    from biodbs.analysis import ora_kegg, ora_go
"""

from biodbs.fetch._func import *
from biodbs.fetch import _func as funcs
from biodbs.fetch._rate_limit import (
    RateLimiter,
    get_rate_limiter,
    request_with_retry,
    retry_with_backoff,
)

__all__ = [
    "funcs",
    # Rate limiting utilities
    "RateLimiter",
    "get_rate_limiter",
    "request_with_retry",
    "retry_with_backoff",
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
    "ncbi_download_blast_database",
    "ncbi_download_taxdump",
    "ncbi_translate_gene_ids",
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
