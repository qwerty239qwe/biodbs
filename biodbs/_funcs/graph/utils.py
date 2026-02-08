"""Utility functions for knowledge graph analysis.

This module provides graph algorithms and analysis utilities for
KnowledgeGraph instances, implemented in pure Python without
external dependencies.

Functions:
    find_shortest_path: Find shortest path between two nodes.
    find_all_paths: Find all paths between two nodes.
    get_neighborhood: Get nodes within N hops of a node.
    get_connected_component: Get all nodes in the same component.
    find_hub_nodes: Find highly connected nodes.
    get_graph_statistics: Get detailed graph statistics.

Example:
    ```python
    from biodbs.graph import find_shortest_path, find_hub_nodes, build_disease_graph

    graph = build_disease_graph(disease_data)
    path = find_shortest_path(graph, "DOID:162", "DOID:1612")
    print(path)
    # ['DOID:162', 'DOID:1612']

    hubs = find_hub_nodes(graph, top_n=5)
    print(hubs[0])
    # ('DOID:162', 15)
    ```
"""

from __future__ import annotations

from collections import deque
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from biodbs._funcs.graph.core import (
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)


# =============================================================================
# Path Finding
# =============================================================================


def find_shortest_path(
    graph: KnowledgeGraph,
    source: str,
    target: str,
    directed: bool = True,
    max_depth: Optional[int] = None,
) -> Optional[List[str]]:
    """Find the shortest path between two nodes using BFS.

    Args:
        graph: The knowledge graph to search.
        source: ID of the source node.
        target: ID of the target node.
        directed: If True, follow edge direction. If False, treat as undirected.
        max_depth: Maximum path length to search.

    Returns:
        List of node IDs forming the shortest path, or None if no path exists.

    Example:
        ```python
        path = find_shortest_path(graph, "DOID:162", "DOID:1612")
        if path:
            print(" -> ".join(path))
        # DOID:162 -> DOID:1612
        ```
    """
    if source not in graph or target not in graph:
        return None

    if source == target:
        return [source]

    # BFS with path tracking
    queue: deque = deque([(source, [source])])
    visited: Set[str] = {source}

    while queue:
        current, path = queue.popleft()

        if max_depth is not None and len(path) > max_depth:
            continue

        # Get neighbors
        neighbors = set()

        # Outgoing edges
        for edge in graph.get_outgoing_edges(current):
            neighbors.add(edge.target)

        # Incoming edges (if undirected)
        if not directed:
            for edge in graph.get_incoming_edges(current):
                neighbors.add(edge.source)

        for neighbor in neighbors:
            if neighbor == target:
                return path + [neighbor]

            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None


def find_all_paths(
    graph: KnowledgeGraph,
    source: str,
    target: str,
    max_depth: int = 5,
    directed: bool = True,
) -> List[List[str]]:
    """Find all paths between two nodes using DFS.

    Warning: This can be slow for large graphs or high max_depth.

    Args:
        graph: The knowledge graph to search.
        source: ID of the source node.
        target: ID of the target node.
        max_depth: Maximum path length.
        directed: If True, follow edge direction. If False, treat as undirected.

    Returns:
        List of paths, where each path is a list of node IDs.

    Example:
        ```python
        paths = find_all_paths(graph, "A", "D", max_depth=3)
        for path in paths:
            print(" -> ".join(path))
        # A -> B -> D
        # A -> C -> D
        ```
    """
    if source not in graph or target not in graph:
        return []

    all_paths: List[List[str]] = []

    def dfs(current: str, path: List[str], visited: Set[str]):
        if current == target:
            all_paths.append(path.copy())
            return

        if len(path) >= max_depth:
            return

        # Get neighbors
        neighbors = set()

        for edge in graph.get_outgoing_edges(current):
            neighbors.add(edge.target)

        if not directed:
            for edge in graph.get_incoming_edges(current):
                neighbors.add(edge.source)

        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs(neighbor, path, visited)
                path.pop()
                visited.remove(neighbor)

    dfs(source, [source], {source})
    return all_paths


