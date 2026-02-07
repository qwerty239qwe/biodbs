"""Graph builder functions for creating knowledge graphs from fetched data.

This module provides functions to build KnowledgeGraph instances from
various biological database data sources.

Functions:
    build_graph: Build a graph from node and edge lists.
    build_disease_graph: Build from Disease Ontology data (DOFetchedData).
    build_go_graph: Build from Gene Ontology data (QuickGOFetchedData).
    build_reactome_graph: Build from Reactome data (ReactomeFetchedData).
    build_kegg_graph: Build from KEGG data (KEGGFetchedData).
    merge_graphs: Merge multiple graphs into one.

Example:
    >>> from biodbs.fetch import DO_Fetcher
    >>> from biodbs.graph import build_disease_graph
    >>>
    >>> fetcher = DO_Fetcher()
    >>> data = fetcher.get_children("DOID:162")
    >>> graph = build_disease_graph(data)
    >>> print(graph.summary())
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from biodbs._funcs.graph.core import (
    DataSource,
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)

if TYPE_CHECKING:
    from biodbs.data.DiseaseOntology.data import DOFetchedData
    from biodbs.data.QuickGO.data import QuickGOFetchedData
    from biodbs.data.Reactome.data import ReactomeFetchedData
    from biodbs.data.KEGG.data import KEGGFetchedData


# =============================================================================
# Generic Builder
# =============================================================================


def build_graph(
    nodes: List[Node],
    edges: Optional[List[Edge]] = None,
    name: str = "KnowledgeGraph",
    description: Optional[str] = None,
    source: DataSource = DataSource.CUSTOM,
) -> KnowledgeGraph:
    """Build a knowledge graph from node and edge lists.

    Args:
        nodes: List of Node objects to add to the graph.
        edges: Optional list of Edge objects to add.
        name: Name for the graph.
        description: Optional description.
        source: Data source for the graph.

    Returns:
        A new KnowledgeGraph instance.

    Example:
        >>> from biodbs.graph import Node, Edge, NodeType, EdgeType, build_graph
        >>>
        >>> nodes = [
        ...     Node(id="A", label="Node A", node_type=NodeType.GENE),
        ...     Node(id="B", label="Node B", node_type=NodeType.GENE),
        ... ]
        >>> edges = [
        ...     Edge(source="A", target="B", relation=EdgeType.INTERACTS_WITH),
        ... ]
        >>> graph = build_graph(nodes, edges, name="MyGraph")
    """
    graph = KnowledgeGraph(name=name, description=description, source=source)
    graph.add_nodes(nodes)
    if edges:
        graph.add_edges(edges)
    return graph


# =============================================================================
# Disease Ontology Builder
# =============================================================================


def build_disease_graph(
    data: "DOFetchedData",
    name: str = "DiseaseOntologyGraph",
    include_xrefs: bool = True,
    include_synonyms: bool = False,
) -> KnowledgeGraph:
    """Build a knowledge graph from Disease Ontology data.

    Creates nodes for each disease term and edges for hierarchical
    relationships (is_a) when parent terms are available.

    Args:
        data: DOFetchedData from Disease Ontology fetcher.
        name: Name for the graph.
        include_xrefs: Include cross-references as node xrefs.
        include_synonyms: Include synonyms in node properties.

    Returns:
        A KnowledgeGraph with disease nodes.

    Example:
        >>> from biodbs.fetch import DO_Fetcher
        >>> from biodbs.graph import build_disease_graph
        >>>
        >>> fetcher = DO_Fetcher()
        >>> data = fetcher.get_children("DOID:162")  # cancer
        >>> graph = build_disease_graph(data)
        >>> print(graph.summary())
    """
    graph = KnowledgeGraph(
        name=name,
        description="Knowledge graph from Disease Ontology",
        source=DataSource.DISEASE_ONTOLOGY,
    )

    # Track which nodes we've added to create edges
    node_ids: Set[str] = set()

    for term in data.terms:
        # Build properties
        properties: Dict[str, Any] = {}
        if term.definition:
            properties["definition"] = term.definition
        if include_synonyms and term.synonyms:
            properties["synonyms"] = tuple(term.synonyms)
        if term.is_obsolete:
            properties["is_obsolete"] = True
        if hasattr(term, "has_children") and term.has_children:
            properties["has_children"] = True
        if hasattr(term, "is_root") and term.is_root:
            properties["is_root"] = True

        # Build xrefs
        xrefs: Set[str] = set()
        if include_xrefs and term.xrefs:
            xrefs = set(term.xrefs)

        # Create node
        node = Node(
            id=term.doid,
            label=term.name,
            node_type=NodeType.DISEASE,
            source=DataSource.DISEASE_ONTOLOGY,
            properties=frozenset(properties.items()) if properties else frozenset(),
            xrefs=frozenset(xrefs),
        )
        graph.add_node(node)
        node_ids.add(term.doid)

    # If we have hierarchical data (from get_children or get_descendants),
    # the parent-child relationships are implicit in the fetch
    # We can create is_a edges based on the query structure
    # For now, edges are created if the fetcher provides relationship info

    return graph


def build_disease_graph_with_hierarchy(
    parent_data: "DOFetchedData",
    children_data: "DOFetchedData",
    name: str = "DiseaseOntologyGraph",
    include_xrefs: bool = True,
) -> KnowledgeGraph:
    """Build a disease graph with explicit parent-child relationships.

    Use this when you have fetched both parent and children terms
    and want to create IS_A edges between them.

    Args:
        parent_data: DOFetchedData containing the parent term(s).
        children_data: DOFetchedData containing child terms.
        name: Name for the graph.
        include_xrefs: Include cross-references as node xrefs.

    Returns:
        A KnowledgeGraph with disease nodes and IS_A edges.

    Example:
        >>> from biodbs.fetch import DO_Fetcher
        >>> from biodbs.graph import build_disease_graph_with_hierarchy
        >>>
        >>> fetcher = DO_Fetcher()
        >>> parent = fetcher.get_term("DOID:162")  # cancer
        >>> children = fetcher.get_children("DOID:162")
        >>> graph = build_disease_graph_with_hierarchy(parent, children)
    """
    # First build graphs from both datasets
    parent_graph = build_disease_graph(
        parent_data, name=name, include_xrefs=include_xrefs
    )
    children_graph = build_disease_graph(
        children_data, name=name, include_xrefs=include_xrefs
    )

    # Merge them
    graph = parent_graph.merge(children_graph)
    graph.name = name
    graph.description = "Knowledge graph from Disease Ontology with hierarchy"

    # Create IS_A edges from each child to each parent
    parent_ids = {term.doid for term in parent_data.terms}
    child_ids = {term.doid for term in children_data.terms}

    for child_id in child_ids:
        for parent_id in parent_ids:
            if child_id != parent_id:  # No self-loops
                edge = Edge(
                    source=child_id,
                    target=parent_id,
                    relation=EdgeType.IS_A,
                )
                graph.add_edge(edge)

    return graph


# =============================================================================
# Gene Ontology Builder
# =============================================================================


def build_go_graph(
    data: "QuickGOFetchedData",
    name: str = "GeneOntologyGraph",
    include_evidence: bool = True,
    create_annotation_edges: bool = True,
) -> KnowledgeGraph:
    """Build a knowledge graph from Gene Ontology (QuickGO) data.

    Creates nodes for GO terms and optionally for gene products,
    with edges representing annotations and ontology relationships.

    Args:
        data: QuickGOFetchedData from QuickGO fetcher.
        name: Name for the graph.
        include_evidence: Include evidence codes in edge properties.
        create_annotation_edges: Create edges between gene products and GO terms.

    Returns:
        A KnowledgeGraph with GO term and gene nodes.

    Example:
        >>> from biodbs.fetch import QuickGO_Fetcher
        >>> from biodbs.graph import build_go_graph
        >>>
        >>> fetcher = QuickGO_Fetcher()
        >>> data = fetcher.search_annotations(geneProductId="UniProtKB:P04637")
        >>> graph = build_go_graph(data)
    """
    graph = KnowledgeGraph(
        name=name,
        description="Knowledge graph from Gene Ontology",
        source=DataSource.GENE_ONTOLOGY,
    )

    go_terms: Dict[str, Dict[str, Any]] = {}  # GO ID -> term info
    gene_products: Set[str] = set()  # gene product IDs
    annotations: List[Tuple[str, str, str, Optional[str]]] = []  # (gene, go, relation, evidence)

    for result in data.results:
        # Extract GO term info
        go_id = result.get("goId") or result.get("go_id")
        go_name = result.get("goName") or result.get("go_name") or result.get("name", "")
        go_aspect = result.get("goAspect") or result.get("aspect")

        if go_id:
            if go_id not in go_terms:
                go_terms[go_id] = {
                    "name": go_name,
                    "aspect": go_aspect,
                }

            # Extract gene product info
            gene_id = result.get("geneProductId") or result.get("db_object_id")
            if gene_id:
                gene_products.add(gene_id)

                # Determine relation type from qualifier
                qualifier = result.get("qualifier") or result.get("goEvidence")
                if qualifier:
                    if "NOT" in str(qualifier).upper():
                        relation = EdgeType.NEGATIVELY_REGULATES
                    elif "part_of" in str(qualifier).lower():
                        relation = EdgeType.PART_OF
                    elif "regulates" in str(qualifier).lower():
                        relation = EdgeType.REGULATES
                    else:
                        relation = EdgeType.ASSOCIATED_WITH
                else:
                    relation = EdgeType.ASSOCIATED_WITH

                evidence = result.get("evidenceCode") or result.get("evidence_code")
                annotations.append((gene_id, go_id, relation.value, evidence))

    # Create GO term nodes
    for go_id, info in go_terms.items():
        properties: Dict[str, Any] = {}
        if info.get("aspect"):
            properties["aspect"] = info["aspect"]

        node = Node(
            id=go_id,
            label=info.get("name", go_id),
            node_type=NodeType.GO_TERM,
            source=DataSource.GENE_ONTOLOGY,
            properties=frozenset(properties.items()) if properties else frozenset(),
        )
        graph.add_node(node)

    # Create gene product nodes
    for gene_id in gene_products:
        # Try to determine if it's a protein (UniProt) or gene
        if gene_id.startswith("UniProtKB:") or gene_id.startswith("UniProt:"):
            node_type = NodeType.PROTEIN
        else:
            node_type = NodeType.GENE

        node = Node(
            id=gene_id,
            label=gene_id.split(":")[-1] if ":" in gene_id else gene_id,
            node_type=node_type,
            source=DataSource.GENE_ONTOLOGY,
        )
        graph.add_node(node)

    # Create annotation edges
    if create_annotation_edges:
        for gene_id, go_id, relation_str, evidence in annotations:
            try:
                relation = EdgeType(relation_str)
            except ValueError:
                relation = EdgeType.ASSOCIATED_WITH

            evidence_set = frozenset([evidence]) if evidence and include_evidence else frozenset()

            edge = Edge(
                source=gene_id,
                target=go_id,
                relation=relation,
                evidence=evidence_set,
            )
            graph.add_edge(edge)

    return graph


# =============================================================================
# Reactome Builder
# =============================================================================


def build_reactome_graph(
    data: "ReactomeFetchedData",
    name: str = "ReactomeGraph",
    include_species: bool = True,
    include_disease_info: bool = True,
) -> KnowledgeGraph:
    """Build a knowledge graph from Reactome pathway data.

    Creates nodes for pathways and edges based on pathway relationships.

    Args:
        data: ReactomeFetchedData from Reactome fetcher.
        name: Name for the graph.
        include_species: Include species info in node properties.
        include_disease_info: Include disease pathway flag in properties.

    Returns:
        A KnowledgeGraph with pathway nodes.

    Example:
        >>> from biodbs.fetch import Reactome_Fetcher
        >>> from biodbs.graph import build_reactome_graph
        >>>
        >>> fetcher = Reactome_Fetcher()
        >>> data = fetcher.analyze(["TP53", "BRCA1", "BRCA2"])
        >>> graph = build_reactome_graph(data)
    """
    graph = KnowledgeGraph(
        name=name,
        description="Knowledge graph from Reactome pathways",
        source=DataSource.REACTOME,
    )

    for pathway in data.pathways:
        properties: Dict[str, Any] = {}

        # Add statistics
        if pathway.p_value is not None:
            properties["p_value"] = pathway.p_value
        if pathway.fdr is not None:
            properties["fdr"] = pathway.fdr
        if pathway.found_entities is not None:
            properties["found_entities"] = pathway.found_entities
        if pathway.total_entities is not None:
            properties["total_entities"] = pathway.total_entities

        # Add species info
        if include_species and pathway.species:
            properties["species"] = pathway.species.name
            properties["taxon_id"] = pathway.species.taxId

        # Add disease info
        if include_disease_info:
            properties["is_disease_pathway"] = pathway.inDisease
            properties["is_lowest_level"] = pathway.llp

        # Add database ID
        properties["db_id"] = pathway.dbId

        node = Node(
            id=pathway.stId,
            label=pathway.name,
            node_type=NodeType.PATHWAY,
            source=DataSource.REACTOME,
            properties=frozenset(properties.items()),
        )
        graph.add_node(node)

    return graph


def build_reactome_hierarchy_graph(
    hierarchy_data: List[Dict[str, Any]],
    name: str = "ReactomeHierarchyGraph",
) -> KnowledgeGraph:
    """Build a knowledge graph from Reactome hierarchy data.

    Creates nodes for pathways and edges for parent-child relationships.

    Args:
        hierarchy_data: List of pathway hierarchy dictionaries from
            Reactome's events hierarchy endpoint.
        name: Name for the graph.

    Returns:
        A KnowledgeGraph with pathway nodes and hierarchy edges.
    """
    graph = KnowledgeGraph(
        name=name,
        description="Knowledge graph from Reactome pathway hierarchy",
        source=DataSource.REACTOME,
    )

    def process_node(node_data: Dict[str, Any], parent_id: Optional[str] = None):
        """Recursively process hierarchy nodes."""
        st_id = node_data.get("stId", "")
        name = node_data.get("name", node_data.get("displayName", ""))

        if not st_id:
            return

        properties: Dict[str, Any] = {}
        if node_data.get("hasDiagram"):
            properties["has_diagram"] = True
        if node_data.get("species"):
            properties["species"] = node_data["species"]

        node = Node(
            id=st_id,
            label=name,
            node_type=NodeType.PATHWAY,
            source=DataSource.REACTOME,
            properties=frozenset(properties.items()) if properties else frozenset(),
        )
        graph.add_node(node)

        # Create edge to parent
        if parent_id and parent_id in graph:
            edge = Edge(
                source=st_id,
                target=parent_id,
                relation=EdgeType.PART_OF,
            )
            graph.add_edge(edge)

        # Process children
        children = node_data.get("children", [])
        for child in children:
            process_node(child, st_id)

    # Process top-level nodes
    for node_data in hierarchy_data:
        process_node(node_data)

    return graph


# =============================================================================
# KEGG Builder
# =============================================================================


def build_kegg_graph(
    data: "KEGGFetchedData",
    name: str = "KEGGGraph",
    node_type: Optional[NodeType] = None,
) -> KnowledgeGraph:
    """Build a knowledge graph from KEGG data.

    Creates nodes from KEGG entries. The node type is inferred from
    the data operation (pathway, compound, drug, etc.) or can be
    explicitly specified.

    Args:
        data: KEGGFetchedData from KEGG fetcher.
        name: Name for the graph.
        node_type: Override the inferred node type.

    Returns:
        A KnowledgeGraph with KEGG nodes.

    Example:
        >>> from biodbs.fetch import kegg_list
        >>> from biodbs.graph import build_kegg_graph
        >>>
        >>> data = kegg_list("pathway", organism="hsa")
        >>> graph = build_kegg_graph(data, name="HumanPathways")
    """
    graph = KnowledgeGraph(
        name=name,
        description="Knowledge graph from KEGG database",
        source=DataSource.KEGG,
    )

    # Infer node type from operation or entry IDs
    inferred_type = node_type
    if inferred_type is None:
        if data.operation == "list":
            # Try to infer from first record
            if data.records:
                entry_id = data.records[0].get("entry_id", "")
                inferred_type = _infer_kegg_node_type(entry_id)
        else:
            inferred_type = NodeType.OTHER

    if inferred_type is None:
        inferred_type = NodeType.OTHER

    for record in data.records:
        entry_id = record.get("entry_id") or record.get("ENTRY", "")
        description = record.get("description") or record.get("NAME", "")

        if not entry_id:
            continue

        # For flat file records, extract more properties
        properties: Dict[str, Any] = {}
        if data.format == "flat_file":
            for key in ["DEFINITION", "PATHWAY", "MODULE", "DISEASE", "DBLINKS"]:
                if key in record:
                    properties[key.lower()] = record[key]

        # Create node
        node = Node(
            id=entry_id,
            label=description if description else entry_id,
            node_type=inferred_type,
            source=DataSource.KEGG,
            properties=frozenset(properties.items()) if properties else frozenset(),
        )
        graph.add_node(node)

    return graph


def build_kegg_link_graph(
    link_data: "KEGGFetchedData",
    source_type: NodeType = NodeType.GENE,
    target_type: NodeType = NodeType.PATHWAY,
    relation: EdgeType = EdgeType.PARTICIPATES_IN,
    name: str = "KEGGLinkGraph",
) -> KnowledgeGraph:
    """Build a knowledge graph from KEGG link data.

    Creates nodes and edges from KEGG link query results.

    Args:
        link_data: KEGGFetchedData from kegg_link operation.
        source_type: Node type for source entries.
        target_type: Node type for target entries.
        relation: Edge type for the links.
        name: Name for the graph.

    Returns:
        A KnowledgeGraph with nodes and edges from link data.

    Example:
        >>> from biodbs.fetch import kegg_link
        >>> from biodbs.graph import build_kegg_link_graph, NodeType
        >>>
        >>> data = kegg_link("pathway", "hsa")  # genes to pathways
        >>> graph = build_kegg_link_graph(
        ...     data,
        ...     source_type=NodeType.GENE,
        ...     target_type=NodeType.PATHWAY,
        ... )
    """
    graph = KnowledgeGraph(
        name=name,
        description="Knowledge graph from KEGG links",
        source=DataSource.KEGG,
    )

    sources: Set[str] = set()
    targets: Set[str] = set()

    for record in link_data.records:
        source_id = record.get("source_id", "")
        target_id = record.get("target_id", "")

        if source_id and target_id:
            sources.add(source_id)
            targets.add(target_id)

    # Create source nodes
    for source_id in sources:
        node = Node(
            id=source_id,
            label=source_id.split(":")[-1] if ":" in source_id else source_id,
            node_type=source_type,
            source=DataSource.KEGG,
        )
        graph.add_node(node)

    # Create target nodes
    for target_id in targets:
        node = Node(
            id=target_id,
            label=target_id.split(":")[-1] if ":" in target_id else target_id,
            node_type=target_type,
            source=DataSource.KEGG,
        )
        graph.add_node(node)

    # Create edges
    for record in link_data.records:
        source_id = record.get("source_id", "")
        target_id = record.get("target_id", "")

        if source_id and target_id:
            edge = Edge(
                source=source_id,
                target=target_id,
                relation=relation,
            )
            graph.add_edge(edge)

    return graph


def _infer_kegg_node_type(entry_id: str) -> NodeType:
    """Infer KEGG node type from entry ID format."""
    if entry_id.startswith("path:") or entry_id.startswith("map"):
        return NodeType.PATHWAY
    elif entry_id.startswith("C"):  # Compound
        return NodeType.COMPOUND
    elif entry_id.startswith("D"):  # Drug
        return NodeType.DRUG
    elif entry_id.startswith("R"):  # Reaction
        return NodeType.REACTION
    elif entry_id.startswith("K"):  # KO (orthology)
        return NodeType.GENE
    elif entry_id.startswith("M"):  # Module
        return NodeType.PATHWAY
    elif ":" in entry_id:  # Organism-specific gene (hsa:1234)
        return NodeType.GENE
    else:
        return NodeType.OTHER


# =============================================================================
# Merge Function
# =============================================================================


def merge_graphs(
    *graphs: KnowledgeGraph,
    name: str = "MergedGraph",
    description: Optional[str] = None,
) -> KnowledgeGraph:
    """Merge multiple knowledge graphs into one.

    Combines all nodes and edges from the input graphs. Duplicate nodes
    (same ID) are kept as-is (first occurrence wins). Duplicate edges
    (same source, target, relation) are deduplicated.

    Args:
        *graphs: Variable number of KnowledgeGraph instances to merge.
        name: Name for the merged graph.
        description: Optional description for the merged graph.

    Returns:
        A new KnowledgeGraph containing all nodes and edges.

    Example:
        >>> from biodbs.graph import merge_graphs, build_disease_graph, build_go_graph
        >>>
        >>> disease_graph = build_disease_graph(disease_data)
        >>> go_graph = build_go_graph(go_data)
        >>> merged = merge_graphs(disease_graph, go_graph, name="BioGraph")
    """
    if not graphs:
        return KnowledgeGraph(name=name, description=description)

    if len(graphs) == 1:
        # Just copy the single graph
        merged = KnowledgeGraph(
            name=name,
            description=description or graphs[0].description,
            source=graphs[0].source,
        )
        merged.add_nodes(graphs[0].nodes)
        merged.add_edges(graphs[0].edges)
        return merged

    # Start with first graph as base
    merged = KnowledgeGraph(
        name=name,
        description=description or f"Merged from {len(graphs)} graphs",
        source=graphs[0].source,
    )

    # Add all nodes and edges from each graph
    for graph in graphs:
        merged.add_nodes(graph.nodes)
        merged.add_edges(graph.edges)

    return merged
