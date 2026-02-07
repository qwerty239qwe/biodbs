"""Tests for biodbs.graph.core module."""

import pytest
from biodbs.graph import (
    Node,
    Edge,
    KnowledgeGraph,
    NodeType,
    EdgeType,
    DataSource,
)


# =============================================================================
# Node Tests
# =============================================================================


class TestNode:
    """Tests for the Node class."""

    def test_node_creation_basic(self):
        """Test creating a basic node."""
        node = Node(id="test:1", label="Test Node")
        assert node.id == "test:1"
        assert node.label == "Test Node"
        assert node.node_type == NodeType.OTHER
        assert node.source == DataSource.CUSTOM

    def test_node_creation_with_type(self):
        """Test creating a node with specific type."""
        node = Node(
            id="DOID:162",
            label="cancer",
            node_type=NodeType.DISEASE,
            source=DataSource.DISEASE_ONTOLOGY,
        )
        assert node.id == "DOID:162"
        assert node.node_type == NodeType.DISEASE
        assert node.source == DataSource.DISEASE_ONTOLOGY

    def test_node_with_properties(self):
        """Test creating a node with properties."""
        node = Node(
            id="test:1",
            label="Test",
            properties=frozenset([("key1", "value1"), ("key2", 42)]),
        )
        assert node.get_property("key1") == "value1"
        assert node.get_property("key2") == 42
        assert node.get_property("nonexistent") is None
        assert node.get_property("nonexistent", "default") == "default"

    def test_node_with_xrefs(self):
        """Test creating a node with cross-references."""
        node = Node(
            id="test:1",
            label="Test",
            xrefs=frozenset(["MESH:D009369", "UMLS:C0006826"]),
        )
        assert "MESH:D009369" in node.xrefs
        assert "UMLS:C0006826" in node.xrefs
        assert len(node.xrefs) == 2

    def test_node_immutability(self):
        """Test that nodes are immutable."""
        node = Node(id="test:1", label="Test")
        with pytest.raises(AttributeError):
            node.id = "test:2"

    def test_node_equality(self):
        """Test node equality is based on ID."""
        node1 = Node(id="test:1", label="Test 1")
        node2 = Node(id="test:1", label="Test 2")  # Same ID, different label
        node3 = Node(id="test:2", label="Test 1")  # Different ID

        assert node1 == node2
        assert node1 != node3

    def test_node_hash(self):
        """Test node hashing for use in sets/dicts."""
        node1 = Node(id="test:1", label="Test")
        node2 = Node(id="test:1", label="Test")
        node3 = Node(id="test:2", label="Test")

        assert hash(node1) == hash(node2)
        node_set = {node1, node3}
        assert len(node_set) == 2

    def test_node_with_properties_method(self):
        """Test with_properties creates new node."""
        node = Node(id="test:1", label="Test")
        new_node = node.with_properties(key1="value1")

        assert node.get_property("key1") is None
        assert new_node.get_property("key1") == "value1"
        assert node.id == new_node.id

    def test_node_to_dict(self):
        """Test converting node to dictionary."""
        node = Node(
            id="test:1",
            label="Test",
            node_type=NodeType.GENE,
            source=DataSource.KEGG,
            properties=frozenset([("key", "value")]),
            xrefs=frozenset(["xref:1"]),
        )
        d = node.to_dict()

        assert d["id"] == "test:1"
        assert d["label"] == "Test"
        assert d["node_type"] == "gene"
        assert d["source"] == "kegg"
        assert d["properties"] == {"key": "value"}
        assert "xref:1" in d["xrefs"]

    def test_node_from_dict(self):
        """Test creating node from dictionary."""
        data = {
            "id": "test:1",
            "label": "Test",
            "node_type": "disease",
            "source": "disease_ontology",
            "properties": {"key": "value"},
            "xrefs": ["xref:1"],
        }
        node = Node.from_dict(data)

        assert node.id == "test:1"
        assert node.label == "Test"
        assert node.node_type == NodeType.DISEASE
        assert node.source == DataSource.DISEASE_ONTOLOGY


# =============================================================================
# Edge Tests
# =============================================================================


