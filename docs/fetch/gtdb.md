# GTDB

GTDB provides Genome Taxonomy Database release files, including taxonomy tables, metadata, trees, release notes, checksums, and large genome/protein archives. biodbs supports GTDB as a public release-file catalog and downloader.

## List Releases

```python
from biodbs.fetch.GTDB import GTDB_Fetcher

fetcher = GTDB_Fetcher()
releases = fetcher.list_releases()

print(releases.names())
```

## List Release Files

```python
files = fetcher.list_release_files("latest")
rep_files = fetcher.list_release_files("latest", "genomic_files_reps")
```

## Fetch Small Text Files

```python
version = fetcher.get_version()
notes = fetcher.get_release_notes()
descriptions = fetcher.get_file_descriptions()
md5sums = fetcher.get_md5sums()

print(version.text)
```

## Fetch Tables

```python
taxonomy = fetcher.get_taxonomy(domain="bac120")
metadata = fetcher.get_metadata(domain="ar53")

df = taxonomy.as_dataframe()
```

Supported domains are `bac120` and `ar53`.

## Download Files

```python
path = fetcher.download_taxonomy("bac120", dest="data/gtdb")
```

Existing files are kept by default. Use `overwrite=True` to download again. Large files are streamed to disk.

## Convenience Functions

```python
from biodbs.fetch import gtdb_get_taxonomy, gtdb_list_releases

releases = gtdb_list_releases()
taxonomy = gtdb_get_taxonomy("bac120")
```

## Notes

GTDB genome and protein archives can be very large. The normal offline test suite does not download archives.
