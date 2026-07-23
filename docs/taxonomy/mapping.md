# Taxonomy Mapping

Build a **canonical / cross-database mapping table** for taxonomic identifiers.
Every source resolves to one hub — the NCBI Taxonomy `taxid` — so mapping between
any two databases is a join on `hub_taxid`.

## Resolve names to a canonical taxon

```python
from biodbs.taxonomy import TaxonomyMapper
from biodbs.fetch.NCBI import NCBI_Fetcher
from biodbs.fetch.GBIF import GBIF_Fetcher

mapper = TaxonomyMapper(ncbi_fetcher=NCBI_Fetcher(), gbif_fetcher=GBIF_Fetcher())
df = mapper.map_names(["Escherichia coli", "Bacteroides fragilis"])
# columns: query, source, source_id, hub_taxid, canonical_name, rank,
#          name_status, match_type, lineage
```

## Offline / bulk resolution with a taxdump

```python
from biodbs.fetch import ncbi_download_taxdump
from biodbs.taxonomy import TaxonomyMapper, load_taxdump

archive = ncbi_download_taxdump("data/ncbi")     # new_taxdump.tar.gz (MD5-verified)
taxdump = load_taxdump(archive)                  # in-memory hub table
mapper = TaxonomyMapper(taxdump=taxdump)         # no network for taxid/rank/lineage
```

## Map a database's lineage strings

```python
from biodbs.fetch import gtdb_get_taxonomy, gtdb_ncbi_crosswalk
from biodbs.taxonomy import TaxonomyMapper, merge_on_hub

crosswalk = gtdb_ncbi_crosswalk()                # {gtdb species: ncbi taxid}
mapper = TaxonomyMapper(taxdump=taxdump, gtdb_crosswalk=crosswalk)

gtdb_lineages = [row.lineage for row in gtdb_get_taxonomy()]   # illustrative
gtdb_df = mapper.map_lineage(gtdb_lineages, source="gtdb")
```

## Join two databases

```python
silva_df = mapper.map_names(silva_names, source="silva")
combined = merge_on_hub(silva_df, gtdb_df, suffixes=("_silva", "_gtdb"))
```

## What each field means

- `hub_taxid` — the canonical NCBI taxonomy id; the join key across databases.
- `canonical_name` / `name_status` — GBIF's accepted name and whether the input was
  `accepted`, a `synonym`, or `unmatched`.
- `match_type` — how the taxid was found: `taxdump`, `ncbi` (esearch), or
  `gtdb-crosswalk`.
- `rank`, `lineage` — from the NCBI taxdump when a taxdump is loaded.
