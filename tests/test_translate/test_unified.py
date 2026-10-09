"""Offline routing and compatibility checks for unified translators."""

from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

import biodbs
from biodbs import translate
from biodbs._funcs.translate import chem, genes, proteins
from biodbs.translate import ChemicalMapper, GeneMapper, ProteinMapper, TranslationDatabase


KEY = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"


@pytest.fixture
def chemical_services(monkeypatch):
    molecule = SimpleNamespace(results=[{
        "molecule_chembl_id": "CHEMBL25",
        "molecule_structures": {"standard_inchi_key": KEY},
    }])
    lookup = Mock(return_value=molecule)
    search = Mock(return_value=SimpleNamespace(get_cids=lambda: [2244]))
    properties = Mock(return_value=SimpleNamespace(results=[{
        "CID": 2244, "InChIKey": KEY, "MolecularFormula": "C9H8O4",
    }]))
    chembl_search = Mock(return_value=molecule)
    monkeypatch.setattr(chem, "chembl_get_molecule", lookup)
    monkeypatch.setattr(chem, "pubchem_search_by_inchikey", search)
    monkeypatch.setattr(chem, "pubchem_get_properties", properties)
    monkeypatch.setattr(chem, "chembl_search_molecules", chembl_search)
    return lookup, search, properties, chembl_search


@pytest.mark.parametrize("mapper_type", [GeneMapper, ChemicalMapper, ProteinMapper])
def test_mapper_exports(mapper_type):
    assert getattr(biodbs, mapper_type.__name__) is mapper_type
    assert getattr(translate, mapper_type.__name__) is mapper_type
    assert mapper_type.__name__ in biodbs.__all__
    assert mapper_type.__name__ in translate.__all__


def test_default_gene_mapper_preserves_ncbi_human_dispatch(monkeypatch):
    fetch = Mock(return_value={"TP53": "7157"})
    monkeypatch.setattr("biodbs.fetch.NCBI.funcs.ncbi_translate_gene_ids", fetch)
    for kwargs in ({}, {"mapper": GeneMapper()}):
        assert genes.translate_gene_ids(["TP53"], "gene_symbol", "entrez_id", return_dict=True, **kwargs) == {"TP53": "7157"}
    assert fetch.call_count == 2
    fetch.assert_called_with(["TP53"], from_type="symbol", to_type="gene_id", taxon="human", return_dict=True)


def test_gene_mapper_respects_backend_and_species(monkeypatch):
    fetch = Mock(return_value={"Trp53": "22059"})
    monkeypatch.setattr(genes, "_translate_via_biomart", fetch)
    mapper = GeneMapper(database="biomart", species="mouse")
    assert genes.translate_gene_ids(["Trp53"], "gene_symbol", "entrez_id", mapper=mapper, return_dict=True) == {"Trp53": "22059"}
    fetch.assert_called_once_with(["Trp53"], "external_gene_name", "entrezgene_id", "mouse", True)


@pytest.mark.parametrize("kwargs", [{"database": "ncbi"}, {"species": "human"}])
def test_gene_mapper_rejects_explicit_conflicts(kwargs):
    with pytest.raises(ValueError, match="conflicts"):
        genes.translate_gene_ids([], "gene_symbol", "entrez_id", mapper=GeneMapper("hgnc", "mouse"), **kwargs)


@pytest.mark.parametrize("kwargs", [{"organism": 9606}, {"reviewed_only": True}])
def test_protein_mapper_rejects_explicit_conflicts(kwargs):
    with pytest.raises(ValueError, match="conflicts"):
        proteins.translate_protein_ids([], "Gene_Name", "UniProtKB", mapper=ProteinMapper(10090, False), **kwargs)


def test_chemical_mapper_rejects_explicit_backend_conflict():
    with pytest.raises(ValueError, match="conflicts"):
        chem.translate_chemical_ids([], "chembl_id", "cid", mapper=ChemicalMapper("chembl"), database="pubchem")


@pytest.mark.parametrize("function,args,mapper", [
    (genes.translate_gene_ids, ([], "symbol", "gene_id"), ChemicalMapper()),
    (chem.translate_chemical_ids, ([], "name", "cid"), ProteinMapper()),
    (proteins.translate_protein_ids, ([], "Gene_Name", "UniProtKB"), GeneMapper()),
])
def test_wrong_mapper_domain_is_rejected(function, args, mapper):
    with pytest.raises(TypeError, match="mapper must be"):
        function(*args, mapper=mapper)


