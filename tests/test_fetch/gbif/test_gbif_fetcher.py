from biodbs.fetch.GBIF.gbif_fetcher import GBIF_Fetcher


class DummyResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload
        self.headers = {"content-type": "application/json"}

    def json(self):
        return self._payload


ECOLI = {
    "usageKey": 11286021,
    "canonicalName": "Escherichia coli",
    "rank": "SPECIES",
    "status": "ACCEPTED",
    "matchType": "EXACT",
    "confidence": 98,
    "synonym": False,
}


def test_match_name_parses_backbone_fields(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GBIF.gbif_fetcher.request_with_retry",
        lambda url, **kwargs: DummyResponse(ECOLI),
    )

    match = GBIF_Fetcher().match_name("Escherichia coli")

    assert match.query == "Escherichia coli"
    assert match.usage_key == 11286021
    assert match.canonical_name == "Escherichia coli"
    assert match.rank == "SPECIES"
    assert match.status == "ACCEPTED"
    assert match.match_type == "EXACT"
    assert match.is_synonym is False


def test_match_name_handles_no_match(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GBIF.gbif_fetcher.request_with_retry",
        lambda url, **kwargs: DummyResponse({"matchType": "NONE", "confidence": 0, "synonym": False}),
    )

    match = GBIF_Fetcher().match_name("Nonexistent taxon")

    assert match.match_type == "NONE"
    assert match.usage_key is None
    assert match.canonical_name is None


def test_match_names_returns_list(monkeypatch):
    monkeypatch.setattr(
        "biodbs.fetch.GBIF.gbif_fetcher.request_with_retry",
        lambda url, **kwargs: DummyResponse(ECOLI),
    )

    data = GBIF_Fetcher().match_names(["Escherichia coli", "Escherichia coli"])

    assert len(data) == 2
    assert data["Escherichia coli"].canonical_name == "Escherichia coli"
