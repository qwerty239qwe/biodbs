import pytest
from biodbs import BioMart


@pytest.fixture
def mart_df():
    srv = BioMart.Server()
    mart_df = srv.list_marts()
    yield mart_df


@pytest.fixture
def mart():
    mart = BioMart.Mart()
    yield mart


@pytest.fixture
def dataset_df(mart):
    dataset_df = mart.list_datasets()
    yield dataset_df


@pytest.fixture
def dataset(mart):
    ds = BioMart.Dataset()
    yield ds


def test_mart_df(mart_df):
    assert "name" in mart_df.columns
    assert "displayName" in mart_df.columns
    assert "host" in mart_df.columns


def test_get_data(dataset):
    df = dataset.get_data(attribs=["ensembl_gene_id",
                                   "ensembl_transcript_id",
                                   "hgnc_symbol",
                                   "uniprotswissprot"],
                          ensembl_gene_id=["ENSG00000139618",
                                           "ENSG00000272104"])
    assert df.columns.to_list() == ["ensembl_gene_id",
                                    "ensembl_transcript_id",
                                    "hgnc_symbol",
                                    "uniprotswissprot"]

@pytest.mark.parametrize("attribs,filters", [
    (["wrong_attr"], {"ensembl_gene_id": "ENSG00000139618"}),
    (["ensembl_gene_id",
      "ensembl_transcript_id",
      "hgnc_symbol",
      "uniprotswissprot"], {"wrong_filter": "ENSG00000139618"})
])
@pytest.mark.xfail(strict=True)
def test_get_data_failing_case(dataset, attribs, filters):
    df = dataset.get_data(attribs=attribs, filter_dict=filters)
