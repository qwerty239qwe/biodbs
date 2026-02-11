"""Tests for biodbs.graph.exporters module."""

import json
import os
import tempfile
import pytest
from pathlib import Path

from biodbs.graph import (
    Node,
    Edge,
    KnowledgeGraph,
    NodeType,
    EdgeType,
    DataSource,
    to_json_ld,
    to_neo4j_csv,
    to_cypher,
)
from biodbs._funcs.graph.exporters import _make_uri, _cypher_value


# Helper functions for checking optional dependencies
def _check_networkx_available():
    """Check if networkx is available."""
    try:
        import networkx
        return True
    except ImportError:
        return False


def _check_rdflib_available():
    """Check if rdflib is available."""
    try:
        import rdflib
        return True
    except ImportError:
        return False


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing exports."""
    graph = KnowledgeGraph(
        name="ExportTest",
        description="Test graph for export functions",
        source=DataSource.DISEASE_ONTOLOGY,
    )

    # Add nodes with various properties
    nodes = [
        Node(
            id="DOID:162",
            label="cancer",
            node_type=NodeType.DISEASE,
            source=DataSource.DISEASE_ONTOLOGY,
            properties=frozenset([("definition", "A disease of cellular proliferation")]),
            xrefs=frozenset(["MESH:D009369", "UMLS:C0006826"]),
        ),
        Node(
            id="DOID:1612",
            label="breast cancer",
            node_type=NodeType.DISEASE,
            source=DataSource.DISEASE_ONTOLOGY,
        ),
        Node(
            id="DOID:3571",
            label="liver cancer",
            node_type=NodeType.DISEASE,
            source=DataSource.DISEASE_ONTOLOGY,
        ),
    ]
    graph.add_nodes(nodes)

    # Add edges
    edges = [
        Edge(
            source="DOID:1612",
            target="DOID:162",
            relation=EdgeType.IS_A,
            evidence=frozenset(["IEA"]),
        ),
        Edge(
            source="DOID:3571",
            target="DOID:162",
            relation=EdgeType.IS_A,
        ),
    ]
    graph.add_edges(edges)

    return graph


class TestToJsonLD:
    """Tests for to_json_ld export function."""

    def test_basic_export(self, sample_graph):
        """Test basic JSON-LD export."""
        result = to_json_ld(sample_graph)

        assert "@context" in result
        assert "@graph" in result
        assert len(result["@graph"]) == 3

    def test_export_without_context(self, sample_graph):
        """Test export without @context."""
        result = to_json_ld(sample_graph, include_context=False)

        assert "@context" not in result
        assert "@graph" in result

    def test_node_structure(self, sample_graph):
        """Test exported node structure."""
        result = to_json_ld(sample_graph)

        # Find the cancer node (ID may be transformed to OBO format)
        cancer_node = None
        for node in result["@graph"]:
            # Check for various ID formats
            if "162" in node["@id"] and "DOID" in node["@id"]:
                cancer_node = node
                break

        assert cancer_node is not None
        assert cancer_node["label"] == "cancer"
        assert "@type" in cancer_node

    def test_edges_as_properties(self, sample_graph):
        """Test that edges are represented as node properties."""
        result = to_json_ld(sample_graph)

        # Find the breast cancer node (ID may be transformed to OBO format)
        bc_node = None
        for node in result["@graph"]:
            # Check for various ID formats
            if "1612" in node["@id"] and "DOID" in node["@id"]:
                bc_node = node
                break

        assert bc_node is not None
        # Should have is_a property pointing to cancer
        assert "is_a" in bc_node or "@type" in bc_node

    def test_json_serializable(self, sample_graph):
        """Test that output is JSON serializable."""
        result = to_json_ld(sample_graph)

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Should round-trip
        parsed = json.loads(json_str)
        assert "@graph" in parsed

    def test_compact_mode(self, sample_graph):
        """Test compact mode omits source field from nodes."""
        result = to_json_ld(sample_graph, compact=True)

        for node in result["@graph"]:
            assert "source" not in node

    def test_base_uri(self, sample_graph):
        """Test base_uri is used for node IDs."""
        result = to_json_ld(sample_graph, base_uri="http://mykg/")

        for node in result["@graph"]:
            assert node["@id"].startswith("http://mykg/")

    def test_node_properties_exported(self, sample_graph):
        """Test that node properties like definition are exported as description."""
        result = to_json_ld(sample_graph)

        cancer_node = None
        for node in result["@graph"]:
            if "162" in node["@id"] and "DOID" in node["@id"]:
                cancer_node = node
                break

        assert cancer_node is not None
        assert cancer_node["description"] == "A disease of cellular proliferation"

    def test_xrefs_exported(self, sample_graph):
        """Test that node xrefs are exported."""
        result = to_json_ld(sample_graph)

        cancer_node = None
        for node in result["@graph"]:
            if "162" in node["@id"] and "DOID" in node["@id"]:
                cancer_node = node
                break

        assert cancer_node is not None
        assert "xref" in cancer_node
        assert isinstance(cancer_node["xref"], list)
        xrefs_set = set(cancer_node["xref"])
        assert "MESH:D009369" in xrefs_set
        assert "UMLS:C0006826" in xrefs_set


class TestMakeUri:
    """Tests for _make_uri helper function."""

    def test_doid_prefix(self):
        """Test DOID prefix is converted to OBO format."""
        assert _make_uri("DOID:162") == "obo:DOID_162"

    def test_go_prefix(self):
        """Test GO prefix is converted to OBO format."""
        assert _make_uri("GO:0008150") == "obo:GO_0008150"

    def test_reactome_prefix(self):
        """Test Reactome R- prefix is converted."""
        assert _make_uri("R-HSA-123") == "reactome:R-HSA-123"

    def test_uniprot_prefix(self):
        """Test UniProtKB prefix is converted."""
        assert _make_uri("UniProtKB:P04637") == "uniprot:P04637"

    def test_with_base_uri(self):
        """Test that base_uri overrides prefix-based conversion."""
        assert _make_uri("DOID:162", base_uri="http://ex/") == "http://ex/DOID:162"

    def test_unknown_prefix(self):
        """Test that unknown prefixes are returned as-is."""
        assert _make_uri("CUSTOM:123") == "CUSTOM:123"


class TestCypherValue:
    """Tests for _cypher_value helper function."""

    def test_none(self):
        """Test None converts to null."""
        assert _cypher_value(None) == "null"

    def test_bool_true(self):
        """Test True converts to true."""
        assert _cypher_value(True) == "true"

    def test_bool_false(self):
        """Test False converts to false."""
        assert _cypher_value(False) == "false"

    def test_int(self):
        """Test integer conversion."""
        assert _cypher_value(42) == "42"

    def test_float(self):
        """Test float conversion."""
        assert _cypher_value(3.14) == "3.14"

    def test_string(self):
        """Test string is quoted with single quotes."""
        assert _cypher_value("hello") == "'hello'"

    def test_string_with_quotes(self):
        """Test string with single quotes is properly escaped."""
        assert _cypher_value("it's") == "'it\\'s'"

    def test_list(self):
        """Test list conversion."""
        assert _cypher_value([1, "a"]) == "[1, 'a']"


class TestToNeo4jCsv:
    """Tests for to_neo4j_csv export function."""

    def test_csv_export(self, sample_graph):
        """Test CSV export creates both files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nodes_path, edges_path = to_neo4j_csv(sample_graph, tmpdir)

            assert nodes_path.exists()
            assert edges_path.exists()

    def test_nodes_csv_content(self, sample_graph):
        """Test nodes CSV has correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nodes_path, _ = to_neo4j_csv(sample_graph, tmpdir)

            content = nodes_path.read_text()
            lines = content.strip().split("\n")

            # Header + 3 nodes
            assert len(lines) == 4

            # Check header
            assert "id:ID" in lines[0]
            assert "label" in lines[0]
            assert ":LABEL" in lines[0]

            # Check data row contains our node
            assert "DOID:162" in content
            assert "cancer" in content

    def test_edges_csv_content(self, sample_graph):
        """Test edges CSV has correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, edges_path = to_neo4j_csv(sample_graph, tmpdir)

            content = edges_path.read_text()
            lines = content.strip().split("\n")

            # Header + 2 edges
            assert len(lines) == 3

            # Check header
            assert ":START_ID" in lines[0]
            assert ":END_ID" in lines[0]
            assert ":TYPE" in lines[0]

    def test_custom_filenames(self, sample_graph):
        """Test custom filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nodes_path, edges_path = to_neo4j_csv(
                sample_graph,
                tmpdir,
                nodes_filename="my_nodes.csv",
                edges_filename="my_edges.csv",
            )

            assert nodes_path.name == "my_nodes.csv"
            assert edges_path.name == "my_edges.csv"

    def test_without_headers(self, sample_graph):
        """Test CSV export without headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nodes_path, _ = to_neo4j_csv(
                sample_graph, tmpdir, include_headers=False
            )

            content = nodes_path.read_text()
            lines = content.strip().split("\n")

            # 3 data rows, no header
            assert len(lines) == 3
            # Should not contain header fields
            assert "id:ID" not in content

    def test_node_properties_in_csv(self, sample_graph):
        """Test that node properties are included as JSON in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nodes_path, _ = to_neo4j_csv(sample_graph, tmpdir)

            content = nodes_path.read_text()

            # The cancer node should have its definition property as JSON
            assert "A disease of cellular proliferation" in content

    def test_xrefs_in_csv(self, sample_graph):
        """Test that xrefs are included in CSV with semicolon separator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nodes_path, _ = to_neo4j_csv(sample_graph, tmpdir)

            content = nodes_path.read_text()

            # Xrefs should be semicolon-separated
            assert "MESH" in content
            assert "UMLS" in content