def get_path_edges(
    graph: KnowledgeGraph,
    path: List[str],
) -> List[Optional[Edge]]:
    """Get the edges along a path.

    Args:
        graph: The knowledge graph.
        path: List of node IDs forming a path.

    Returns:
        List of Edge objects (or None if edge not found) between consecutive nodes.
    """
    edges: List[Optional[Edge]] = []
    for i in range(len(path) - 1):
        edge = graph.get_edge(path[i], path[i + 1])
        edges.append(edge)
    return edges


# =============================================================================
# Neighborhood and Component
# =============================================================================


def get_neighborhood(
    graph: KnowledgeGraph,
    node_id: str,
    hops: int = 1,
    directed: bool = False,
    include_edges: bool = False,
) -> Dict[str, Any]:
    """Get nodes within N hops of a starting node.

    Args:
        graph: The knowledge graph.
        node_id: ID of the center node.
        hops: Number of hops (distance) to include.
        directed: If True, only follow outgoing edges.
        include_edges: If True, include edges in the result.

    Returns:
        Dictionary with "nodes" (and optionally "edges") keys.

    Example:
        ```python
        neighborhood = get_neighborhood(graph, "DOID:162", hops=2)
        print(f"Found {len(neighborhood['nodes'])} nodes within 2 hops")
        # Found 25 nodes within 2 hops
        ```
    """
    if node_id not in graph:
        return {"nodes": [], "edges": []} if include_edges else {"nodes": []}

    visited: Set[str] = {node_id}
    current_level = {node_id}
    collected_edges: Set[Edge] = set()

    for _ in range(hops):
        next_level: Set[str] = set()

        for current in current_level:
            # Outgoing edges
            for edge in graph.get_outgoing_edges(current):
                if edge.target not in visited:
                    next_level.add(edge.target)
                    visited.add(edge.target)
                if include_edges:
                    collected_edges.add(edge)

            # Incoming edges (if undirected)
            if not directed:
                for edge in graph.get_incoming_edges(current):
                    if edge.source not in visited:
                        next_level.add(edge.source)
                        visited.add(edge.source)
                    if include_edges:
                        collected_edges.add(edge)

        current_level = next_level

    # Get actual node objects
    nodes = [graph.get_node(nid) for nid in visited if graph.get_node(nid)]

    result: Dict[str, Any] = {"nodes": nodes}
    if include_edges:
        result["edges"] = list(collected_edges)

    return result


def get_connected_component(
    graph: KnowledgeGraph,
    node_id: str,
    directed: bool = False,
) -> Set[str]:
    """Get all nodes in the same connected component.

    Args:
        graph: The knowledge graph.
        node_id: ID of a node in the component.
        directed: If True, use strongly connected component semantics.

    Returns:
        Set of node IDs in the same component.

    Example:
        ```python
        component = get_connected_component(graph, "DOID:162")
        print(f"Component has {len(component)} nodes")
        # Component has 47 nodes
        ```
    """
    if node_id not in graph:
        return set()

    visited: Set[str] = set()
    queue: deque = deque([node_id])

    while queue:
        current = queue.popleft()

        if current in visited:
            continue
        visited.add(current)

        # Outgoing edges
        for edge in graph.get_outgoing_edges(current):
            if edge.target not in visited:
                queue.append(edge.target)

        # Incoming edges (for undirected or weak connectivity)
        if not directed:
            for edge in graph.get_incoming_edges(current):
                if edge.source not in visited:
                    queue.append(edge.source)

    return visited


def get_all_connected_components(
    graph: KnowledgeGraph,
    directed: bool = False,
) -> List[Set[str]]:
    """Get all connected components in the graph.

    Args:
        graph: The knowledge graph.
        directed: If True, find strongly connected components.

    Returns:
        List of sets, each containing node IDs in a component.
    """
    remaining = set(node.id for node in graph.nodes)
    components: List[Set[str]] = []

    while remaining:
        # Pick any remaining node
        start = next(iter(remaining))
        component = get_connected_component(graph, start, directed)
        components.append(component)
        remaining -= component

    return components


