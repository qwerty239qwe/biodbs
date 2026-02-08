"""Core data structures for knowledge graph module.

This module provides the fundamental building blocks for constructing
biological knowledge graphs from ontology data sources.

Classes:
    Node: Represents a node (entity) in the knowledge graph.
    Edge: Represents a directed edge (relationship) between nodes.
    KnowledgeGraph: Container for nodes and edges with graph operations.

Enums:
    NodeType: Types of biological entities (genes, proteins, diseases, etc.)
    EdgeType: Types of relationships between entities.
    DataSource: Supported data sources for building graphs.

Example:
    ```python
    from biodbs.graph import KnowledgeGraph, Node, Edge, NodeType, EdgeType

    # Create nodes
    node1 = Node(id="DOID:162", label="cancer", node_type=NodeType.DISEASE)
    node2 = Node(id="DOID:1612", label="breast cancer", node_type=NodeType.DISEASE)

    # Create edge
    edge = Edge(source="DOID:1612", target="DOID:162", relation=EdgeType.IS_A)

    # Build graph
    graph = KnowledgeGraph(name="DiseaseGraph")
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge(edge)
    print(graph)
    # KnowledgeGraph(name='DiseaseGraph', nodes=2, edges=1)
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

if TYPE_CHECKING:
    import pandas as pd


# =============================================================================
# Enums
# =============================================================================


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph.

    Each node type represents a different biological entity category.
    """

    GENE = "gene"
    PROTEIN = "protein"
    DISEASE = "disease"
    PATHWAY = "pathway"
    GO_TERM = "go_term"
    REACTION = "reaction"
    COMPOUND = "compound"
    DRUG = "drug"
    PHENOTYPE = "phenotype"
    ORGANISM = "organism"
    PUBLICATION = "publication"
    OTHER = "other"


class EdgeType(str, Enum):
    """Types of edges (relationships) in the knowledge graph.

    Each edge type represents a different kind of relationship
    between biological entities.
    """

    # Ontology relationships
    IS_A = "is_a"
    PART_OF = "part_of"
    HAS_PART = "has_part"

    # Regulatory relationships
    REGULATES = "regulates"
    POSITIVELY_REGULATES = "positively_regulates"
    NEGATIVELY_REGULATES = "negatively_regulates"

    # Participation
    PARTICIPATES_IN = "participates_in"
    HAS_PARTICIPANT = "has_participant"
    CATALYZES = "catalyzes"
    PRODUCES = "produces"
    CONSUMES = "consumes"

    # Associations
    ASSOCIATED_WITH = "associated_with"
    INTERACTS_WITH = "interacts_with"
    TARGETS = "targets"

    # Cross-references
    XREF = "xref"
    SAME_AS = "same_as"

    # Sequence relationships
    ENCODES = "encodes"
    TRANSCRIBES = "transcribes"
    TRANSLATES = "translates"

    # Other
    RELATED_TO = "related_to"
    OTHER = "other"


class DataSource(str, Enum):
    """Supported data sources for knowledge graph construction."""

    DISEASE_ONTOLOGY = "disease_ontology"
    GENE_ONTOLOGY = "gene_ontology"
    REACTOME = "reactome"
    KEGG = "kegg"
    QUICKGO = "quickgo"
    UNIPROT = "uniprot"
    ENSEMBL = "ensembl"
    PUBCHEM = "pubchem"
    CHEMBL = "chembl"
    CUSTOM = "custom"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass(frozen=True)
