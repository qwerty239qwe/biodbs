# Graph Analysis

The graph module includes built-in utilities for analyzing knowledge graphs without requiring external dependencies.

## Path Finding

### Shortest Path

Find the shortest path between two nodes:

```python
from biodbs.graph import find_shortest_path

path = find_shortest_path(graph, "DOID:1612", "DOID:4")
if path:
    print(" -> ".join(path))
    # DOID:1612 -> DOID:162 -> DOID:14566 -> DOID:4
```

### Options

```python
path = find_shortest_path(
    graph,
    source="DOID:1612",
    target="DOID:4",
    directed=True,    # Follow edge direction
    max_depth=10,     # Maximum path length
)
```

### All Paths

Find all paths between two nodes (use with caution on large graphs):

```python
from biodbs.graph import find_all_paths

paths = find_all_paths(
    graph,
    source="DOID:1612",
    target="DOID:4",
    max_depth=5,
)

for path in paths:
    print(" -> ".join(path))
```

## Neighborhood Analysis

### Get Neighborhood

Get all nodes within N hops of a starting node:

```python
from biodbs.graph import get_neighborhood

# Nodes within 2 hops
result = get_neighborhood(graph, "DOID:162", hops=2)
print(f"Found {len(result['nodes'])} nodes")

# Include edges
result = get_neighborhood(
    graph,
    "DOID:162",
    hops=2,
    include_edges=True,
)
print(f"Found {len(result['edges'])} edges")
```

### Connected Components

Get all nodes in the same connected component:

```python
from biodbs.graph import get_connected_component

component = get_connected_component(graph, "DOID:162")
print(f"Component has {len(component)} nodes")
```

## Hub Detection

Find highly connected nodes (hubs):

```python
from biodbs.graph import find_hub_nodes

# Top 10 most connected nodes
hubs = find_hub_nodes(graph, top_n=10)
for node_id, degree in hubs:
    node = graph.get_node(node_id)
    print(f"{node.label}: {degree} connections")
```

### Filter by Node Type

```python
from biodbs.graph import NodeType

# Only disease hubs
disease_hubs = find_hub_nodes(
    graph,
    top_n=5,
    direction="both",      # "outgoing", "incoming", or "both"
    node_type=NodeType.DISEASE,
)
```

## Graph Statistics

Get comprehensive statistics about a graph:

```python
from biodbs.graph import get_graph_statistics

stats = get_graph_statistics(graph)

print(f"Nodes: {stats['num_nodes']}")
print(f"Edges: {stats['num_edges']}")
print(f"Density: {stats['density']:.4f}")
print(f"Average degree: {stats['avg_degree']:.2f}")
print(f"Connected components: {stats['num_components']}")
```

### Available Statistics

| Statistic | Description |
|-----------|-------------|
| `num_nodes` | Total number of nodes |
| `num_edges` | Total number of edges |
| `density` | Graph density (edges / possible edges) |
| `avg_degree` | Average node degree |
| `max_degree` | Maximum node degree |
| `min_degree` | Minimum node degree |
| `avg_out_degree` | Average outgoing edges per node |
| `avg_in_degree` | Average incoming edges per node |
| `num_isolated` | Nodes with no connections |
| `num_components` | Number of connected components |
| `largest_component_size` | Size of largest component |
| `num_self_loops` | Number of self-loop edges |
| `node_type_counts` | Counts by node type |
| `edge_type_counts` | Counts by edge type |

### Formatted Output

```python
from biodbs.graph.utils import format_statistics

stats = get_graph_statistics(graph)
print(format_statistics(stats))
```

## Filtering

### Filter Nodes

```python
# By type
diseases = graph.filter_nodes(node_type=NodeType.DISEASE)

# By source
do_nodes = graph.filter_nodes(source=DataSource.DISEASE_ONTOLOGY)

# Custom predicate
obsolete = graph.filter_nodes(
    predicate=lambda n: n.get_property("is_obsolete") == True
)
```

### Filter Edges

```python
# By relation type
is_a_edges = graph.filter_edges(relation=EdgeType.IS_A)

# By weight
strong_edges = graph.filter_edges(min_weight=0.8)

# Custom predicate
with_evidence = graph.filter_edges(
    predicate=lambda e: len(e.evidence) > 0
)
```

## Subgraph Extraction

Extract subgraphs for focused analysis:

```python
# By node IDs
subgraph = graph.subgraph({"DOID:162", "DOID:1612", "DOID:3571"})

# From neighborhood
neighborhood = get_neighborhood(graph, "DOID:162", hops=2)
subgraph = graph.subgraph({n.id for n in neighborhood["nodes"]})

# From connected component
component = get_connected_component(graph, "DOID:162")
subgraph = graph.subgraph(component)
```

## Advanced Analysis with NetworkX

For more advanced algorithms, export to NetworkX:

```python
from biodbs.graph import to_networkx
import networkx as nx

G = to_networkx(graph)

# PageRank
pagerank = nx.pagerank(G)
top_nodes = sorted(pagerank.items(), key=lambda x: -x[1])[:10]

# Betweenness centrality
betweenness = nx.betweenness_centrality(G)

# Community detection
communities = nx.community.louvain_communities(G)

# Clustering coefficient
clustering = nx.clustering(G)

# Shortest path lengths
lengths = dict(nx.all_pairs_shortest_path_length(G))
```

## Related Resources

- **[Building Graphs](building.md)** - Create graphs from biological data sources.
- **[Exporting Graphs](exporting.md)** - Export to NetworkX for advanced algorithms, or to other formats.
