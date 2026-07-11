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

Paths are relative to the SILVA file base (`fileadmin/silva_databases/current/`):

```python
path = fetcher.download_file("README.txt", dest="data/silva")
```

Existing files are kept by default. Use `overwrite=True` to download again. If a
path resolves to a SILVA CMS browse page instead of a real file, the download
raises an `APIError` rather than silently saving an HTML page.

## Classifier Resources

SILVA nests classifier files by release and marker, so `filename` is the full
path **below** the classifier directory:

```python
# a taxonomic-weight classifier
path = fetcher.download_classifier(
    kind="qiime2",
    filename="2025.7/taxonomic-weights/SILVA_138.2_Ref_NR99_taxonomic-weight_human-oral.qza",
    dest="data/silva",
)

# a weighted region classifier
path = fetcher.download_classifier(
    kind="qiime2",
    filename="2025.7/SSU/V4V5-515f-926r/weighted/human-oral/"
             "SILVA138.2_SSURef_NR99_weighted_classifier_V4V5-515f-926r_human-oral.qza",
    dest="data/silva",
)
```

Supported classifier/resource directories:

- `qiime2`
- `dada2`
- `kraken2`
- `megan`
- `exports`

Browse the SILVA site (e.g. `current-release/QIIME2/...`) to find the exact
nested path for the classifier you need.

## Convenience Functions

```python
from biodbs.fetch import silva_get_version, silva_list_current_files

version = silva_get_version()
files = silva_list_current_files()
```

## Notes

Many SILVA release assets are large. The normal offline test suite does not download release archives or classifier files.