def test_chembl_to_pubchem_is_unified_and_deduplicated(chemical_services):
    lookup, search, properties, _ = chemical_services
    result = chem.translate_chemical_ids(["CHEMBL25", "CHEMBL25"], "chembl_id", "cid")
    assert result.to_dict("list") == {"chembl_id": ["CHEMBL25", "CHEMBL25"], "cid": [2244, 2244]}
    lookup.assert_called_once_with("CHEMBL25")
    search.assert_called_once_with(KEY)
    properties.assert_not_called()


def test_cross_database_multiple_targets_share_properties(chemical_services):
    _, _, properties, chembl_search = chemical_services
    result = chem.translate_chemical_ids(
        ["CHEMBL25", "CHEMBL25"], "chembl_id", ["cid", "formula", "chembl_id"], return_dict=True
    )
    assert result == {"CHEMBL25": {"cid": 2244, "formula": "C9H8O4", "chembl_id": "CHEMBL25"}}
    properties.assert_called_once_with(2244, properties=["MolecularFormula", "InChIKey"])
    chembl_search.assert_called_once_with(KEY, limit=1)


@pytest.mark.parametrize("return_dict", [False, True])
def test_chemical_wrappers_keep_legacy_outputs(chemical_services, return_dict):
    forward = chem.translate_chembl_to_pubchem(["CHEMBL25", "CHEMBL25"], return_dict)
    reverse = chem.translate_pubchem_to_chembl(["2244", "2244"], return_dict)
    if return_dict:
        assert forward == {"CHEMBL25": 2244}
        assert reverse == {"2244": "CHEMBL25"}
    else:
        pd.testing.assert_frame_equal(forward, pd.DataFrame({"chembl_id": ["CHEMBL25"] * 2, "pubchem_cid": [2244] * 2}))
        pd.testing.assert_frame_equal(reverse, pd.DataFrame({"pubchem_cid": ["2244"] * 2, "chembl_id": ["CHEMBL25"] * 2}))


@pytest.mark.parametrize("wrapper,columns", [
    (chem.translate_chembl_to_pubchem, ["chembl_id", "pubchem_cid"]),
    (chem.translate_pubchem_to_chembl, ["pubchem_cid", "chembl_id"]),
])
def test_chemical_wrapper_empty_schema(wrapper, columns, chemical_services):
    assert list(wrapper([]).columns) == columns
    assert wrapper([], True) == {}
    for service in chemical_services:
        service.assert_not_called()


def test_unified_reverse_mapping_rejects_wrong_structure(chemical_services):
    chemical_services[3].return_value = SimpleNamespace(results=[{
        "molecule_chembl_id": "CHEMBL_WRONG", "molecule_structures": {"standard_inchi_key": "WRONG"},
    }])
    assert chem.translate_chemical_ids([2244], "cid", "chembl_id", True) == {2244: None}


def test_missing_chembl_structure_is_not_a_cid(chemical_services):
    chemical_services[0].return_value = SimpleNamespace(results=[{
        "cross_references": [{"xref_src": "PubChem", "xref_id": "123"}], "molecule_structures": None,
    }])
    assert chem.translate_chemical_ids(["CHEMBL25"], "chembl_id", "cid", True) == {"CHEMBL25": None}
    chemical_services[1].assert_not_called()


@pytest.mark.parametrize("module,ids,source,target,native_source,native_target", [
    (chem, ["cpd:C00022"], "kegg_compound", "pubchem_sid", "compound", "pubchem"),
    (genes, ["hsa:7157"], "kegg_gene", "entrez_id", "hsa", "ncbi-geneid"),
])
def test_kegg_main_and_legacy_share_conversion(module, ids, source, target, native_source, native_target, monkeypatch):
    expected = pd.DataFrame({"source_id": ids, "target_id": [native_target + ":123"]})
    convert = Mock(return_value=SimpleNamespace(as_dataframe=lambda: expected.copy()))
    monkeypatch.setattr(module, "kegg_conv", convert)
    main = module.translate_chemical_ids if module is chem else module.translate_gene_ids
    legacy = module.translate_chemical_ids_kegg if module is chem else module.translate_gene_ids_kegg
    pd.testing.assert_frame_equal(main(ids, source, target, database="kegg"), expected)
    pd.testing.assert_frame_equal(legacy(ids, native_source, native_target), expected)
    convert.assert_called_with(target_db=native_target, source=ids)
    convert.reset_mock()
    empty = main([], source, target, database="kegg")
    assert list(empty.columns) == ["source_id", "target_id"]
    assert empty.empty
    convert.assert_not_called()
    main([], source, target, database="kegg", bulk=True)
    convert.assert_called_once_with(target_db=native_target, source=native_source)
    convert.reset_mock()
    legacy([], native_source, native_target)
    convert.assert_called_once_with(target_db=native_target, source=native_source)


