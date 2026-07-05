"""EUKARYOME reference-set fetcher (static direct-URL downloads).

URL pattern verified against RESCRIPt's ``get_eukaryome.py``:
``https://sisu.ut.ee/wp-content/uploads/sites/643/General_EUK_{marker}_v{version}.zip``
"""

from __future__ import annotations

from pathlib import Path

from biodbs.exceptions import raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_BASE_URL = "https://sisu.ut.ee/wp-content/uploads/sites/643/"
_HOST = "sisu.ut.ee"
_DEFAULT_VERSION = "2.0"
MARKERS = ("SSU", "LSU", "ITS", "longread")

get_rate_limiter().set_rate(_HOST, 3)


class EUKARYOME_Fetcher:
    """Fetcher for EUKARYOME rRNA reference archives."""

    def __init__(self, base_url: str = _BASE_URL):
        self.base_url = base_url

    def build_url(self, marker: str, version: str = _DEFAULT_VERSION) -> str:
        """Build the download URL for a marker/version."""
        return f"{self.base_url}General_EUK_{self._canonical(marker)}_v{version}.zip"

    def download(
        self, marker: str, dest: str | Path, version: str = _DEFAULT_VERSION, overwrite: bool = False
    ) -> Path:
        """Download a EUKARYOME marker archive to *dest*.

        Downloads the ``.zip`` as published. Some archives contain a nested 7z
        that must be extracted separately (7z is not in the stdlib).
        """
        url = self.build_url(marker, version)
        target = Path(dest)
        if target.is_dir() or str(dest).endswith(("/", "\\")):
            target = target / url.rsplit("/", 1)[-1]
        if target.exists() and not overwrite:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        response = request_with_retry(url, stream=True)
        raise_for_status(response, "EUKARYOME", url=url)
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return target

    @staticmethod
    def _canonical(marker: str) -> str:
        for valid in MARKERS:
            if marker.lower() == valid.lower():
                return valid
        options = ", ".join(MARKERS)
        raise ValueError(f"Unsupported marker: {marker!r}. Valid markers: {options}")
