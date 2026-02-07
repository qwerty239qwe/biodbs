"""biodbs - Biological Database Access Library.

This library provides easy access to various biological databases through
four main namespaces:

1. biodbs.fetch - Data fetching functions (low-level API wrappers)
   from biodbs.fetch import pubchem_get_compound, kegg_get, ensembl_lookup

2. biodbs.translate - ID translation functions
   from biodbs.translate import translate_gene_ids, translate_chemical_ids

3. biodbs.analysis - Analysis functions (ORA, enrichment, etc.)
   from biodbs.analysis import ora_kegg, ora_go, ora_enrichr

4. biodbs.graph - Knowledge graph construction and analysis
   from biodbs.graph import KnowledgeGraph, build_disease_graph, to_networkx

All functions are also available at the top level for convenience:
   from biodbs import pubchem_get_compound, translate_gene_ids, ora_kegg
"""

__version__ = 0.01

# =============================================================================
# Fetch functions (low-level API wrappers for biological databases)
# =============================================================================
from biodbs.fetch._func import *

# =============================================================================
# Submodule namespaces (for organized imports)
# =============================================================================
from biodbs import fetch
from biodbs import translate
from biodbs import analysis
from biodbs import graph

# =============================================================================
# Translate functions (ID mapping between databases)
# =============================================================================
from biodbs._funcs.translate import (
    translate_gene_ids,
    translate_gene_ids_kegg,
    translate_chemical_ids,
    translate_chemical_ids_kegg,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
)

# =============================================================================
# Analysis functions (enrichment analysis, statistics, etc.)
# =============================================================================
from biodbs._funcs.analysis import (
    ora,
    ora_kegg,
    ora_go,
    ora_enrichr,
    ORAResult,
    hypergeometric_test,
    multiple_test_correction,
)

# =============================================================================
# Graph functions (knowledge graph construction and analysis)
# =============================================================================
from biodbs._funcs.graph import (
    # Core classes
    KnowledgeGraph,
    Node,
    Edge,
    # Enums
    NodeType,
    EdgeType,
    DataSource,
    # Builders
    build_graph,
    build_disease_graph,
    build_go_graph,
    build_reactome_graph,
    build_kegg_graph,
    merge_graphs,
    # Exporters
    to_networkx,
    to_json_ld,
    to_rdf,
    to_neo4j_csv,
    to_cypher,
    # Utilities
    find_shortest_path,
    find_all_paths,
    get_neighborhood,
    get_connected_component,
    find_hub_nodes,
    get_graph_statistics,
)


__all__ = [
    # Submodules
    "fetch",
    "translate",
    "analysis",
    "graph",

    # ==========================================================================
    # FETCH FUNCTIONS - Low-level API wrappers
    # ==========================================================================
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
    # Ensembl REST API
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

    # ==========================================================================
    # TRANSLATE FUNCTIONS - ID mapping between databases
    # ==========================================================================
    "translate_gene_ids",
    "translate_gene_ids_kegg",
    "translate_chemical_ids",
    "translate_chemical_ids_kegg",
    "translate_chembl_to_pubchem",
    "translate_pubchem_to_chembl",

    # ==========================================================================
    # ANALYSIS FUNCTIONS - Enrichment analysis, statistics
    # ==========================================================================
    "ora",
    "ora_kegg",
    "ora_go",
    "ora_enrichr",
    "ORAResult",
    "hypergeometric_test",
    "multiple_test_correction",

    # ==========================================================================
    # GRAPH FUNCTIONS - Knowledge graph construction and analysis
    # ==========================================================================
    # Core classes
    "KnowledgeGraph",
    "Node",
    "Edge",
    # Enums
    "NodeType",
    "EdgeType",
    "DataSource",
    # Builders
    "build_graph",
    "build_disease_graph",
    "build_go_graph",
    "build_reactome_graph",
    "build_kegg_graph",
    "merge_graphs",
    # Exporters
    "to_networkx",
    "to_json_ld",
    "to_rdf",
    "to_neo4j_csv",
    "to_cypher",
    # Utilities
    "find_shortest_path",
    "find_all_paths",
    "get_neighborhood",
    "get_connected_component",
    "find_hub_nodes",
    "get_graph_statistics",
]