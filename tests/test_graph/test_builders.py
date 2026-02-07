"""Tests for biodbs.graph.builders module."""

import pytest
from biodbs.graph import (
    Node,
    Edge,
    KnowledgeGraph,
    NodeType,
    EdgeType,
    DataSource,
    build_graph,
    merge_graphs,
)


class TestBuildGraph:
    """Tests for the build_graph function."""

    def test_build_empty_graph(self):
        """Test building an empty graph."""
        graph = build_graph([], name="Empty")
        assert graph.name == "Empty"
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_build_graph_with_nodes(self):
        """Test building a graph with nodes only."""
        nodes = [
            Node(id="A", label="Node A"),
            Node(id="B", label="Node B"),
        ]
        graph = build_graph(nodes, name="NodesOnly")

        assert graph.node_count == 2
        assert graph.edge_count == 0
        assert "A" in graph
        assert "B" in graph

    def test_build_graph_with_edges(self):
        """Test building a graph with nodes and edges."""
        nodes = [
            Node(id="A", label="Node A"),
            Node(id="B", label="Node B"),
            Node(id="C", label="Node C"),
        ]
        edges = [
            Edge(source="A", target="B", relation=EdgeType.IS_A),
            Edge(source="B", target="C", relation=EdgeType.PART_OF),
        ]
        graph = build_graph(nodes, edges, name="WithEdges")

        assert graph.node_count == 3
        assert graph.edge_count == 2
        assert graph.has_edge("A", "B")
        assert graph.has_edge("B", "C")

    def test_build_graph_with_source(self):
        """Test building a graph with a data source."""
        nodes = [Node(id="A", label="A")]
        graph = build_graph(
            nodes,
            name="Test",
            source=DataSource.KEGG,
            description="Test graph",
        )

        assert graph.source == DataSource.KEGG
        assert graph.description == "Test graph"


class TestMergeGraphs:
    """Tests for the merge_graphs function."""

    @pytest.fixture
    def graph1(self):
        """Create first test graph."""
        graph = KnowledgeGraph(name="Graph1")
        graph.add_node(Node(id="A", label="A", node_type=NodeType.DISEASE))
        graph.add_node(Node(id="B", label="B", node_type=NodeType.DISEASE))
        graph.add_edge(Edge(source="A", target="B", relation=EdgeType.IS_A))
        return graph

    @pytest.fixture
    def graph2(self):
        """Create second test graph."""
        graph = KnowledgeGraph(name="Graph2")
        graph.add_node(Node(id="C", label="C", node_type=NodeType.GENE))
        graph.add_node(Node(id="D", label="D", node_type=NodeType.GENE))
        graph.add_edge(Edge(source="C", target="D", relation=EdgeType.INTERACTS_WITH))
        return graph

    def test_merge_empty_graphs(self):
        """Test merging no graphs."""
        merged = merge_graphs()
        assert merged.node_count == 0
        assert merged.edge_count == 0

    def test_merge_single_graph(self, graph1):
        """Test merging a single graph."""
        merged = merge_graphs(graph1, name="Merged")
        assert merged.name == "Merged"
        assert merged.node_count == 2
        assert merged.edge_count == 1

    def test_merge_two_graphs(self, graph1, graph2):
        """Test merging two graphs."""
        merged = merge_graphs(graph1, graph2, name="Merged")

        assert merged.node_count == 4
        assert merged.edge_count == 2
        assert "A" in merged
        assert "C" in merged
        assert merged.has_edge("A", "B")
        assert merged.has_edge("C", "D")

    def test_merge_with_overlapping_nodes(self, graph1):
        """Test merging graphs with overlapping nodes."""
        graph3 = KnowledgeGraph(name="Graph3")
        graph3.add_node(Node(id="A", label="Different A"))  # Same ID
        graph3.add_node(Node(id="E", label="E"))

        merged = merge_graphs(graph1, graph3)

        # Node count should be 3 (A, B, E) - duplicate A is skipped
        assert merged.node_count == 3
        # Original A's label should be kept (first occurrence wins)
        assert merged.get_node("A").label == "A"

    def test_merge_with_connecting_edge(self, graph1, graph2):
        """Test merging graphs and adding connecting edge."""
        merged = merge_graphs(graph1, graph2, name="Connected")

        # Add an edge connecting the two graphs
        merged.add_edge(Edge(source="B", target="C", relation=EdgeType.ASSOCIATED_WITH))

        assert merged.edge_count == 3
        assert merged.has_edge("B", "C")


class TestBuildDiseaseGraph:
    """Tests for build_disease_graph function.

    These tests use mocked data since we don't want to make actual API calls.
    """

    def test_placeholder(self):
        """Placeholder test - real tests would use mocked DOFetchedData."""
        # TODO: Add tests with mocked Disease Ontology data
        pass


class TestBuildGOGraph:
    """Tests for build_go_graph function.

    These tests use mocked data since we don't want to make actual API calls.
    """

    def test_placeholder(self):
        """Placeholder test - real tests would use mocked QuickGOFetchedData."""
        # TODO: Add tests with mocked QuickGO data
        pass


class TestBuildReactomeGraph:
    """Tests for build_reactome_graph function.

    These tests use mocked data since we don't want to make actual API calls.
    """

    def test_placeholder(self):
        """Placeholder test - real tests would use mocked ReactomeFetchedData."""
        # TODO: Add tests with mocked Reactome data
        pass


class TestBuildKEGGGraph:
    """Tests for build_kegg_graph function.

    These tests use mocked data since we don't want to make actual API calls.
    """

    def test_placeholder(self):
        """Placeholder test - real tests would use mocked KEGGFetchedData."""
        # TODO: Add tests with mocked KEGG data
        pass
