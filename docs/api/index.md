# API Reference

Complete API reference for the `biodbs` package.

## Modules

### biodbs.fetch

Data fetching from biological databases.

<div class="doc-summary" markdown>

**Fetcher Classes**

- `UniProt_Fetcher`
- `PubChem_Fetcher`
- `Ensembl_Fetcher`
- `BioMart_Fetcher`
- `KEGG_Fetcher`
- `ChEMBL_Fetcher`
- `QuickGO_Fetcher`
- `HPA_Fetcher`
- `NCBI_Fetcher`
- `FDA_Fetcher`
- `Reactome_Fetcher`
- `DiseaseOntology_Fetcher`
- `EnrichR_Fetcher`

**Key Functions**

- [`uniprot_get_entry`][biodbs.fetch.uniprot.funcs.uniprot_get_entry]
- [`uniprot_search`][biodbs.fetch.uniprot.funcs.uniprot_search]
- [`pubchem_get_compound`][biodbs.fetch.pubchem.funcs.pubchem_get_compound]
- [`ensembl_lookup`][biodbs.fetch.ensembl.funcs.ensembl_lookup]
- [`kegg_get`][biodbs.fetch.KEGG.funcs.kegg_get]
- [`kegg_link`][biodbs.fetch.KEGG.funcs.kegg_link]

</div>

[Full Fetch API Reference](fetch.md){ .md-button }

---

### biodbs.translate

ID translation between biological databases.

<div class="doc-summary" markdown>

**Gene Translation**

- [`translate_gene_ids`][biodbs._funcs.translate.genes.translate_gene_ids]
- [`translate_gene_ids_kegg`][biodbs._funcs.translate.genes.translate_gene_ids_kegg]

**Protein Translation**

- [`translate_protein_ids`][biodbs._funcs.translate.proteins.translate_protein_ids]
- [`translate_gene_to_uniprot`][biodbs._funcs.translate.proteins.translate_gene_to_uniprot]
- [`translate_uniprot_to_gene`][biodbs._funcs.translate.proteins.translate_uniprot_to_gene]
- [`translate_uniprot_to_pdb`][biodbs._funcs.translate.proteins.translate_uniprot_to_pdb]
- [`translate_uniprot_to_ensembl`][biodbs._funcs.translate.proteins.translate_uniprot_to_ensembl]

**Chemical Translation**

- [`translate_chemical_ids`][biodbs._funcs.translate.chem.translate_chemical_ids]
- [`translate_chembl_to_pubchem`][biodbs._funcs.translate.chem.translate_chembl_to_pubchem]
- [`translate_pubchem_to_chembl`][biodbs._funcs.translate.chem.translate_pubchem_to_chembl]

</div>

[Full Translate API Reference](translate.md){ .md-button }

---

### biodbs.analysis

Statistical analysis and enrichment functions.

<div class="doc-summary" markdown>

**Classes**

- [`ORAResult`][biodbs._funcs.analysis.ora.ORAResult]
- [`ORATermResult`][biodbs._funcs.analysis.ora.ORATermResult]
- [`Pathway`][biodbs._funcs.analysis.ora.Pathway]

**Enums**

- [`Species`][biodbs._funcs.analysis.ora.Species]
- [`GOAspect`][biodbs._funcs.analysis.ora.GOAspect]
- [`CorrectionMethod`][biodbs._funcs.analysis.ora.CorrectionMethod]
- [`PathwayDatabase`][biodbs._funcs.analysis.ora.PathwayDatabase]

**Functions**

- [`ora`][biodbs._funcs.analysis.ora.ora]
- [`ora_kegg`][biodbs._funcs.analysis.ora.ora_kegg]
- [`ora_go`][biodbs._funcs.analysis.ora.ora_go]
- [`ora_reactome`][biodbs._funcs.analysis.ora.ora_reactome]
- [`ora_enrichr`][biodbs._funcs.analysis.ora.ora_enrichr]
- [`hypergeometric_test`][biodbs._funcs.analysis.ora.hypergeometric_test]

</div>

[Full Analysis API Reference](analysis.md){ .md-button }

---

### biodbs.graph

Knowledge graph building and analysis.

<div class="doc-summary" markdown>

**Classes**

- [`KnowledgeGraph`][biodbs._funcs.graph.core.KnowledgeGraph]
- [`Node`][biodbs._funcs.graph.core.Node]
- [`Edge`][biodbs._funcs.graph.core.Edge]

**Enums**

- [`NodeType`][biodbs._funcs.graph.core.NodeType]
- [`EdgeType`][biodbs._funcs.graph.core.EdgeType]
- [`DataSource`][biodbs._funcs.graph.core.DataSource]

**Builder Functions**

- [`build_graph`][biodbs._funcs.graph.builders.build_graph]
- [`build_disease_graph`][biodbs._funcs.graph.builders.build_disease_graph]
- [`build_go_graph`][biodbs._funcs.graph.builders.build_go_graph]
- [`build_reactome_graph`][biodbs._funcs.graph.builders.build_reactome_graph]
- [`build_kegg_graph`][biodbs._funcs.graph.builders.build_kegg_graph]
- [`merge_graphs`][biodbs._funcs.graph.builders.merge_graphs]

**Export Functions**

- [`to_networkx`][biodbs._funcs.graph.exporters.to_networkx]
- [`to_json_ld`][biodbs._funcs.graph.exporters.to_json_ld]
- [`to_rdf`][biodbs._funcs.graph.exporters.to_rdf]
- [`to_neo4j_csv`][biodbs._funcs.graph.exporters.to_neo4j_csv]
- [`to_cypher`][biodbs._funcs.graph.exporters.to_cypher]

**Utility Functions**

- [`find_shortest_path`][biodbs._funcs.graph.utils.find_shortest_path]
- [`find_all_paths`][biodbs._funcs.graph.utils.find_all_paths]
- [`get_neighborhood`][biodbs._funcs.graph.utils.get_neighborhood]
- [`find_hub_nodes`][biodbs._funcs.graph.utils.find_hub_nodes]
- [`get_graph_statistics`][biodbs._funcs.graph.utils.get_graph_statistics]

</div>

[Full Graph API Reference](graph.md){ .md-button }
