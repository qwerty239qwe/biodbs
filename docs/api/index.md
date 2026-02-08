# API Reference

Complete API reference for the `biodbs` package.

## Modules

### biodbs.fetch

Data fetching from biological databases.

<div class="doc-summary" markdown>

**Fetcher Classes**

- [`UniProt_Fetcher`](fetch.md#uniprot_fetcher) - Fetch protein data from UniProt REST API
- [`PubChem_Fetcher`](fetch.md#pubchem_fetcher) - Fetch chemical data from PubChem PUG REST/View APIs
- [`Ensembl_Fetcher`](fetch.md#ensembl_fetcher) - Fetch genomic data from Ensembl REST API
- [`BioMart_Fetcher`](fetch.md#biomart_fetcher) - Query Ensembl BioMart for gene annotations
- [`KEGG_Fetcher`](fetch.md#kegg_fetcher) - Fetch pathway and gene data from KEGG API
- [`ChEMBL_Fetcher`](fetch.md#chembl_fetcher) - Fetch bioactivity data from ChEMBL API
- [`QuickGO_Fetcher`](fetch.md#quickgo_fetcher) - Fetch GO annotations from QuickGO API
- [`HPA_Fetcher`](fetch.md#hpa_fetcher) - Fetch protein expression from Human Protein Atlas
- [`NCBI_Fetcher`](fetch.md#ncbi_fetcher) - Fetch gene data from NCBI Entrez
- [`FDA_Fetcher`](fetch.md#fda_fetcher) - Fetch drug/device data from openFDA
- [`Reactome_Fetcher`](fetch.md#reactome_fetcher) - Fetch pathway data from Reactome
- [`DO_Fetcher`](fetch.md#do_fetcher) - Fetch disease terms from Disease Ontology
- [`EnrichR_Fetcher`](fetch.md#enrichr_fetcher) - Perform gene set enrichment via EnrichR

**Key Functions**

- [`uniprot_get_entry`](fetch.md#uniprot_get_entry) - Get a UniProt entry by accession
- [`uniprot_search`](fetch.md#uniprot_search) - Search UniProtKB with query
- [`pubchem_get_compound`](fetch.md#pubchem_get_compound) - Get compound by CID
- [`ensembl_lookup`](fetch.md#ensembl_lookup) - Lookup entity by Ensembl ID
- [`kegg_get`](fetch.md#kegg_get) - Get KEGG entry by ID
- [`kegg_link`](fetch.md#kegg_link) - Get cross-references between databases

</div>

[Full Fetch API Reference](fetch.md){ .md-button }

---

### biodbs.translate

ID translation between biological databases.

<div class="doc-summary" markdown>

**Gene Translation**

- [`translate_gene_ids`](translate.md#translate_gene_ids) - Translate gene IDs between databases via BioMart
- [`translate_gene_ids_kegg`](translate.md#translate_gene_ids_kegg) - Translate gene IDs using KEGG API

**Protein Translation**

- [`translate_protein_ids`](translate.md#translate_protein_ids) - Translate protein IDs via UniProt ID mapping
- [`translate_gene_to_uniprot`](translate.md#translate_gene_to_uniprot) - Map gene symbols to UniProt accessions
- [`translate_uniprot_to_gene`](translate.md#translate_uniprot_to_gene) - Map UniProt accessions to gene symbols
- [`translate_uniprot_to_pdb`](translate.md#translate_uniprot_to_pdb) - Map UniProt accessions to PDB IDs
- [`translate_uniprot_to_ensembl`](translate.md#translate_uniprot_to_ensembl) - Map UniProt accessions to Ensembl gene IDs

**Chemical Translation**

- [`translate_chemical_ids`](translate.md#translate_chemical_ids) - Translate chemical IDs via PubChem
- [`translate_chembl_to_pubchem`](translate.md#translate_chembl_to_pubchem) - Map ChEMBL IDs to PubChem CIDs
- [`translate_pubchem_to_chembl`](translate.md#translate_pubchem_to_chembl) - Map PubChem CIDs to ChEMBL IDs

</div>

[Full Translate API Reference](translate.md){ .md-button }

---

### biodbs.analysis

Statistical analysis and enrichment functions.

<div class="doc-summary" markdown>

**Classes**

- [`ORAResult`](analysis.md#oraresult) - Container for over-representation analysis results
- [`ORATermResult`](analysis.md#oratermresult) - Single term result from ORA
- [`Pathway`](analysis.md#pathway) - Represents a biological pathway with gene sets

**Enums**

- [`Species`](analysis.md#species) - Supported species for ORA
- [`GOAspect`](analysis.md#goaspect) - Gene Ontology aspects (BP, MF, CC)
- [`CorrectionMethod`](analysis.md#correctionmethod) - Multiple testing correction methods
- [`PathwayDatabase`](analysis.md#pathwaydatabase) - Pathway database sources

**Functions**

- [`ora`](analysis.md#ora) - Generic ORA against any pathway database
- [`ora_kegg`](analysis.md#ora_kegg) - ORA against KEGG pathways
- [`ora_go`](analysis.md#ora_go) - ORA against Gene Ontology terms
- [`ora_reactome`](analysis.md#ora_reactome) - ORA against Reactome pathways
- [`ora_enrichr`](analysis.md#ora_enrichr) - ORA via EnrichR web service
- [`hypergeometric_test`](analysis.md#hypergeometric_test) - Compute hypergeometric p-value

</div>

[Full Analysis API Reference](analysis.md){ .md-button }

---

### biodbs.graph

Knowledge graph building and analysis.

<div class="doc-summary" markdown>

**Classes**

- [`KnowledgeGraph`](graph.md#knowledgegraph) - Container for nodes and edges with graph operations
- [`Node`](graph.md#node) - Represents a biological entity
- [`Edge`](graph.md#edge) - Represents a relationship between nodes

**Enums**

- [`NodeType`](graph.md#nodetype) - Types of nodes (GENE, PROTEIN, DISEASE, etc.)
- [`EdgeType`](graph.md#edgetype) - Types of edges (IS_A, PART_OF, etc.)
- [`DataSource`](graph.md#datasource) - Data sources (DISEASE_ONTOLOGY, GENE_ONTOLOGY, etc.)

**Builder Functions**

- [`build_graph`](graph.md#build_graph) - Build graph from nodes and edges
- [`build_disease_graph`](graph.md#build_disease_graph) - Build graph from Disease Ontology data
- [`build_go_graph`](graph.md#build_go_graph) - Build graph from QuickGO data
- [`build_reactome_graph`](graph.md#build_reactome_graph) - Build graph from Reactome data
- [`build_kegg_graph`](graph.md#build_kegg_graph) - Build graph from KEGG data
- [`merge_graphs`](graph.md#merge_graphs) - Merge multiple graphs

**Export Functions**

- [`to_networkx`](graph.md#to_networkx) - Export to NetworkX DiGraph
- [`to_json_ld`](graph.md#to_json_ld) - Export to JSON-LD for KG-RAG
- [`to_rdf`](graph.md#to_rdf) - Export to RDF format
- [`to_neo4j_csv`](graph.md#to_neo4j_csv) - Export to Neo4j CSV format
- [`to_cypher`](graph.md#to_cypher) - Generate Cypher queries

**Utility Functions**

- [`find_shortest_path`](graph.md#find_shortest_path) - Find shortest path between nodes
- [`find_all_paths`](graph.md#find_all_paths) - Find all paths between nodes
- [`get_neighborhood`](graph.md#get_neighborhood) - Get nodes within N hops
- [`find_hub_nodes`](graph.md#find_hub_nodes) - Find highly connected nodes
- [`get_graph_statistics`](graph.md#get_graph_statistics) - Get graph statistics

</div>

[Full Graph API Reference](graph.md){ .md-button }
