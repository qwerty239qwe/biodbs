# MIDORI2

MIDORI2 provides quality-controlled, QIIME-formatted mitochondrial reference files
built from GenBank. Releases are static, so biodbs builds the download URL from the
gene, version, and options. Each gene has a `.fasta.gz` sequence file and a matching
`.taxon.gz` taxonomy sidecar.

## Download a File

```python
from biodbs.fetch.MIDORI2 import MIDORI2_Fetcher

fetcher = MIDORI2_Fetcher()
version = "GenBank271_2026-04-07"  # full version string

seqs = fetcher.download("CO1", dest="data/midori2", version=version)
taxa = fetcher.download("CO1", dest="data/midori2", version=version, kind="taxon")
```

Options:

- `kind`: `"fasta"` (sequences, default) or `"taxon"` (taxonomy sidecar)
- `unique`: `True` for the unique set (default), `False` for longest
- `species`: `True` for species-level (`QIIME_sp`) files

## Just the URL

```python
url = fetcher.build_url("srRNA", version, species=True)
```

## Convenience Functions

```python
from biodbs.fetch import midori2_download, midori2_build_url

path = midori2_download("CO1", dest="data/midori2", version="GenBank271_2026-04-07")
url = midori2_build_url("CO1", "GenBank271_2026-04-07", kind="taxon")
```

The version is the full `GenBankNNN_YYYY-MM-DD` string; check
[reference-midori.info](https://www.reference-midori.info/) for the current release.