def test_kegg_scalar_dict_selects_first_hit_without_dropping_dataframe_rows(monkeypatch):
    frame = pd.DataFrame({"source_id": ["cpd:C00022"] * 2, "target_id": ["pubchem:1", "pubchem:2"]})
    monkeypatch.setattr(chem, "kegg_conv", Mock(return_value=SimpleNamespace(as_dataframe=lambda: frame)))
    assert chem.translate_chemical_ids(["cpd:C00022"], "kegg_compound", "pubchem_sid", True) == {"cpd:C00022": "pubchem:1"}
    assert len(chem.translate_chemical_ids(["cpd:C00022"], "kegg_compound", "pubchem_sid")) == 2


@pytest.mark.parametrize("source,target", [("kegg_compound", "cid"), ("cid", "kegg_compound"), ("chembl_id", "pubchem_sid")])
def test_kegg_never_confuses_cid_with_sid(source, target, monkeypatch):
    convert = Mock()
    monkeypatch.setattr(chem, "kegg_conv", convert)
    with pytest.raises(ValueError, match="Unsupported KEGG"):
        chem.translate_chemical_ids(["123"], source, target, database="kegg")
    convert.assert_not_called()


@pytest.mark.parametrize("database", ["pubchem", "unknown"])
def test_explicit_chemical_backend_does_not_silently_fallback(database, chemical_services):
    with pytest.raises(ValueError):
        chem.translate_chemical_ids(["CHEMBL25"], "chembl_id", "cid", database=database)
    for service in chemical_services:
        service.assert_not_called()


def test_gene_kegg_enum_and_mouse_mapper(monkeypatch):
    frame = pd.DataFrame({"source_id": ["mmu:22059"], "target_id": ["ncbi-geneid:22059"]})
    convert = Mock(return_value=SimpleNamespace(as_dataframe=lambda: frame))
    monkeypatch.setattr(genes, "kegg_conv", convert)
    mapper = GeneMapper(TranslationDatabase.KEGG, "mouse")
    pd.testing.assert_frame_equal(genes.translate_gene_ids(["mmu:22059"], "kegg_gene", "entrez_id", mapper=mapper), frame)
    assert mapper.map(["mmu:22059"], "kegg_gene", "entrez_id", True) == {"mmu:22059": "ncbi-geneid:22059"}


def test_invalid_gene_kegg_pair_is_rejected_before_request(monkeypatch):
    convert = Mock()
    monkeypatch.setattr(genes, "kegg_conv", convert)
    with pytest.raises(ValueError, match="requires an organism"):
        genes.translate_gene_ids(["TP53"], "gene_symbol", "entrez_id", database="kegg")
    convert.assert_not_called()


def test_protein_mapper_and_gene_wrapper_preserve_review_filter(monkeypatch):
    fetch = Mock(return_value={"Trp53": "P02340"})
    monkeypatch.setattr(proteins, "gene_to_uniprot", fetch)
    mapper = ProteinMapper(organism=10090, reviewed_only=False)
    assert proteins.translate_protein_ids(["Trp53"], "Gene_Name", "UniProtKB", return_dict=True, mapper=mapper) == {"Trp53": "P02340"}
    fetch.assert_called_with(["Trp53"], organism=10090, reviewed_only=False)
    assert proteins.translate_gene_to_uniprot(["Trp53"], 10090, False) == {"Trp53": "P02340"}
    fetch.assert_called_with(["Trp53"], organism=10090, reviewed_only=False)


@pytest.mark.parametrize("wrapper,target,column,all_matches", [
    (proteins.translate_uniprot_to_pdb, "PDB", "pdb_id", True),
    (proteins.translate_uniprot_to_refseq, "RefSeq_Protein", "refseq_id", True),
    (proteins.translate_uniprot_to_ensembl, "Ensembl", "ensembl_id", False),
])
def test_protein_wrappers_keep_scalar_list_and_dataframe_contracts(wrapper, target, column, all_matches, monkeypatch):
    mapping = {"P04637": ["first", "second"], "missing": []}
    fetch = Mock(return_value=mapping)
    monkeypatch.setattr(proteins, "uniprot_map_ids", fetch)
    expected = mapping if all_matches else {"P04637": "first", "missing": None}
    assert wrapper(["P04637", "missing"]) == expected
    frame = wrapper(["P04637", "missing"], False)
    assert list(frame.columns) == ["uniprot_accession", column]
    assert frame[column].tolist() == (["first", "second", None] if all_matches else ["first", None])
    assert proteins.translate_protein_ids(["P04637", "missing"], "UniProtKB_AC-ID", target, return_dict=True, all_matches=all_matches) == expected
    fetch.assert_called_with(["P04637", "missing"], from_db="UniProtKB_AC-ID", to_db=target)


