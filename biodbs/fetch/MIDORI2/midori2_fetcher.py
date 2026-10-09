"""MIDORI2 QIIME downloads from versioned Zenodo bundles or a legacy mirror."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

from biodbs.exceptions import APIError, raise_for_status
from biodbs.fetch._download import download_binary
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_KINDS = ("fasta", "taxon")
_GENES = (
    "ATP6",
    "ATP8",
    "CO1",
    "CO2",
    "CO3",
    "Cytb",
    "ND1",
    "ND2",
    "ND3",
    "ND4",
    "ND4L",
    "ND5",
    "ND6",
    "lrRNA",
    "srRNA",
)
_VERSION_RE = re.compile(r"(?:GenBank|GB)(\d+)(?:_\d{4}-\d{2}-\d{2})?")

get_rate_limiter().set_rate("zenodo.org", 3)


class MIDORI2_Fetcher:
    """Fetcher for MIDORI2 QIIME-formatted reference files."""

    def __init__(self, base_url: str | None = None):
        """Use Zenodo by default; *base_url* selects a legacy direct-file mirror."""
        self.base_url = base_url
        self._records: dict[str, dict] = {}
        self._loaded_concepts: set[int] = set()

    @staticmethod
    def _member(gene: str, version: str, kind: str, unique: bool, species: bool) -> str:
        if kind not in _KINDS:
            raise ValueError(
                f"Unsupported kind: {kind!r}. Valid kinds: {', '.join(_KINDS)}"
            )
        match = _VERSION_RE.fullmatch(version)
        if not match:
            raise ValueError(
                f"Unrecognised MIDORI2 version: {version!r}. "
                "Expected 'GB271' or 'GenBank271_2026-04-07'."
            )
        if gene not in _GENES:
            raise ValueError(
                f"Unsupported MIDORI2 gene: {gene!r}. Valid genes: {', '.join(_GENES)}"
            )
        num = match.group(1)
        uniq_dir = "uniq" if unique else "longest"
        uniq_tag = "UNIQ" if unique else "LONGEST"
        qiime_dir = "QIIME_sp" if species else "QIIME"
        sp_tag = "SP_" if species else ""
        filename = f"MIDORI2_{uniq_tag}_NUC_{sp_tag}GB{num}_{gene}_QIIME.{kind}.gz"
        return f"{qiime_dir}/{uniq_dir}/{filename}"

    @staticmethod
    def _json(url: str) -> dict:
        response = request_with_retry(url)
        try:
            raise_for_status(response, "MIDORI2", url=url)
            return response.json()
        finally:
            response.close()

    def _archive(self, member: str) -> dict:
        version = re.search(r"GB\d+", member).group()
        # GB237--GB272 are under the legacy concept DOI; newer releases have their own.
        concepts = (
            (22849929, 22685700) if int(version[2:]) <= 272 else (22685700, 22849929)
        )
        for concept in concepts:
            if version in self._records:
                break
            if concept in self._loaded_concepts:
                continue
            latest = self._json(f"https://zenodo.org/api/records/{concept}")
            self._records[latest["metadata"].get("version", "")] = latest
            url = latest["links"]["versions"]
            while version not in self._records and url:
                page = self._json(url)
                for record in page["hits"]["hits"]:
                    self._records[record["metadata"].get("version", "")] = record
                url = page.get("links", {}).get("next")
            if not url:
                self._loaded_concepts.add(concept)
        if version not in self._records:
            raise ValueError(f"MIDORI2 version {version!r} is not published on Zenodo.")
        key = f"MIDORI2_{version}_{member.split('/')[0]}.zip"
        for archive in self._records[version]["files"]:
            if archive["key"] == key:
                return archive
        raise ValueError(f"MIDORI2 {version} does not publish {key!r}.")

    def build_url(
        self,
        gene: str,
        version: str,
        kind: str = "fasta",
        unique: bool = True,
        species: bool = False,
    ) -> str:
        """Resolve the ZIP URL containing the requested file (network required).

        With an explicit legacy *base_url*, return the direct file URL instead.
        """
        member = self._member(gene, version, kind, unique, species)
        if self.base_url is not None:
            return f"{self.base_url.rstrip('/')}/{version}/{member}"
        return self._archive(member)["links"]["self"]

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
        """Download and atomically extract one gzip file, removing the temporary ZIP.

        *dest* may be a file or directory (including a new suffixless directory).
        Existing files are reused unless *overwrite* is true. Zenodo downloads
        require temporary disk space for the complete QIIME/QIIME_sp bundle.
        """
        member = self._member(gene, version, kind, unique, species)
        target = Path(dest)
        if (
            target.is_dir()
            or (not target.suffix and not target.is_file())
            or str(dest).endswith(("/", "\\"))
        ):
            target = target / member.rsplit("/", 1)[-1]
        if target.exists() and not overwrite:
            return target
        if self.base_url is not None:
            url = self.build_url(gene, version, kind, unique, species)
            return download_binary(
                url, target, "MIDORI2", overwrite=overwrite, reject_html=True
            )
        archive = self._archive(member)
        url = archive["links"]["self"]
        checksum = archive.get("checksum", "")
        if not re.fullmatch(r"md5:[0-9a-f]{32}", checksum):
            raise APIError(
                "MIDORI2 archive lacks a valid Zenodo MD5 checksum.",
                service="MIDORI2",
                url=url,
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        # shortcut: Fetch the full bundle per file; add range reads if transfers become too costly.
        with tempfile.TemporaryDirectory(
            prefix=".midori2-", dir=target.parent
        ) as temp_dir:
            bundle = download_binary(
                url, Path(temp_dir) / archive["key"], "MIDORI2", reject_html=True
            )
            digest = hashlib.md5()
            with bundle.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != checksum[4:]:
                raise APIError(
                    "MIDORI2 archive checksum mismatch.", service="MIDORI2", url=url
                )
            part = Path(temp_dir) / "extracted.part"
            with ZipFile(bundle) as zipped:
                if member not in zipped.namelist():
                    raise ValueError(f"MIDORI2 archive does not contain {member!r}.")
                with zipped.open(member) as source, part.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
            os.replace(part, target)
        return target