class Node:
    """A node (entity) in the knowledge graph.

    Nodes are immutable (frozen) to ensure graph integrity.

    Attributes:
        id: Unique identifier for the node (e.g., "DOID:162", "GO:0008150").
        label: Human-readable label for the node.
        node_type: Type of biological entity this node represents.
        source: Data source this node originated from.
        properties: Additional properties as a frozen dict.
        xrefs: Cross-references to other databases.
    """

    id: str
    label: str
    node_type: NodeType = NodeType.OTHER
    source: DataSource = DataSource.CUSTOM
    properties: FrozenSet[Tuple[str, Any]] = field(default_factory=frozenset)
    xrefs: FrozenSet[str] = field(default_factory=frozenset)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            return self.id == other.id
        return False

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value by key."""
        for k, v in self.properties:
            if k == key:
                return v
        return default

    def get_properties_dict(self) -> Dict[str, Any]:
        """Get properties as a dictionary."""
        return dict(self.properties)

    def with_properties(self, **kwargs: Any) -> "Node":
        """Create a new node with additional/updated properties."""
        props = dict(self.properties)
        props.update(kwargs)
        return Node(
            id=self.id,
            label=self.label,
            node_type=self.node_type,
            source=self.source,
            properties=frozenset(props.items()),
            xrefs=self.xrefs,
        )

    def with_xrefs(self, *xrefs: str) -> "Node":
        """Create a new node with additional cross-references."""
        return Node(
            id=self.id,
            label=self.label,
            node_type=self.node_type,
            source=self.source,
            properties=self.properties,
            xrefs=self.xrefs | frozenset(xrefs),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "label": self.label,
            "node_type": self.node_type.value,
            "source": self.source.value,
            "properties": dict(self.properties),
            "xrefs": list(self.xrefs),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """Create a Node from dictionary representation."""
        return cls(
            id=data["id"],
            label=data["label"],
            node_type=NodeType(data.get("node_type", "other")),
            source=DataSource(data.get("source", "custom")),
            properties=frozenset(data.get("properties", {}).items()),
            xrefs=frozenset(data.get("xrefs", [])),
        )


@dataclass(frozen=True)
class Edge:
    """A directed edge (relationship) in the knowledge graph.

    Edges are immutable (frozen) to ensure graph integrity.

    Attributes:
        source: ID of the source node.
        target: ID of the target node.
        relation: Type of relationship.
        weight: Optional edge weight (default 1.0).
        evidence: Evidence supporting this relationship.
        properties: Additional properties as a frozen dict.
    """

    source: str
    target: str
    relation: EdgeType = EdgeType.RELATED_TO
    weight: float = 1.0
    evidence: FrozenSet[str] = field(default_factory=frozenset)
    properties: FrozenSet[Tuple[str, Any]] = field(default_factory=frozenset)

    def __hash__(self) -> int:
        return hash((self.source, self.target, self.relation))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Edge):
            return (
                self.source == other.source
                and self.target == other.target
                and self.relation == other.relation
            )
        return False

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value by key."""
        for k, v in self.properties:
            if k == key:
                return v
        return default

    def get_properties_dict(self) -> Dict[str, Any]:
        """Get properties as a dictionary."""
        return dict(self.properties)

    def with_properties(self, **kwargs: Any) -> "Edge":
        """Create a new edge with additional/updated properties."""
        props = dict(self.properties)
        props.update(kwargs)
        return Edge(
            source=self.source,
            target=self.target,
            relation=self.relation,
            weight=self.weight,
            evidence=self.evidence,
            properties=frozenset(props.items()),
        )

    def with_evidence(self, *evidence: str) -> "Edge":
        """Create a new edge with additional evidence."""
        return Edge(
            source=self.source,
            target=self.target,
            relation=self.relation,
            weight=self.weight,
            evidence=self.evidence | frozenset(evidence),
            properties=self.properties,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value,
            "weight": self.weight,
            "evidence": list(self.evidence),
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        """Create an Edge from dictionary representation."""
        return cls(
            source=data["source"],
            target=data["target"],
            relation=EdgeType(data.get("relation", "related_to")),
            weight=data.get("weight", 1.0),
            evidence=frozenset(data.get("evidence", [])),
            properties=frozenset(data.get("properties", {}).items()),
        )


# =============================================================================
# Knowledge Graph Container
# =============================================================================


class KnowledgeGraph:
    """Container for a biological knowledge graph.

    Provides methods for adding/removing nodes and edges, filtering,
    subgraph extraction, merging, and computing statistics.

    Attributes:
        name: Name of the knowledge graph.
        description: Optional description.
        source: Primary data source for this graph.

    Example:
        ```python
        from biodbs.graph import KnowledgeGraph, Node, Edge, NodeType, EdgeType

        graph = KnowledgeGraph(name="DiseaseOntologyGraph")
        graph.add_node(Node(id="DOID:162", label="cancer", node_type=NodeType.DISEASE))
        graph.add_node(Node(id="DOID:1612", label="breast cancer", node_type=NodeType.DISEASE))
        graph.add_edge(Edge(source="DOID:1612", target="DOID:162", relation=EdgeType.IS_A))
        print(graph.summary())
        # KnowledgeGraph: DiseaseOntologyGraph
        # Nodes: 2
        # Edges: 1
        #
        # Node types:
        #   disease: 2
        #
        # Edge types:
        #   is_a: 1
        ```
    """

    def __init__(
        self,
        name: str = "KnowledgeGraph",
        description: Optional[str] = None,
        source: DataSource = DataSource.CUSTOM,
    ):
        """Initialize a new KnowledgeGraph.

        Args:
            name: Name of the graph.
            description: Optional description.
            source: Primary data source for this graph.
        """
        self.name = name
        self.description = description
        self.source = source

        # Internal storage
        self._nodes: Dict[str, Node] = {}
        self._edges: Set[Edge] = set()
        self._outgoing: Dict[str, Set[Edge]] = {}  # node_id -> outgoing edges
        self._incoming: Dict[str, Set[Edge]] = {}  # node_id -> incoming edges

    # -------------------------------------------------------------------------
    # Basic Properties
    # -------------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self._nodes

    def __iter__(self) -> Iterator[Node]:
        """Iterate over all nodes in the graph."""
        return iter(self._nodes.values())

    def __repr__(self) -> str:
        """Return a string representation."""
        return (
            f"KnowledgeGraph(name='{self.name}', "
            f"nodes={len(self._nodes)}, edges={len(self._edges)})"
        )

    @property
    def nodes(self) -> List[Node]:
        """Get all nodes as a list."""
        return list(self._nodes.values())

    @property
    def edges(self) -> List[Edge]:
        """Get all edges as a list."""
        return list(self._edges)

    @property
    def node_count(self) -> int:
        """Get the number of nodes."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Get the number of edges."""
        return len(self._edges)

    # -------------------------------------------------------------------------
    # Node Operations
    # -------------------------------------------------------------------------

    def add_node(self, node: Node) -> bool:
        """Add a node to the graph.

        Args:
            node: The node to add.

        Returns:
            True if the node was added, False if it already existed.
        """
        if node.id in self._nodes:
            return False
        self._nodes[node.id] = node
        self._outgoing[node.id] = set()
        self._incoming[node.id] = set()
        return True

    def add_nodes(self, nodes: List[Node]) -> int:
        """Add multiple nodes to the graph.

        Args:
            nodes: List of nodes to add.

        Returns:
            Number of nodes actually added (excludes duplicates).
        """
        count = 0
        for node in nodes:
            if self.add_node(node):
                count += 1
        return count

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID.

        Args:
            node_id: The node identifier.

        Returns:
            The Node if found, None otherwise.
        """
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists.

        Args:
            node_id: The node identifier.

        Returns:
            True if the node exists.
        """
        return node_id in self._nodes

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its connected edges.

        Args:
            node_id: The node identifier.

        Returns:
            True if the node was removed, False if it didn't exist.
        """
        if node_id not in self._nodes:
            return False

        # Remove all edges connected to this node
        edges_to_remove = self._outgoing.get(node_id, set()) | self._incoming.get(
            node_id, set()
        )
        for edge in edges_to_remove:
            self._edges.discard(edge)
            if edge.source in self._outgoing:
                self._outgoing[edge.source].discard(edge)
            if edge.target in self._incoming:
                self._incoming[edge.target].discard(edge)

        # Remove node
        del self._nodes[node_id]
        self._outgoing.pop(node_id, None)
        self._incoming.pop(node_id, None)
        return True

    # -------------------------------------------------------------------------
    # Edge Operations
    # -------------------------------------------------------------------------

    def add_edge(self, edge: Edge) -> bool:
        """Add an edge to the graph.

        Args:
            edge: The edge to add.

        Returns:
            True if the edge was added, False if it already existed
            or if source/target nodes don't exist.
        """
        if edge in self._edges:
            return False

        # Ensure both nodes exist
        if edge.source not in self._nodes or edge.target not in self._nodes:
            return False

        self._edges.add(edge)
        self._outgoing[edge.source].add(edge)
        self._incoming[edge.target].add(edge)
        return True

    def add_edges(self, edges: List[Edge]) -> int:
        """Add multiple edges to the graph.

        Args:
            edges: List of edges to add.

        Returns:
            Number of edges actually added.
        """
        count = 0
        for edge in edges:
            if self.add_edge(edge):
                count += 1
        return count

    def get_edge(
        self, source: str, target: str, relation: Optional[EdgeType] = None
    ) -> Optional[Edge]:
        """Get an edge between two nodes.

        Args:
            source: Source node ID.
            target: Target node ID.
            relation: Optional relation type to match.

        Returns:
            The Edge if found, None otherwise.
        """
        for edge in self._outgoing.get(source, set()):
            if edge.target == target:
                if relation is None or edge.relation == relation:
                    return edge
        return None

    def has_edge(
        self, source: str, target: str, relation: Optional[EdgeType] = None
    ) -> bool:
        """Check if an edge exists between two nodes.

        Args:
            source: Source node ID.
            target: Target node ID.
            relation: Optional relation type to match.

        Returns:
            True if the edge exists.
        """
        return self.get_edge(source, target, relation) is not None

    def remove_edge(self, edge: Edge) -> bool:
        """Remove an edge from the graph.

        Args:
            edge: The edge to remove.

        Returns:
            True if the edge was removed, False if it didn't exist.
        """
        if edge not in self._edges:
            return False

        self._edges.discard(edge)
        self._outgoing[edge.source].discard(edge)
        self._incoming[edge.target].discard(edge)
        return True

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Get all outgoing edges from a node.

        Args:
            node_id: The node identifier.

        Returns:
            List of outgoing edges.
        """
        return list(self._outgoing.get(node_id, set()))

    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """Get all incoming edges to a node.

        Args:
            node_id: The node identifier.

        Returns:
            List of incoming edges.
        """
        return list(self._incoming.get(node_id, set()))

    def get_neighbors(
        self, node_id: str, direction: str = "both"
    ) -> List[str]:
        """Get neighboring node IDs.

        Args:
            node_id: The node identifier.
            direction: "outgoing", "incoming", or "both".

        Returns:
            List of neighboring node IDs.
        """
        neighbors = set()

        if direction in ("outgoing", "both"):
            for edge in self._outgoing.get(node_id, set()):
                neighbors.add(edge.target)

        if direction in ("incoming", "both"):
            for edge in self._incoming.get(node_id, set()):
                neighbors.add(edge.source)

        return list(neighbors)

    # -------------------------------------------------------------------------
    # Filtering
    # -------------------------------------------------------------------------

    def filter_nodes(
        self,
        predicate: Optional[Callable[[Node], bool]] = None,
        node_type: Optional[NodeType] = None,
        source: Optional[DataSource] = None,
    ) -> List[Node]:
        """Filter nodes by predicate or attributes.

        Args:
            predicate: Function that returns True for nodes to include.
            node_type: Filter by node type.
            source: Filter by data source.

        Returns:
            List of matching nodes.
        """
        result = []
        for node in self._nodes.values():
            if node_type is not None and node.node_type != node_type:
                continue
            if source is not None and node.source != source:
                continue
            if predicate is not None and not predicate(node):
                continue
            result.append(node)
        return result

    def filter_edges(
        self,
        predicate: Optional[Callable[[Edge], bool]] = None,
        relation: Optional[EdgeType] = None,
        min_weight: Optional[float] = None,
    ) -> List[Edge]:
        """Filter edges by predicate or attributes.

        Args:
            predicate: Function that returns True for edges to include.
            relation: Filter by relation type.
            min_weight: Filter by minimum weight.

        Returns:
            List of matching edges.
        """
        result = []
        for edge in self._edges:
            if relation is not None and edge.relation != relation:
                continue
            if min_weight is not None and edge.weight < min_weight:
                continue
            if predicate is not None and not predicate(edge):
                continue
            result.append(edge)
        return result

    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """Get all nodes of a specific type.

        Args:
            node_type: The node type to filter by.

        Returns:
            List of nodes with the specified type.
        """
        return self.filter_nodes(node_type=node_type)

    def get_edges_by_relation(self, relation: EdgeType) -> List[Edge]:
        """Get all edges with a specific relation type.

        Args:
            relation: The relation type to filter by.

        Returns:
            List of edges with the specified relation.
        """
        return self.filter_edges(relation=relation)

    # -------------------------------------------------------------------------
    # Subgraph Operations
    # -------------------------------------------------------------------------

    def subgraph(self, node_ids: Set[str]) -> "KnowledgeGraph":
        """Create a subgraph containing only the specified nodes.

        Args:
            node_ids: Set of node IDs to include.

        Returns:
            A new KnowledgeGraph containing the subgraph.
        """
        subgraph = KnowledgeGraph(
            name=f"{self.name}_subgraph",
            description=f"Subgraph of {self.name}",
            source=self.source,
        )

        # Add nodes
        for node_id in node_ids:
            node = self._nodes.get(node_id)
            if node:
                subgraph.add_node(node)

        # Add edges where both endpoints are in the subgraph
        for edge in self._edges:
            if edge.source in node_ids and edge.target in node_ids:
                subgraph.add_edge(edge)

        return subgraph

    def induced_subgraph(self, node_ids: Set[str]) -> "KnowledgeGraph":
        """Alias for subgraph() - creates induced subgraph.

        Args:
            node_ids: Set of node IDs to include.

        Returns:
            A new KnowledgeGraph containing the induced subgraph.
        """
        return self.subgraph(node_ids)

    # -------------------------------------------------------------------------
    # Merge Operations
    # -------------------------------------------------------------------------

    def merge(self, other: "KnowledgeGraph") -> "KnowledgeGraph":
        """Merge another graph into a new graph.

        Args:
            other: The graph to merge with this one.

        Returns:
            A new KnowledgeGraph containing all nodes and edges from both.
        """
        merged = KnowledgeGraph(
            name=f"{self.name}+{other.name}",
            description=f"Merged graph from {self.name} and {other.name}",
            source=self.source,
        )

        # Add all nodes from both graphs
        merged.add_nodes(self.nodes)
        merged.add_nodes(other.nodes)

        # Add all edges from both graphs
        merged.add_edges(self.edges)
        merged.add_edges(other.edges)

        return merged

    def update(self, other: "KnowledgeGraph") -> int:
        """Update this graph with nodes and edges from another graph.

        Unlike merge(), this modifies the current graph in place.

        Args:
            other: The graph to merge into this one.

        Returns:
            Total number of new nodes and edges added.
        """
        count = self.add_nodes(other.nodes)
        count += self.add_edges(other.edges)
        return count

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_node_type_counts(self) -> Dict[NodeType, int]:
        """Get counts of nodes by type.

        Returns:
            Dictionary mapping NodeType to count.
        """
        counts: Dict[NodeType, int] = {}
        for node in self._nodes.values():
            counts[node.node_type] = counts.get(node.node_type, 0) + 1
        return counts

    def get_edge_type_counts(self) -> Dict[EdgeType, int]:
        """Get counts of edges by relation type.

        Returns:
            Dictionary mapping EdgeType to count.
        """
        counts: Dict[EdgeType, int] = {}
        for edge in self._edges:
            counts[edge.relation] = counts.get(edge.relation, 0) + 1
        return counts

    def get_degree(self, node_id: str, direction: str = "both") -> int:
        """Get the degree of a node.

        Args:
            node_id: The node identifier.
            direction: "outgoing", "incoming", or "both".

        Returns:
            The degree of the node.
        """
        if node_id not in self._nodes:
            return 0

        if direction == "outgoing":
            return len(self._outgoing.get(node_id, set()))
        elif direction == "incoming":
            return len(self._incoming.get(node_id, set()))
        else:
            return len(self._outgoing.get(node_id, set())) + len(
                self._incoming.get(node_id, set())
            )

    def summary(self) -> str:
        """Get a text summary of the graph.

        Returns:
            A formatted string with graph statistics.
        """
        lines = [
            f"KnowledgeGraph: {self.name}",
            f"Nodes: {self.node_count}",
            f"Edges: {self.edge_count}",
        ]

        if self.description:
            lines.insert(1, f"Description: {self.description}")

        node_counts = self.get_node_type_counts()
        if node_counts:
            lines.append("\nNode types:")
            for node_type, count in sorted(
                node_counts.items(), key=lambda x: -x[1]
            ):
                lines.append(f"  {node_type.value}: {count}")

        edge_counts = self.get_edge_type_counts()
        if edge_counts:
            lines.append("\nEdge types:")
            for edge_type, count in sorted(
                edge_counts.items(), key=lambda x: -x[1]
            ):
                lines.append(f"  {edge_type.value}: {count}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary representation.

        Returns:
            Dictionary containing all graph data.
        """
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeGraph":
        """Create a KnowledgeGraph from a dictionary representation.

        Args:
            data: Dictionary containing graph data.

        Returns:
            A new KnowledgeGraph instance.
        """
        graph = cls(
            name=data.get("name", "KnowledgeGraph"),
            description=data.get("description"),
            source=DataSource(data.get("source", "custom")),
        )

        # Add nodes first
        for node_data in data.get("nodes", []):
            graph.add_node(Node.from_dict(node_data))

        # Then add edges
        for edge_data in data.get("edges", []):
            graph.add_edge(Edge.from_dict(edge_data))

        return graph

    def nodes_as_dataframe(
        self, engine: str = "pandas"
    ) -> "pd.DataFrame":
        """Convert nodes to a DataFrame.

        Args:
            engine: "pandas" or "polars".

        Returns:
            DataFrame with node data.
        """
        data = [node.to_dict() for node in self._nodes.values()]

        if engine == "pandas":
            import pandas as pd
            return pd.DataFrame(data)
        elif engine == "polars":
            import polars as pl
            return pl.DataFrame(data)
        else:
            raise ValueError(f"Unsupported engine: {engine}")

    def edges_as_dataframe(
        self, engine: str = "pandas"
    ) -> "pd.DataFrame":
        """Convert edges to a DataFrame.

        Args:
            engine: "pandas" or "polars".

        Returns:
            DataFrame with edge data.
        """
        data = [edge.to_dict() for edge in self._edges]

        if engine == "pandas":
            import pandas as pd
            return pd.DataFrame(data)
        elif engine == "polars":
            import polars as pl
            return pl.DataFrame(data)
        else:
            raise ValueError(f"Unsupported engine: {engine}")
