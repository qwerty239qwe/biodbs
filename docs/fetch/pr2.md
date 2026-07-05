# PR2

PR2 (Protist Ribosomal Reference) publishes its reference sequence and taxonomy
files as assets on GitHub releases. biodbs supports PR2 as a release catalog and
downloader over the GitHub API.

## List Releases

```python
from biodbs.fetch.PR2 import PR2_Fetcher

fetcher = PR2_Fetcher()
releases = fetcher.list_releases()

print(releases.names())  # release tags, newest first
```

## List Release Assets

```python
# assets for the latest release
assets = fetcher.list_assets()

# assets for a specific release tag
assets = fetcher.list_assets(tag="v5.0.0")

print(assets.names())
fasta = assets.filter("*.fasta.gz")
```

## Download an Asset

```python
path = fetcher.download_asset(
    "pr2_version_5.0.0_SSU_taxo_long.fasta.gz",
    dest="data/pr2",
)
```

Existing files are kept by default. Use `overwrite=True` to download again. The
latest release is used unless you pass `tag=`. Files are streamed to disk.

## Convenience Functions

```python
from biodbs.fetch import pr2_list_releases, pr2_list_assets, pr2_download_asset

releases = pr2_list_releases()
assets = pr2_list_assets()
path = pr2_download_asset("pr2_version_5.0.0_SSU_UTAX.fasta.gz", dest="data/pr2")
```

## Notes

Asset names include the version and marker (e.g. `SSU`), so filter the asset
listing rather than hard-coding filenames. The normal offline test suite does
not download release assets.
