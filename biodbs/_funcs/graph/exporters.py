"""Export functions for knowledge graphs.

This module provides functions to export KnowledgeGraph instances to
various formats for use with different tools and applications.

Functions:
    to_networkx: Export to NetworkX DiGraph.
    to_json_ld: Export to JSON-LD format (for KG-RAG).
    to_rdf: Export to RDF format (Turtle or XML).
    to_neo4j_csv: Export CSV files for Neo4j import.
    to_cypher: Generate Cypher queries for Neo4j.

Dependencies:
    - networkx: Required for to_networkx()
    - rdflib: Required for to_rdf()
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

from biodbs._funcs.graph.core import (
    DataSource,
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)

if TYPE_CHECKING:
    import networkx as nx
    from rdflib import Graph as RDFGraph


# =============================================================================
# NetworkX Export
# =============================================================================


def to_networkx(
    graph: KnowledgeGraph,
    include_properties: bool = True,
    include_xrefs: bool = True,
) -> "nx.DiGraph":
    """Export a KnowledgeGraph to a NetworkX directed graph.

    Requires the networkx package to be installed.

    Args:
        graph: The KnowledgeGraph to export.
        include_properties: Include node/edge properties as attributes.
        include_xrefs: Include cross-references as node attributes.

    Returns:
        A NetworkX DiGraph with the same nodes and edges.

    Raises:
        ImportError: If networkx is not installed.

    Example:
        ```python
        from biodbs.graph import to_networkx, build_disease_graph
        import networkx as nx

        graph = build_disease_graph(disease_data)
        nx_graph = to_networkx(graph)
        centrality = nx.degree_centrality(nx_graph)
        print(f"Nodes: {nx_graph.number_of_nodes()}")
        # Nodes: 47
        ```
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError(
            "networkx is required for to_networkx(). "
            "Install it with: pip install networkx"
        )

    G = nx.DiGraph()
    G.graph["name"] = graph.name
    G.graph["source"] = graph.source.value
    if graph.description:
        G.graph["description"] = graph.description

    # Add nodes
    for node in graph.nodes:
        attrs: Dict[str, Any] = {
            "label": node.label,
            "node_type": node.node_type.value,
            "source": node.source.value,
        }

        if include_properties:
            attrs.update(node.get_properties_dict())

        if include_xrefs and node.xrefs:
            attrs["xrefs"] = list(node.xrefs)

        G.add_node(node.id, **attrs)

    # Add edges
    for edge in graph.edges:
        attrs: Dict[str, Any] = {
            "relation": edge.relation.value,
            "weight": edge.weight,
        }

        if include_properties:
            attrs.update(edge.get_properties_dict())

        if edge.evidence:
            attrs["evidence"] = list(edge.evidence)

        G.add_edge(edge.source, edge.target, **attrs)

    return G


# =============================================================================
# JSON-LD Export
# =============================================================================

# Standard JSON-LD context for biological knowledge graphs
BIOKG_CONTEXT = {
    "@context": {
        "@vocab": "http://www.w3.org/2002/07/owl#",
        "schema": "http://schema.org/",
        "bioschemas": "https://bioschemas.org/",
        "obo": "http://purl.obolibrary.org/obo/",
        "doid": "http://purl.obolibrary.org/obo/DOID_",
        "go": "http://purl.obolibrary.org/obo/GO_",
        "kegg": "https://www.kegg.jp/entry/",
        "reactome": "https://reactome.org/content/detail/",
        "uniprot": "https://www.uniprot.org/uniprot/",
        "id": "@id",
        "type": "@type",
        "label": "rdfs:label",
        "description": "schema:description",
        "xref": {
            "@id": "obo:hasDbXref",
            "@type": "@id",
        },
        "is_a": {
            "@id": "rdfs:subClassOf",
            "@type": "@id",
        },
        "part_of": {
            "@id": "obo:BFO_0000050",
            "@type": "@id",
        },
        "participates_in": {
            "@id": "obo:RO_0000056",
            "@type": "@id",
        },
        "regulates": {
            "@id": "obo:RO_0002211",
            "@type": "@id",
        },
    }
}


