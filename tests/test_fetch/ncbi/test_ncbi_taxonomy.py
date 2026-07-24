import pytest

from biodbs.exceptions import APIError
from biodbs.fetch.NCBI import NCBI_Fetcher


class _Resp:
    status_code = 200

    def __init__(self, idlist):
        self._idlist = idlist

    def json(self):
        return {"esearchresult": {"idlist": self._idlist}}


class _ErrorResp:
    """Fake response with a non-200 status, shaped for raise_for_status."""

    status_code = 500
    text = "Internal Server Error"
    headers = {}

    def json(self):
        return {}


def test_taxonomy_name_to_id_maps_resolved_names(monkeypatch):
    calls = []

    def fake_request(url=None, method="GET", params=None, **kwargs):
        calls.append(params["term"])
        idlist = ["562"] if "Escherichia coli" in params["term"] else []
        return _Resp(idlist)

    monkeypatch.setattr("biodbs.fetch.NCBI.ncbi_fetcher.request_with_retry", fake_request)

    result = NCBI_Fetcher().taxonomy_name_to_id(["Escherichia coli", "Not A Taxon"])

    assert result == {"Escherichia coli": 562}
    assert any("Escherichia coli" in term for term in calls)


def test_taxonomy_name_to_id_raises_on_non_200(monkeypatch):
    def fake_request(url=None, method="GET", params=None, **kwargs):
        return _ErrorResp()

    monkeypatch.setattr("biodbs.fetch.NCBI.ncbi_fetcher.request_with_retry", fake_request)

    with pytest.raises(APIError):
        NCBI_Fetcher().taxonomy_name_to_id(["Escherichia coli"])


def test_taxonomy_name_to_id_includes_api_key_param(monkeypatch):
    captured_params = []

    def fake_request(url=None, method="GET", params=None, **kwargs):
        captured_params.append(params)
        return _Resp(["562"])

    monkeypatch.setattr("biodbs.fetch.NCBI.ncbi_fetcher.request_with_retry", fake_request)

    NCBI_Fetcher(api_key="KEY").taxonomy_name_to_id(["Escherichia coli"])
    assert captured_params[-1]["api_key"] == "KEY"

    captured_params.clear()
    # NCBI_APIConfig falls back to os.environ["NCBI_API_KEY"]; clear it so the
    # no-key assertion is hermetic regardless of the developer/CI environment.
    monkeypatch.delenv("NCBI_API_KEY", raising=False)
    NCBI_Fetcher().taxonomy_name_to_id(["Escherichia coli"])
    assert "api_key" not in captured_params[-1]
