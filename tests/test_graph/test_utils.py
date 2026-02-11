"""Tests for biodbs._funcs.graph.utils module."""

import pytest
from biodbs._funcs.graph.core import (
    DataSource,
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)
from biodbs._funcs.graph.utils import (
    compute_betweenness_centrality,
    compute_degree_distribution,
    find_all_paths,
    find_hub_nodes,
    find_shortest_path,
    format_statistics,
    get_all_connected_components,
    get_connected_component,
    get_graph_statistics,
    get_neighborhood,
    get_path_edges,
)


@pytest.fixture
def diamond_graph():
    """Diamond graph: A->B, A->C, B->D, C->D plus isolated E and chain F->G->H."""
    g = KnowledgeGraph(name="TestGraph", source=DataSource.CUSTOM)
    for nid in "ABCDEFGH":
        g.add_node(Node(id=nid, label=nid, node_type=NodeType.GENE))
    g.add_edge(Edge(source="A", target="B", relation=EdgeType.IS_A))
    g.add_edge(Edge(source="A", target="C", relation=EdgeType.PART_OF))
    g.add_edge(Edge(source="B", target="D", relation=EdgeType.IS_A))
    g.add_edge(Edge(source="C", target="D", relation=EdgeType.PART_OF))
    # isolated E — no edges
    # chain F->G->H
    g.add_edge(Edge(source="F", target="G", relation=EdgeType.RELATED_TO))
    g.add_edge(Edge(source="G", target="H", relation=EdgeType.RELATED_TO))
    return g


@pytest.fixture
def empty_graph():
    return KnowledgeGraph(name="Empty", source=DataSource.CUSTOM)


@pytest.fixture
def single_node_graph():
    g = KnowledgeGraph(name="Single", source=DataSource.CUSTOM)
    g.add_node(Node(id="X", label="X"))
    return g


# =============================================================================
# TestFindShortestPath
# =============================================================================


class TestFindShortestPath:
    def test_direct_edge(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "A", "B")
        assert path == ["A", "B"]

    def test_two_hop_path(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "A", "D")
        assert len(path) == 3
        assert path[0] == "A"
        assert path[-1] == "D"

    def test_same_node(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "A", "A")
        assert path == ["A"]

    def test_no_path_directed(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "D", "A", directed=True)
        assert path is None

    def test_undirected_reverse(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "D", "A", directed=False)
        assert path is not None
        assert path[0] == "D"
        assert path[-1] == "A"

    def test_nonexistent_source(self, diamond_graph):
        assert find_shortest_path(diamond_graph, "Z", "A") is None

    def test_nonexistent_target(self, diamond_graph):
        assert find_shortest_path(diamond_graph, "A", "Z") is None

    def test_disconnected_nodes(self, diamond_graph):
        assert find_shortest_path(diamond_graph, "A", "E") is None

    def test_max_depth_too_short(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "A", "D", max_depth=1)
        assert path is None

    def test_max_depth_sufficient(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "A", "D", max_depth=3)
        assert path is not None
        assert len(path) == 3

    def test_chain_path(self, diamond_graph):
        path = find_shortest_path(diamond_graph, "F", "H")
        assert path == ["F", "G", "H"]


# =============================================================================
# TestFindAllPaths
# =============================================================================


class TestFindAllPaths:
    def test_two_paths_diamond(self, diamond_graph):
        paths = find_all_paths(diamond_graph, "A", "D", max_depth=5)
        assert len(paths) == 2
        assert ["A", "B", "D"] in paths
        assert ["A", "C", "D"] in paths

    def test_single_path(self, diamond_graph):
        paths = find_all_paths(diamond_graph, "F", "H", max_depth=5)
        assert paths == [["F", "G", "H"]]

    def test_no_path(self, diamond_graph):
        paths = find_all_paths(diamond_graph, "D", "A", directed=True)
        assert paths == []

    def test_undirected(self, diamond_graph):
        paths = find_all_paths(diamond_graph, "D", "A", directed=False, max_depth=5)
        assert len(paths) >= 2

    def test_nonexistent_node(self, diamond_graph):
        assert find_all_paths(diamond_graph, "Z", "A") == []

    def test_max_depth_limits(self, diamond_graph):
        paths = find_all_paths(diamond_graph, "A", "D", max_depth=1)
        assert paths == []

    def test_max_depth_exact(self, diamond_graph):
        paths = find_all_paths(diamond_graph, "A", "D", max_depth=3)
        # max_depth=3 allows paths with up to 3 nodes (2 edges)
        assert len(paths) == 2

    def test_same_source_target(self, diamond_graph):
        paths = find_all_paths(diamond_graph, "A", "A")
        assert paths == [["A"]]


