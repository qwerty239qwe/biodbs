"""Regression tests for bugs fixed in v0.2.1."""

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from biodbs._funcs.graph.core import (
    DataSource,
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)
from biodbs._funcs.graph.builders import build_kegg_graph
from biodbs.data.Ensembl.data import EnsemblFetchedData, EnsemblDataManager


# =============================================================================
# Bug 1: build_kegg_graph crashes with TypeError on flat_file list values
#
# KEGG flat_file records have list-valued fields (PATHWAY, MODULE, etc.)
# that caused frozenset(properties.items()) to raise TypeError because
# lists are unhashable.
# =============================================================================


class TestKeggFlatFileListValues:
    """Regression: build_kegg_graph must handle list-valued flat_file fields."""

    def _make_kegg_data(self, records, fmt="flat_file", operation="get"):
        data = SimpleNamespace()
        data.records = records
        data.format = fmt
        data.operation = operation
        return data

    def test_flat_file_with_pathway_list(self):
        """PATHWAY field is a list — should not crash."""
        records = [{
            "entry_id": "hsa:7157",
            "NAME": "TP53",
            "DEFINITION": "tumor protein p53",
            "PATHWAY": ["hsa04110  Cell cycle", "hsa04115  p53 signaling pathway"],
        }]
        data = self._make_kegg_data(records)
        graph = build_kegg_graph(data)
        node = graph.get_node("hsa:7157")
        assert node is not None
        # List should be converted to tuple
        pathway_val = node.get_property("pathway")
        assert isinstance(pathway_val, tuple)
        assert len(pathway_val) == 2

    def test_flat_file_with_multiple_list_fields(self):
        """Multiple list fields (PATHWAY, MODULE, DISEASE, DBLINKS) all work."""
        records = [{
            "entry_id": "hsa:7157",
            "NAME": "TP53",
            "PATHWAY": ["hsa04110  Cell cycle"],
            "MODULE": ["M00693  Cell cycle"],
            "DISEASE": ["H00004  Chronic myeloid leukemia"],
            "DBLINKS": ["NCBI-GeneID: 7157", "UniProt: P04637"],
        }]
        data = self._make_kegg_data(records)
        graph = build_kegg_graph(data)
        node = graph.get_node("hsa:7157")
        assert node is not None
        # All list fields stored as tuples
        for field in ["pathway", "module", "disease", "dblinks"]:
            val = node.get_property(field)
            assert isinstance(val, tuple), f"{field} should be tuple, got {type(val)}"

    def test_flat_file_string_field_unchanged(self):
        """DEFINITION (a string field) should remain a string, not be wrapped."""
        records = [{
            "entry_id": "hsa:7157",
            "NAME": "TP53",
            "DEFINITION": "tumor protein p53",
        }]
        data = self._make_kegg_data(records)
        graph = build_kegg_graph(data)
        node = graph.get_node("hsa:7157")
        assert node.get_property("definition") == "tumor protein p53"

    def test_flat_file_mixed_fields(self):
        """Mix of string and list fields in same record."""
        records = [{
            "entry_id": "hsa:7157",
            "NAME": "TP53",
            "DEFINITION": "tumor protein p53",
            "PATHWAY": ["hsa04110  Cell cycle"],
        }]
        data = self._make_kegg_data(records)
        graph = build_kegg_graph(data)
        node = graph.get_node("hsa:7157")
        assert isinstance(node.get_property("definition"), str)
        assert isinstance(node.get_property("pathway"), tuple)


# =============================================================================
# Bug 2: get_degree("both") double-counts self-loops
#
# A self-loop edge (source == target) appeared in both _outgoing and
# _incoming sets, so get_degree("both") counted it twice.
# =============================================================================


