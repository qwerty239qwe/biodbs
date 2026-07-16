"""Live integration tests for HOMD/MOMD 16S RefSeq listings (network required).

Guards against the two-host layout: HOMD releases live on ``homd.org`` and MOMD
releases on ``momd.org``. Checks listings only — no large FASTA is downloaded.
"""

import pytest

from biodbs.fetch.HOMD import HOMD_Fetcher

pytestmark = pytest.mark.integration


def test_versioned_homd_16s_listing():
    names = HOMD_Fetcher().list_16s_refseq("15.22").names()
    assert "HOMD_16S_rRNA_RefSeq_V15.22.fasta" in names
    assert "HOMD_16S_rRNA_RefSeq_V15.22.qiime.taxonomy" in names


def test_momd_16s_listing_uses_momd_host():
    names = HOMD_Fetcher().list_16s_refseq("5.1", "momd").names()
    assert "MOMD_16S_rRNA_RefSeq_V5.1.fasta" in names