# =============================================================================
# Hub Detection and Centrality
# =============================================================================


def find_hub_nodes(
    graph: KnowledgeGraph,
    top_n: int = 10,
    direction: str = "both",
    node_type: Optional[NodeType] = None,
) -> List[Tuple[str, int]]:
    """Find the most highly connected nodes (hubs).

    Args:
        graph: The knowledge graph.
        top_n: Number of top hubs to return.
        direction: "outgoing", "incoming", or "both".
        node_type: Optional filter by node type.

    Returns:
        List of (node_id, degree) tuples, sorted by degree descending.

    Example:
        ```python
        hubs = find_hub_nodes(graph, top_n=5)
        for node_id, degree in hubs:
            print(f"{node_id}: {degree} connections")
        # DOID:162: 15 connections
        # DOID:4: 12 connections
        # ...
        ```
    """
    degrees: List[Tuple[str, int]] = []

    for node in graph.nodes:
        if node_type is not None and node.node_type != node_type:
            continue

        degree = graph.get_degree(node.id, direction)
        degrees.append((node.id, degree))

    # Sort by degree descending
    degrees.sort(key=lambda x: -x[1])

    return degrees[:top_n]


def compute_degree_distribution(
    graph: KnowledgeGraph,
    direction: str = "both",
) -> Dict[int, int]:
    """Compute the degree distribution of the graph.

    Args:
        graph: The knowledge graph.
        direction: "outgoing", "incoming", or "both".

    Returns:
        Dictionary mapping degree to count of nodes with that degree.
    """
    distribution: Dict[int, int] = {}

    for node in graph.nodes:
        degree = graph.get_degree(node.id, direction)
        distribution[degree] = distribution.get(degree, 0) + 1

    return dict(sorted(distribution.items()))


def compute_betweenness_centrality(
    graph: KnowledgeGraph,
    normalized: bool = True,
    sample_size: Optional[int] = None,
) -> Dict[str, float]:
    """Compute approximate betweenness centrality for all nodes.

    Uses BFS-based algorithm. For large graphs, use sample_size
    to compute approximate centrality.

    Args:
        graph: The knowledge graph.
        normalized: If True, normalize by (n-1)(n-2)/2.
        sample_size: If set, sample this many source nodes.

    Returns:
        Dictionary mapping node_id to betweenness centrality score.
    """
    node_ids = [node.id for node in graph.nodes]
    n = len(node_ids)

    if n < 2:
        return {nid: 0.0 for nid in node_ids}

    centrality: Dict[str, float] = {nid: 0.0 for nid in node_ids}

    # Select source nodes
    if sample_size and sample_size < n:
        import random
        sources = random.sample(node_ids, sample_size)
    else:
        sources = node_ids

    for source in sources:
        # BFS from source
        stack: List[str] = []
        predecessors: Dict[str, List[str]] = {nid: [] for nid in node_ids}
        sigma: Dict[str, int] = {nid: 0 for nid in node_ids}
        sigma[source] = 1
        distance: Dict[str, int] = {nid: -1 for nid in node_ids}
        distance[source] = 0

        queue: deque = deque([source])

        while queue:
            v = queue.popleft()
            stack.append(v)

            for edge in graph.get_outgoing_edges(v):
                w = edge.target
                if distance[w] < 0:
                    queue.append(w)
                    distance[w] = distance[v] + 1

                if distance[w] == distance[v] + 1:
                    sigma[w] += sigma[v]
                    predecessors[w].append(v)

        # Accumulation
        delta: Dict[str, float] = {nid: 0.0 for nid in node_ids}

        while stack:
            w = stack.pop()
            for v in predecessors[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])

            if w != source:
                centrality[w] += delta[w]

    # Normalization
    if normalized and n > 2:
        norm = 2.0 / ((n - 1) * (n - 2))
        centrality = {k: v * norm for k, v in centrality.items()}

    return centrality


