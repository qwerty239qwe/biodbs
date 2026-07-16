# HOMD

HOMD provides curated Human Oral Microbiome Database taxonomy, genome metadata, 16S reference sequences, phage, CRISPR, AMR, and phylogeny resources. biodbs supports HOMD as a public download/table catalog.

## List FTP Files

```python
from biodbs.fetch.HOMD import HOMD_Fetcher

fetcher = HOMD_Fetcher()
files = fetcher.list_ftp()

print(files.names())
```

To list a subdirectory:

```python
refseq_files = fetcher.list_ftp("16S_rRNA_refseq")
```

## List Batch Downloads

```python
downloads = fetcher.list_downloads()
print(downloads.names())
```

## Fetch Tables

```python
taxa = fetcher.get_taxon_table()
genomes = fetcher.get_genome_metadata()
crispr = fetcher.get_crispr_table()

df = taxa.as_dataframe()
```

You can also fetch any tabular HOMD file directly:

```python
table = fetcher.get_table("ftp/some_file.tsv")
```

## Download Files

```python
path = fetcher.download_file("ftp/16S_rRNA_refseq/example.fasta", dest="data/homd")
```

Existing files are kept by default. Use `overwrite=True` to download again. Large files are streamed to disk.

## 16S RefSeq (HOMD and MOMD)

16S rRNA RefSeq releases are versioned per source. `version` accepts a release like
`"15.22"` (or `"current"` for the latest); `source` is `"homd"` (default) or `"momd"`
(the mouse database, served from `momd.org`).

```python
files = fetcher.list_16s_refseq(version="15.22")

# unaligned FASTA + QIIME taxonomy for a pinned HOMD release
homd_fasta = fetcher.download_16s_refseq("data/homd", version="15.22")
homd_taxonomy = fetcher.download_16s_taxonomy("data/homd", version="15.22")

# the same for a MOMD release
momd_fasta = fetcher.download_16s_refseq("data/momd", version="5.1", source="momd")
momd_taxonomy = fetcher.download_16s_taxonomy("data/momd", version="5.1", source="momd")
```

Without `filename`, `download_16s_refseq` selects the unaligned `.fasta` reference
(not the `.aligned.fasta`/`.p9.fasta` variants); `download_16s_taxonomy` selects the
`.qiime.taxonomy` sidecar. Pin an explicit `version` for reproducible pipelines.

## Convenience Functions

```python
from biodbs.fetch import homd_get_taxon_table, homd_list_ftp

taxa = homd_get_taxon_table()
files = homd_list_ftp("genomes")
```

## Notes

This integration targets public HOMD downloads and reference tables. It does not automate BLAST, login-only pages, or detail-page scraping.
