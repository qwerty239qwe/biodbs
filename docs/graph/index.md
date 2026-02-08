# Knowledge Graph Module

The `biodbs.graph` module provides tools for building knowledge graphs from biological ontology data.

**Related sections:**

- [API Reference](../api/graph.md) - Complete function and class documentation
- [Data Fetching](../fetch/index.md) - Fetch ontology data for graph building
- [Disease Ontology](../fetch/disease-ontology.md) - Disease hierarchy data
- [Reactome](../fetch/reactome.md) - Pathway data for graphs

These graphs can be used for:

- **KG-RAG**: Knowledge Graph Retrieval Augmented Generation for LLM applications
- **Network Analysis**: Identify hub genes, find paths between entities
- **Data Integration**: Merge data from multiple sources into unified graphs
- **Visualization**: Export to NetworkX, Neo4j, or RDF for visualization

## Installation

The core graph functionality requires no additional dependencies. For optional export formats:

```bash
# NetworkX export support
pip install biodbs[graph]

# Or install dependencies separately
pip install networkx rdflib
```

## Quick Start

```python
from biodbs.graph import (
    KnowledgeGraph, Node, Edge,
    NodeType, EdgeType,
    build_disease_graph,
    to_json_ld, to_networkx
)
from biodbs.fetch import DO_Fetcher  # See: fetch/disease-ontology.md

# Build a graph from Disease Ontology
fetcher = DO_Fetcher()
cancer_data = fetcher.get_children("DOID:162")
graph = build_disease_graph(cancer_data)

print(graph.summary())
# KnowledgeGraph: DiseaseOntologyGraph
# Nodes: 47
# Edges: 46
```

## Core Concepts

### Nodes

Nodes represent biological entities like genes, proteins, diseases, or pathways.

```python
from biodbs.graph import Node, NodeType, DataSource

node = Node(
    id="DOID:162",
    label="cancer",
    node_type=NodeType.DISEASE,
    source=DataSource.DISEASE_ONTOLOGY,
    properties=frozenset([("definition", "A disease of cellular proliferation")]),
    xrefs=frozenset(["MESH:D009369", "UMLS:C0006826"]),
)
```

### Edges

Edges represent relationships between nodes.

```python
from biodbs.graph import Edge, EdgeType

edge = Edge(
    source="DOID:1612",  # breast cancer
    target="DOID:162",   # cancer
    relation=EdgeType.IS_A,
    weight=1.0,
    evidence=frozenset(["IEA"]),
)
```

### KnowledgeGraph

The container class for nodes and edges with graph operations.

```python
from biodbs.graph import KnowledgeGraph

graph = KnowledgeGraph(name="MyGraph")
graph.add_node(node)
graph.add_edge(edge)

# Query the graph
neighbors = graph.get_neighbors("DOID:162")
subgraph = graph.subgraph({"DOID:162", "DOID:1612"})
```

## Supported Data Sources

| Source | Builder Function | Node Types |
|--------|------------------|------------|
| Disease Ontology | `build_disease_graph()` | Disease |
| Gene Ontology (QuickGO) | `build_go_graph()` | GO Term, Gene, Protein |
| Reactome | `build_reactome_graph()` | Pathway |
| KEGG | `build_kegg_graph()` | Pathway, Gene, Compound |

## Export Formats

| Format | Function | Use Case |
|--------|----------|----------|
| NetworkX | `to_networkx()` | Graph algorithms, visualization |
| JSON-LD | `to_json_ld()` | KG-RAG, semantic web |
| RDF | `to_rdf()` | SPARQL queries, linked data |
| Neo4j CSV | `to_neo4j_csv()` | Neo4j import |
| Cypher | `to_cypher()` | Neo4j queries |

## Next Steps

- [Building Graphs](building.md) - Create graphs from various data sources
- [Exporting Graphs](exporting.md) - Export to different formats
- [Graph Analysis](analysis.md) - Path finding, centrality, statistics
- [API Reference](../api/graph.md) - Complete API documentation with enums
- [Disease Ontology Fetcher](../fetch/disease-ontology.md) - Fetch disease data
- [QuickGO Fetcher](../fetch/quickgo.md) - Fetch GO annotation data