# =============================================================================
# Graph Statistics
# =============================================================================


def get_graph_statistics(
    graph: KnowledgeGraph,
    compute_centrality: bool = False,
) -> Dict[str, Any]:
    """Get comprehensive statistics about the graph.

    Args:
        graph: The knowledge graph.
        compute_centrality: If True, compute betweenness centrality (slower).

    Returns:
        Dictionary with various statistics.

    Example:
        ```python
        stats = get_graph_statistics(graph)
        print(f"Density: {stats['density']:.4f}")
        # Density: 0.0213
        print(f"Components: {stats['num_components']}")
        # Components: 1
        ```
    """
    n = graph.node_count
    m = graph.edge_count

    stats: Dict[str, Any] = {
        "name": graph.name,
        "source": graph.source.value,
        "num_nodes": n,
        "num_edges": m,
    }

    if n > 0:
        # Density (for directed graph: m / (n * (n-1)))
        max_edges = n * (n - 1) if n > 1 else 1
        stats["density"] = m / max_edges if max_edges > 0 else 0.0

        # Degree statistics
        degrees = [graph.get_degree(node.id, "both") for node in graph.nodes]
        stats["avg_degree"] = sum(degrees) / n
        stats["max_degree"] = max(degrees)
        stats["min_degree"] = min(degrees)

        # Out-degree statistics
        out_degrees = [graph.get_degree(node.id, "outgoing") for node in graph.nodes]
        stats["avg_out_degree"] = sum(out_degrees) / n

        # In-degree statistics
        in_degrees = [graph.get_degree(node.id, "incoming") for node in graph.nodes]
        stats["avg_in_degree"] = sum(in_degrees) / n

        # Isolated nodes (degree 0)
        stats["num_isolated"] = sum(1 for d in degrees if d == 0)

        # Connected components
        components = get_all_connected_components(graph)
        stats["num_components"] = len(components)
        stats["largest_component_size"] = max(len(c) for c in components) if components else 0

        # Node type distribution
        stats["node_type_counts"] = graph.get_node_type_counts()

        # Edge type distribution
        stats["edge_type_counts"] = graph.get_edge_type_counts()

        # Self-loops
        stats["num_self_loops"] = sum(
            1 for edge in graph.edges if edge.source == edge.target
        )

        # Compute centrality if requested
        if compute_centrality and n <= 1000:  # Only for smaller graphs
            stats["betweenness_centrality"] = compute_betweenness_centrality(
                graph, normalized=True
            )

    return stats


def format_statistics(stats: Dict[str, Any]) -> str:
    """Format graph statistics as a readable string.

    Args:
        stats: Dictionary from get_graph_statistics().

    Returns:
        Formatted string representation.
    """
    lines = [
        f"Graph Statistics: {stats.get('name', 'Unknown')}",
        "=" * 50,
        f"Nodes: {stats.get('num_nodes', 0)}",
        f"Edges: {stats.get('num_edges', 0)}",
        f"Density: {stats.get('density', 0):.6f}",
        "",
        "Degree Statistics:",
        f"  Average: {stats.get('avg_degree', 0):.2f}",
        f"  Maximum: {stats.get('max_degree', 0)}",
        f"  Minimum: {stats.get('min_degree', 0)}",
        "",
        f"Isolated nodes: {stats.get('num_isolated', 0)}",
        f"Self-loops: {stats.get('num_self_loops', 0)}",
        f"Connected components: {stats.get('num_components', 0)}",
        f"Largest component: {stats.get('largest_component_size', 0)} nodes",
    ]

    if stats.get("node_type_counts"):
        lines.append("")
        lines.append("Node types:")
        for node_type, count in stats["node_type_counts"].items():
            lines.append(f"  {node_type.value}: {count}")

    if stats.get("edge_type_counts"):
        lines.append("")
        lines.append("Edge types:")
        for edge_type, count in stats["edge_type_counts"].items():
            lines.append(f"  {edge_type.value}: {count}")

    return "\n".join(lines)
