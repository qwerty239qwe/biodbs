"""Accuracy contracts and request-count checks, not just non-empty output."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from biodbs.translate import (
    translate_chemical_ids, translate_gene_ids, translate_protein_ids, translate_uniprot_to_refseq,
    translate_chembl_to_pubchem, translate_pubchem_to_chembl,
)
from biodbs.fetch.NCBI.funcs import ncbi_translate_gene_ids
from biodbs.fetch.uniprot import UniProt_Fetcher
from biodbs.fetch.NCBI import NCBI_Fetcher
from biodbs._funcs.translate.genes import _translate_via_biomart


@pytest.mark.parametrize("id_type,id_value", [
    ("ensembl_gene_id", "ENSG00000141510"),
    ("ensembl_transcript_id", "ENST00000269305"),
    ("ensembl_protein_id", "ENSP00000269305"),
])
def test_ensembl_identity_is_local(id_type, id_value):
    with patch("biodbs.fetch.ensembl.funcs.ensembl_lookup") as lookup:
        result = translate_gene_ids([id_value], id_type, id_type,
                                    database="ensembl", return_dict=True)
    assert result == {id_value: id_value}
    lookup.assert_not_called()


@pytest.mark.parametrize("target,expected", [
    ("entrez_id", "7157"),
    ("ensembl_transcript_id", "ENST00000269305"),
    ("ensembl_protein_id", "ENSP00000269305"),
])
def test_ensembl_symbol_returns_requested_namespace(target, expected):
    with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol",
               return_value=SimpleNamespace(results=[{"id": "ENSG00000141510", "type": "gene"}])), \
         patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs",
               return_value=SimpleNamespace(results=[{"dbname": "EntrezGene", "primary_id": "7157"}])), \
         patch("biodbs.fetch.ensembl.funcs.ensembl_lookup",
               return_value=SimpleNamespace(results=[{"Transcript": [{
                   "id": "ENST00000269305", "is_canonical": 1,
                   "Translation": {"id": "ENSP00000269305"},
               }]}])):
        result = translate_gene_ids(["TP53"], "gene_symbol", target,
                                    database="ensembl", return_dict=True)
    assert result == {"TP53": expected}


@pytest.mark.parametrize("size", [1, 100, 1000])
def test_hgnc_multiple_targets_fetch_each_unique_input_once(size):
    ids = ["TP53", "MISSING"] * size
    fetch = Mock(side_effect=lambda field, value: SimpleNamespace(results=[
        SimpleNamespace(entrez_id="7157", ensembl_gene_id="ENSG00000141510")
    ] if value == "TP53" else []))
    with patch("biodbs.fetch.HGNC.hgnc_fetcher.HGNC_Fetcher") as cls:
        cls.return_value.fetch = fetch
        result = translate_gene_ids(ids, "gene_symbol", ["entrez_id", "ensembl_gene_id"],
                                    database="hgnc")
    assert fetch.call_count == 2
    assert result.symbol.tolist() == ids
    assert result.entrez_id.iloc[0] == "7157"
    assert pd.isna(result.entrez_id.iloc[1])


@pytest.mark.parametrize("wrong_accession", ["NM_0005460.1", "NM_OTHER.1"])
def test_ncbi_accession_association_requires_exact_base_not_prefix_or_fallback(wrong_accession):
    genes = [SimpleNamespace(symbol="TP53", transcripts=[
        SimpleNamespace(accession_version="NM_000546.6", protein=None)
    ]), SimpleNamespace(symbol="WRONG", transcripts=[
        SimpleNamespace(accession_version=wrong_accession, protein=None)
    ])]
    with patch("biodbs.fetch.NCBI.funcs.NCBI_Fetcher") as cls:
        cls.return_value.get_genes_by_accession.return_value = SimpleNamespace(genes=genes)
        result = ncbi_translate_gene_ids(["NM_000546", "NM_UNKNOWN"],
                                         "refseq_accession", "symbol", return_dict=True)
    assert result == {"NM_000546": "TP53"}


def test_ncbi_accession_keeps_multiple_queries_for_same_gene():
    gene = SimpleNamespace(symbol="TP53", transcripts=[SimpleNamespace(
        accession_version="NM_000546.6", protein={"accession_version": "NP_000537.3"}
    )])
    ids = ["NM_000546", "NM_000546.6", "NP_000537.3"]
    with patch("biodbs.fetch.NCBI.funcs.NCBI_Fetcher") as cls:
        cls.return_value.get_genes_by_accession.return_value = SimpleNamespace(genes=[gene])
        result = ncbi_translate_gene_ids(ids, "refseq_accession", "symbol", return_dict=True)
    assert result == dict.fromkeys(ids, "TP53")


@pytest.mark.parametrize("missing", [None, float("nan"), pd.NA, ""])
def test_biomart_dict_omits_missing_ids(missing):
    data = Mock()
    data.as_dataframe.return_value = pd.DataFrame([
        {"symbol": "TP53", "gene_id": "7157"},
        {"symbol": "MISSING", "gene_id": missing},
        {"symbol": missing, "gene_id": "123"},
    ])
    with patch("biodbs._funcs.translate.genes.biomart_convert_ids", return_value=data):
        result = _translate_via_biomart(["TP53", "MISSING"], "symbol", "gene_id", "human", True)
    assert result == {"TP53": "7157"}


def test_multiple_gene_targets_keep_missing_columns_and_duplicate_input_rows():
    with patch("biodbs._funcs.translate.genes._translate_via_ncbi", return_value={"TP53": "7157"}):
        result = translate_gene_ids(["TP53", "MISSING", "TP53"], "gene_symbol", ["entrez_id"])
    assert result.symbol.tolist() == ["TP53", "MISSING", "TP53"]
    assert result.gene_id.iloc[0] == "7157"
    assert pd.isna(result.gene_id.iloc[1])


def test_multiple_protein_targets_keep_missing_columns_and_duplicate_input_rows():
    ids = ["P04637", "MISSING", "P04637"]
    with patch("biodbs._funcs.translate.proteins.uniprot_map_ids",
               return_value={"P04637": ["7157"]}) as mapping:
        result = translate_protein_ids(ids, "UniProtKB_AC-ID", ["GeneID"])
    mapping.assert_called_once_with(["P04637", "MISSING"], from_db="UniProtKB_AC-ID", to_db="GeneID")
    assert result["from"].tolist() == ids
    assert result.GeneID.iloc[0] == "7157"
    assert pd.isna(result.GeneID.iloc[1])


@pytest.mark.parametrize("return_dict", [False, True])
def test_ensembl_symbol_normalization_keeps_original_query_keys(return_dict):
    with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs_symbol", return_value=SimpleNamespace(
        results=[{"id": "ENSG00000141510", "type": "gene"}]
    )), patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs", return_value=SimpleNamespace(
        results=[{"dbname": "HGNC", "display_id": "TP53"}]
    )):
        result = translate_gene_ids(["p53", "p53"], "gene_symbol", "gene_symbol",
                                    database="ensembl", return_dict=return_dict)
    if return_dict:
        assert result == {"p53": "TP53"}
    else:
        assert result.HGNC.tolist() == ["TP53", "TP53"]


def test_repeated_ensembl_inputs_need_one_xref_request():
    ids = ["ENSG00000141510"] * 1000
    with patch("biodbs.fetch.ensembl.funcs.ensembl_get_xrefs", return_value=SimpleNamespace(
        results=[{"dbname": "EntrezGene", "primary_id": "7157"}]
    )) as xref:
        result = translate_gene_ids(ids, "ensembl_gene_id", "entrez_id", database="ensembl")
    assert xref.call_count == 1
    assert result.EntrezGene.tolist() == ["7157"] * 1000


def test_ncbi_refseq_protein_does_not_return_mrna():
    gene = SimpleNamespace(transcripts=[SimpleNamespace(
        accession_version="NM_000546.6", protein={"accession_version": "NP_000537.3"}
    )], symbol="TP53")
    with patch("biodbs.fetch.NCBI.funcs.NCBI_Fetcher") as cls:
        cls.return_value.get_genes_by_symbol.return_value = SimpleNamespace(genes=[gene])
        result = translate_gene_ids(["TP53"], "gene_symbol", "refseq_protein", return_dict=True)
    assert result == {"TP53": "NP_000537.3"}


@pytest.mark.parametrize("from_type,to_type", [
    ("gene_symbol", "refseq_protein"), ("refseq_protein", "gene_symbol"),
])
def test_hgnc_rejects_protein_namespace_instead_of_using_mrna(from_type, to_type):
    with pytest.raises(ValueError, match="refseq_protein"):
        translate_gene_ids(["TP53"], from_type, to_type, database="hgnc")


@pytest.mark.parametrize("targets", ["cid", ["cid", "formula"]])
def test_empty_chemical_dict(targets):
    assert translate_chemical_ids([], "name", targets, return_dict=True) == {}


@pytest.mark.parametrize("targets", ["formula", ["formula"]])
def test_chemical_dict_keeps_original_string_cid_keys(targets):
    with patch("biodbs._funcs.translate.chem.pubchem_get_properties",
               return_value=SimpleNamespace(results=[{"MolecularFormula": "C9H8O4"}])):
        result = translate_chemical_ids(["2244"], "cid", targets, return_dict=True)
    expected = "C9H8O4" if isinstance(targets, str) else {"formula": "C9H8O4"}
    assert result == {"2244": expected}


def test_chemical_name_normalization_preserves_input_dict_key():
    with patch("biodbs._funcs.translate.chem.pubchem_search_by_name",
               return_value=SimpleNamespace(get_cids=lambda: [2244])), \
         patch("biodbs._funcs.translate.chem.pubchem_get_properties",
               return_value=SimpleNamespace(results=[{"IUPACName": "2-acetyloxybenzoic acid"}])):
        assert translate_chemical_ids(["aspirin"], "name", "name", return_dict=True) == {
            "aspirin": "2-acetyloxybenzoic acid"
        }


def test_chemical_dict_uses_none_not_nan_for_mixed_missing_results():
    with patch("biodbs._funcs.translate.chem.pubchem_search_by_name", side_effect=lambda name:
               SimpleNamespace(get_cids=lambda: [2244] if name == "aspirin" else [])):
        result = translate_chemical_ids(["aspirin", "MISSING"], "name", ["cid"], return_dict=True)
    assert result == {"aspirin": {"cid": 2244}, "MISSING": {"cid": None}}
    assert type(result["aspirin"]["cid"]) is int


@pytest.mark.parametrize("method,ids", [
    ("get_genes_by_id", [7157, 1956]),
    ("get_genes_by_symbol", ["TP53", "EGFR"]),
    ("get_genes_by_accession", ["NM_000546", "NM_005228"]),
])
def test_ncbi_explicit_id_fetches_read_every_page(method, ids):
    fetcher = NCBI_Fetcher()
    first = {"reports": [{"gene": {"gene_id": 7157, "symbol": "TP53"}}],
             "total_count": 2, "next_page_token": "next", "warnings": ["first"]}
    second = {"reports": [{"gene": {"gene_id": 1956, "symbol": "EGFR"}}], "total_count": 2}
    with patch.object(fetcher, "_make_request", side_effect=[first, second]) as request:
        result = getattr(fetcher, method)(ids, page_size=1)
    assert [gene.gene_id for gene in result.genes] == [7157, 1956]
    assert result.total_count == 2
    assert result.next_page_token is None
    assert result.query_ids == ids
    assert result.warnings == ["first"]
    assert request.call_count == 2
    assert "page_token" not in request.call_args_list[0].kwargs["params"]
    assert request.call_args_list[1].kwargs["params"]["page_token"] == "next"


def test_ncbi_repeated_page_token_fails_instead_of_looping():
    fetcher = NCBI_Fetcher()
    with patch.object(fetcher, "_make_request", return_value={"reports": [], "next_page_token": "same"}):
        with pytest.raises(ConnectionError, match="repeated"):
            fetcher.get_genes_by_id([7157])


@pytest.mark.parametrize("key", [None, "OTHER-STRUCTURE"])
def test_chembl_search_hit_requires_matching_structure(key):
    with patch("biodbs._funcs.translate.chem.pubchem_get_properties",
               return_value=SimpleNamespace(results=[{"InChIKey": "ASPIRIN-KEY"}])), \
         patch("biodbs._funcs.translate.chem.chembl_search_molecules", return_value=SimpleNamespace(
             results=[{"molecule_chembl_id": "CHEMBL_WRONG",
                       "molecule_structures": {"standard_inchi_key": key}}]
         )):
        assert translate_pubchem_to_chembl([2244], return_dict=True) == {2244: None}


def test_chembl_pubchem_cross_reference_is_not_used_as_a_compound_id():
    with patch("biodbs._funcs.translate.chem.chembl_get_molecule", return_value=SimpleNamespace(
        results=[{"cross_references": [{"xref_src": "PubChem", "xref_id": "999999"}],
                  "molecule_structures": {"standard_inchi_key": "ASPIRIN-KEY"}}]
    )), patch("biodbs._funcs.translate.chem.pubchem_search_by_inchikey",
              return_value=SimpleNamespace(get_cids=lambda: [2244])):
        assert translate_chembl_to_pubchem(["CHEMBL25"], return_dict=True) == {"CHEMBL25": 2244}


def _response(payload, status=200, headers=None):
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    response.json = Mock(return_value=payload)
    return response


def test_uniprot_mapping_reads_all_pages_and_keeps_unmapped_inputs():
    first = _response({"results": [{"from": "P04637", "to": "7157"}]}, headers={
        "Link": '<https://rest.uniprot.org/idmapping/results/job?cursor=next>; rel="next"',
    })
    second = _response({"results": [{"from": "P00533", "to": "1956"},
                                    {"from": "P04637", "to": "7157"}]})
    with patch("biodbs.fetch.uniprot.uniprot_fetcher.request_with_retry",
               side_effect=[_response({"jobId": "job"}), first, second]) as request, \
         patch("requests.get", return_value=_response({}, 303, {
             "Location": "https://rest.uniprot.org/idmapping/results/job",
         })):
        result = UniProt_Fetcher().map_ids(["P04637", "P00533", "MISSING"], to_db="GeneID")
    assert result == {"P04637": ["7157"], "P00533": ["1956"], "MISSING": []}
    assert request.call_count == 3


@pytest.mark.integration
@pytest.mark.parametrize("database,species,symbol,expected", [
    ("ncbi", "human", "TP53", "7157"),
    ("ncbi", "human", "BRCA1", "672"),
    ("ncbi", "human", "EGFR", "1956"),
    ("ncbi", "mouse", "Trp53", "22059"),
    ("hgnc", "human", "TP53", "7157"),
    ("ensembl", "human", "TP53", "7157"),
    ("uniprot", "human", "TP53", "7157"),
])
def test_live_gene_reference_ids(database, species, symbol, expected):
    result = translate_gene_ids([symbol], "gene_symbol", "entrez_id",
                                species=species, database=database, return_dict=True)
    assert result == {symbol: expected}


@pytest.mark.integration
def test_live_uniprot_refseq_protein_namespace():
    result = translate_uniprot_to_refseq(["P04637"])
    assert "NP_000537" in {accession.split(".")[0] for accession in result["P04637"]}


@pytest.mark.integration
def test_live_ncbi_explicit_gene_ids_read_every_page():
    result = NCBI_Fetcher().get_genes_by_id([7157, 1956], page_size=1)
    assert {gene.gene_id for gene in result.genes} == {7157, 1956}
    assert result.next_page_token is None


@pytest.mark.integration
def test_live_ncbi_refseq_inputs_keep_query_association():
    result = translate_gene_ids(["NM_000546", "NM_007294"], "refseq_mrna", "gene_symbol", return_dict=True)
    assert result == {"NM_000546": "TP53", "NM_007294": "BRCA1"}


@pytest.mark.integration
def test_live_aspirin_chembl_pubchem_round_trip():
    assert translate_chembl_to_pubchem(["CHEMBL25"], return_dict=True) == {"CHEMBL25": 2244}
    assert translate_pubchem_to_chembl([2244], return_dict=True) == {2244: "CHEMBL25"}


@pytest.mark.integration
@pytest.mark.parametrize("name,cid,formula,key", [
    ("aspirin", 2244, "C9H8O4", "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"),
    ("caffeine", 2519, "C8H10N4O2", "RYYVLZVUVIJVGH-UHFFFAOYSA-N"),
])
def test_live_chemical_reference_ids(name, cid, formula, key):
    result = translate_chemical_ids([name], "name", ["cid", "formula", "inchikey"], return_dict=True)
    assert result == {name: {"cid": cid, "formula": formula, "inchikey": key}}
