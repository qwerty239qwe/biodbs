from biodbs.fetch.NCBI import NCBI_Fetcher


class _Resp:
    status_code = 200

    def __init__(self, idlist):
        self._idlist = idlist

    def json(self):
        return {"esearchresult": {"idlist": self._idlist}}


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