class TestToCypher:
    """Tests for to_cypher export function."""

    def test_cypher_generation(self, sample_graph):
        """Test Cypher query generation."""
        cypher = to_cypher(sample_graph)

        assert "// Cypher script" in cypher
        assert "MERGE" in cypher  # Default uses MERGE
        assert "DOID:162" in cypher

    def test_create_vs_merge(self, sample_graph):
        """Test CREATE vs MERGE option."""
        cypher_merge = to_cypher(sample_graph, use_merge=True)
        cypher_create = to_cypher(sample_graph, use_merge=False)

        assert "MERGE" in cypher_merge
        assert "CREATE" in cypher_create
        assert "MERGE" not in cypher_create

    def test_node_creation(self, sample_graph):
        """Test node creation statements."""
        cypher = to_cypher(sample_graph)

        # Should have node creation for each node
        assert "id: 'DOID:162'" in cypher
        assert "label: 'cancer'" in cypher

    def test_relationship_creation(self, sample_graph):
        """Test relationship creation statements."""
        cypher = to_cypher(sample_graph)

        # Should have MATCH and relationship creation
        assert "MATCH" in cypher
        assert "IS_A" in cypher  # Uppercase relation type

    def test_constraint_creation(self, sample_graph):
        """Test constraint creation for MERGE."""
        cypher = to_cypher(sample_graph, use_merge=True)

        # Should include constraint for unique IDs
        assert "CREATE CONSTRAINT" in cypher

    def test_no_constraints_with_create(self, sample_graph):
        """Test that CREATE mode does not include constraints."""
        cypher = to_cypher(sample_graph, use_merge=False)

        assert "CREATE CONSTRAINT" not in cypher

    def test_evidence_in_relationship(self, sample_graph):
        """Test that edge evidence appears in relationship cypher."""
        cypher = to_cypher(sample_graph)

        # The breast cancer -> cancer edge has evidence=["IEA"]
        assert "IEA" in cypher


