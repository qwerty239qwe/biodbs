"""PR2 (Protist Ribosomal Reference) release fetcher via the GitHub API."""

from __future__ import annotations

from pathlib import Path

from biodbs.data.PR2 import PR2Asset, PR2Release, PR2AssetListData, PR2ReleaseListData
from biodbs.exceptions import raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_RELEASES_URL = "https://api.github.com/repos/pr2database/pr2database/releases"
_HOST = "api.github.com"

get_rate_limiter().set_rate(_HOST, 5)


class PR2_Fetcher:
    """Fetcher for PR2 GitHub releases and their downloadable assets."""

    def __init__(self, releases_url: str = _RELEASES_URL):
        self.releases_url = releases_url

    def list_releases(self) -> PR2ReleaseListData:
        """List PR2 releases (newest first)."""
        response = request_with_retry(self.releases_url)
        raise_for_status(response, "PR2", url=self.releases_url)
        return PR2ReleaseListData([_parse_release(raw) for raw in response.json()])

    def list_assets(self, tag: str | None = None) -> PR2AssetListData:
        """List assets for a release; the latest release when *tag* is None."""
        return PR2AssetListData(self._select_release(tag).assets)

    def download_asset(
        self, name: str, dest: str | Path, tag: str | None = None, overwrite: bool = False
    ) -> Path:
        """Download a release asset by name to *dest*."""
        assets = {asset.name: asset for asset in self._select_release(tag).assets}
        asset = assets.get(name)
        if asset is None:
            valid = ", ".join(sorted(assets))
            raise ValueError(f"Unknown PR2 asset: {name!r}. Available: {valid}")

        target = Path(dest)
        if target.is_dir() or str(dest).endswith(("/", "\\")):
            target = target / name
        if target.exists() and not overwrite:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        response = request_with_retry(asset.url, stream=True)
        raise_for_status(response, "PR2", url=asset.url)
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return target

    def _select_release(self, tag: str | None) -> PR2Release:
        releases = self.list_releases().releases
        if not releases:
            raise ValueError("No PR2 releases found.")
        if tag is None:
            return releases[0]  # ponytail: GitHub returns releases newest-first
        for release in releases:
            if release.tag == tag:
                return release
        valid = ", ".join(release.tag for release in releases)
        raise ValueError(f"Unknown PR2 release tag: {tag!r}. Available: {valid}")


def _parse_release(raw: dict) -> PR2Release:
    assets = [
        PR2Asset(name=a["name"], url=a["browser_download_url"], size=a.get("size"))
        for a in raw.get("assets", [])
    ]
    return PR2Release(
        tag=raw.get("tag_name", ""),
        url=raw.get("html_url", ""),
        published=raw.get("published_at"),
        assets=assets,
    )
