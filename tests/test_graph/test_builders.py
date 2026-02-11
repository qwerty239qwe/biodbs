"""Tests for biodbs.graph.builders module."""

from types import SimpleNamespace
from unittest.mock import MagicMock

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
from biodbs._funcs.graph.builders import (
    build_disease_graph,
    build_disease_graph_with_hierarchy,
    build_go_graph,
    build_reactome_graph,
    build_kegg_graph,
    build_kegg_link_graph,
    _infer_kegg_node_type,
)


class TestBuildGraph:
    """Tests for the build_graph function."""

    def test_build_empty_graph(self):
        graph = build_graph([], name="Empty")
        assert graph.name == "Empty"
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_build_graph_with_nodes(self):
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
        graph = KnowledgeGraph(name="Graph1")
        graph.add_node(Node(id="A", label="A", node_type=NodeType.DISEASE))
        graph.add_node(Node(id="B", label="B", node_type=NodeType.DISEASE))
        graph.add_edge(Edge(source="A", target="B", relation=EdgeType.IS_A))
        return graph

    @pytest.fixture
    def graph2(self):
        graph = KnowledgeGraph(name="Graph2")
        graph.add_node(Node(id="C", label="C", node_type=NodeType.GENE))
        graph.add_node(Node(id="D", label="D", node_type=NodeType.GENE))
        graph.add_edge(Edge(source="C", target="D", relation=EdgeType.INTERACTS_WITH))
        return graph

    def test_merge_empty_graphs(self):
        merged = merge_graphs()
        assert merged.node_count == 0
        assert merged.edge_count == 0

    def test_merge_single_graph(self, graph1):
        merged = merge_graphs(graph1, name="Merged")
        assert merged.name == "Merged"
        assert merged.node_count == 2
        assert merged.edge_count == 1

    def test_merge_two_graphs(self, graph1, graph2):
        merged = merge_graphs(graph1, graph2, name="Merged")
        assert merged.node_count == 4
        assert merged.edge_count == 2
        assert "A" in merged
        assert "C" in merged
        assert merged.has_edge("A", "B")
        assert merged.has_edge("C", "D")

    def test_merge_with_overlapping_nodes(self, graph1):
        graph3 = KnowledgeGraph(name="Graph3")
        graph3.add_node(Node(id="A", label="Different A"))
        graph3.add_node(Node(id="E", label="E"))
        merged = merge_graphs(graph1, graph3)
        assert merged.node_count == 3
        assert merged.get_node("A").label == "A"

    def test_merge_with_connecting_edge(self, graph1, graph2):
        merged = merge_graphs(graph1, graph2, name="Connected")
        merged.add_edge(Edge(source="B", target="C", relation=EdgeType.ASSOCIATED_WITH))
        assert merged.edge_count == 3
        assert merged.has_edge("B", "C")


# =============================================================================
# Helpers for mocking fetched data objects
# =============================================================================


def _make_do_term(doid, name, definition=None, synonyms=None, xrefs=None,
                  is_obsolete=False, has_children=False, is_root=False):
    return SimpleNamespace(
        doid=doid, name=name, definition=definition,
        synonyms=synonyms or [], xrefs=xrefs or [],
        is_obsolete=is_obsolete, has_children=has_children, is_root=is_root,
    )


def _make_do_data(terms):
    data = MagicMock()
    data.terms = terms
    return data


def _make_quickgo_data(results):
    data = MagicMock()
    data.results = results
    return data


def _make_reactome_pathway(stId, name, dbId=1, p_value=None, fdr=None,
                           found_entities=None, total_entities=None,
                           species=None, inDisease=False, llp=False):
    pw = SimpleNamespace(
        stId=stId, name=name, dbId=dbId,
        p_value=p_value, fdr=fdr,
        found_entities=found_entities, total_entities=total_entities,
        species=species, inDisease=inDisease, llp=llp,
    )
    return pw


def _make_reactome_data(pathways):
    data = MagicMock()
    data.pathways = pathways
    return data


def _make_kegg_data(records, operation="list", fmt="tabular"):
    data = MagicMock()
    data.records = records
    data.operation = operation
    data.format = fmt
    return data


# =============================================================================
# TestBuildDiseaseGraph
# =============================================================================