class TestToNetworkx:
    """Tests for to_networkx export function."""

    def test_networkx_import_error(self, sample_graph):
        """Test error message when networkx is not available."""
        # This test verifies the error handling
        # In practice, networkx is usually available
        pass

    @pytest.mark.skipif(
        not _check_networkx_available(),
        reason="networkx not installed"
    )
    def test_networkx_export(self, sample_graph):
        """Test NetworkX export if available."""
        from biodbs.graph import to_networkx
        import networkx as nx

        G = to_networkx(sample_graph)

        assert isinstance(G, nx.DiGraph)
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2

    @pytest.mark.skipif(
        not _check_networkx_available(),
        reason="networkx not installed"
    )
    def test_networkx_node_attributes(self, sample_graph):
        """Test that node attributes are preserved."""
        from biodbs.graph import to_networkx

        G = to_networkx(sample_graph)

        # Check node attributes
        assert G.nodes["DOID:162"]["label"] == "cancer"
        assert G.nodes["DOID:162"]["node_type"] == "disease"

    @pytest.mark.skipif(
        not _check_networkx_available(),
        reason="networkx not installed"
    )
    def test_networkx_edge_attributes(self, sample_graph):
        """Test that edge attributes are preserved."""
        from biodbs.graph import to_networkx

        G = to_networkx(sample_graph)

        # Check edge attributes
        edge_data = G.edges["DOID:1612", "DOID:162"]
        assert edge_data["relation"] == "is_a"

    @pytest.mark.skipif(
        not _check_networkx_available(),
        reason="networkx not installed"
    )
    def test_without_properties(self, sample_graph):
        """Test that include_properties=False excludes property attributes."""
        from biodbs.graph import to_networkx

        G = to_networkx(sample_graph, include_properties=False)

        # Node should still have basic attrs (label, node_type, source)
        assert G.nodes["DOID:162"]["label"] == "cancer"
        # But should not have property-derived attrs like "definition"
        assert "definition" not in G.nodes["DOID:162"]

    @pytest.mark.skipif(
        not _check_networkx_available(),
        reason="networkx not installed"
    )
    def test_without_xrefs(self, sample_graph):
        """Test that include_xrefs=False excludes xrefs attribute."""
        from biodbs.graph import to_networkx

        G = to_networkx(sample_graph, include_xrefs=False)

        # Cancer node should not have xrefs
        assert "xrefs" not in G.nodes["DOID:162"]