# =============================================================================
# TestGetPathEdges
# =============================================================================


class TestGetPathEdges:
    def test_edges_along_path(self, diamond_graph):
        edges = get_path_edges(diamond_graph, ["A", "B", "D"])
        assert len(edges) == 2
        assert edges[0] is not None
        assert edges[0].source == "A"
        assert edges[0].target == "B"
        assert edges[1].source == "B"
        assert edges[1].target == "D"

    def test_empty_path(self, diamond_graph):
        assert get_path_edges(diamond_graph, []) == []

    def test_single_node_path(self, diamond_graph):
        assert get_path_edges(diamond_graph, ["A"]) == []

    def test_missing_edge_returns_none(self, diamond_graph):
        edges = get_path_edges(diamond_graph, ["A", "D"])
        assert len(edges) == 1
        assert edges[0] is None


# =============================================================================
# TestGetNeighborhood
# =============================================================================


class TestGetNeighborhood:
    def test_one_hop_outgoing(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "A", hops=1, directed=True)
        node_ids = {n.id for n in result["nodes"]}
        assert "A" in node_ids
        assert "B" in node_ids
        assert "C" in node_ids

    def test_one_hop_undirected(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "D", hops=1, directed=False)
        node_ids = {n.id for n in result["nodes"]}
        assert "D" in node_ids
        assert "B" in node_ids
        assert "C" in node_ids

    def test_two_hops(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "A", hops=2, directed=True)
        node_ids = {n.id for n in result["nodes"]}
        assert "D" in node_ids

    def test_include_edges(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "A", hops=1, include_edges=True)
        assert "edges" in result
        assert len(result["edges"]) >= 2

    def test_nonexistent_node(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "Z", hops=1)
        assert result["nodes"] == []

    def test_nonexistent_node_with_edges(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "Z", hops=1, include_edges=True)
        assert result["nodes"] == []
        assert result["edges"] == []

    def test_isolated_node(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "E", hops=1)
        assert len(result["nodes"]) == 1
        assert result["nodes"][0].id == "E"

    def test_zero_hops(self, diamond_graph):
        result = get_neighborhood(diamond_graph, "A", hops=0)
        assert len(result["nodes"]) == 1
        assert result["nodes"][0].id == "A"


# =============================================================================
# TestGetConnectedComponent
# =============================================================================


class TestGetConnectedComponent:
    def test_diamond_component(self, diamond_graph):
        comp = get_connected_component(diamond_graph, "A", directed=False)
        assert {"A", "B", "C", "D"} == comp

    def test_chain_component(self, diamond_graph):
        comp = get_connected_component(diamond_graph, "F", directed=False)
        assert {"F", "G", "H"} == comp

    def test_isolated_node(self, diamond_graph):
        comp = get_connected_component(diamond_graph, "E", directed=False)
        assert comp == {"E"}

    def test_nonexistent_node(self, diamond_graph):
        assert get_connected_component(diamond_graph, "Z") == set()

    def test_directed_component(self, diamond_graph):
        comp = get_connected_component(diamond_graph, "A", directed=True)
        assert "A" in comp
        assert "B" in comp
        assert "D" in comp


# =============================================================================
# TestGetAllConnectedComponents
# =============================================================================


class TestGetAllConnectedComponents:
    def test_three_components(self, diamond_graph):
        comps = get_all_connected_components(diamond_graph, directed=False)
        sizes = sorted(len(c) for c in comps)
        assert sizes == [1, 3, 4]

    def test_empty_graph(self, empty_graph):
        assert get_all_connected_components(empty_graph) == []

    def test_single_node(self, single_node_graph):
        comps = get_all_connected_components(single_node_graph)
        assert len(comps) == 1
        assert comps[0] == {"X"}


