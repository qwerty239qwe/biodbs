# SILVA

SILVA provides quality-checked aligned SSU and LSU rRNA sequence datasets and classifier resources. biodbs supports SILVA as a release-file catalog and downloader.

## List Release Files

```python
from biodbs.fetch.SILVA import SILVA_Fetcher

fetcher = SILVA_Fetcher()
files = fetcher.list_current_files()

print(files.names())
```

To list a subdirectory:

```python
qiime2_files = fetcher.list_current_files("QIIME2/")
```

## Version, README, Citation

```python
version = fetcher.get_version()
readme = fetcher.get_readme()
citation = fetcher.get_citation()

print(version.text)
```

## Download Files

```python
path = fetcher.download_file("README.txt", dest="data/silva")
```

Existing files are kept by default. Use `overwrite=True` to download again.

## Classifier Resources

```python
path = fetcher.download_classifier(
    kind="qiime2",
    filename="taxonomy.qza",
    dest="data/silva",
)
```

Supported classifier/resource directories:

- `qiime2`
- `dada2`
- `kraken2`
- `megan`
- `exports`

## Convenience Functions

```python
from biodbs.fetch import silva_get_version, silva_list_current_files

version = silva_get_version()
files = silva_list_current_files()
```

## Notes

Many SILVA release assets are large. The normal offline test suite does not download release archives or classifier files.

