# GreenGenes

GreenGenes publishes its reference releases as an open HTTP directory tree at
`ftp.microbio.me/greengenes_release/`. biodbs browses that tree and downloads
files. (GreenGenes2 is served by the separate `q2-greengenes2` plugin and is not
covered here.)

## List Releases

```python
from biodbs.fetch.GreenGenes import GreenGenes_Fetcher

fetcher = GreenGenes_Fetcher()
releases = fetcher.list_releases()

print(releases.names())  # e.g. gg_13_8_otus, gg_13_5, 2022.10, 2024.09
```

## Browse Files

```python
files = fetcher.list_files("gg_13_8_otus/taxonomy")
print(files.names())
fasta = fetcher.list_files("gg_13_8_otus/rep_set").filter("*.fasta")
```

## Download a File

```python
path = fetcher.download_file(
    "gg_13_8_otus/taxonomy/99_otu_taxonomy.txt",
    dest="data/greengenes",
)
```

Existing files are kept by default (`overwrite=True` to refetch). Files stream to disk.

## Convenience Functions

```python
from biodbs.fetch import greengenes_list_releases, greengenes_list_files, greengenes_download_file

releases = greengenes_list_releases()
files = greengenes_list_files("gg_13_8_otus/rep_set")
path = greengenes_download_file("gg_13_8_otus/rep_set/99_otus.fasta", dest="data/greengenes")
```