# =============================================================================
# TestFindHubNodes
# =============================================================================


class TestFindHubNodes:
    def test_highest_degree(self, diamond_graph):
        hubs = find_hub_nodes(diamond_graph, top_n=2)
        hub_ids = [h[0] for h in hubs]
        # A and D should be hubs (each has degree 2 outgoing/incoming)
        assert "A" in hub_ids or "D" in hub_ids

    def test_top_n_limits(self, diamond_graph):
        hubs = find_hub_nodes(diamond_graph, top_n=3)
        assert len(hubs) == 3

    def test_outgoing_direction(self, diamond_graph):
        hubs = find_hub_nodes(diamond_graph, top_n=1, direction="outgoing")
        assert hubs[0][0] == "A"  # A has 2 outgoing edges
        assert hubs[0][1] == 2

    def test_incoming_direction(self, diamond_graph):
        hubs = find_hub_nodes(diamond_graph, top_n=1, direction="incoming")
        assert hubs[0][0] == "D"  # D has 2 incoming edges
        assert hubs[0][1] == 2

    def test_filter_by_type(self, diamond_graph):
        hubs = find_hub_nodes(diamond_graph, node_type=NodeType.DISEASE)
        assert hubs == []  # All nodes are GENE type


# =============================================================================
# TestComputeDegreeDistribution
# =============================================================================


class TestComputeDegreeDistribution:
    def test_distribution_keys(self, diamond_graph):
        dist = compute_degree_distribution(diamond_graph)
        assert isinstance(dist, dict)
        # E has degree 0
        assert 0 in dist

    def test_sorted_keys(self, diamond_graph):
        dist = compute_degree_distribution(diamond_graph)
        keys = list(dist.keys())
        assert keys == sorted(keys)

    def test_outgoing_only(self, diamond_graph):
        dist = compute_degree_distribution(diamond_graph, direction="outgoing")
        assert isinstance(dist, dict)


# =============================================================================
# TestComputeBetweennessCentrality
# =============================================================================


class TestComputeBetweennessCentrality:
    def test_returns_all_nodes(self, diamond_graph):
        bc = compute_betweenness_centrality(diamond_graph)
        assert len(bc) == diamond_graph.node_count

    def test_isolated_node_zero(self, diamond_graph):
        bc = compute_betweenness_centrality(diamond_graph)
        assert bc["E"] == 0.0

    def test_single_node_graph(self, single_node_graph):
        bc = compute_betweenness_centrality(single_node_graph)
        assert bc["X"] == 0.0

    def test_normalized_values(self, diamond_graph):
        bc = compute_betweenness_centrality(diamond_graph, normalized=True)
        for v in bc.values():
            assert v >= 0.0


# =============================================================================
# TestGetGraphStatistics
# =============================================================================


class TestGetGraphStatistics:
    def test_basic_stats(self, diamond_graph):
        stats = get_graph_statistics(diamond_graph)
        assert stats["num_nodes"] == 8
        assert stats["num_edges"] == 6
        assert stats["name"] == "TestGraph"
        assert "density" in stats
        assert "avg_degree" in stats

    def test_empty_graph(self, empty_graph):
        stats = get_graph_statistics(empty_graph)
        assert stats["num_nodes"] == 0
        assert stats["num_edges"] == 0

    def test_with_centrality(self, diamond_graph):
        stats = get_graph_statistics(diamond_graph, compute_centrality=True)
        assert "betweenness_centrality" in stats


# =============================================================================
# TestFormatStatistics
# =============================================================================


class TestFormatStatistics:
    def test_contains_key_info(self, diamond_graph):
        stats = get_graph_statistics(diamond_graph)
        text = format_statistics(stats)
        assert "TestGraph" in text
        assert "Nodes: 8" in text
        assert "Edges: 6" in text

    def test_includes_node_types(self, diamond_graph):
        stats = get_graph_statistics(diamond_graph)
        text = format_statistics(stats)
        assert "Node types:" in text
        assert "gene" in text