class TestBuildDiseaseGraph:
    """Tests for build_disease_graph with mocked DOFetchedData."""

    def test_basic_node_creation(self):
        data = _make_do_data([_make_do_term("DOID:162", "cancer")])
        graph = build_disease_graph(data)
        assert graph.node_count == 1
        node = graph.get_node("DOID:162")
        assert node.label == "cancer"
        assert node.node_type == NodeType.DISEASE

    def test_multiple_terms(self):
        terms = [
            _make_do_term("DOID:162", "cancer"),
            _make_do_term("DOID:1612", "breast cancer"),
            _make_do_term("DOID:1324", "lung cancer"),
        ]
        graph = build_disease_graph(_make_do_data(terms))
        assert graph.node_count == 3

    def test_xrefs_included(self):
        term = _make_do_term("DOID:162", "cancer", xrefs=["MESH:D009369", "NCI:C9305"])
        graph = build_disease_graph(_make_do_data([term]), include_xrefs=True)
        node = graph.get_node("DOID:162")
        assert "MESH:D009369" in node.xrefs

    def test_xrefs_excluded(self):
        term = _make_do_term("DOID:162", "cancer", xrefs=["MESH:D009369"])
        graph = build_disease_graph(_make_do_data([term]), include_xrefs=False)
        node = graph.get_node("DOID:162")
        assert len(node.xrefs) == 0

    def test_synonyms_included(self):
        term = _make_do_term("DOID:162", "cancer", synonyms=["malignant neoplasm"])
        graph = build_disease_graph(_make_do_data([term]), include_synonyms=True)
        node = graph.get_node("DOID:162")
        props = node.get_properties_dict()
        assert "synonyms" in props

    def test_synonyms_excluded_by_default(self):
        term = _make_do_term("DOID:162", "cancer", synonyms=["malignant neoplasm"])
        graph = build_disease_graph(_make_do_data([term]))
        node = graph.get_node("DOID:162")
        props = node.get_properties_dict()
        assert "synonyms" not in props

    def test_definition_stored(self):
        term = _make_do_term("DOID:162", "cancer", definition="A disease...")
        graph = build_disease_graph(_make_do_data([term]))
        node = graph.get_node("DOID:162")
        assert node.get_property("definition") == "A disease..."

    def test_obsolete_flag(self):
        term = _make_do_term("DOID:999", "old disease", is_obsolete=True)
        graph = build_disease_graph(_make_do_data([term]))
        node = graph.get_node("DOID:999")
        assert node.get_property("is_obsolete") is True

    def test_empty_data(self):
        graph = build_disease_graph(_make_do_data([]))
        assert graph.node_count == 0

    def test_graph_source(self):
        graph = build_disease_graph(_make_do_data([]))
        assert graph.source == DataSource.DISEASE_ONTOLOGY


class TestBuildDiseaseGraphWithHierarchy:
    def test_creates_is_a_edges(self):
        parent = _make_do_data([_make_do_term("DOID:4", "disease")])
        children = _make_do_data([
            _make_do_term("DOID:162", "cancer"),
            _make_do_term("DOID:1579", "autoimmune disease"),
        ])
        graph = build_disease_graph_with_hierarchy(parent, children)
        assert graph.node_count == 3
        assert graph.edge_count == 2
        assert graph.has_edge("DOID:162", "DOID:4")
        assert graph.has_edge("DOID:1579", "DOID:4")


# =============================================================================
# TestBuildGOGraph
# =============================================================================


