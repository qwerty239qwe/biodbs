"""Convenience functions for Reactome API access.

These functions provide a simple interface for common Reactome operations
without needing to instantiate a fetcher object.

Example:
    >>> from biodbs.fetch.Reactome.funcs import reactome_analyze
    >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
    >>> result = reactome_analyze(genes)
    >>> print(result.significant_pathways().as_dataframe())
"""

from typing import Dict, Any, List, Optional
from biodbs.data.Reactome.data import (
    ReactomeFetchedData,
    ReactomePathwaysData,
    ReactomeSpeciesData,
)

# Module-level fetcher instance (lazy initialization)
_fetcher = None


def _get_fetcher():
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        from biodbs.fetch.Reactome.reactome_fetcher import Reactome_Fetcher
        _fetcher = Reactome_Fetcher()
    return _fetcher


def reactome_analyze(
    identifiers: List[str],
    species: str = "Homo sapiens",
    interactors: bool = False,
    page_size: int = 100,
    sort_by: str = "ENTITIES_FDR",
    order: str = "ASC",
    resource: str = "TOTAL",
    p_value: float = 1.0,
    include_disease: bool = True,
    min_entities: Optional[int] = None,
    max_entities: Optional[int] = None,
) -> ReactomeFetchedData:
    """Perform Reactome pathway over-representation analysis.

    Args:
        identifiers: List of identifiers (gene symbols, UniProt IDs, etc.).
        species: Species name (e.g., "Homo sapiens", "Mus musculus").
        interactors: Include interactors in analysis.
        page_size: Number of results to return.
        sort_by: Sort field (ENTITIES_FDR, ENTITIES_PVALUE, NAME).
        order: Sort order (ASC, DESC).
        resource: Resource filter (TOTAL, UNIPROT, ENSEMBL, etc.).
        p_value: P-value cutoff for filtering.
        include_disease: Include disease pathways.
        min_entities: Minimum pathway size.
        max_entities: Maximum pathway size.

    Returns:
        ReactomeFetchedData with pathway enrichment results.

    Example:
        >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
        >>> result = reactome_analyze(genes)
        >>> print(f"Found {len(result.pathways)} pathways")
        Found 172 pathways
        >>> df = result.significant_pathways(fdr_threshold=0.05).as_dataframe()
        >>> print(df[["stId", "name", "fdr", "found", "total"]].head(3).to_string())
                  stId                                        name           fdr  found  total
        0  R-HSA-6796648  TP53 Regulates Transcription of DNA Repai...  1.08e-06      7     86
        1  R-HSA-3700989              Transcriptional Regulation by TP53  6.45e-04      9    487
        2  R-HSA-6806003  Regulation of TP53 Expression and Degradation  6.45e-04      4     46
    """
    fetcher = _get_fetcher()
    return fetcher.analyze(
        identifiers=identifiers,
        species=species,
        interactors=interactors,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
        resource=resource,
        p_value=p_value,
        include_disease=include_disease,
        min_entities=min_entities,
        max_entities=max_entities,
    )


def reactome_analyze_projection(
    identifiers: List[str],
    species: str = "Homo sapiens",
    interactors: bool = False,
    page_size: int = 100,
) -> ReactomeFetchedData:
    """Analyze identifiers and project results to Homo sapiens.

    Useful for analyzing data from other species while viewing results
    in the context of human pathways.

    Args:
        identifiers: List of identifiers.
        species: Source species name (for mapping).
        interactors: Include interactors.
        page_size: Results per page.

    Returns:
        ReactomeFetchedData with human-projected pathway results.

    Example:
        >>> # Analyze mouse genes projected to human pathways
        >>> result = reactome_analyze_projection(
        ...     ["Trp53", "Brca1", "Egfr"],
        ...     species="Mus musculus"
        ... )
    """
    fetcher = _get_fetcher()
    return fetcher.analyze_projection(
        identifiers=identifiers,
        species=species,
        interactors=interactors,
        page_size=page_size,
    )


def reactome_analyze_single(
    identifier: str,
    species: str = "Homo sapiens",
    interactors: bool = False,
) -> ReactomeFetchedData:
    """Analyze a single identifier.

    Args:
        identifier: Single identifier to analyze.
        species: Species filter.
        interactors: Include interactors.

    Returns:
        ReactomeFetchedData with pathways containing the identifier.

    Example:
        >>> result = reactome_analyze_single("TP53")
        >>> print(result.get_pathway_names()[:5])
    """
    fetcher = _get_fetcher()
    return fetcher.analyze_single(
        identifier=identifier,
        species=species,
        interactors=interactors,
    )