class TestEdge:
    """Tests for the Edge class."""

    def test_edge_creation_basic(self):
        """Test creating a basic edge."""
        edge = Edge(source="A", target="B")
        assert edge.source == "A"
        assert edge.target == "B"
        assert edge.relation == EdgeType.RELATED_TO
        assert edge.weight == 1.0

    def test_edge_creation_with_relation(self):
        """Test creating an edge with specific relation."""
        edge = Edge(
            source="child",
            target="parent",
            relation=EdgeType.IS_A,
            weight=0.9,
        )
        assert edge.relation == EdgeType.IS_A
        assert edge.weight == 0.9

    def test_edge_with_evidence(self):
        """Test creating an edge with evidence."""
        edge = Edge(
            source="A",
            target="B",
            evidence=frozenset(["PMID:12345", "IDA"]),
        )
        assert "PMID:12345" in edge.evidence
        assert "IDA" in edge.evidence

    def test_edge_immutability(self):
        """Test that edges are immutable."""
        edge = Edge(source="A", target="B")
        with pytest.raises(AttributeError):
            edge.source = "C"

    def test_edge_equality(self):
        """Test edge equality based on source, target, and relation."""
        edge1 = Edge(source="A", target="B", relation=EdgeType.IS_A)
        edge2 = Edge(source="A", target="B", relation=EdgeType.IS_A, weight=0.5)
        edge3 = Edge(source="A", target="B", relation=EdgeType.PART_OF)

        assert edge1 == edge2  # Same source, target, relation
        assert edge1 != edge3  # Different relation

    def test_edge_to_dict(self):
        """Test converting edge to dictionary."""
        edge = Edge(
            source="A",
            target="B",
            relation=EdgeType.IS_A,
            weight=0.8,
            evidence=frozenset(["ev1"]),
        )
        d = edge.to_dict()

        assert d["source"] == "A"
        assert d["target"] == "B"
        assert d["relation"] == "is_a"
        assert d["weight"] == 0.8
        assert "ev1" in d["evidence"]

    def test_edge_from_dict(self):
        """Test creating edge from dictionary."""
        data = {
            "source": "A",
            "target": "B",
            "relation": "is_a",
            "weight": 0.9,
            "evidence": ["ev1", "ev2"],
        }
        edge = Edge.from_dict(data)

        assert edge.source == "A"
        assert edge.target == "B"
        assert edge.relation == EdgeType.IS_A
        assert edge.weight == 0.9


# =============================================================================
# KnowledgeGraph Tests
# =============================================================================


