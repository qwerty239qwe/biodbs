# UNITE

UNITE distributes fungal and eukaryote ITS reference releases through PlutoF DOIs.
biodbs resolves a release DOI from a maintained table, asks the PlutoF public API
for the newest archive URL, and downloads the `.tgz`.

## Download a Release Archive

```python
from biodbs.fetch.UNITE import UNITE_Fetcher, UNITE_DOIS

print(list(UNITE_DOIS))  # available versions, e.g. '2025-02-19', '2024-04-04', ...

fetcher = UNITE_Fetcher()
path = fetcher.download("2025-02-19", dest="data/unite", taxon_group="fungi")
```

Options:

- `taxon_group`: `"fungi"` (default) or `"eukaryotes"`
- `singletons`: `False` (default) or `True` to include global/singleton sequences

After download, extract the `.tgz` and select the release files you need (UNITE
ships several clustering thresholds and a `_dev` developer set).

## Resolve DOI / URL Only

```python
doi = fetcher.resolve_doi("2025-02-19", "fungi")
url = fetcher.get_download_url("2025-02-19", "fungi")
```

## Convenience Functions

```python
from biodbs.fetch import unite_download, unite_resolve_doi, unite_get_download_url

path = unite_download("2025-02-19", dest="data/unite")
doi = unite_resolve_doi("2025-02-19", "eukaryotes", singletons=True)
```

The DOI table is the maintenance point — new UNITE releases are added to
`UNITE_DOIS` (see [unite.ut.ee/repository.php](https://unite.ut.ee/repository.php)).