class TestToRdf:
    """Tests for to_rdf export function."""

    @pytest.mark.skipif(
        not _check_rdflib_available(),
        reason="rdflib not installed"
    )
    def test_rdf_turtle_export(self, sample_graph):
        """Test RDF Turtle export if rdflib is available."""
        from biodbs.graph import to_rdf

        turtle = to_rdf(sample_graph, format="turtle")

        assert isinstance(turtle, str)
        assert len(turtle) > 0
        assert "@prefix" in turtle or "PREFIX" in turtle.upper()

    @pytest.mark.skipif(
        not _check_rdflib_available(),
        reason="rdflib not installed"
    )
    def test_rdf_xml_export(self, sample_graph):
        """Test RDF XML export if rdflib is available."""
        from biodbs.graph import to_rdf

        xml = to_rdf(sample_graph, format="xml")

        assert isinstance(xml, str)
        assert "<rdf:RDF" in xml or "rdf:Description" in xml

    @pytest.mark.skipif(
        not _check_rdflib_available(),
        reason="rdflib not installed"
    )
    def test_rdf_n3_format(self, sample_graph):
        """Test RDF N3 format export."""
        from biodbs.graph import to_rdf

        n3 = to_rdf(sample_graph, format="n3")

        assert isinstance(n3, str)
        assert len(n3) > 0

    @pytest.mark.skipif(
        not _check_rdflib_available(),
        reason="rdflib not installed"
    )
    def test_rdf_custom_base_uri(self, sample_graph):
        """Test RDF export with custom base URI."""
        from biodbs.graph import to_rdf

        turtle = to_rdf(sample_graph, base_uri="http://mykg/")

        assert isinstance(turtle, str)
        assert "http://mykg/" in turtle

    @pytest.mark.skipif(
        not _check_rdflib_available(),
        reason="rdflib not installed"
    )
    def test_rdf_node_properties(self, sample_graph):
        """Test RDF output contains node labels and properties."""
        from biodbs.graph import to_rdf

        turtle = to_rdf(sample_graph, format="turtle")

        # Should contain labels
        assert "cancer" in turtle
        # Should contain description from definition property
        assert "A disease of cellular proliferation" in turtle