class TestBuildGOGraph:
    """Tests for build_go_graph with mocked QuickGOFetchedData."""

    def test_go_term_nodes(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "biological_process", "goAspect": "bp"},
        ])
        graph = build_go_graph(data, create_annotation_edges=False)
        assert graph.node_count == 1
        node = graph.get_node("GO:0008150")
        assert node.node_type == NodeType.GO_TERM
        assert node.label == "biological_process"

    def test_gene_product_nodes(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:P04637"},
        ])
        graph = build_go_graph(data)
        assert graph.has_node("UniProtKB:P04637")
        node = graph.get_node("UniProtKB:P04637")
        assert node.node_type == NodeType.PROTEIN

    def test_non_uniprot_gene_type(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "HGNC:TP53"},
        ])
        graph = build_go_graph(data)
        node = graph.get_node("HGNC:TP53")
        assert node.node_type == NodeType.GENE

    def test_annotation_edge_created(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:P04637",
             "qualifier": "enables", "evidenceCode": "IDA"},
        ])
        graph = build_go_graph(data)
        assert graph.has_edge("UniProtKB:P04637", "GO:0008150")

    def test_qualifier_not(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:P04637",
             "qualifier": "NOT|enables"},
        ])
        graph = build_go_graph(data)
        edge = graph.get_edge("UniProtKB:P04637", "GO:0008150")
        assert edge.relation == EdgeType.NEGATIVELY_REGULATES

    def test_qualifier_part_of(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:P04637",
             "qualifier": "part_of"},
        ])
        graph = build_go_graph(data)
        edge = graph.get_edge("UniProtKB:P04637", "GO:0008150")
        assert edge.relation == EdgeType.PART_OF

    def test_evidence_included(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:P04637",
             "qualifier": "enables", "evidenceCode": "IDA"},
        ])
        graph = build_go_graph(data, include_evidence=True)
        edge = graph.get_edge("UniProtKB:P04637", "GO:0008150")
        assert "IDA" in edge.evidence

    def test_no_annotation_edges(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:P04637"},
        ])
        graph = build_go_graph(data, create_annotation_edges=False)
        assert graph.edge_count == 0

    def test_empty_results(self):
        graph = build_go_graph(_make_quickgo_data([]))
        assert graph.node_count == 0

    def test_duplicate_go_terms_merged(self):
        data = _make_quickgo_data([
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:P04637"},
            {"goId": "GO:0008150", "goName": "bp", "geneProductId": "UniProtKB:Q12345"},
        ])
        graph = build_go_graph(data)
        go_nodes = graph.filter_nodes(node_type=NodeType.GO_TERM)
        assert len(go_nodes) == 1


# =============================================================================
# TestBuildReactomeGraph
# =============================================================================


class TestBuildReactomeGraph:
    """Tests for build_reactome_graph with mocked ReactomeFetchedData."""

    def test_basic_pathway_node(self):
        pw = _make_reactome_pathway("R-HSA-123", "Cell Cycle")
        graph = build_reactome_graph(_make_reactome_data([pw]))
        assert graph.node_count == 1
        node = graph.get_node("R-HSA-123")
        assert node.label == "Cell Cycle"
        assert node.node_type == NodeType.PATHWAY

    def test_species_info(self):
        species = SimpleNamespace(name="Homo sapiens", taxId=9606)
        pw = _make_reactome_pathway("R-HSA-123", "Cell Cycle", species=species)
        graph = build_reactome_graph(_make_reactome_data([pw]), include_species=True)
        node = graph.get_node("R-HSA-123")
        assert node.get_property("species") == "Homo sapiens"
        assert node.get_property("taxon_id") == 9606

    def test_species_excluded(self):
        species = SimpleNamespace(name="Homo sapiens", taxId=9606)
        pw = _make_reactome_pathway("R-HSA-123", "Cell Cycle", species=species)
        graph = build_reactome_graph(_make_reactome_data([pw]), include_species=False)
        node = graph.get_node("R-HSA-123")
        assert node.get_property("species") is None

    def test_disease_info(self):
        pw = _make_reactome_pathway("R-HSA-123", "CC", inDisease=True, llp=True)
        graph = build_reactome_graph(_make_reactome_data([pw]))
        node = graph.get_node("R-HSA-123")
        assert node.get_property("is_disease_pathway") is True
        assert node.get_property("is_lowest_level") is True

    def test_p_value_and_fdr(self):
        pw = _make_reactome_pathway("R-HSA-123", "CC", p_value=0.001, fdr=0.01)
        graph = build_reactome_graph(_make_reactome_data([pw]))
        node = graph.get_node("R-HSA-123")
        assert node.get_property("p_value") == 0.001
        assert node.get_property("fdr") == 0.01

    def test_entity_counts(self):
        pw = _make_reactome_pathway("R-HSA-123", "CC", found_entities=5, total_entities=100)
        graph = build_reactome_graph(_make_reactome_data([pw]))
        node = graph.get_node("R-HSA-123")
        assert node.get_property("found_entities") == 5

    def test_empty_data(self):
        graph = build_reactome_graph(_make_reactome_data([]))
        assert graph.node_count == 0

    def test_graph_source(self):
        graph = build_reactome_graph(_make_reactome_data([]))
        assert graph.source == DataSource.REACTOME


