"""MIDORI2 reference-database fetcher (static direct-URL downloads).

URL pattern verified against RESCRIPt's ``get_midori2.py``. Example::

    {base}/{version}/{QIIME|QIIME_sp}/{uniq|longest}/
        MIDORI2_{UNIQ|LONGEST}_NUC_{SP_|}GB{NNN}_{gene}_QIIME.{fasta|taxon}.gz

``version`` is the full string, e.g. ``GenBank271_2026-04-07``; ``NNN`` (271) is
extracted from it. Each gene has a ``.fasta.gz`` sequence file and a matching
``.taxon.gz`` taxonomy sidecar.
"""

from __future__ import annotations

import re
from pathlib import Path

from biodbs.exceptions import raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_BASE_URL = "https://www.reference-midori.info/download/Databases/"
_HOST = "www.reference-midori.info"
_KINDS = ("fasta", "taxon")
_VERSION_RE = re.compile(r"GenBank(\d+)")

get_rate_limiter().set_rate(_HOST, 3)


class MIDORI2_Fetcher:
    """Fetcher for MIDORI2 QIIME-formatted reference files."""

    def __init__(self, base_url: str = _BASE_URL):
        self.base_url = base_url

    def build_url(
        self,
        gene: str,
        version: str,
        kind: str = "fasta",
        unique: bool = True,
        species: bool = False,
    ) -> str:
        """Build the download URL for a gene/version and options."""
        if kind not in _KINDS:
            raise ValueError(f"Unsupported kind: {kind!r}. Valid kinds: {', '.join(_KINDS)}")
        match = _VERSION_RE.search(version)
        if not match:
            raise ValueError(
                f"Unrecognised MIDORI2 version: {version!r}. "
                "Expected a full string like 'GenBank271_2026-04-07'."
            )
        num = match.group(1)
        uniq_dir = "uniq" if unique else "longest"
        uniq_tag = "UNIQ" if unique else "LONGEST"
        qiime_dir = "QIIME_sp" if species else "QIIME"
        sp_tag = "SP_" if species else ""
        filename = f"MIDORI2_{uniq_tag}_NUC_{sp_tag}GB{num}_{gene}_QIIME.{kind}.gz"
        return f"{self.base_url}{version}/{qiime_dir}/{uniq_dir}/{filename}"

    def download(
        self,
        gene: str,
        dest: str | Path,
        version: str,
        kind: str = "fasta",
        unique: bool = True,
        species: bool = False,
        overwrite: bool = False,
    ) -> Path:
        """Download a MIDORI2 file to *dest*."""
        url = self.build_url(gene, version, kind=kind, unique=unique, species=species)
        target = Path(dest)
        if target.is_dir() or str(dest).endswith(("/", "\\")):
            target = target / url.rsplit("/", 1)[-1]
        if target.exists() and not overwrite:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        response = request_with_retry(url, stream=True)
        raise_for_status(response, "MIDORI2", url=url)
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return target