def test_multitarget_protein_all_matches(monkeypatch):
    fetch = Mock(return_value={"P04637": ["first", "second"]})
    monkeypatch.setattr(proteins, "uniprot_map_ids", fetch)
    assert proteins.translate_protein_ids(["P04637"], "UniProtKB_AC-ID", ["PDB", "RefSeq_Protein"], return_dict=True, all_matches=True) == {
        "P04637": {"PDB": ["first", "second"], "RefSeq_Protein": ["first", "second"]},
    }


def test_default_taxon_mapper_uses_online_ncbi_without_taxdump_download(monkeypatch):
    fetcher = Mock()
    fetcher.taxonomy_name_to_id.return_value = {"Escherichia coli": 562}
    constructor = Mock(return_value=fetcher)
    monkeypatch.setattr("biodbs.fetch.NCBI.NCBI_Fetcher", constructor)
    result = translate.translate_taxon_names(["Escherichia coli"])
    assert result.loc[0, "hub_taxid"] == 562
    assert result.loc[0, "match_type"] == "ncbi"
    fetcher.download_taxdump.assert_not_called()


def test_reverse_chemical_properties_are_batched_and_matched_by_cid(monkeypatch):
    properties = Mock(return_value=SimpleNamespace(results=[
        {"CID": 3672, "InChIKey": "KEY2"}, {"CID": 2244, "InChIKey": "KEY1"},
    ]))
    search = Mock(side_effect=lambda key, limit: SimpleNamespace(results=[{
        "molecule_chembl_id": "CHEMBL25" if key == "KEY1" else "CHEMBL521",
        "molecule_structures": {"standard_inchi_key": key},
    }]))
    monkeypatch.setattr(chem, "pubchem_get_properties", properties)
    monkeypatch.setattr(chem, "chembl_search_molecules", search)
    result = chem.translate_pubchem_to_chembl([2244, 3672, 2244])
    assert result["chembl_id"].tolist() == ["CHEMBL25", "CHEMBL521", "CHEMBL25"]
    properties.assert_called_once_with([2244, 3672], properties=["InChIKey"])
    assert search.call_count == 2


def test_reverse_chemical_outage_does_not_fan_out_retries(monkeypatch):
    from biodbs.exceptions import APIServerError

    properties = Mock(side_effect=APIServerError("PubChem unavailable", status_code=503))
    search = Mock()
    monkeypatch.setattr(chem, "pubchem_get_properties", properties)
    monkeypatch.setattr(chem, "chembl_search_molecules", search)
    assert chem.translate_pubchem_to_chembl([2244, 3672], True) == {2244: None, 3672: None}
    properties.assert_called_once()
    search.assert_not_called()


@pytest.mark.parametrize("module,source,target", [
    (chem, "kegg_compound", ["pubchem_sid", "chebi"]),
    (genes, "kegg_gene", ["entrez_id", "uniprot_id"]),
])
def test_kegg_multiple_targets_are_rejected_before_request(module, source, target, monkeypatch):
    convert = Mock()
    monkeypatch.setattr(module, "kegg_conv", convert)
    main = module.translate_chemical_ids if module is chem else module.translate_gene_ids
    with pytest.raises(ValueError, match="single target"):
        main([], source, target, database="kegg", bulk=True)
    convert.assert_not_called()


@pytest.mark.parametrize("module,args", [
    (chem, ([], "name", "cid")), (genes, ([], "gene_symbol", "entrez_id")),
])
def test_bulk_conversion_requires_kegg_backend(module, args):
    main = module.translate_chemical_ids if module is chem else module.translate_gene_ids
    with pytest.raises(ValueError, match="only supported by KEGG"):
        main(*args, bulk=True)


def test_all_matches_does_not_change_multitarget_dataframe_contract(monkeypatch):
    monkeypatch.setattr(proteins, "uniprot_map_ids", Mock(return_value={"P04637": ["first", "second"]}))
    args = (["P04637"], "UniProtKB_AC-ID", ["PDB", "RefSeq_Protein"])
    pd.testing.assert_frame_equal(
        proteins.translate_protein_ids(*args),
        proteins.translate_protein_ids(*args, all_matches=True),
    )
