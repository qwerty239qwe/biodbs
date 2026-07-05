"""UNITE fetcher via the PlutoF DOI REST API.

Flow verified against RESCRIPt's ``get_unite.py``: a maintained
``version -> taxon_group -> singletons -> DOI`` table resolves a DOI, the PlutoF
public DOI API returns the media file URL, and the ``.tgz`` archive is downloaded.
Extraction / ``_dev`` filtering / cluster-id selection are left to the caller.
"""

from __future__ import annotations

from pathlib import Path

from biodbs.exceptions import raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_HOST = "api.plutof.ut.ee"
_API_URL = "https://api.plutof.ut.ee/v1/public/dois/?format=vnd.api%2Bjson&identifier="
TAXON_GROUPS = ("fungi", "eukaryotes")

# Source: https://unite.ut.ee/repository.php (copied from RESCRIPt get_unite.py).
# This table is the maintenance point — add new releases here.
UNITE_DOIS = {
    "2025-02-19": {
        "fungi": {False: "10.15156/BIO/3301241", True: "10.15156/BIO/3301242"},
        "eukaryotes": {False: "10.15156/BIO/3301243", True: "10.15156/BIO/3301244"},
    },
    "2024-04-04": {
        "fungi": {False: "10.15156/BIO/2959336", True: "10.15156/BIO/2959337"},
        "eukaryotes": {False: "10.15156/BIO/2959338", True: "10.15156/BIO/2959339"},
    },
    "2023-07-18": {
        "fungi": {False: "10.15156/BIO/2938079", True: "10.15156/BIO/2938080"},
        "eukaryotes": {False: "10.15156/BIO/2938081", True: "10.15156/BIO/2938082"},
    },
    "2022-10-16": {
        "fungi": {False: "10.15156/BIO/2483915", True: "10.15156/BIO/2483916"},
        "eukaryotes": {False: "10.15156/BIO/2483917", True: "10.15156/BIO/2483918"},
    },
    "2021-05-10": {
        "fungi": {False: "10.15156/BIO/1264708", True: "10.15156/BIO/1264763"},
        "eukaryotes": {False: "10.15156/BIO/1264819", True: "10.15156/BIO/1264861"},
    },
    "2020-02-20": {
        "fungi": {False: "10.15156/BIO/786385", True: "10.15156/BIO/786387"},
        "eukaryotes": {False: "10.15156/BIO/786386", True: "10.15156/BIO/786388"},
    },
}

get_rate_limiter().set_rate(_HOST, 3)


class UNITE_Fetcher:
    """Fetcher for UNITE release archives via PlutoF DOIs."""

    def __init__(self, api_url: str = _API_URL, dois: dict = UNITE_DOIS):
        self.api_url = api_url
        self.dois = dois

    def resolve_doi(self, version: str, taxon_group: str = "fungi", singletons: bool = False) -> str:
        """Look up the DOI for a release from the maintained table."""
        if version not in self.dois:
            valid = ", ".join(sorted(self.dois))
            raise ValueError(f"Unknown UNITE version: {version!r}. Available versions: {valid}")
        groups = self.dois[version]
        if taxon_group not in groups:
            valid = ", ".join(sorted(groups))
            raise ValueError(f"Unknown taxon_group: {taxon_group!r}. Available: {valid}")
        return groups[taxon_group][bool(singletons)]

    def get_download_url(
        self, version: str, taxon_group: str = "fungi", singletons: bool = False
    ) -> str:
        """Resolve the newest media (archive) URL for a release via PlutoF."""
        doi = self.resolve_doi(version, taxon_group, singletons)
        url = self.api_url + doi
        response = request_with_retry(url)
        raise_for_status(response, "UNITE", url=url)
        # DOI files can be updated; the last media entry is the newest.
        return response.json()["data"][0]["attributes"]["media"][-1]["url"]

    def download(
        self,
        version: str,
        dest: str | Path,
        taxon_group: str = "fungi",
        singletons: bool = False,
        overwrite: bool = False,
    ) -> Path:
        """Download a UNITE release archive (.tgz) to *dest*."""
        url = self.get_download_url(version, taxon_group, singletons)
        target = Path(dest)
        if target.is_dir() or str(dest).endswith(("/", "\\")):
            name = url.rsplit("/", 1)[-1].split("?")[0]
            if "." not in name:
                name = f"unite_{version}_{taxon_group}.tgz"
            target = target / name
        if target.exists() and not overwrite:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        response = request_with_retry(url, stream=True)
        raise_for_status(response, "UNITE", url=url)
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return target
