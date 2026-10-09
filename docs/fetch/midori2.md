# MIDORI2

MIDORI2 provides quality-controlled, QIIME-formatted mitochondrial reference files
built from GenBank. Releases are now hosted on Zenodo as ZIP bundles, rather than
individual files on reference-midori.info. biodbs resolves the requested release
and extracts its `.fasta.gz` sequence file or `.taxon.gz` taxonomy sidecar.

## Download a File

```python
from biodbs.fetch.MIDORI2 import MIDORI2_Fetcher

fetcher = MIDORI2_Fetcher()
version = "GB271"  # also accepts the legacy "GenBank271_2026-04-07" spelling

seqs = fetcher.download("CO1", dest="data/midori2", version=version)
taxa = fetcher.download("CO1", dest="data/midori2", version=version, kind="taxon")
```

Options:

- `kind`: `"fasta"` (sequences, default) or `"taxon"` (taxonomy sidecar)
- `unique`: `True` for the unique set (default), `False` for longest
- `species`: `True` for the `QIIME_sp` variant, which includes ambiguous species names

Existing output files are reused unless `overwrite=True`. A new suffixless
destination such as `data/midori2` is treated as a directory; use a filename
with a suffix for a custom output path.

Each uncached download transfers the complete QIIME or QIIME_sp ZIP bundle and
temporarily needs space for that ZIP plus the requested file. For example,
GB271's QIIME ZIP is approximately 444 MiB. Its published Zenodo MD5 is checked
before extraction, and ZIP integrity is checked while reading the member.
Only the requested gzip file is kept; temporary files are removed on success
or failure, and failed overwrites preserve existing output. Separate sequence
and taxonomy downloads each transfer the bundle; there is no persistent ZIP cache.

## Just the URL

```python
url = fetcher.build_url("srRNA", version, species=True)
```

`build_url` now performs a metadata lookup and returns the **ZIP bundle URL**,
not a direct gzip URL. `kind` and `unique` select members inside the same ZIP;
`species` selects a different ZIP. Use `download` to get the individual file.
Release metadata is reused within a fetcher. An unavailable version raises
instead of silently switching to a newer release.

For an existing mirror that retains the old individual-file layout, explicitly
pass its root URL; this keeps direct URLs and downloads without Zenodo lookups:

```python
mirror = MIDORI2_Fetcher(base_url="https://your-mirror.example/Databases/")
url = mirror.build_url("CO1", "GenBank271_2026-04-07")
```

## Convenience Functions

```python
from biodbs.fetch import midori2_download, midori2_build_url

path = midori2_download("CO1", dest="data/midori2", version="GenBank271_2026-04-07")
url = midori2_build_url("CO1", "GenBank271_2026-04-07", kind="taxon")
```

Choose an explicit `GBNNN` release (or its legacy `GenBankNNN_YYYY-MM-DD` spelling).
The GenBank number selects the snapshot; the legacy date suffix is not a separate
Zenodo version. Check the [official download page](https://www.reference-midori.info/download.html)
for the [current releases](https://doi.org/10.5281/zenodo.22685700) and the
[GB237–GB272 archive](https://doi.org/10.5281/zenodo.22849929).
