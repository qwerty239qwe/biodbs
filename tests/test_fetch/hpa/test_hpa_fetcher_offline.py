"""Offline tests for Human Protein Atlas fetcher behavior."""

import gzip
import json

import pytest

from biodbs.data.HPA.data import HPAFetchedData
from biodbs.fetch.HPA.hpa_fetcher import HPA_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text="", content=b""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.content = content

    def json(self):
        return self._json_data

    def iter_content(self, chunk_size=8192):
        yield self.content


def test_hpa_get_gene_json_tsv_and_404(monkeypatch):
    def fake_json_get(url, headers=None):
        return DummyResponse(json_data={"Gene": "TP53", "Ensembl": "ENSG00000141510"})

    monkeypatch.setattr("biodbs.fetch.HPA.hpa_fetcher.requests.get", fake_json_get)
    data = HPA_Fetcher().get_gene("ENSG00000141510")
    assert data.results[0]["Gene"] == "TP53"

    monkeypatch.setattr(
        "biodbs.fetch.HPA.hpa_fetcher.requests.get",
        lambda url, headers=None: DummyResponse(text="Gene\tEnsembl\nTP53\tENSG\n"),
    )
    tsv = HPA_Fetcher().get_gene("ENSG00000141510", format="tsv")
    assert tsv.results[0]["Gene"] == "TP53"

    monkeypatch.setattr(
        "biodbs.fetch.HPA.hpa_fetcher.requests.get",
        lambda url, headers=None: DummyResponse(status_code=404),
    )
    assert HPA_Fetcher().get_gene("ENSG00000000000").results == []


def test_hpa_search_and_search_download_handle_compressed_json(monkeypatch):
    payload = gzip.compress(json.dumps([{"Gene": "TP53"}]).encode())

    monkeypatch.setattr(
        "biodbs.fetch.HPA.hpa_fetcher.requests.get",
        lambda url, params=None, headers=None: DummyResponse(content=payload),
    )

    assert HPA_Fetcher().search("TP53", compress="yes").results == [{"Gene": "TP53"}]
    assert HPA_Fetcher().search_download("TP53", compress="yes").results == [{"Gene": "TP53"}]


def test_hpa_search_download_raises_helpful_bad_request(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.HPA.hpa_fetcher.requests.get",
        lambda url, params=None, headers=None: DummyResponse(status_code=400, text="too broad"),
    )

    with pytest.raises(ValueError, match="too broad"):
        HPA_Fetcher().search_download("protein", columns=["g"])


def test_hpa_get_genes_combines_and_ignores_failed_remaining(monkeypatch):
    fetcher = HPA_Fetcher()

    monkeypatch.setattr(
        fetcher,
        "get_gene",
        lambda ensembl_id, format="json": HPAFetchedData([{"Ensembl": ensembl_id}], format=format),
    )
    monkeypatch.setattr(
        fetcher,
        "schedule_process",
        lambda **kwargs: [HPAFetchedData([{"Ensembl": "ENSG2"}]), RuntimeError("failed")],
    )

    data = fetcher.get_genes(["ENSG1", "ENSG2", "ENSG3"])
    assert [row["Ensembl"] for row in data.results] == ["ENSG1", "ENSG2"]


def test_hpa_get_all_concat_and_stream(monkeypatch, tmp_path):
    fetcher = HPA_Fetcher()
    result = HPAFetchedData([{"Gene": "TP53"}], query_type="search_download")
    monkeypatch.setattr(fetcher, "search_download", lambda **kwargs: result)

    assert fetcher.get_all("TP53").results == [{"Gene": "TP53"}]
    with pytest.raises(ValueError, match="stream_to_storage"):
        fetcher.get_all("TP53", method="stream_to_storage")

    streaming = HPA_Fetcher(storage_path=tmp_path)
    monkeypatch.setattr(streaming, "search_download", lambda **kwargs: result)
    path = streaming.get_all("TP53", method="stream_to_storage")
    assert path.name == "hpa_TP53.jsonl"
    assert path.exists()


def test_hpa_convenience_methods_delegate_expected_columns(monkeypatch):
    fetcher = HPA_Fetcher()
    calls = []

    def fake_search_download(search, columns=None, format="json", compress="no"):
        calls.append((search, columns, format, compress))
        return HPAFetchedData([{"Gene": search}], query_type="search_download")

    monkeypatch.setattr(fetcher, "search_download", fake_search_download)

    fetcher.get_expression("TP53")
    fetcher.get_subcellular_location("TP53")
    fetcher.get_pathology("TP53")
    fetcher.get_protein_class("TP53")
    fetcher.get_tissue_expression("TP53", tissues=["rna_liver"])
    fetcher.get_blood_expression("TP53")
    fetcher.get_brain_expression("TP53")

    assert len(calls) == 7
    assert "rna_liver" in calls[4][1]
    assert HPA_Fetcher.list_columns()


def test_hpa_download_bulk_data_uses_output_path(monkeypatch, tmp_path):
    output = tmp_path / "proteinatlas.json.gz"
    monkeypatch.setattr(
        "biodbs.fetch.HPA.hpa_fetcher.requests.get",
        lambda url, stream=False: DummyResponse(content=b"bulk-data"),
    )

    path = HPA_Fetcher().download_bulk_data(file_type="json", output_path=str(output))
    assert path == output
    assert output.read_bytes() == b"bulk-data"

    with pytest.raises(ValueError, match="output_path required"):
        HPA_Fetcher().download_bulk_data(file_type="json")
