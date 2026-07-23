"""Live GBIF backbone tests (network required)."""

import pytest

from biodbs.fetch.GBIF import GBIF_Fetcher

pytestmark = pytest.mark.integration


def test_match_escherichia_coli_live():
    match = GBIF_Fetcher().match_name("Escherichia coli")
    assert match.canonical_name == "Escherichia coli"
    assert match.rank == "SPECIES"
    assert match.status == "ACCEPTED"
    assert match.match_type in {"EXACT", "FUZZY"}
    assert isinstance(match.usage_key, int)