def to_json_ld(
    graph: KnowledgeGraph,
    include_context: bool = True,
    compact: bool = False,
    base_uri: Optional[str] = None,
) -> Dict[str, Any]:
    """Export a KnowledgeGraph to JSON-LD format.

    JSON-LD is ideal for KG-RAG (Knowledge Graph Retrieval Augmented
    Generation) applications as it provides structured, semantically
    rich data that can be easily processed by LLMs.

    Args:
        graph: The KnowledgeGraph to export.
        include_context: Include JSON-LD @context.
        compact: Use compact representation (less verbose).
        base_uri: Base URI for node IDs.

    Returns:
        A dictionary in JSON-LD format.

    Example:
        ```python
        from biodbs.graph import to_json_ld, build_disease_graph
        import json

        graph = build_disease_graph(disease_data)
        json_ld = to_json_ld(graph)
        # Use in RAG pipeline
        context = json.dumps(json_ld, indent=2)
        print(json_ld["@type"])
        # schema:Dataset
        ```
    """
    result: Dict[str, Any] = {}

    # Add context
    if include_context:
        result.update(BIOKG_CONTEXT)

    # Graph metadata
    result["@type"] = "schema:Dataset"
    result["schema:name"] = graph.name
    if graph.description:
        result["schema:description"] = graph.description
    result["schema:creator"] = "biodbs"
    result["schema:source"] = graph.source.value

    # Build nodes as @graph
    nodes_list: List[Dict[str, Any]] = []

    for node in graph.nodes:
        node_obj = _node_to_json_ld(node, base_uri, compact)

        # Add outgoing edges as properties
        outgoing = graph.get_outgoing_edges(node.id)
        for edge in outgoing:
            relation_key = _edge_type_to_json_ld_key(edge.relation)
            target_id = _make_uri(edge.target, base_uri)

            if relation_key in node_obj:
                # Multiple edges of same type
                if isinstance(node_obj[relation_key], list):
                    node_obj[relation_key].append(target_id)
                else:
                    node_obj[relation_key] = [node_obj[relation_key], target_id]
            else:
                node_obj[relation_key] = target_id

        nodes_list.append(node_obj)

    result["@graph"] = nodes_list

    return result


def _node_to_json_ld(
    node: Node,
    base_uri: Optional[str] = None,
    compact: bool = False,
) -> Dict[str, Any]:
    """Convert a Node to JSON-LD object."""
    obj: Dict[str, Any] = {
        "@id": _make_uri(node.id, base_uri),
        "@type": _node_type_to_json_ld_type(node.node_type),
        "label": node.label,
    }

    if not compact:
        obj["source"] = node.source.value

    # Add properties
    props = node.get_properties_dict()
    if props:
        if "definition" in props:
            obj["description"] = props.pop("definition")
        for key, value in props.items():
            obj[key] = value

    # Add xrefs
    if node.xrefs:
        obj["xref"] = list(node.xrefs)

    return obj


def _make_uri(node_id: str, base_uri: Optional[str] = None) -> str:
    """Create a URI for a node ID."""
    if base_uri:
        return f"{base_uri}{node_id}"

    # Use standard prefixes for known ID patterns
    if node_id.startswith("DOID:"):
        return f"obo:DOID_{node_id.split(':')[1]}"
    elif node_id.startswith("GO:"):
        return f"obo:GO_{node_id.split(':')[1]}"
    elif node_id.startswith("R-"):
        return f"reactome:{node_id}"
    elif node_id.startswith("UniProtKB:"):
        return f"uniprot:{node_id.split(':')[1]}"

    return node_id


def _node_type_to_json_ld_type(node_type: NodeType) -> str:
    """Map NodeType to JSON-LD type."""
    type_map = {
        NodeType.DISEASE: "obo:DOID_4",  # disease
        NodeType.GENE: "bioschemas:Gene",
        NodeType.PROTEIN: "bioschemas:Protein",
        NodeType.PATHWAY: "bioschemas:BioChemEntity",
        NodeType.GO_TERM: "obo:GO_0008150",  # biological process (generic)
        NodeType.COMPOUND: "bioschemas:ChemicalSubstance",
        NodeType.DRUG: "schema:Drug",
        NodeType.REACTION: "obo:GO_0003824",  # catalytic activity
        NodeType.PHENOTYPE: "obo:PATO_0000001",  # quality
        NodeType.ORGANISM: "schema:Taxon",
        NodeType.PUBLICATION: "schema:ScholarlyArticle",
        NodeType.OTHER: "schema:Thing",
    }
    return type_map.get(node_type, "schema:Thing")


