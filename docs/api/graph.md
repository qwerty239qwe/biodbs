# Graph Module API Reference

Complete API reference for `biodbs.graph` module.

## Quick Import

```python
from biodbs.graph import (
    # Core classes
    KnowledgeGraph, Node, Edge,
    # Enums
    NodeType, EdgeType, DataSource,
    # Builders
    build_graph, build_disease_graph, build_go_graph,
    build_reactome_graph, build_kegg_graph, merge_graphs,
    # Exporters
    to_networkx, to_json_ld, to_rdf, to_neo4j_csv, to_cypher,
    # Utilities
    find_shortest_path, find_all_paths, get_neighborhood,
    get_connected_component, find_hub_nodes, get_graph_statistics,
)
```

---

## Enums

### NodeType

::: biodbs._funcs.graph.core.NodeType
    options:
      show_root_heading: true
      members_order: source

### EdgeType

::: biodbs._funcs.graph.core.EdgeType
    options:
      show_root_heading: true
      members_order: source

### DataSource

::: biodbs._funcs.graph.core.DataSource
    options:
      show_root_heading: true
      members_order: source

---

## Core Classes

### Node

::: biodbs._funcs.graph.core.Node
    options:
      show_root_heading: true
      members_order: source
      show_source: false

### Edge

::: biodbs._funcs.graph.core.Edge
    options:
      show_root_heading: true
      members_order: source
      show_source: false

### KnowledgeGraph

::: biodbs._funcs.graph.core.KnowledgeGraph
    options:
      show_root_heading: true
      members_order: source
      show_source: false

---

## Builder Functions

### build_graph

::: biodbs._funcs.graph.builders.build_graph
    options:
      show_root_heading: true

### build_disease_graph

::: biodbs._funcs.graph.builders.build_disease_graph
    options:
      show_root_heading: true

### build_disease_graph_with_hierarchy

::: biodbs._funcs.graph.builders.build_disease_graph_with_hierarchy
    options:
      show_root_heading: true

### build_go_graph

::: biodbs._funcs.graph.builders.build_go_graph
    options:
      show_root_heading: true

### build_reactome_graph

::: biodbs._funcs.graph.builders.build_reactome_graph
    options:
      show_root_heading: true

### build_reactome_hierarchy_graph

::: biodbs._funcs.graph.builders.build_reactome_hierarchy_graph
    options:
      show_root_heading: true

### build_kegg_graph

::: biodbs._funcs.graph.builders.build_kegg_graph
    options:
      show_root_heading: true

### build_kegg_link_graph

::: biodbs._funcs.graph.builders.build_kegg_link_graph
    options:
      show_root_heading: true

### merge_graphs

::: biodbs._funcs.graph.builders.merge_graphs
    options:
      show_root_heading: true

---

## Export Functions

### to_networkx

::: biodbs._funcs.graph.exporters.to_networkx
    options:
      show_root_heading: true

### to_json_ld

::: biodbs._funcs.graph.exporters.to_json_ld
    options:
      show_root_heading: true

### to_rdf

::: biodbs._funcs.graph.exporters.to_rdf
    options:
      show_root_heading: true

### to_neo4j_csv

::: biodbs._funcs.graph.exporters.to_neo4j_csv
    options:
      show_root_heading: true

### to_cypher

::: biodbs._funcs.graph.exporters.to_cypher
    options:
      show_root_heading: true

---

## Utility Functions

### find_shortest_path

::: biodbs._funcs.graph.utils.find_shortest_path
    options:
      show_root_heading: true

### find_all_paths

::: biodbs._funcs.graph.utils.find_all_paths
    options:
      show_root_heading: true

### get_neighborhood

::: biodbs._funcs.graph.utils.get_neighborhood
    options:
      show_root_heading: true

### get_connected_component

::: biodbs._funcs.graph.utils.get_connected_component
    options:
      show_root_heading: true

### get_all_connected_components

::: biodbs._funcs.graph.utils.get_all_connected_components
    options:
      show_root_heading: true

### find_hub_nodes

::: biodbs._funcs.graph.utils.find_hub_nodes
    options:
      show_root_heading: true

### compute_degree_distribution

::: biodbs._funcs.graph.utils.compute_degree_distribution
    options:
      show_root_heading: true

### get_graph_statistics

::: biodbs._funcs.graph.utils.get_graph_statistics
    options:
      show_root_heading: true

### format_statistics

::: biodbs._funcs.graph.utils.format_statistics
    options:
      show_root_heading: true