class TestSelfLoopDegree:
    """Regression: get_degree('both') must not double-count self-loops."""

    def test_self_loop_degree_both(self):
        """A node with only a self-loop should have degree 1, not 2."""
        g = KnowledgeGraph(name="Test", source=DataSource.CUSTOM)
        g.add_node(Node(id="A", label="A"))
        g.add_edge(Edge(source="A", target="A", relation=EdgeType.RELATED_TO))
        assert g.get_degree("A", "both") == 1

    def test_self_loop_degree_outgoing(self):
        """Outgoing degree for self-loop should be 1."""
        g = KnowledgeGraph(name="Test", source=DataSource.CUSTOM)
        g.add_node(Node(id="A", label="A"))
        g.add_edge(Edge(source="A", target="A", relation=EdgeType.RELATED_TO))
        assert g.get_degree("A", "outgoing") == 1

    def test_self_loop_degree_incoming(self):
        """Incoming degree for self-loop should be 1."""
        g = KnowledgeGraph(name="Test", source=DataSource.CUSTOM)
        g.add_node(Node(id="A", label="A"))
        g.add_edge(Edge(source="A", target="A", relation=EdgeType.RELATED_TO))
        assert g.get_degree("A", "incoming") == 1

    def test_self_loop_plus_normal_edges(self):
        """Node with self-loop + normal edges: degree = unique edges count."""
        g = KnowledgeGraph(name="Test", source=DataSource.CUSTOM)
        g.add_node(Node(id="A", label="A"))
        g.add_node(Node(id="B", label="B"))
        # Self-loop on A
        g.add_edge(Edge(source="A", target="A", relation=EdgeType.RELATED_TO))
        # Normal edge A -> B
        g.add_edge(Edge(source="A", target="B", relation=EdgeType.IS_A))
        # A has 2 unique edges: self-loop + A->B
        assert g.get_degree("A", "both") == 2

    def test_node_both_directions_no_self_loop(self):
        """Node with both incoming and outgoing edges, no self-loop."""
        g = KnowledgeGraph(name="Test", source=DataSource.CUSTOM)
        g.add_node(Node(id="A", label="A"))
        g.add_node(Node(id="B", label="B"))
        g.add_node(Node(id="C", label="C"))
        g.add_edge(Edge(source="A", target="B", relation=EdgeType.IS_A))
        g.add_edge(Edge(source="C", target="A", relation=EdgeType.PART_OF))
        # A has 2 unique edges: A->B (outgoing) + C->A (incoming)
        assert g.get_degree("A", "both") == 2


# =============================================================================
# Bug 3: SQLiteDialect.get_connection leaked context manager
#
# get_connection() called __enter__() on a @contextmanager without
# ever calling __exit__(), leaking the generator and never closing
# the connection.
# =============================================================================


class TestSQLiteDialectGetConnection:
    """Regression: SQLiteDialect.get_connection must return a usable connection
    without leaking context manager resources."""

    def test_get_connection_returns_usable_connection(self, tmp_path):
        from biodbs.data._base import BaseDBManager
        from biodbs._funcs.analysis._cache import SQLiteDialect

        mgr = BaseDBManager(tmp_path)
        db_path = tmp_path / "test.db"
        dialect = SQLiteDialect(db_path, mgr._sqlite_connection)

        conn = dialect.get_connection()
        try:
            # Should be a real sqlite3 connection
            assert isinstance(conn, sqlite3.Connection)
            # Should be able to execute queries
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO test VALUES (1)")
            conn.commit()
            cursor = conn.execute("SELECT id FROM test")
            assert cursor.fetchone()[0] == 1
        finally:
            conn.close()

    def test_connection_context_manager_commits_and_closes(self, tmp_path):
        from biodbs.data._base import BaseDBManager
        from biodbs._funcs.analysis._cache import SQLiteDialect

        mgr = BaseDBManager(tmp_path)
        db_path = tmp_path / "test.db"
        dialect = SQLiteDialect(db_path, mgr._sqlite_connection)

        # Use the connection() context manager
        with dialect.connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO test VALUES (42)")

        # Data should be committed — verify by opening a new connection
        verify_conn = sqlite3.connect(db_path)
        try:
            cursor = verify_conn.execute("SELECT id FROM test")
            assert cursor.fetchone()[0] == 42
        finally:
            verify_conn.close()


# =============================================================================
# Bug 4: EnsemblDataManager.save_ensembl_data calls non-existent method
#
# save_ensembl_data() called self.update_metadata(key, str(filepath))
# but the parent class BaseDBManager only has _update_metadata (with
# underscore prefix). This raised AttributeError when saving FASTA data
# with a cache key.
# =============================================================================


class TestEnsemblSaveFastaMetadata:
    """Regression: save_ensembl_data must call _update_metadata, not update_metadata."""

    def test_save_fasta_with_key_does_not_raise(self, tmp_path):
        """Saving FASTA with a key should update metadata without AttributeError."""
        mgr = EnsemblDataManager(storage_path=tmp_path)
        data = EnsemblFetchedData(
            ">ENSP00000269305\nMEEPQSDPSVEPP\n",
            content_type="fasta",
        )
        filepath = mgr.save_ensembl_data(data, "test_seq", fmt="fasta", key="my_key")
        assert filepath is not None
        assert filepath.exists()
        # Metadata should have been updated
        assert "my_key" in mgr._metadata
        assert mgr._metadata["my_key"]["filepath"] == str(filepath)
