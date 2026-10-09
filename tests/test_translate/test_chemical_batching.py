"""Request-count and exact-CID checks for batched chemical translation."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from biodbs._funcs.translate import chem
from biodbs.exceptions import APIError
from biodbs.exceptions import APIRateLimitError, APIServerError, APITimeoutError
from requests.exceptions import RequestException


def properties(cids, properties):
    cids = cids if isinstance(cids, list) else [cids]
    # Intentionally reverse the server's ordering: association must be by CID.
    return SimpleNamespace(results=[{
        "CID": cid, "MolecularFormula": f"formula-{cid}", "ConnectivitySMILES": f"smiles-{cid}",
    } for cid in reversed(cids)])


@pytest.mark.parametrize("multiple", [False, True])
@pytest.mark.parametrize("duplicates,requests", [(False, 10), (True, 1)])
def test_thousand_cids_are_batched_and_duplicates_preserved(monkeypatch, multiple, duplicates, requests):
    fetch = Mock(side_effect=properties)
    monkeypatch.setattr(chem, "pubchem_get_properties", fetch)
    ids = ["2244"] * 1000 if duplicates else [str(i) for i in range(1, 1001)]
    target = ["formula", "smiles", "cid"] if multiple else "formula"
    result = chem.translate_chemical_ids(ids, "cid", target)
    assert fetch.call_count == requests
    assert result["cid"].tolist() == [int(cid) for cid in ids]
    assert result["formula"].tolist() == [f"formula-{cid}" for cid in ids]
    if multiple:
        assert result["smiles"].tolist() == [f"smiles-{cid}" for cid in ids]
    assert all(len(call.args[0]) <= 100 if isinstance(call.args[0], list) else True
               for call in fetch.call_args_list)


def test_duplicate_names_and_aliases_share_cid_property_fetch(monkeypatch):
    search = Mock(return_value=SimpleNamespace(get_cids=lambda: [2244]))
    fetch = Mock(side_effect=properties)
    monkeypatch.setattr(chem, "pubchem_search_by_name", search)
    monkeypatch.setattr(chem, "pubchem_get_properties", fetch)
    result = chem.translate_chemical_ids(["aspirin", "acetylsalicylic acid", "aspirin"], "name", ["cid", "formula"])
    assert search.call_count == 2
    fetch.assert_called_once_with(2244, properties=["MolecularFormula"])
    assert result["name"].tolist() == ["aspirin", "acetylsalicylic acid", "aspirin"]
    assert result["formula"].tolist() == ["formula-2244"] * 3


@pytest.mark.parametrize("failure", ["exception", "empty", "partial"])
def test_invalid_cid_does_not_discard_good_compounds(monkeypatch, failure):
    def fetch(cids, properties):
        if isinstance(cids, list):
            if failure == "exception":
                raise APIError("invalid compound")
            if failure == "empty":
                return SimpleNamespace(results=[])
            return SimpleNamespace(results=[{"CID": 1, "MolecularFormula": "good"}])
        if cids == 2:
            raise APIError("invalid compound")
        return SimpleNamespace(results=[{"CID": 1, "MolecularFormula": "good"}])

    mock = Mock(side_effect=fetch)
    monkeypatch.setattr(chem, "pubchem_get_properties", mock)
    result = chem.translate_chemical_ids(["1", "2", "invalid"], "cid", "formula", return_dict=True)
    assert result == {"1": "good", "2": None, "invalid": None}
    assert mock.call_count == (2 if failure == "partial" else 3)


def test_unlabelled_batch_response_is_not_associated_by_position(monkeypatch):
    def fetch(cids, properties):
        if isinstance(cids, list):
            return SimpleNamespace(results=[{"MolecularFormula": "wrong"}] * 2)
        return SimpleNamespace(results=[{"CID": cids, "MolecularFormula": str(cids)}])

    mock = Mock(side_effect=fetch)
    monkeypatch.setattr(chem, "pubchem_get_properties", mock)
    assert chem.translate_chemical_ids(["1", "2"], "cid", "formula", return_dict=True) == {"1": "1", "2": "2"}
    assert mock.call_count == 3


@pytest.mark.parametrize("target", ["formula", ["formula", "cid"]])
def test_batched_property_programming_errors_still_propagate(monkeypatch, target):
    monkeypatch.setattr(chem, "pubchem_get_properties", Mock(side_effect=RuntimeError("bug")))
    with pytest.raises(RuntimeError, match="bug"):
        chem.translate_chemical_ids(["1", "2"], "cid", target)


def test_normalized_name_dictionary_keeps_original_keys(monkeypatch):
    monkeypatch.setattr(chem, "pubchem_search_by_name", Mock(return_value=SimpleNamespace(get_cids=lambda: [1])))
    monkeypatch.setattr(chem, "pubchem_get_properties", Mock(return_value=SimpleNamespace(results=[{"CID": 1, "IUPACName": "normalized"}])))
    assert chem.translate_chemical_ids(["alias"], "name", "name", return_dict=True) == {"alias": "normalized"}


@pytest.mark.parametrize("error", [
    APIRateLimitError("PubChem"), APIServerError("PubChem", 503),
    APITimeoutError("PubChem"), RequestException("offline"),
])
def test_service_failures_do_not_fan_out_into_individual_requests(monkeypatch, error):
    fetch = Mock(side_effect=error)
    monkeypatch.setattr(chem, "pubchem_get_properties", fetch)
    result = chem.translate_chemical_ids(["1", "2", "1"], "cid", "formula", return_dict=True)
    assert result == {"1": None, "2": None}
    assert fetch.call_count == 1


def test_wrapped_network_error_does_not_fan_out(monkeypatch):
    error = APIError("network unavailable")
    error.__cause__ = RequestException("offline")
    fetch = Mock(side_effect=error)
    monkeypatch.setattr(chem, "pubchem_get_properties", fetch)
    assert chem.translate_chemical_ids(["1", "2"], "cid", "formula", return_dict=True) == {"1": None, "2": None}
    assert fetch.call_count == 1
