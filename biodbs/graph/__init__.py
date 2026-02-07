"""Knowledge Graph module for biodbs.

This module provides tools for building knowledge graphs from biological
ontology data (Disease Ontology, Gene Ontology, Reactome, KEGG). The graphs
can be used for KG-RAG (Knowledge Graph Retrieval Augmented Generation)
applications and graph analysis.

Core Classes:
    Node: Represents a node (entity) in the knowledge graph.
    Edge: Represents a directed edge (relationship) between nodes.
    KnowledgeGraph: Container for nodes and edges with graph operations.

Enums:
    NodeType: Types of biological entities (GENE, PROTEIN, DISEASE, etc.)
    EdgeType: Types of relationships (IS_A, PART_OF, REGULATES, etc.)
    DataSource: Supported data sources (DISEASE_ONTOLOGY, GENE_ONTOLOGY, etc.)

Builder Functions:
    build_graph: Build a graph from node and edge lists.
    build_disease_graph: Build from DOFetchedData.
    build_go_graph: Build from QuickGOFetchedData.
    build_reactome_graph: Build from ReactomeFetchedData.
    build_kegg_graph: Build from KEGGFetchedData.
    merge_graphs: Merge multiple graphs into one.

Export Functions:
    to_networkx: Export to NetworkX DiGraph.
    to_json_ld: Export to JSON-LD format (for KG-RAG).
    to_rdf: Export to RDF format (Turtle or XML).
    to_neo4j_csv: Export CSV files for Neo4j import.
    to_cypher: Generate Cypher queries for Neo4j.

Utility Functions:
    find_shortest_path: Find shortest path between two nodes.
    find_all_paths: Find all paths between two nodes.
    get_neighborhood: Get nodes within N hops of a node.
    get_connected_component: Get all nodes in the same component.
    find_hub_nodes: Find highly connected nodes.
    get_graph_statistics: Get detailed graph statistics.

Example:
    >>> from biodbs.graph import (
    ...     KnowledgeGraph, Node, Edge, NodeType, EdgeType,
    ...     build_disease_graph, to_networkx, to_json_ld
    ... )
    >>> from biodbs.fetch import DO_Fetcher
    >>>
    >>> # Build graph from Disease Ontology data
    >>> do_fetcher = DO_Fetcher()
    >>> cancer_data = do_fetcher.get_children("DOID:162")
    >>> disease_graph = build_disease_graph(cancer_data)
    >>> print(disease_graph.summary())
    >>>
    >>> # Export for KG-RAG applications
    >>> json_ld = to_json_ld(disease_graph)
    >>>
    >>> # Export to NetworkX for graph algorithms
    >>> import networkx as nx
    >>> nx_graph = to_networkx(disease_graph)
    >>> centrality = nx.degree_centrality(nx_graph)

Dependencies:
    Required: None (core functionality is pure Python)
    Optional:
        - networkx: For to_networkx() export and advanced algorithms
        - rdflib: For to_rdf() export
"""

from biodbs._funcs.graph.core import (
    # Enums
    NodeType,
    EdgeType,
    DataSource,
    # Data classes
    Node,
    Edge,
    # Container
    KnowledgeGraph,
)

from biodbs._funcs.graph.builders import (
    build_graph,
    build_disease_graph,
    build_go_graph,
    build_reactome_graph,
    build_kegg_graph,
    merge_graphs,
)

from biodbs._funcs.graph.exporters import (
    to_networkx,
    to_json_ld,
    to_rdf,
    to_neo4j_csv,
    to_cypher,
)

from biodbs._funcs.graph.utils import (
    find_shortest_path,
    find_all_paths,
    get_neighborhood,
    get_connected_component,
    find_hub_nodes,
    get_graph_statistics,
)

__all__ = [
    # Enums
    "NodeType",
    "EdgeType",
    "DataSource",
    # Data classes
    "Node",
    "Edge",
    # Container
    "KnowledgeGraph",
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