def reactome_get_result_by_token(
    token: str,
    species: Optional[str] = None,
    page_size: int = 100,
    page: int = 1,
) -> ReactomeFetchedData:
    """Retrieve analysis results by token.

    Args:
        token: Analysis token from previous analysis.
        species: Species filter.
        page_size: Results per page.
        page: Page number.

    Returns:
        ReactomeFetchedData with analysis results.

    Example:
        >>> # Get first result
        >>> result = reactome_analyze(genes)
        >>> token = result.token
        >>> # Later, retrieve the same results
        >>> result2 = reactome_get_result_by_token(token)
    """
    fetcher = _get_fetcher()
    return fetcher.get_result_by_token(
        token=token,
        species=species,
        page_size=page_size,
        page=page,
    )


def reactome_get_found_entities(
    token: str,
    pathway_id: str,
) -> List[Dict[str, Any]]:
    """Get entities found in a specific pathway.

    Args:
        token: Analysis token.
        pathway_id: Pathway stable ID (e.g., "R-HSA-123456").

    Returns:
        List of found entity dictionaries.

    Example:
        >>> result = reactome_analyze(genes)
        >>> entities = reactome_get_found_entities(result.token, "R-HSA-69278")
        >>> print([e["id"] for e in entities])
    """
    fetcher = _get_fetcher()
    return fetcher.get_found_entities(token=token, pathway_id=pathway_id)


def reactome_get_not_found(token: str) -> List[str]:
    """Get identifiers that were not found in Reactome.

    Args:
        token: Analysis token.

    Returns:
        List of unmapped identifier strings.

    Example:
        >>> result = reactome_analyze(genes)
        >>> not_found = reactome_get_not_found(result.token)
        >>> print(f"Unmapped: {not_found}")
    """
    fetcher = _get_fetcher()
    return fetcher.get_not_found_identifiers(token=token)


def reactome_map_identifiers(
    identifiers: List[str],
    interactors: bool = False,
) -> List[Dict[str, Any]]:
    """Map identifiers to Reactome entities without analysis.

    Args:
        identifiers: List of identifiers to map (gene symbols, UniProt IDs, etc.).
        interactors: Include interactor mapping.

    Returns:
        List of mapped entity dictionaries showing Reactome mappings.

    Example:
        >>> mapped = reactome_map_identifiers(["TP53", "BRCA1"])
        >>> print(f"Mapped {len(mapped)} identifiers")
        Mapped 2 identifiers
        >>> for entity in mapped:
        ...     maps_to = entity.get('mapsTo', [])
        ...     print(f"  {entity['identifier']}: {len(maps_to)} Reactome entities")
        TP53: 48 Reactome entities
        BRCA1: 12 Reactome entities
    """
    fetcher = _get_fetcher()
    return fetcher.map_identifiers(
        identifiers=identifiers,
        interactors=interactors,
    )


def reactome_get_pathways_top(
    species: str = "Homo sapiens",
) -> ReactomePathwaysData:
    """Get top-level pathways for a species.

    Args:
        species: Species name (e.g., "Homo sapiens").

    Returns:
        ReactomePathwaysData with top-level pathway information.

    Example:
        >>> pathways = reactome_get_pathways_top("Homo sapiens")
        >>> print(f"Found {len(pathways)} top-level pathways")
        Found 28 top-level pathways
        >>> print(pathways.get_pathway_names()[:5])
        ['Autophagy', 'Cell Cycle', 'Cell-Cell communication', 'Cellular responses to stimuli', 'Chromatin organization']
    """
    fetcher = _get_fetcher()
    return fetcher.get_pathways_top(species=species)


def reactome_get_pathways_for_entity(
    entity_id: str,
) -> ReactomePathwaysData:
    """Get pathways containing a specific entity.

    Args:
        entity_id: Entity identifier (UniProt accession, gene symbol, etc.).

    Returns:
        ReactomePathwaysData with lowest-level pathways containing the entity.

    Example:
        >>> pathways = reactome_get_pathways_for_entity("P04637")  # TP53
        >>> print(f"TP53 is in {len(pathways)} pathways")
        TP53 is in 86 pathways
        >>> print(pathways.get_pathway_names()[:3])
        ['TP53 Regulates Transcription of DNA Repair Genes', 'TP53 regulates transcription of additional cell cycle genes whose exact role in the p53 pathway remain uncertain', 'TP53 Regulates Transcription of Genes Involved in G2 Cell Cycle Arrest']
    """
    fetcher = _get_fetcher()
    return fetcher.get_pathways_for_entity(entity_id=entity_id)


