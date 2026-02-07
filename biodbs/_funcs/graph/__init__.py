"""Internal graph module exports.

This module provides the internal implementations for the graph module.
Use `biodbs.graph` for the public API.
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
