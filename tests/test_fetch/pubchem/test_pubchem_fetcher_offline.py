"""Offline tests for PubChem fetcher convenience and batching behavior."""

from biodbs.data.PubChem.data import PUGRestFetchedData, PUGViewFetchedData
from biodbs.fetch.pubchem import PubChem_Fetcher


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, content=b""):
        self.status_code = status_code
        self._json_data = json_data
        self.content = content

    def json(self):
        return self._json_data


def test_pubchem_pug_rest_get_json_binary_and_404(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.pubchem.pubchem_fetcher.request_with_retry",
        lambda url, params=None: DummyResponse(
            json_data={"PC_Compounds": [{"id": {"id": {"cid": 2244}}}]}
        ),
    )
    compound = PubChem_Fetcher().get("compound", "cid", 2244)
    assert compound.results[0]["id"]["id"]["cid"] == 2244

    monkeypatch.setattr(
        "biodbs.fetch.pubchem.pubchem_fetcher.request_with_retry",
        lambda url, params=None: DummyResponse(content=b"PNG"),
    )
    image = PubChem_Fetcher().get("compound", "cid", 2244, output="PNG")
    assert image.binary_data == b"PNG"

    monkeypatch.setattr(
        "biodbs.fetch.pubchem.pubchem_fetcher.request_with_retry",
        lambda url, params=None: DummyResponse(status_code=404),
    )
    assert PubChem_Fetcher().get("compound", "cid", 999999).results == []


def test_pubchem_convenience_methods_delegate_to_get(monkeypatch):
    fetcher = PubChem_Fetcher()
    calls = []

    def fake_get(**kwargs):
        calls.append(kwargs)
        return PUGRestFetchedData({"IdentifierList": {"CID": [2244]}}, domain="compound")

    monkeypatch.setattr(fetcher, "get", fake_get)

    fetcher.get_compound(2244)
    fetcher.get_compounds([2244, 3672])
    fetcher.get_substance(10)
    fetcher.get_assay(20)
    fetcher.search_by_name("aspirin")
    fetcher.search_by_smiles("CCO")
    fetcher.search_by_inchikey("KEY")
    fetcher.search_by_formula("C9H8O4")
    fetcher.get_properties(2244)
    fetcher.get_synonyms(2244)
    fetcher.get_cids_by_name("aspirin")
    fetcher.get_sids_for_compound(2244)
    fetcher.get_aids_for_compound(2244)
    fetcher.similarity_search("CCO", threshold=95, max_records=5)
    fetcher.substructure_search("c1ccccc1", max_records=5)
    fetcher.get_compound_image(2244)
    fetcher.get_compound_sdf(2244)
    fetcher.get_description(2244)

    assert len(calls) == 18
    assert calls[0] == {"domain": "compound", "namespace": "cid", "identifiers": 2244}
    assert calls[8]["operation"] == "property"
    assert calls[13]["namespace"] == "fastsimilarity_2d"
    assert calls[15]["output"] == "PNG"
    assert calls[16]["output"] == "SDF"


def test_pubchem_get_all_batches_and_skips_failed_results(monkeypatch):
    fetcher = PubChem_Fetcher()

    def fake_get(domain, namespace, identifiers, operation=None, properties=None, **kwargs):
        return PUGRestFetchedData(
            {"IdentifierList": {"CID": list(identifiers)}},
            domain=domain,
            operation=operation,
        )

    monkeypatch.setattr(fetcher, "get", fake_get)
    monkeypatch.setattr(
        fetcher,
        "schedule_process",
        lambda **kwargs: [
            PUGRestFetchedData({"IdentifierList": {"CID": [3, 4]}}, domain="compound"),
            RuntimeError("failed"),
        ],
    )

    data = fetcher.get_all("compound", "cid", [1, 2, 3, 4, 5], batch_size=2)
    assert data.get_cids() == [1, 2, 3, 4]


def test_pubchem_get_all_empty_single_and_stream(monkeypatch, tmp_path):
    assert PubChem_Fetcher().get_all("compound", "cid", []).results == []

    single = PubChem_Fetcher()
    monkeypatch.setattr(
        single,
        "get",
        lambda **kwargs: PUGRestFetchedData(
            {"IdentifierList": {"CID": kwargs["identifiers"]}},
            domain="compound",
        ),
    )
    assert single.get_all("compound", "cid", [2244]).get_cids() == [2244]

    streaming = PubChem_Fetcher(storage_path=tmp_path)
    batch = PUGRestFetchedData({"IdentifierList": {"CID": [2244]}}, domain="compound")
    path = streaming._finalise_pubchem("stream_to_storage", [batch], "compound", "cids")
    assert path.name == "pubchem_compound_cids.jsonl"
    assert path.exists()


def test_pubchem_pug_view_fetch_and_wrappers(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.pubchem.pubchem_fetcher.request_with_retry",
        lambda url, params=None: DummyResponse(
            json_data={
                "Record": {
                    "RecordNumber": 2244,
                    "Section": [{"TOCHeading": "Safety and Hazards"}],
                }
            }
        ),
    )

    fetcher = PubChem_Fetcher()
    view = fetcher.get_view(2244, heading="Safety and Hazards")
    assert isinstance(view, PUGViewFetchedData)
    assert view.record_id == 2244

    calls = []

    def fake_view(record_id, record_type="compound", heading=None, output="JSON"):
        calls.append((record_id, record_type, heading, output))
        return PUGViewFetchedData(
            {"Record": {"RecordNumber": record_id}},
            record_type=record_type,
        )

    monkeypatch.setattr(fetcher, "get_view", fake_view)
    fetcher.get_compound_annotations(2244)
    fetcher.get_substance_annotations(10)
    fetcher.get_safety_data(2244)
    fetcher.get_pharmacology(2244)
    fetcher.get_names_and_identifiers(2244)
    fetcher.get_physical_properties(2244)

    assert calls[0] == (2244, "compound", None, "JSON")
    assert calls[1] == (10, "substance", None, "JSON")
    assert {call[2] for call in calls[2:]} == {
        "Safety and Hazards",
        "Pharmacology and Biochemistry",
        "Names and Identifiers",
        "Chemical and Physical Properties",
    }
