"""Offline tests for public fetch convenience functions."""

import pandas as pd
import pytest

from biodbs.fetch.KEGG import funcs as kegg_funcs
from biodbs.fetch.NCBI import funcs as ncbi_funcs
from biodbs.fetch.QuickGO import funcs as quickgo_funcs
from biodbs.fetch.Reactome import funcs as reactome_funcs


class RecordingFetcher:
    def __init__(self):
        self.calls = []

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        return kwargs

    def get_all(self, **kwargs):
        self.calls.append(("get_all", kwargs))
        return kwargs

    def __getattr__(self, name):
        def recorder(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return {"method": name, "args": args, "kwargs": kwargs}

        return recorder


def test_kegg_convenience_functions_route_to_fetcher(monkeypatch):
    fetcher = RecordingFetcher()
    monkeypatch.setattr(kegg_funcs, "_fetcher", fetcher)

    kegg_funcs.kegg_info("pathway")
    kegg_funcs.kegg_list("pathway", organism="hsa")
    kegg_funcs.kegg_find("compound", "aspirin", option="exact_mass")
    kegg_funcs.kegg_get("hsa:7157", option="aaseq")
    kegg_funcs.kegg_get_batch(["hsa:7157"], batch_size=5)
    kegg_funcs.kegg_conv("ncbi-geneid", ["hsa:7157"])
    kegg_funcs.kegg_conv("ncbi-geneid", "hsa")
    kegg_funcs.kegg_link("pathway", ["hsa:7157"])
    kegg_funcs.kegg_link("pathway", "hsa")
    kegg_funcs.kegg_ddi(["D00001"])

    assert fetcher.calls[0] == ("get", {"operation": "info", "database": "pathway"})
    assert fetcher.calls[3][1]["dbentries"] == ["hsa:7157"]
    assert fetcher.calls[4][0] == "get_all"
    assert fetcher.calls[5][1]["dbentries"] == ["hsa:7157"]
    assert fetcher.calls[6][1]["source_db"] == "hsa"


def test_quickgo_convenience_functions_route_to_fetcher(monkeypatch):
    fetcher = RecordingFetcher()
    monkeypatch.setattr(quickgo_funcs, "_fetcher", fetcher)

    quickgo_funcs.quickgo_search_terms("apoptosis", limit=5)
    quickgo_funcs.quickgo_get_terms("GO:0006915")
    quickgo_funcs.quickgo_get_term_children("GO:0008150")
    quickgo_funcs.quickgo_get_term_ancestors("GO:0006915")
    quickgo_funcs.quickgo_search_annotations(
        go_id="GO:1",
        taxon_id=9606,
        gene_product_id="UniProtKB:P04637",
        evidence_code="IDA",
    )
    quickgo_funcs.quickgo_search_annotations_all(go_id="GO:1", taxon_id=9606, max_records=10)
    quickgo_funcs.quickgo_download_annotations(go_id="GO:1", taxon_id=9606, download_format="gaf")
    quickgo_funcs.quickgo_get_gene_product("P04637")

    assert fetcher.calls[0][1]["endpoint"] == "search"
    assert fetcher.calls[1][1]["ids"] == ["GO:0006915"]
    assert fetcher.calls[5][0] == "get_all"
    assert fetcher.calls[6][1]["downloadFormat"] == "gaf"
    assert fetcher.calls[7][1]["geneProductId"] == "P04637"


class FakeGene:
    def __init__(self, gene_id=7157, symbol="TP53"):
        self.gene_id = gene_id
        self.symbol = symbol
        self.ensembl_gene_ids = ["ENSG00000141510"]
        self.swiss_prot_accessions = ["P04637"]
        self.transcripts = [type("Transcript", (), {"accession_version": "NM_000546.6"})()]


class FakeGenes:
    def __init__(self, genes=None):
        self.genes = genes or [FakeGene()]

    def to_id_mapping(self):
        return {gene.symbol: gene.gene_id for gene in self.genes}

    def to_symbol_mapping(self):
        return {gene.gene_id: gene.symbol for gene in self.genes}


class FakeNCBIFetcher:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def get_gene_info(self, identifiers, taxon="human"):
        return {"identifiers": identifiers, "taxon": taxon, "api_key": self.api_key}

    def get_genes_by_symbol(self, symbols, taxon="human"):
        return FakeGenes([FakeGene(symbol=symbol, gene_id=index + 1) for index, symbol in enumerate(symbols)])

    def get_genes_by_id(self, ids):
        return FakeGenes([FakeGene(gene_id=int(gene_id), symbol=f"SYM{gene_id}") for gene_id in ids])

    def get_genes_by_accession(self, ids):
        return FakeGenes([FakeGene()])

    def get_taxonomy(self, taxons):
        return {"taxons": taxons}


def test_ncbi_convenience_functions_and_translation(monkeypatch):
    monkeypatch.setattr(ncbi_funcs, "NCBI_Fetcher", FakeNCBIFetcher)
    monkeypatch.setattr(ncbi_funcs, "_ensembl_ids_to_ncbi", lambda ids: {ids[0]: 7157})

    assert ncbi_funcs.ncbi_get_gene(["TP53"], taxon="human", api_key="key")["api_key"] == "key"
    assert ncbi_funcs.ncbi_symbol_to_id(["TP53"]) == {"TP53": 1}
    assert isinstance(ncbi_funcs.ncbi_symbol_to_id(["TP53"], return_dict=False), pd.DataFrame)
    assert ncbi_funcs.ncbi_id_to_symbol([7157]) == {7157: "SYM7157"}
    assert isinstance(ncbi_funcs.ncbi_id_to_symbol([7157], return_dict=False), pd.DataFrame)
    assert ncbi_funcs.ncbi_get_taxonomy([9606]) == {"taxons": [9606]}
    assert ncbi_funcs.ncbi_translate_gene_ids(["TP53"], "symbol", "entrez-id", return_dict=True) == {
        "TP53": "1"
    }
    assert ncbi_funcs.ncbi_translate_gene_ids(["7157"], "gene-id", "symbol", return_dict=True) == {
        "7157": "SYM7157"
    }
    assert ncbi_funcs.ncbi_translate_gene_ids(
        ["ENSG00000141510"], "ensembl", "uniprot", return_dict=True
    ) == {"ENSG00000141510": "P04637"}
    assert not ncbi_funcs.ncbi_translate_gene_ids(["ENSG0"], "ensembl", "symbol", return_dict=False).empty
    assert ncbi_funcs.ncbi_translate_gene_ids(["NM_000546"], "refseq", "ensembl", return_dict=True)

    with pytest.raises(ValueError, match="Unsupported from_type"):
        ncbi_funcs.ncbi_translate_gene_ids(["x"], "bad", "symbol")
    with pytest.raises(ValueError, match="Unsupported to_type"):
        ncbi_funcs.ncbi_translate_gene_ids(["TP53"], "symbol", "bad")


def test_ncbi_extract_to_val_branches():
    gene = FakeGene()

    assert ncbi_funcs._extract_to_val(gene, "symbol") == "TP53"
    assert ncbi_funcs._extract_to_val(gene, "ncbi_gene_id") == "7157"
    assert ncbi_funcs._extract_to_val(gene, "ensembl") == "ENSG00000141510"
    assert ncbi_funcs._extract_to_val(gene, "uniprot") == "P04637"
    assert ncbi_funcs._extract_to_val(gene, "refseq") == "NM_000546.6"

    gene.transcripts = []
    assert ncbi_funcs._extract_to_val(gene, "refseq") is None
    with pytest.raises(ValueError):
        ncbi_funcs._extract_to_val(gene, "bad")


def test_reactome_convenience_functions_route_to_fetcher(monkeypatch):
    fetcher = RecordingFetcher()
    monkeypatch.setattr(reactome_funcs, "_fetcher", fetcher)

    reactome_funcs.reactome_analyze(["TP53"], min_entities=1, max_entities=5)
    reactome_funcs.reactome_analyze_projection(["Trp53"], species="Mus musculus")
    reactome_funcs.reactome_analyze_single("TP53")
    reactome_funcs.reactome_get_result_by_token("tok")
    reactome_funcs.reactome_get_found_entities("tok", "R-HSA-1")
    reactome_funcs.reactome_get_not_found("tok")
    reactome_funcs.reactome_map_identifiers(["TP53"])
    reactome_funcs.reactome_get_pathways_top()
    reactome_funcs.reactome_get_pathways_for_entity("P04637")
    reactome_funcs.reactome_get_species()
    reactome_funcs.reactome_get_species_main()
    reactome_funcs.reactome_get_database_version()
    reactome_funcs.reactome_query_entry("R-HSA-1")
    reactome_funcs.reactome_get_participants("R-HSA-1")
    reactome_funcs.reactome_get_participants_reference_entities("R-HSA-1")

    methods = [call[0] for call in fetcher.calls]
    assert methods[:4] == [
        "analyze",
        "analyze_projection",
        "analyze_single",
        "get_result_by_token",
    ]
    assert "get_species_main" in methods
    assert "get_participants_reference_entities" in methods
