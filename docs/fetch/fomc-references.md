# FOMC Reference Sources

biodbs can fetch the source artifacts needed to build a FOMC-style combined
16S reference set:

```python
from biodbs.fetch.HOMD import HOMD_Fetcher
from biodbs.fetch.NCBI import NCBI_Fetcher

oral = HOMD_Fetcher()
homd_fasta = oral.download_16s_refseq("refs/homd", version="15.22")
homd_taxonomy = oral.download_16s_taxonomy("refs/homd", version="15.22")
momd_fasta = oral.download_16s_refseq(
    "refs/momd", version="5.1", source="momd"
)
momd_taxonomy = oral.download_16s_taxonomy(
    "refs/momd", version="5.1", source="momd"
)

ncbi = NCBI_Fetcher()
ncbi_db = ncbi.download_blast_database("16S_ribosomal_RNA", "refs/ncbi")
ncbi_taxonomy = ncbi.download_taxdump("refs/ncbi")
```

The original FOMC publication used the older `16SMicrobial` NCBI database;
the current oral workflow uses `16S_ribosomal_RNA` with `new_taxdump`.

biodbs fetches and verifies source artifacts. Archive extraction, sequence
filtering, taxonomy normalization, reference combination, `makeblastdb`, and
the FOMC assignment algorithm remain workflow responsibilities.
