# SILVA

SILVA provides quality-checked aligned SSU and LSU rRNA sequence datasets and classifier resources. biodbs supports SILVA as a release-file catalog and downloader.

## List Release Files

```python
from biodbs.fetch.SILVA import SILVA_Fetcher

fetcher = SILVA_Fetcher()
files = fetcher.list_current_files()

print(files.names())
```

To browse into a subdirectory:

```python
qiime2 = fetcher.list_current_files("QIIME2")
release = next(entry.name for entry in qiime2 if entry.is_dir)
ssu = fetcher.list_current_files(f"QIIME2/{release}/SSU") # -> marker regions
```

`list_current_files()` returns immediate directories and downloadable files.
Directory entries use SILVA's `/current-release/` browse URLs and have
`is_dir=True`; file entries use their direct `/fileadmin/silva_databases/current/`
URLs and have `is_dir=False`. Walk down to a leaf directory to discover the exact
classifier filenames, then pass the nested path to `download_classifier`:

```python
leaves = fetcher.list_current_files(f"QIIME2/{release}/taxonomic-weights")
for f in leaves:
    print(f.name, f.is_dir)
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
# Select a published human-oral classifier from the listing above.
classifier = leaves.filter("*human-oral.qza")[0]
path = fetcher.download_classifier(
    kind="qiime2",
    filename=f"{release}/taxonomic-weights/{classifier.name}",
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
nested path for the classifier you need. Do not hard-code a release folder under
`current`: old release folders can disappear when SILVA publishes a new release.
For reproducible analyses, record the exact release and use its archived files.

## Convenience Functions

```python
from biodbs.fetch import silva_get_version, silva_list_current_files

version = silva_get_version()
files = silva_list_current_files()
```

## Notes

Many SILVA release assets are large. The normal offline test suite does not download release archives or classifier files.