def _edge_type_to_json_ld_key(edge_type: EdgeType) -> str:
    """Map EdgeType to JSON-LD property key."""
    key_map = {
        EdgeType.IS_A: "is_a",
        EdgeType.PART_OF: "part_of",
        EdgeType.HAS_PART: "has_part",
        EdgeType.REGULATES: "regulates",
        EdgeType.POSITIVELY_REGULATES: "positively_regulates",
        EdgeType.NEGATIVELY_REGULATES: "negatively_regulates",
        EdgeType.PARTICIPATES_IN: "participates_in",
        EdgeType.HAS_PARTICIPANT: "has_participant",
        EdgeType.ASSOCIATED_WITH: "associated_with",
        EdgeType.INTERACTS_WITH: "interacts_with",
        EdgeType.XREF: "xref",
        EdgeType.SAME_AS: "same_as",
    }
    return key_map.get(edge_type, "related_to")


# =============================================================================
# RDF Export
# =============================================================================


def to_rdf(
    graph: KnowledgeGraph,
    format: Literal["turtle", "xml", "n3", "nt"] = "turtle",
    base_uri: str = "http://example.org/biokg/",
) -> str:
    """Export a KnowledgeGraph to RDF format.

    Requires the rdflib package to be installed.

    Args:
        graph: The KnowledgeGraph to export.
        format: RDF serialization format ("turtle", "xml", "n3", "nt").
        base_uri: Base URI for the graph.

    Returns:
        RDF data as a string in the specified format.

    Raises:
        ImportError: If rdflib is not installed.

    Example:
        ```python
        from biodbs.graph import to_rdf, build_disease_graph

        graph = build_disease_graph(disease_data)
        turtle = to_rdf(graph, format="turtle")
        print(turtle[:200])
        # @prefix base: <http://example.org/biokg/> .
        # @prefix biokg: <http://example.org/biokg/vocab/> .
        # ...
        ```
    """
    try:
        from rdflib import Graph as RDFGraph
        from rdflib import Literal, Namespace, URIRef
        from rdflib.namespace import OWL, RDF, RDFS, XSD
    except ImportError:
        raise ImportError(
            "rdflib is required for to_rdf(). "
            "Install it with: pip install rdflib"
        )

    g = RDFGraph()

    # Define namespaces
    BASE = Namespace(base_uri)
    OBO = Namespace("http://purl.obolibrary.org/obo/")
    SCHEMA = Namespace("http://schema.org/")
    BIOKG = Namespace(base_uri + "vocab/")

    g.bind("base", BASE)
    g.bind("obo", OBO)
    g.bind("schema", SCHEMA)
    g.bind("biokg", BIOKG)

    # Add nodes
    for node in graph.nodes:
        node_uri = URIRef(base_uri + node.id.replace(":", "_"))

        # Type
        type_uri = _node_type_to_rdf_type(node.node_type, OBO, SCHEMA)
        g.add((node_uri, RDF.type, type_uri))

        # Label
        g.add((node_uri, RDFS.label, Literal(node.label)))

        # Source
        g.add((node_uri, BIOKG.source, Literal(node.source.value)))

        # Properties
        props = node.get_properties_dict()
        if "definition" in props:
            g.add((node_uri, SCHEMA.description, Literal(props["definition"])))
        for key, value in props.items():
            if key != "definition" and isinstance(value, (str, int, float, bool)):
                g.add((node_uri, BIOKG[key], Literal(value)))

        # Xrefs
        for xref in node.xrefs:
            g.add((node_uri, OBO.hasDbXref, Literal(xref)))

    # Add edges
    for edge in graph.edges:
        source_uri = URIRef(base_uri + edge.source.replace(":", "_"))
        target_uri = URIRef(base_uri + edge.target.replace(":", "_"))
        predicate = _edge_type_to_rdf_predicate(edge.relation, OBO, RDFS, BIOKG)

        g.add((source_uri, predicate, target_uri))

        # Add edge weight if not 1.0
        if edge.weight != 1.0:
            # Create a reified statement for the weight
            pass  # Simplified for now

    return g.serialize(format=format)


