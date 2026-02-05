"""Reactome API fetcher module."""

from biodbs.fetch.Reactome.reactome_fetcher import (
    Reactome_APIConfig,
    Reactome_Fetcher,
)
from biodbs.fetch.Reactome.funcs import (
    # Analysis
    reactome_analyze,
    reactome_analyze_projection,
    reactome_analyze_single,
    reactome_get_result_by_token,
    reactome_get_found_entities,
    reactome_get_not_found,
    reactome_map_identifiers,
    # Pathways
    reactome_get_pathways_top,
    reactome_get_pathways_for_entity,
    # Species
    reactome_get_species,
    reactome_get_species_main,
    # Database
    reactome_get_database_version,
    reactome_query_entry,
    # Participants (for pathway gene members)
    reactome_get_participants,
    reactome_get_participants_reference_entities,
    reactome_get_pathway_genes,
    reactome_get_all_pathways_with_genes,
    # Events
    reactome_get_event_ancestors,
    # Entities
    reactome_get_complex_subunits,
    reactome_get_entity_component_of,
    # Diseases
    reactome_get_diseases,
    reactome_get_diseases_doid,
    # Mapping
    reactome_map_to_reactions,
)

__all__ = [
    "Reactome_APIConfig",
    "Reactome_Fetcher",
    # Analysis functions
    "reactome_analyze",
    "reactome_analyze_projection",
    "reactome_analyze_single",
    "reactome_get_result_by_token",
    "reactome_get_found_entities",
    "reactome_get_not_found",
    "reactome_map_identifiers",
    # Pathways
    "reactome_get_pathways_top",
    "reactome_get_pathways_for_entity",
    # Species
    "reactome_get_species",
    "reactome_get_species_main",
    # Database
    "reactome_get_database_version",
    "reactome_query_entry",
    # Participants (for pathway gene members)
    "reactome_get_participants",
    "reactome_get_participants_reference_entities",
    "reactome_get_pathway_genes",
    "reactome_get_all_pathways_with_genes",
    # Events
    "reactome_get_event_ancestors",
    # Entities
    "reactome_get_complex_subunits",
    "reactome_get_entity_component_of",
    # Diseases
    "reactome_get_diseases",
    "reactome_get_diseases_doid",
    # Mapping
    "reactome_map_to_reactions",
]
