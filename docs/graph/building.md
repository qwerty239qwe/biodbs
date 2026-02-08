# Building Knowledge Graphs

This guide covers how to build knowledge graphs from various biological data sources.

## Generic Graph Building

Build a graph from custom nodes and edges:

```python
from biodbs.graph import build_graph, Node, Edge, NodeType, EdgeType

nodes = [
    Node(id="gene:TP53", label="TP53", node_type=NodeType.GENE),
    Node(id="gene:BRCA1", label="BRCA1", node_type=NodeType.GENE),
    Node(id="pathway:apoptosis", label="Apoptosis", node_type=NodeType.PATHWAY),
]

edges = [
    Edge(source="gene:TP53", target="pathway:apoptosis", relation=EdgeType.PARTICIPATES_IN),
    Edge(source="gene:BRCA1", target="pathway:apoptosis", relation=EdgeType.PARTICIPATES_IN),
]

graph = build_graph(nodes, edges, name="MyGraph")
```

## Disease Ontology

Build graphs from Disease Ontology data:

```python
from biodbs.fetch import DO_Fetcher
from biodbs.graph import build_disease_graph

fetcher = DO_Fetcher()

# Get children of a disease term
cancer_data = fetcher.get_children("DOID:162")
graph = build_disease_graph(cancer_data)

print(graph.summary())
```

### Options

```python
graph = build_disease_graph(
    cancer_data,
    name="CancerGraph",
    include_xrefs=True,      # Include cross-references (MESH, UMLS, etc.)
    include_synonyms=False,  # Include synonyms in properties
)
```

### With Hierarchy

To create IS_A edges between parent and children:

```python
from biodbs.graph import build_disease_graph_with_hierarchy

parent = fetcher.get_term("DOID:162")
children = fetcher.get_children("DOID:162")

graph = build_disease_graph_with_hierarchy(parent, children)
# Now has IS_A edges from each child to parent
```

## Gene Ontology (QuickGO)

Build graphs from GO annotations:

```python
from biodbs.fetch import QuickGO_Fetcher
from biodbs.graph import build_go_graph

fetcher = QuickGO_Fetcher()

# Get annotations for a protein
data = fetcher.search_annotations(geneProductId="UniProtKB:P04637")
graph = build_go_graph(data)

print(graph.summary())
```

### Options

```python
graph = build_go_graph(
    data,
    name="TP53_GO",
    include_evidence=True,         # Include evidence codes on edges
    create_annotation_edges=True,  # Create edges between genes and GO terms
)
```

## Reactome Pathways

Build graphs from Reactome analysis results:

```python
from biodbs.fetch import Reactome_Fetcher
from biodbs.graph import build_reactome_graph

fetcher = Reactome_Fetcher()

# Analyze a gene list
data = fetcher.analyze(["TP53", "BRCA1", "BRCA2"])
graph = build_reactome_graph(data)

print(graph.summary())
```

### Options

```python
graph = build_reactome_graph(
    data,
    name="CancerPathways",
    include_species=True,       # Include species info
    include_disease_info=True,  # Include disease pathway flags
)
```

### Pathway Hierarchy

Build from Reactome pathway hierarchy:

```python
from biodbs.graph import build_reactome_hierarchy_graph

# Get hierarchy from fetcher
hierarchy = fetcher.get_events_hierarchy("Homo sapiens")
graph = build_reactome_hierarchy_graph(hierarchy)
# Creates PART_OF edges between pathways
```

## KEGG

Build graphs from KEGG data:

```python
from biodbs.fetch import kegg_list, kegg_link
from biodbs.graph import build_kegg_graph, build_kegg_link_graph

# From pathway list
pathways = kegg_list("pathway", organism="hsa")
graph = build_kegg_graph(pathways, name="HumanPathways")

# From gene-pathway links
links = kegg_link("pathway", "hsa")
graph = build_kegg_link_graph(
    links,
    source_type=NodeType.GENE,
    target_type=NodeType.PATHWAY,
    relation=EdgeType.PARTICIPATES_IN,
)
```

## Merging Graphs

Combine multiple graphs into one:

```python
from biodbs.graph import merge_graphs

# Build individual graphs
disease_graph = build_disease_graph(disease_data)
go_graph = build_go_graph(go_data)
reactome_graph = build_reactome_graph(reactome_data)

# Merge them
merged = merge_graphs(
    disease_graph,
    go_graph,
    reactome_graph,
    name="IntegratedGraph",
)

print(merged.summary())
```

!!! note
    When merging, duplicate nodes (same ID) are kept as-is (first occurrence wins).
    Duplicate edges (same source, target, relation) are deduplicated.

## Adding Custom Nodes and Edges

After building, you can extend the graph:

```python
# Add nodes
graph.add_node(Node(id="custom:1", label="Custom Node"))

# Add edges (both nodes must exist)
graph.add_edge(Edge(
    source="custom:1",
    target="DOID:162",
    relation=EdgeType.ASSOCIATED_WITH,
))

# Update from another graph
other_graph = build_go_graph(go_data)
graph.update(other_graph)  # Modifies in place
```

## Related Resources

### Data Sources

- **[Disease Ontology](../fetch/disease-ontology.md)** - Fetch disease terms and hierarchies for `build_disease_graph()`.
- **[QuickGO](../fetch/quickgo.md)** - Fetch GO annotations for `build_go_graph()`.
- **[Reactome](../fetch/reactome.md)** - Fetch pathway data for `build_reactome_graph()`.
- **[KEGG](../fetch/kegg.md)** - Fetch pathway and gene data for `build_kegg_graph()`.

### Next Steps

- **[Exporting Graphs](exporting.md)** - Export to NetworkX, JSON-LD, RDF, or Neo4j.
- **[Graph Analysis](analysis.md)** - Find paths, hubs, and compute statistics.