def reactome_get_species() -> ReactomeSpeciesData:
    """Get all species in Reactome.

    Returns:
        ReactomeSpeciesData with all species information.

    Example:
        >>> species = reactome_get_species()
        >>> print(f"Reactome contains {len(species)} species")
        Reactome contains 17251 species
        >>> print(species.get_species_names()[:5])
        ['Entries without species', 'Acacia catechu', 'Acacia confusa', 'Acacia senegal', 'Acetivibrio thermocellus']
    """
    fetcher = _get_fetcher()
    return fetcher.get_species()


def reactome_get_species_main() -> ReactomeSpeciesData:
    """Get main species with curated or inferred pathways.

    Returns:
        ReactomeSpeciesData with main model organism species.

    Example:
        >>> species = reactome_get_species_main()
        >>> print(f"Found {len(species)} main species")
        Found 16 main species
        >>> for s in species.species[:5]:
        ...     print(f"  {s['displayName']}: taxId={s.get('taxId')}")
        Homo sapiens: taxId=9606
        Mus musculus: taxId=10090
        Rattus norvegicus: taxId=10116
        Gallus gallus: taxId=9031
        Danio rerio: taxId=7955
    """
    fetcher = _get_fetcher()
    return fetcher.get_species_main()


def reactome_get_database_version() -> str:
    """Get current Reactome database version.

    Returns:
        Database version string (integer).

    Example:
        >>> version = reactome_get_database_version()
        >>> print(f"Reactome version: {version}")
        Reactome version: 89
    """
    fetcher = _get_fetcher()
    return fetcher.get_database_version()


def reactome_query_entry(entry_id: str) -> Dict[str, Any]:
    """Query a Reactome entry by ID.

    Args:
        entry_id: Reactome stable ID (e.g., "R-HSA-123456").

    Returns:
        Entry details dictionary with name, type, species, and other metadata.

    Example:
        >>> entry = reactome_query_entry("R-HSA-69278")
        >>> print(f"Name: {entry['displayName']}")
        Name: Cell Cycle, Mitotic
        >>> print(f"Type: {entry['schemaClass']}")
        Type: Pathway
        >>> print(f"Species: {entry['species'][0]['displayName']}")
        Species: Homo sapiens
        >>> # Get pathway summary
        >>> summation = entry.get('summation', [{}])[0].get('text', '')
        >>> print(f"Summary: {summation[:100]}...")
        Summary: The replication of the genome and the subsequent segregation of chromosomes into daughter cel...
    """
    fetcher = _get_fetcher()
    return fetcher.query_entry(entry_id=entry_id)


# =============================================================================
# Participants functions (for getting pathway gene members)
# =============================================================================


def reactome_get_participants(event_id: str) -> List[Dict[str, Any]]:
    """Get all participants in an event (pathway/reaction).

    Args:
        event_id: Reactome stable ID (e.g., "R-HSA-69278").

    Returns:
        List of participant dictionaries containing physical entity info.

    Example:
        >>> participants = reactome_get_participants("R-HSA-69278")
        >>> print(f"Found {len(participants)} participants")
        Found 2154 participants
        >>> for p in participants[:3]:
        ...     print(f"  {p.get('displayName')}")
        p21 Cip1 [cytosol]
        Phospho-Histone H2AX [nucleoplasm]
        AURKA [cytosol]
    """
    fetcher = _get_fetcher()
    return fetcher.get_participants(event_id)