def _node_type_to_rdf_type(
    node_type: NodeType,
    OBO: Any,
    SCHEMA: Any,
) -> Any:
    """Map NodeType to RDF type URI."""
    type_map = {
        NodeType.DISEASE: OBO.DOID_4,
        NodeType.GENE: SCHEMA.Gene,
        NodeType.PROTEIN: SCHEMA.Protein,
        NodeType.PATHWAY: OBO.PW_0000001,
        NodeType.GO_TERM: OBO.GO_0008150,
        NodeType.COMPOUND: SCHEMA.ChemicalSubstance,
        NodeType.DRUG: SCHEMA.Drug,
        NodeType.REACTION: OBO.GO_0003824,
        NodeType.PHENOTYPE: OBO.PATO_0000001,
        NodeType.ORGANISM: SCHEMA.Taxon,
        NodeType.PUBLICATION: SCHEMA.ScholarlyArticle,
        NodeType.OTHER: SCHEMA.Thing,
    }
    return type_map.get(node_type, SCHEMA.Thing)


def _edge_type_to_rdf_predicate(
    edge_type: EdgeType,
    OBO: Any,
    RDFS: Any,
    BIOKG: Any,
) -> Any:
    """Map EdgeType to RDF predicate URI."""
    predicate_map = {
        EdgeType.IS_A: RDFS.subClassOf,
        EdgeType.PART_OF: OBO.BFO_0000050,
        EdgeType.HAS_PART: OBO.BFO_0000051,
        EdgeType.REGULATES: OBO.RO_0002211,
        EdgeType.POSITIVELY_REGULATES: OBO.RO_0002213,
        EdgeType.NEGATIVELY_REGULATES: OBO.RO_0002212,
        EdgeType.PARTICIPATES_IN: OBO.RO_0000056,
        EdgeType.HAS_PARTICIPANT: OBO.RO_0000057,
        EdgeType.ASSOCIATED_WITH: BIOKG.associatedWith,
        EdgeType.INTERACTS_WITH: OBO.RO_0002434,
        EdgeType.XREF: OBO.hasDbXref,
        EdgeType.SAME_AS: OBO.IAO_0000039,
    }
    return predicate_map.get(edge_type, BIOKG.relatedTo)


# =============================================================================
# Neo4j Export
# =============================================================================


