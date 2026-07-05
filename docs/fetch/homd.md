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

## 16S RefSeq

```python
files = fetcher.list_16s_refseq()
path = fetcher.download_16s_refseq(dest="data/homd")
```

If `filename` is omitted, the first FASTA-like file in the 16S RefSeq directory is used.

## Convenience Functions

```python
from biodbs.fetch import homd_get_taxon_table, homd_list_ftp

taxa = homd_get_taxon_table()
files = homd_list_ftp("genomes")
```

## Notes

This integration targets public HOMD downloads and reference tables. It does not automate BLAST, login-only pages, or detail-page scraping.