def reactome_get_participants_reference_entities(
    event_id: str,
) -> List[Dict[str, Any]]:
    """Get reference entities (genes/proteins) for an event.

    Returns external database references (UniProt, NCBI Gene, etc.)
    for all participants in a pathway or reaction.

    Args:
        event_id: Reactome stable ID.

    Returns:
        List of reference entity dictionaries containing:
            - identifier: External ID (e.g., UniProt accession)
            - databaseName: Source database
            - geneName: Gene symbol (if available)

    Example:
        >>> refs = reactome_get_participants_reference_entities("R-HSA-69278")
        >>> print(f"Found {len(refs)} reference entities")
        Found 604 reference entities
        >>> # Filter to UniProt entries with gene names
        >>> proteins = [r for r in refs if r.get('databaseName') == 'UniProt']
        >>> for ref in proteins[:5]:
        ...     gene = ref.get('geneName', ['N/A'])
        ...     gene = gene[0] if isinstance(gene, list) else gene
        ...     print(f"  {gene}: {ref.get('identifier')}")
        PHLDA1: Q8WV24
        AURKA: O14965
        CEP63: Q96MT8
        TUBGCP2: Q9BSJ2
        KIF11: P52732
    """
    fetcher = _get_fetcher()
    return fetcher.get_participants_reference_entities(event_id)


def reactome_get_pathway_genes(
    pathway_id: str,
    id_type: str = "gene_symbol",
) -> List[str]:
    """Get gene identifiers for a pathway.

    Args:
        pathway_id: Reactome pathway stable ID.
        id_type: Type of ID to return:
            - "gene_symbol": Gene symbols (default)
            - "uniprot": UniProt accessions

    Returns:
        List of unique gene identifiers.

    Example:
        >>> # Get genes in "Cell Cycle, Mitotic" pathway
        >>> genes = reactome_get_pathway_genes("R-HSA-69278")
        >>> print(f"Found {len(genes)} unique genes")
        Found 601 unique genes
        >>> print(genes[:10])
        ['PSMD6', 'MCM4', 'PLK1', 'CCNB1', 'CDK1', 'PCNA', 'MCM7', 'ORC1', 'CDC20', 'BUB1']

        >>> # Get UniProt IDs instead
        >>> proteins = reactome_get_pathway_genes("R-HSA-69278", id_type="uniprot")
        >>> print(f"Found {len(proteins)} unique proteins")
        Found 575 unique proteins
        >>> print(proteins[:5])
        ['Q15596', 'P33991', 'P53350', 'P14635', 'P06493']
    """
    fetcher = _get_fetcher()
    return fetcher.get_pathway_genes(pathway_id, id_type=id_type)


def reactome_get_all_pathways_with_genes(
    species: str = "Homo sapiens",
    id_type: str = "gene_symbol",
    include_hierarchy: bool = True,
) -> Dict[str, tuple]:
    """Get all pathways with their gene members for a species.

    Builds a complete pathway-gene mapping suitable for local
    over-representation analysis.

    Args:
        species: Species name (e.g., "Homo sapiens").
        id_type: Gene ID type ("gene_symbol" or "uniprot").
        include_hierarchy: Include all pathways in hierarchy.

    Returns:
        Dict mapping pathway_id -> (pathway_name, set of gene IDs).

    Example:
        >>> pathways = reactome_get_all_pathways_with_genes("Homo sapiens")
        >>> print(f"Found {len(pathways)} pathways with genes")
        Found 2615 pathways with genes
        >>> # Show first 3 pathways
        >>> for pid, (name, genes) in list(pathways.items())[:3]:
        ...     print(f"  {pid}: {name[:40]}... ({len(genes)} genes)")
        R-HSA-164843: 2-LTR circle formation... (13 genes)
        R-HSA-73843: 5-Phosphoribose 1-diphosphate biosynthe... (3 genes)
        R-HSA-499943: A]TP hydrolysis by myosin VI... (8 genes)

    Note:
        This makes many API calls and may take several minutes on first run.
        Results are cached for subsequent calls.
    """
    fetcher = _get_fetcher()
    return fetcher.get_all_pathways_with_genes(
        species=species,
        id_type=id_type,
        include_hierarchy=include_hierarchy,
    )


# =============================================================================
# Event functions
# =============================================================================


def reactome_get_event_ancestors(event_id: str) -> List[Dict[str, Any]]:
    """Get ancestor pathways for an event.

    Args:
        event_id: Reactome stable ID.

    Returns:
        List of ancestor pathway dictionaries (from root to parent).

    Example:
        >>> ancestors = reactome_get_event_ancestors("R-HSA-6796648")
        >>> print(f"Found {len(ancestors)} ancestor chains")
        Found 1 ancestor chains
        >>> # Each chain is a list of ancestors from root to immediate parent
        >>> for chain in ancestors:
        ...     print(" -> ".join([a.get('displayName', '')[:30] for a in chain]))
        Gene expression (Transcription -> Transcriptional Regulation b -> TP53 Regulates Transcription o
    """
    fetcher = _get_fetcher()
    return fetcher.get_event_ancestors(event_id)


