# Exporting Knowledge Graphs

Export your knowledge graph to various formats for different use cases.

## JSON-LD (for KG-RAG)

JSON-LD is ideal for Knowledge Graph Retrieval Augmented Generation (KG-RAG) applications:

```python
from biodbs.graph import to_json_ld
import json

# Export to JSON-LD
json_ld = to_json_ld(graph)

# Use in RAG pipeline
context = json.dumps(json_ld, indent=2)
print(context)
```

### Output Structure

```json
{
  "@context": {
    "@vocab": "http://www.w3.org/2002/07/owl#",
    "schema": "http://schema.org/",
    "obo": "http://purl.obolibrary.org/obo/",
    ...
  },
  "@type": "schema:Dataset",
  "schema:name": "DiseaseOntologyGraph",
  "@graph": [
    {
      "@id": "obo:DOID_162",
      "@type": "obo:DOID_4",
      "label": "cancer",
      "description": "A disease of cellular proliferation",
      "is_a": "obo:DOID_14566"
    },
    ...
  ]
}
```

### Options

```python
json_ld = to_json_ld(
    graph,
    include_context=True,   # Include @context
    compact=False,          # Verbose output
    base_uri=None,          # Custom base URI
)
```

## NetworkX

Export to NetworkX for graph algorithms:

```python
from biodbs.graph import to_networkx
import networkx as nx

# Requires: pip install networkx
G = to_networkx(graph)

# Now use any NetworkX algorithm
centrality = nx.degree_centrality(G)
pagerank = nx.pagerank(G)
communities = nx.community.louvain_communities(G)

# Visualize
import matplotlib.pyplot as plt
nx.draw(G, with_labels=True)
plt.show()
```

### Options

```python
G = to_networkx(
    graph,
    include_properties=True,  # Node/edge properties as attributes
    include_xrefs=True,       # Cross-references as node attributes
)

# Access attributes
print(G.nodes["DOID:162"]["label"])  # "cancer"
print(G.edges["DOID:1612", "DOID:162"]["relation"])  # "is_a"
```

## RDF (Turtle/XML)

Export to RDF for semantic web applications:

```python
from biodbs.graph import to_rdf

# Requires: pip install rdflib
turtle = to_rdf(graph, format="turtle")
print(turtle)

# Or XML format
xml = to_rdf(graph, format="xml")
```

### Output (Turtle)

```turtle
@prefix base: <http://example.org/biokg/> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

base:DOID_162 a obo:DOID_4 ;
    rdfs:label "cancer" ;
    rdfs:subClassOf base:DOID_14566 .
```

### Options

```python
rdf = to_rdf(
    graph,
    format="turtle",  # "turtle", "xml", "n3", "nt"
    base_uri="http://example.org/biokg/",
)
```

## Neo4j CSV Import

Export CSV files for Neo4j bulk import:

```python
from biodbs.graph import to_neo4j_csv

nodes_path, edges_path = to_neo4j_csv(
    graph,
    output_dir="./neo4j_import/",
)

print(f"Nodes: {nodes_path}")
print(f"Edges: {edges_path}")
```

### Generated Files

**nodes.csv:**
```csv
id:ID,label,node_type,source,properties:string,xrefs:string[],:LABEL
DOID:162,cancer,disease,disease_ontology,"{""definition"": ""...""}",MESH:D009369;UMLS:C0006826,Disease
```

**relationships.csv:**
```csv
:START_ID,:END_ID,weight:float,evidence:string[],properties:string,:TYPE
DOID:1612,DOID:162,1.0,IEA,,IS_A
```

### Import to Neo4j

```bash
neo4j-admin database import full \
  --nodes=neo4j_import/nodes.csv \
  --relationships=neo4j_import/relationships.csv \
  neo4j
```

### Options

```python
to_neo4j_csv(
    graph,
    output_dir="./neo4j_import/",
    nodes_filename="nodes.csv",
    edges_filename="relationships.csv",
    include_headers=True,
)
```

## Cypher Queries

Generate Cypher scripts for Neo4j:

```python
from biodbs.graph import to_cypher

cypher = to_cypher(graph)
print(cypher)
```

### Output

```cypher
// Cypher script generated from KnowledgeGraph: DiseaseOntologyGraph
// Nodes: 47, Edges: 46

CREATE CONSTRAINT IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE;

// Create nodes
MERGE (:Disease {id: 'DOID:162', label: 'cancer', source: 'disease_ontology'});
MERGE (:Disease {id: 'DOID:1612', label: 'breast cancer', source: 'disease_ontology'});

// Create relationships
MATCH (a {id: 'DOID:1612'}), (b {id: 'DOID:162'}) MERGE (a)-[:IS_A {weight: 1.0}]->(b);
```

### Options

```python
cypher = to_cypher(
    graph,
    batch_size=100,    # Statements per transaction
    use_merge=True,    # MERGE vs CREATE (prevents duplicates)
)
```

## DataFrame Export

Export nodes/edges as DataFrames:

```python
# Nodes as DataFrame
nodes_df = graph.nodes_as_dataframe(engine="pandas")
print(nodes_df.head())

# Edges as DataFrame
edges_df = graph.edges_as_dataframe(engine="polars")
print(edges_df.head())
```

## Dictionary Export

Export to plain Python dictionaries:

```python
# Full graph
data = graph.to_dict()

# Save as JSON
import json
with open("graph.json", "w") as f:
    json.dump(data, f, indent=2)

# Reload
from biodbs.graph import KnowledgeGraph
restored = KnowledgeGraph.from_dict(data)
```