# =============================================================================
# TestBuildKEGGGraph
# =============================================================================


class TestBuildKEGGGraph:
    """Tests for build_kegg_graph with mocked KEGGFetchedData."""

    def test_basic_node_creation(self):
        records = [{"entry_id": "hsa:1234", "description": "TP53"}]
        data = _make_kegg_data(records)
        graph = build_kegg_graph(data)
        assert graph.node_count == 1
        node = graph.get_node("hsa:1234")
        assert node.label == "TP53"

    def test_inferred_gene_type(self):
        records = [{"entry_id": "hsa:1234", "description": "TP53"}]
        data = _make_kegg_data(records)
        graph = build_kegg_graph(data)
        node = graph.get_node("hsa:1234")
        assert node.node_type == NodeType.GENE

    def test_inferred_pathway_type(self):
        records = [{"entry_id": "path:hsa04110", "description": "Cell cycle"}]
        data = _make_kegg_data(records)
        graph = build_kegg_graph(data)
        node = graph.get_node("path:hsa04110")
        assert node.node_type == NodeType.PATHWAY

    def test_explicit_node_type_override(self):
        records = [{"entry_id": "C00001", "description": "water"}]
        data = _make_kegg_data(records)
        graph = build_kegg_graph(data, node_type=NodeType.DRUG)
        node = graph.get_node("C00001")
        assert node.node_type == NodeType.DRUG

    def test_flat_file_properties(self):
        records = [{"entry_id": "hsa:1234", "description": "TP53",
                     "DEFINITION": "tumor protein p53"}]
        data = _make_kegg_data(records, fmt="flat_file")
        graph = build_kegg_graph(data)
        node = graph.get_node("hsa:1234")
        assert node.get_property("definition") == "tumor protein p53"

    def test_empty_records(self):
        graph = build_kegg_graph(_make_kegg_data([]))
        assert graph.node_count == 0

    def test_skip_empty_entry_id(self):
        records = [{"entry_id": "", "description": "nothing"}]
        data = _make_kegg_data(records)
        graph = build_kegg_graph(data)
        assert graph.node_count == 0

    def test_non_list_operation_default_type(self):
        records = [{"entry_id": "K00001", "description": "some ortholog"}]
        data = _make_kegg_data(records, operation="get")
        graph = build_kegg_graph(data)
        node = graph.get_node("K00001")
        assert node.node_type == NodeType.OTHER


class TestBuildKEGGLinkGraph:
    def test_creates_nodes_and_edges(self):
        records = [
            {"source_id": "hsa:1234", "target_id": "path:hsa04110"},
            {"source_id": "hsa:5678", "target_id": "path:hsa04110"},
        ]
        data = _make_kegg_data(records, operation="link")
        graph = build_kegg_link_graph(data)
        assert graph.node_count == 3
        assert graph.edge_count == 2

    def test_skip_empty_ids(self):
        records = [{"source_id": "", "target_id": ""}]
        data = _make_kegg_data(records, operation="link")
        graph = build_kegg_link_graph(data)
        assert graph.node_count == 0
        assert graph.edge_count == 0


class TestInferKeggNodeType:
    def test_pathway(self):
        assert _infer_kegg_node_type("path:hsa04110") == NodeType.PATHWAY

    def test_map_pathway(self):
        assert _infer_kegg_node_type("map00010") == NodeType.PATHWAY

    def test_compound(self):
        assert _infer_kegg_node_type("C00001") == NodeType.COMPOUND

    def test_drug(self):
        assert _infer_kegg_node_type("D00001") == NodeType.DRUG

    def test_reaction(self):
        assert _infer_kegg_node_type("R00001") == NodeType.REACTION

    def test_orthology(self):
        assert _infer_kegg_node_type("K00001") == NodeType.GENE

    def test_module(self):
        assert _infer_kegg_node_type("M00001") == NodeType.PATHWAY

    def test_organism_gene(self):
        assert _infer_kegg_node_type("hsa:1234") == NodeType.GENE

    def test_unknown(self):
        assert _infer_kegg_node_type("xyz") == NodeType.OTHER