# =============================================================================
# Entity functions
# =============================================================================


def reactome_get_complex_subunits(complex_id: str) -> List[Dict[str, Any]]:
    """Get subunits of a complex.

    Args:
        complex_id: Reactome complex stable ID.

    Returns:
        List of subunit dictionaries with entity details.

    Example:
        >>> # Get subunits of the p53 tetramer complex
        >>> subunits = reactome_get_complex_subunits("R-HSA-3209194")
        >>> print(f"Found {len(subunits)} subunits")
        Found 1 subunits
        >>> for s in subunits:
        ...     print(f"  {s.get('displayName')}")
        TP53 [nucleoplasm]
    """
    fetcher = _get_fetcher()
    return fetcher.get_complex_subunits(complex_id)


def reactome_get_entity_component_of(entity_id: str) -> List[Dict[str, Any]]:
    """Get complexes/sets that contain an entity.

    Args:
        entity_id: Reactome entity stable ID.

    Returns:
        List of container complexes/sets that include this entity.

    Example:
        >>> # Find complexes containing TP53 protein
        >>> containers = reactome_get_entity_component_of("R-HSA-69488")
        >>> print(f"TP53 is part of {len(containers)} complexes/sets")
        TP53 is part of 15 complexes/sets
        >>> for c in containers[:3]:
        ...     print(f"  {c.get('displayName')}")
        p-S15,S20-TP53 Tetramer [nucleoplasm]
        p-S33,S46-TP53 [nucleoplasm]
        TP53 Tetramer [nucleoplasm]
    """
    fetcher = _get_fetcher()
    return fetcher.get_entity_component_of(entity_id)


# =============================================================================
# Disease functions
# =============================================================================


def reactome_get_diseases() -> List[Dict[str, Any]]:
    """Get all disease objects in Reactome.

    Returns:
        List of disease dictionaries with disease annotations.

    Example:
        >>> diseases = reactome_get_diseases()
        >>> print(f"Reactome contains {len(diseases)} diseases")
        Reactome contains 770 diseases
        >>> for d in diseases[:5]:
        ...     print(f"  {d.get('displayName')}")
        3-Methylcrotonyl-CoA carboxylase 1 deficiency
        3-Methylcrotonyl-CoA carboxylase 2 deficiency
        3-hydroxyisobutryl-CoA hydrolase deficiency
        3-methylglutaconic aciduria
        46 XX gonadal dysgenesis
    """
    fetcher = _get_fetcher()
    return fetcher.get_diseases()


def reactome_get_diseases_doid() -> List[str]:
    """Get all Disease Ontology IDs (DOIDs) in Reactome.

    Returns:
        List of DOID strings for cross-referencing with Disease Ontology.

    Example:
        >>> doids = reactome_get_diseases_doid()
        >>> print(f"Found {len(doids)} Disease Ontology IDs")
        Found 478 Disease Ontology IDs
        >>> print(doids[:10])
        ['DOID:0050674', 'DOID:0050694', 'DOID:0050697', 'DOID:0050702', ...]
    """
    fetcher = _get_fetcher()
    return fetcher.get_diseases_doid()


# =============================================================================
# Mapping functions
# =============================================================================


def reactome_map_to_reactions(
    identifier: str,
    resource: str = "UniProt",
) -> List[Dict[str, Any]]:
    """Map an identifier to Reactome reactions.

    Args:
        identifier: External identifier (e.g., UniProt accession).
        resource: Source database ("UniProt", "NCBI", "ENSEMBL", etc.).

    Returns:
        List of reaction dictionaries where the identifier participates.

    Example:
        >>> reactions = reactome_map_to_reactions("P04637")  # TP53
        >>> print(f"TP53 participates in {len(reactions)} reactions")
        TP53 participates in 201 reactions
        >>> for r in reactions[:3]:
        ...     print(f"  {r.get('stId')}: {r.get('displayName')[:50]}...")
        R-HSA-6785631: TP53 Tetramer binds the CDKN1A Gene Promoter...
        R-HSA-6791465: TP53 Tetramer binds the TP53AIP1 Gene Promoter...
        R-HSA-6791471: TP53 Tetramer binds the PIDD1 Gene Promoter...
    """
    fetcher = _get_fetcher()
    return fetcher.map_to_reactions(identifier, resource=resource)
