"""Live HOMD and MOMD reference-listing contracts."""

import pytest

from biodbs.fetch.HOMD import HOMD_Fetcher

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("source", "version", "tag"),
    [("homd", "15.22", "HOMD"), ("momd", "5.1", "MOMD")],
)
def test_versioned_16s_release_exposes_canonical_files(source, version, tag):
    names = HOMD_Fetcher().list_16s_refseq(version, source).names()
    prefix = f"{tag}_16S_rRNA_RefSeq_V{version}"

    assert f"{prefix}.fasta" in names
    assert f"{prefix}.qiime.taxonomy" in names