class TestKnowledgeGraph:
    """Tests for the KnowledgeGraph class."""

    @pytest.fixture
    def sample_graph(self):
        """Create a sample graph for testing."""
        graph = KnowledgeGraph(name="TestGraph")

        # Add nodes
        nodes = [
            Node(id="A", label="Node A", node_type=NodeType.DISEASE),
            Node(id="B", label="Node B", node_type=NodeType.DISEASE),
            Node(id="C", label="Node C", node_type=NodeType.DISEASE),
            Node(id="D", label="Node D", node_type=NodeType.GENE),
        ]
        graph.add_nodes(nodes)

        # Add edges
        edges = [
            Edge(source="B", target="A", relation=EdgeType.IS_A),
            Edge(source="C", target="A", relation=EdgeType.IS_A),
            Edge(source="D", target="B", relation=EdgeType.ASSOCIATED_WITH),
        ]
        graph.add_edges(edges)

        return graph

    def test_graph_creation(self):
        """Test creating an empty graph."""
        graph = KnowledgeGraph(name="Test", description="Test graph")
        assert graph.name == "Test"
        assert graph.description == "Test graph"
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_add_node(self, sample_graph):
        """Test adding nodes."""
        assert sample_graph.node_count == 4
        assert "A" in sample_graph
        assert "B" in sample_graph

    def test_add_duplicate_node(self, sample_graph):
        """Test adding duplicate node returns False."""
        new_node = Node(id="A", label="Duplicate")
        result = sample_graph.add_node(new_node)
        assert result is False
        assert sample_graph.node_count == 4

    def test_get_node(self, sample_graph):
        """Test getting a node by ID."""
        node = sample_graph.get_node("A")
        assert node is not None
        assert node.label == "Node A"

        assert sample_graph.get_node("nonexistent") is None

    def test_remove_node(self, sample_graph):
        """Test removing a node removes associated edges."""
        assert sample_graph.has_node("B")
        assert sample_graph.edge_count == 3

        sample_graph.remove_node("B")

        assert not sample_graph.has_node("B")
        assert sample_graph.edge_count == 1  # Only C->A remains

    def test_add_edge(self, sample_graph):
        """Test adding edges."""
        assert sample_graph.edge_count == 3
        assert sample_graph.has_edge("B", "A")

    def test_add_edge_missing_node(self, sample_graph):
        """Test adding edge with missing nodes returns False."""
        edge = Edge(source="A", target="nonexistent")
        result = sample_graph.add_edge(edge)
        assert result is False

    def test_get_edge(self, sample_graph):
        """Test getting an edge."""
        edge = sample_graph.get_edge("B", "A")
        assert edge is not None
        assert edge.relation == EdgeType.IS_A

        assert sample_graph.get_edge("A", "B") is None  # Wrong direction

    def test_get_outgoing_edges(self, sample_graph):
        """Test getting outgoing edges."""
        outgoing = sample_graph.get_outgoing_edges("B")
        assert len(outgoing) == 1
        assert outgoing[0].target == "A"

    def test_get_incoming_edges(self, sample_graph):
        """Test getting incoming edges."""
        incoming = sample_graph.get_incoming_edges("A")
        assert len(incoming) == 2

    def test_get_neighbors(self, sample_graph):
        """Test getting neighbors."""
        neighbors = sample_graph.get_neighbors("A", direction="both")
        assert "B" in neighbors
        assert "C" in neighbors

        neighbors = sample_graph.get_neighbors("B", direction="outgoing")
        assert "A" in neighbors
        assert "D" not in neighbors  # D points to B, not vice versa

    def test_filter_nodes(self, sample_graph):
        """Test filtering nodes."""
        diseases = sample_graph.filter_nodes(node_type=NodeType.DISEASE)
        assert len(diseases) == 3

        genes = sample_graph.filter_nodes(node_type=NodeType.GENE)
        assert len(genes) == 1

    def test_filter_edges(self, sample_graph):
        """Test filtering edges."""
        is_a_edges = sample_graph.filter_edges(relation=EdgeType.IS_A)
        assert len(is_a_edges) == 2

    def test_subgraph(self, sample_graph):
        """Test creating a subgraph."""
        subgraph = sample_graph.subgraph({"A", "B"})
        assert subgraph.node_count == 2
        assert subgraph.edge_count == 1  # Only B->A

    def test_merge(self, sample_graph):
        """Test merging graphs."""
        other = KnowledgeGraph(name="Other")
        other.add_node(Node(id="E", label="Node E"))
        other.add_node(Node(id="A", label="Duplicate"))  # Will be skipped

        merged = sample_graph.merge(other)
        assert merged.node_count == 5
        assert merged.get_node("E") is not None

    def test_get_degree(self, sample_graph):
        """Test getting node degree."""
        assert sample_graph.get_degree("A", "incoming") == 2
        assert sample_graph.get_degree("A", "outgoing") == 0
        assert sample_graph.get_degree("A", "both") == 2

    def test_node_type_counts(self, sample_graph):
        """Test getting node type counts."""
        counts = sample_graph.get_node_type_counts()
        assert counts[NodeType.DISEASE] == 3
        assert counts[NodeType.GENE] == 1

    def test_to_dict(self, sample_graph):
        """Test converting graph to dictionary."""
        d = sample_graph.to_dict()
        assert d["name"] == "TestGraph"
        assert len(d["nodes"]) == 4
        assert len(d["edges"]) == 3

    def test_from_dict(self, sample_graph):
        """Test creating graph from dictionary."""
        d = sample_graph.to_dict()
        restored = KnowledgeGraph.from_dict(d)

        assert restored.name == sample_graph.name
        assert restored.node_count == sample_graph.node_count
        assert restored.edge_count == sample_graph.edge_count

    def test_iteration(self, sample_graph):
        """Test iterating over nodes."""
        node_ids = [node.id for node in sample_graph]
        assert len(node_ids) == 4
        assert "A" in node_ids

    def test_summary(self, sample_graph):
        """Test summary output."""
        summary = sample_graph.summary()
        assert "TestGraph" in summary
        assert "Nodes: 4" in summary
        assert "Edges: 3" in summary


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests for enum types."""

    def test_node_type_values(self):
        """Test NodeType enum values."""
        assert NodeType.GENE.value == "gene"
        assert NodeType.PROTEIN.value == "protein"
        assert NodeType.DISEASE.value == "disease"
        assert NodeType.PATHWAY.value == "pathway"
        assert NodeType.GO_TERM.value == "go_term"

    def test_edge_type_values(self):
        """Test EdgeType enum values."""
        assert EdgeType.IS_A.value == "is_a"
        assert EdgeType.PART_OF.value == "part_of"
        assert EdgeType.REGULATES.value == "regulates"
        assert EdgeType.PARTICIPATES_IN.value == "participates_in"

    def test_data_source_values(self):
        """Test DataSource enum values."""
        assert DataSource.DISEASE_ONTOLOGY.value == "disease_ontology"
        assert DataSource.GENE_ONTOLOGY.value == "gene_ontology"
        assert DataSource.REACTOME.value == "reactome"
        assert DataSource.KEGG.value == "kegg"
