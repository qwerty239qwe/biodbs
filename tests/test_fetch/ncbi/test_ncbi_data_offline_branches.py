"""Additional branch tests for NCBI data containers."""

import pytest

from biodbs.data.NCBI.data import (
    NCBIDataManager,
    NCBIGeneFetchedData,
    NCBIGenomeFetchedData,
    NCBITaxonomyFetchedData,
)


GENE_REPORTS = [
    {
        "gene": {
            "geneId": 7157,
            "symbol": "TP53",
            "description": "tumor protein p53",
            "taxId": 9606,
            "taxname": "Homo sapiens",
            "commonName": "human",
            "type": "protein-coding",
            "chromosomes": ["17"],
            "synonyms": ["p53"],
            "swissProtAccessions": ["P04637"],
            "ensemblGeneIds": ["ENSG00000141510"],
        }
    },
    {"malformed": object()},
]


def test_ncbi_gene_indexing_flatten_polars_and_manager(tmp_path):
    data = NCBIGeneFetchedData({"reports": GENE_REPORTS, "warnings": ["warn"]}, query_ids=[7157])

    assert len(data) == 1
    assert data[0].symbol == "TP53"
    assert data["TP53"].gene_id == 7157
    assert data["7157"].symbol == "TP53"
    assert [gene.symbol for gene in data] == ["TP53"]
    with pytest.raises(KeyError):
        _ = data["missing"]
    with pytest.raises(TypeError):
        _ = data[object()]

    assert data.as_dict(columns=["symbol"]) == [{"symbol": "TP53"}]
    assert data.as_dataframe(flatten=True).iloc[0]["symbol"] == "TP53"
    assert data.as_dataframe(engine="polars").height == 1
    assert "swiss_prot" in data.show_columns()
    assert data.filter_by_type("other").genes == []
    assert "Warnings: 1" in data.summary()
    assert "query=1 ids" in repr(data)

    empty = NCBIGeneFetchedData("bad")
    assert empty.as_dataframe().empty
    assert empty.as_dataframe(engine="polars").is_empty()

    data += NCBIGeneFetchedData(GENE_REPORTS)
    assert len(data) == 2

    manager = NCBIDataManager(tmp_path)
    assert manager.save_gene_data(data, "genes", fmt="csv", columns=["symbol"]).exists()
    assert manager.save_gene_data(data, "genes", fmt="json").exists()
    assert manager.save_gene_data(data, "genes", fmt="jsonl").exists()
    with pytest.raises(ValueError, match="Cannot save format"):
        manager.save_gene_data(NCBIGeneFetchedData({}), "empty", fmt="csv")


def test_ncbi_taxonomy_legacy_and_empty_branches():
    legacy = NCBITaxonomyFetchedData(
        [{"taxId": 9606, "organismName": "Homo sapiens", "commonName": "human", "rank": "species"}],
        query_taxons=[9606],
    )
    assert len(legacy) == 1
    assert "query=1 ids" in repr(legacy)
    assert legacy.as_dict(columns=["tax_id"]) == [{"tax_id": 9606}]
    assert legacy.as_dataframe(engine="polars").height == 1
    assert legacy.get_taxon(1) is None
    assert legacy.get_taxon_by_name("sapiens").tax_id == 9606
    assert legacy.get_taxon_by_name("missing") is None

    empty = NCBITaxonomyFetchedData("bad")
    assert empty.as_dataframe().empty
    assert empty.as_dataframe(engine="polars").is_empty()


def test_ncbi_genome_columns_polars_and_empty():
    content = [
        {
            "accession": "GCF_000001405.40",
            "organismName": "Homo sapiens",
            "organismTaxId": 9606,
            "assemblyInfo": {"assemblyName": "GRCh38", "assemblyLevel": "Chromosome"},
        },
        {"bad": object()},
    ]
    data = NCBIGenomeFetchedData(content, query_accessions=["GCF_000001405.40"])

    assert len(data) == 1
    assert "query=1 accessions" in repr(data)
    assert data.results[0].accession == "GCF_000001405.40"
    assert data.as_dict(columns=["accession"]) == [{"accession": "GCF_000001405.40"}]
    assert data.as_dataframe(engine="polars").height == 1
    assert data.get_accessions() == ["GCF_000001405.40"]

    empty = NCBIGenomeFetchedData("bad")
    assert empty.as_dataframe().empty
    assert empty.as_dataframe(engine="polars").is_empty()
