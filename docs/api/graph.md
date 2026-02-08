# Graph Module API Reference

Complete API reference for `biodbs.graph` module.

## Summary

### Core Classes

| Class | Description |
|-------|-------------|
| [`Node`](#node) | Immutable node representing a biological entity |
| [`Edge`](#edge) | Immutable edge representing a relationship |
| [`KnowledgeGraph`](#knowledgegraph) | Container for nodes and edges with graph operations |

### Enums

| Enum | Description |
|------|-------------|
| [`NodeType`](#nodetype) | Types of biological entities (gene, protein, disease, etc.) |
| [`EdgeType`](#edgetype) | Types of relationships (is_a, part_of, regulates, etc.) |
| [`DataSource`](#datasource) | Supported data sources for graph construction |

### Builder Functions

| Function | Description |
|----------|-------------|
| [`build_graph`](#build_graph) | Create graph from nodes and edges |
| [`build_disease_graph`](#build_disease_graph) | Build from Disease Ontology data |
| [`build_go_graph`](#build_go_graph) | Build from Gene Ontology data |
| [`build_reactome_graph`](#build_reactome_graph) | Build from Reactome data |
| [`build_kegg_graph`](#build_kegg_graph) | Build from KEGG data |
| [`merge_graphs`](#merge_graphs) | Merge multiple graphs |

### Export Functions

| Function | Description |
|----------|-------------|
| [`to_networkx`](#to_networkx) | Export to NetworkX graph |
| [`to_json_ld`](#to_json_ld) | Export to JSON-LD format |
| [`to_rdf`](#to_rdf) | Export to RDF format |
| [`to_neo4j_csv`](#to_neo4j_csv) | Export to Neo4j CSV files |
| [`to_cypher`](#to_cypher) | Export to Cypher queries |

### Utility Functions

| Function | Description |
|----------|-------------|
| [`find_shortest_path`](#find_shortest_path) | Find shortest path between nodes |
| [`find_all_paths`](#find_all_paths) | Find all paths up to max length |
| [`get_neighborhood`](#get_neighborhood) | Get nodes within N hops |
| [`get_connected_component`](#get_connected_component) | Get connected component containing node |
| [`find_hub_nodes`](#find_hub_nodes) | Find high-degree hub nodes |
| [`get_graph_statistics`](#get_graph_statistics) | Compute graph statistics |

---

## Enums

### NodeType

Types of nodes representing biological entities.

| Member | Value | Description |
|--------|-------|-------------|
| `GENE` | `"gene"` | Gene entity |
| `PROTEIN` | `"protein"` | Protein entity |
| `DISEASE` | `"disease"` | Disease entity |
| `PATHWAY` | `"pathway"` | Biological pathway |
| `GO_TERM` | `"go_term"` | Gene Ontology term |
| `REACTION` | `"reaction"` | Biochemical reaction |
| `COMPOUND` | `"compound"` | Chemical compound |
| `DRUG` | `"drug"` | Drug/pharmaceutical |
| `PHENOTYPE` | `"phenotype"` | Phenotype |
| `ORGANISM` | `"organism"` | Organism/species |
| `PUBLICATION` | `"publication"` | Scientific publication |
| `OTHER` | `"other"` | Other entity type |

::: biodbs._funcs.graph.core.NodeType
    options:
      show_root_heading: true
      members_order: source

### EdgeType

Types of relationships between biological entities.

| Member | Value | Category |
|--------|-------|----------|
| `IS_A` | `"is_a"` | Ontology |
| `PART_OF` | `"part_of"` | Ontology |
| `HAS_PART` | `"has_part"` | Ontology |
| `REGULATES` | `"regulates"` | Regulatory |
| `POSITIVELY_REGULATES` | `"positively_regulates"` | Regulatory |
| `NEGATIVELY_REGULATES` | `"negatively_regulates"` | Regulatory |
| `PARTICIPATES_IN` | `"participates_in"` | Participation |
| `HAS_PARTICIPANT` | `"has_participant"` | Participation |
| `CATALYZES` | `"catalyzes"` | Participation |
| `PRODUCES` | `"produces"` | Participation |
| `CONSUMES` | `"consumes"` | Participation |
| `ASSOCIATED_WITH` | `"associated_with"` | Association |
| `INTERACTS_WITH` | `"interacts_with"` | Association |
| `TARGETS` | `"targets"` | Association |
| `XREF` | `"xref"` | Cross-reference |
| `SAME_AS` | `"same_as"` | Cross-reference |
| `ENCODES` | `"encodes"` | Sequence |
| `TRANSCRIBES` | `"transcribes"` | Sequence |
| `TRANSLATES` | `"translates"` | Sequence |
| `RELATED_TO` | `"related_to"` | Other |
| `OTHER` | `"other"` | Other |

::: biodbs._funcs.graph.core.EdgeType
    options:
      show_root_heading: true
      members_order: source

### DataSource

Supported data sources for graph construction.

| Member | Value | Description |
|--------|-------|-------------|
| `DISEASE_ONTOLOGY` | `"disease_ontology"` | Disease Ontology |
| `GENE_ONTOLOGY` | `"gene_ontology"` | Gene Ontology |
| `REACTOME` | `"reactome"` | Reactome pathways |
| `KEGG` | `"kegg"` | KEGG database |
| `QUICKGO` | `"quickgo"` | QuickGO annotations |
| `UNIPROT` | `"uniprot"` | UniProt |
| `ENSEMBL` | `"ensembl"` | Ensembl |
| `PUBCHEM` | `"pubchem"` | PubChem |
| `CHEMBL` | `"chembl"` | ChEMBL |
| `CUSTOM` | `"custom"` | Custom data source |

::: biodbs._funcs.graph.core.DataSource
    options:
      show_root_heading: true
      members_order: source

---

## Core Classes

### Node

::: biodbs._funcs.graph.core.Node
    options:
      show_root_heading: true
      members_order: source
      show_source: false

### Edge

::: biodbs._funcs.graph.core.Edge
    options:
      show_root_heading: true
      members_order: source
      show_source: false

### KnowledgeGraph

::: biodbs._funcs.graph.core.KnowledgeGraph
    options:
      show_root_heading: true
      members_order: source
      show_source: false

---

## Builder Functions

### build_graph

::: biodbs._funcs.graph.builders.build_graph
    options:
      show_root_heading: true

### build_disease_graph

::: biodbs._funcs.graph.builders.build_disease_graph
    options:
      show_root_heading: true

### build_disease_graph_with_hierarchy

::: biodbs._funcs.graph.builders.build_disease_graph_with_hierarchy
    options:
      show_root_heading: true

### build_go_graph

::: biodbs._funcs.graph.builders.build_go_graph
    options:
      show_root_heading: true

### build_reactome_graph

::: biodbs._funcs.graph.builders.build_reactome_graph
    options:
      show_root_heading: true

### build_reactome_hierarchy_graph

::: biodbs._funcs.graph.builders.build_reactome_hierarchy_graph
    options:
      show_root_heading: true

### build_kegg_graph

::: biodbs._funcs.graph.builders.build_kegg_graph
    options:
      show_root_heading: true

### build_kegg_link_graph

::: biodbs._funcs.graph.builders.build_kegg_link_graph
    options:
      show_root_heading: true

### merge_graphs

::: biodbs._funcs.graph.builders.merge_graphs
    options:
      show_root_heading: true

---

## Export Functions

### to_networkx

::: biodbs._funcs.graph.exporters.to_networkx
    options:
      show_root_heading: true

### to_json_ld

::: biodbs._funcs.graph.exporters.to_json_ld
    options:
      show_root_heading: true

### to_rdf

::: biodbs._funcs.graph.exporters.to_rdf
    options:
      show_root_heading: true

### to_neo4j_csv

::: biodbs._funcs.graph.exporters.to_neo4j_csv
    options:
      show_root_heading: true

### to_cypher

::: biodbs._funcs.graph.exporters.to_cypher
    options:
      show_root_heading: true

---

## Utility Functions

### find_shortest_path

::: biodbs._funcs.graph.utils.find_shortest_path
    options:
      show_root_heading: true

### find_all_paths

::: biodbs._funcs.graph.utils.find_all_paths
    options:
      show_root_heading: true

### get_neighborhood

::: biodbs._funcs.graph.utils.get_neighborhood
    options:
      show_root_heading: true

### get_connected_component

::: biodbs._funcs.graph.utils.get_connected_component
    options:
      show_root_heading: true

### get_all_connected_components

::: biodbs._funcs.graph.utils.get_all_connected_components
    options:
      show_root_heading: true

### find_hub_nodes

::: biodbs._funcs.graph.utils.find_hub_nodes
    options:
      show_root_heading: true

### compute_degree_distribution

::: biodbs._funcs.graph.utils.compute_degree_distribution
    options:
      show_root_heading: true

### get_graph_statistics

::: biodbs._funcs.graph.utils.get_graph_statistics
    options:
      show_root_heading: true

### format_statistics

::: biodbs._funcs.graph.utils.format_statistics
    options:
      show_root_heading: true
