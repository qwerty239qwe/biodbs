# FOMC Reference Sources

The FOMC-inspired oral-microbiome workflow combines HOMD, MOMD, and NCBI
full-length 16S references. biodbs downloads and integrity-checks the **source
artifacts**; the consuming workflow remains responsible for extraction, taxonomy
conversion, filtering, and BLAST database construction.

```python
from pathlib import Path

from biodbs.fetch.HOMD import HOMD_Fetcher
from biodbs.fetch.NCBI import NCBI_Fetcher

root = Path("reference_databases/fomc_16s/sources")

# Oral (HOMD) and mouse-oral (MOMD) 16S references, pinned to explicit releases.
oral = HOMD_Fetcher()
homd_fasta = oral.download_16s_refseq(root / "homd", version="15.22")
homd_taxonomy = oral.download_16s_taxonomy(root / "homd", version="15.22")
momd_fasta = oral.download_16s_refseq(root / "momd", version="5.1", source="momd")
momd_taxonomy = oral.download_16s_taxonomy(root / "momd", version="5.1", source="momd")

# NCBI 16S BLAST database and taxonomy dump (MD5-verified).
ncbi = NCBI_Fetcher()
ncbi_blast_db = ncbi.download_blast_database("16S_ribosomal_RNA", root / "ncbi")
ncbi_taxdump = ncbi.download_taxdump(root / "ncbi")
```

Use explicit HOMD and MOMD versions for reproducibility. NCBI's named BLAST
database is updated in place; retain the downloaded archive and its verified
checksum in your workflow manifest.

## What biodbs does and does not do

biodbs fetches and integrity-checks the source files above (HOMD/MOMD 16S FASTA and
QIIME taxonomy, the NCBI BLAST database archive, and the NCBI taxonomy dump). Each
download streams to a temporary file and is moved into place only after the whole
transfer — and any published MD5 — succeeds, so a partial download is never cached.

biodbs does **not** extract archives, run BLAST/VSEARCH, normalise taxonomy, combine
references, or perform the FOMC assignment itself — those remain in the downstream
pipeline.