def to_neo4j_csv(
    graph: KnowledgeGraph,
    output_dir: Union[str, Path],
    nodes_filename: str = "nodes.csv",
    edges_filename: str = "relationships.csv",
    include_headers: bool = True,
) -> Tuple[Path, Path]:
    """Export a KnowledgeGraph to CSV files for Neo4j import.

    Creates two CSV files: one for nodes and one for relationships,
    formatted for Neo4j's LOAD CSV or neo4j-admin import.

    Args:
        graph: The KnowledgeGraph to export.
        output_dir: Directory to write CSV files.
        nodes_filename: Filename for nodes CSV.
        edges_filename: Filename for relationships CSV.
        include_headers: Include Neo4j import headers.

    Returns:
        Tuple of (nodes_path, edges_path).

    Example:
        ```python
        from biodbs.graph import to_neo4j_csv, build_disease_graph

        graph = build_disease_graph(disease_data)
        nodes_path, edges_path = to_neo4j_csv(graph, "./neo4j_import/")
        print(f"Nodes: {nodes_path}")
        # Nodes: neo4j_import/nodes.csv
        print(f"Edges: {edges_path}")
        # Edges: neo4j_import/relationships.csv
        ```
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    nodes_path = output_dir / nodes_filename
    edges_path = output_dir / edges_filename

    # Write nodes CSV
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if include_headers:
            # Neo4j import headers
            writer.writerow([
                "id:ID",
                "label",
                "node_type",
                "source",
                "properties:string",
                "xrefs:string[]",
                ":LABEL",
            ])

        for node in graph.nodes:
            # Convert properties to JSON string
            props_json = json.dumps(node.get_properties_dict()) if node.properties else ""

            # Convert xrefs to Neo4j array format
            xrefs_str = ";".join(node.xrefs) if node.xrefs else ""

            # Label for Neo4j (node type as label)
            neo4j_label = node.node_type.value.title().replace("_", "")

            writer.writerow([
                node.id,
                node.label,
                node.node_type.value,
                node.source.value,
                props_json,
                xrefs_str,
                neo4j_label,
            ])

    # Write relationships CSV
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if include_headers:
            # Neo4j import headers
            writer.writerow([
                ":START_ID",
                ":END_ID",
                "weight:float",
                "evidence:string[]",
                "properties:string",
                ":TYPE",
            ])

        for edge in graph.edges:
            # Convert evidence to Neo4j array format
            evidence_str = ";".join(edge.evidence) if edge.evidence else ""

            # Convert properties to JSON string
            props_json = json.dumps(edge.get_properties_dict()) if edge.properties else ""

            # Relationship type (uppercase with underscores)
            rel_type = edge.relation.value.upper()

            writer.writerow([
                edge.source,
                edge.target,
                edge.weight,
                evidence_str,
                props_json,
                rel_type,
            ])

    return nodes_path, edges_path


def to_cypher(
    graph: KnowledgeGraph,
    batch_size: int = 100,
    use_merge: bool = True,
) -> str:
    """Generate Cypher queries to create the graph in Neo4j.

    Creates CREATE or MERGE statements for nodes and relationships.

    Args:
        graph: The KnowledgeGraph to export.
        batch_size: Number of statements per transaction.
        use_merge: Use MERGE instead of CREATE (prevents duplicates).

    Returns:
        Cypher script as a string.

    Example:
        ```python
        from biodbs.graph import to_cypher, build_disease_graph

        graph = build_disease_graph(disease_data)
        cypher = to_cypher(graph)
        print(cypher[:150])
        # // Cypher script generated from KnowledgeGraph: DiseaseOntologyGraph
        # // Nodes: 47, Edges: 0
        # ...
        ```
    """
    lines: List[str] = []
    command = "MERGE" if use_merge else "CREATE"

    # Header comment
    lines.append(f"// Cypher script generated from KnowledgeGraph: {graph.name}")
    lines.append(f"// Nodes: {graph.node_count}, Edges: {graph.edge_count}")
    lines.append("")

    # Create constraints for efficient MERGE
    if use_merge:
        node_types_used = {node.node_type for node in graph.nodes}
        for node_type in node_types_used:
            label = node_type.value.title().replace("_", "")
            lines.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) "
                f"REQUIRE n.id IS UNIQUE;"
            )
        lines.append("")

    # Create nodes
    lines.append("// Create nodes")
    for i, node in enumerate(graph.nodes):
        if i > 0 and i % batch_size == 0:
            lines.append("")

        label = node.node_type.value.title().replace("_", "")
        props = {
            "id": node.id,
            "label": node.label,
            "source": node.source.value,
        }
        props.update(node.get_properties_dict())

        # Escape special characters in strings
        props_str = ", ".join(
            f"{k}: {_cypher_value(v)}"
            for k, v in props.items()
        )

        lines.append(f"{command} (:{label} {{{props_str}}});")

    lines.append("")

    # Create relationships
    lines.append("// Create relationships")
    for i, edge in enumerate(graph.edges):
        if i > 0 and i % batch_size == 0:
            lines.append("")

        rel_type = edge.relation.value.upper()

        props: Dict[str, Any] = {"weight": edge.weight}
        if edge.evidence:
            props["evidence"] = list(edge.evidence)
        props.update(edge.get_properties_dict())

        props_str = ", ".join(
            f"{k}: {_cypher_value(v)}"
            for k, v in props.items()
        )

        lines.append(
            f"MATCH (a {{id: {_cypher_value(edge.source)}}}), "
            f"(b {{id: {_cypher_value(edge.target)}}}) "
            f"{command} (a)-[:{rel_type} {{{props_str}}}]->(b);"
        )

    return "\n".join(lines)


def _cypher_value(value: Any) -> str:
    """Convert a Python value to Cypher literal."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Escape single quotes and backslashes
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    elif isinstance(value, (list, tuple)):
        items = ", ".join(_cypher_value(v) for v in value)
        return f"[{items}]"
    else:
        # Convert to string
        escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
