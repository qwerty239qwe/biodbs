# Build an offline mapping database

For a reusable reference, fetch a **whole source dataset**, save it once, and
query the local copy. Translating a list of your own IDs only creates a snapshot
for those IDs; it does not build a reference for arbitrary future inputs.

There is no single biodbs call that builds a universal gene/chemical/taxon
database. Use the smallest route that covers the identifiers you need:

| Reference | Shortest route | Coverage |
| --- | --- | --- |
| Human gene symbols, HGNC, Entrez, Ensembl | `hgnc_fetch("status", "Approved")` | All approved HGNC human records; some cross-references are missing |
| KEGG genes to Entrez or UniProt | `translate_gene_ids([], ..., database="kegg", bulk=True)` | All available mappings for one KEGG organism |
| KEGG compounds/drugs to ChEBI or PubChem SID | `translate_chemical_ids([], ..., bulk=True)` | All available mappings in the selected KEGG source |
| NCBI taxon names, taxids, ranks, parents | `ncbi_download_taxdump()` then `load_taxdump()` | Full NCBI taxonomy, not a universal crosswalk between taxonomy systems |
| Other gene species/annotations | Unfiltered `biomart_query()` for a species dataset | The selected Ensembl dataset and attributes |
| Whole ChEMBL to PubChem CID crosswalk | `build_chemical_mapping_db("mapping.db")` | All published UniChem source 1 to source 22 pairs |

The examples below use pandas (already required by biodbs) and Python's standard
library `sqlite3`. No additional database dependency is needed. Build into a new
file: `to_sql()` defaults to failing if a table exists, not silently replacing it.

## Human gene reference: fetch once, save once

```python
import sqlite3
from biodbs.fetch import hgnc_fetch

data = hgnc_fetch("status", "Approved")
assert len(data) > 0 and len(data) == data.num_found
genes = data.as_dataframe()[["hgnc_id", "symbol", "entrez_id", "ensembl_gene_id"]]
with sqlite3.connect("human_genes.db") as db:
    genes.to_sql("gene", db, index=False)
    db.execute("CREATE INDEX gene_symbol ON gene(symbol)")
```

This retrieves full records in one call, rather than making a request per gene.
[HGNC documents the approved-status bulk query](https://www.genenames.org/help/rest/).
It includes non-protein-coding loci, not just protein-coding genes. HGNC covers
humans, not genes from every organism. Missing Entrez/Ensembl values remain SQL
`NULL`; keep them rather than inventing a match.

The full HGNC DataFrame contains list-valued fields, so directly saving all
columns with `to_sql()` fails. Select scalar columns as above. To support aliases,
previous symbols, UniProt accessions, or RefSeq accessions, store a separate
two-column table per field using `explode()` and remove missing/empty values:

```python
links = data.as_dataframe()[["hgnc_id", "uniprot_ids"]].explode("uniprot_ids")
links = links.dropna(subset=["uniprot_ids"])
links = links[links["uniprot_ids"] != ""].drop_duplicates()
with sqlite3.connect("human_genes.db") as db:
    links.to_sql("gene_uniprot", db, index=False)
    db.execute("CREATE INDEX uniprot_accession ON gene_uniprot(uniprot_ids)")
```

This preserves multiple accessions per gene. Aliases and previous symbols can
also identify multiple genes: query all matching rows, not only the first one.

## Chemical reference: all KEGG compound to ChEBI mappings

```python
import sqlite3
from biodbs.translate import translate_chemical_ids

chemicals = translate_chemical_ids([], "kegg_compound", "chebi", bulk=True)
assert not chemicals.empty
with sqlite3.connect("chemicals.db") as db:
    chemicals.to_sql("compound_chebi", db, index=False)
    db.execute("CREATE INDEX compound_source ON compound_chebi(source_id)")
```

An empty input plus explicit `bulk=True` requests the whole source crosswalk.
Without `bulk=True`, an empty input returns no mappings. Keep the DataFrame:
scalar dictionaries can discard additional targets for a source ID.

For KEGG compounds to PubChem **substance IDs**, use `"pubchem_sid"` instead of
`"chebi"`. Returned IDs keep their prefixes, such as `cpd:C00001`,
`chebi:15377`, and `pubchem:3303`. **KEGG's PubChem crosswalk uses SID, not CID.**
It does not cover all PubChem compounds or all chemicals.
[The KEGG API manual defines these conversion namespaces](https://www.kegg.jp/kegg/docs/keggapi.html).
KEGG's API is restricted to academic use; check
[its terms and rate limits](https://www.kegg.jp/kegg/rest/) before building a reference.

The same route builds a whole organism's KEGG gene crosswalk:

```python
from biodbs.translate import translate_gene_ids

genes = translate_gene_ids(
    [], "kegg_gene", "entrez_id", species="human", database="kegg", bulk=True,
)
```

Save this DataFrame with `to_sql()` as above. Use `species="mouse"` for mouse,
or `to_type="uniprot_id"` for the UniProt crosswalk. This maps KEGG gene IDs,
not gene symbols, and contains only the mappings published by KEGG.

For a whole ChEMBL/PubChem **CID** crosswalk, use the
[path-based UniChem builder](#full-chemblpubchem-cid-reference) below.
`bulk=True` on the online translators remains KEGG-only. Do not loop over every
PubChem CID with the online translator to construct a full database.

## Taxonomy reference: download once, resolve offline

```python
from biodbs.fetch import ncbi_download_taxdump
from biodbs.taxonomy import TaxonomyMapper, load_taxdump

archive = ncbi_download_taxdump("data/ncbi")
taxdump = load_taxdump(archive)
mapper = TaxonomyMapper(taxdump=taxdump, use_gbif=False)
result = mapper.map_names(["Escherichia coli", "Bacillus coli"])
assert result.hub_taxid.tolist() == [562, 562]
```

The archive itself is the reusable full reference. On later runs, call
`load_taxdump("data/ncbi/new_taxdump.tar.gz")` without downloading it again.
With no online fetchers attached, this mapper resolves locally. Downloading the
archive does not build a SQLite file: `load_taxdump()` loads dictionaries into
RAM. Expect substantial memory use for the full reference.

If you need SQL queries without loading the archive on each run, export the
loaded dictionaries once. This avoids computing/storing a lineage string for
every name:

```python
import sqlite3

with sqlite3.connect("taxonomy.db") as db:
    db.execute("CREATE TABLE taxon (taxid INTEGER PRIMARY KEY, name TEXT, rank TEXT, parent INTEGER)")
    db.executemany("INSERT INTO taxon VALUES (?, ?, ?, ?)", (
        (taxid, taxdump.names.get(taxid), taxdump.ranks.get(taxid), parent)
        for taxid, parent in taxdump.parents.items()
    ))
    db.execute("CREATE TABLE taxon_name (name TEXT PRIMARY KEY, taxid INTEGER)")
    db.executemany("INSERT INTO taxon_name VALUES (?, ?)", taxdump.name_to_taxid.items())
    db.execute("CREATE TABLE merged (old_taxid INTEGER PRIMARY KEY, taxid INTEGER)")
    db.executemany("INSERT INTO merged VALUES (?, ?)", taxdump.merged.items())
```

Query this file with `sqlite3`, not `TaxonomyMapper`: the mapper does not accept a
SQLite backend. The name index mirrors the current taxdump parser: names are
lowercased, and a name shared by multiple taxids keeps the first occurrence.
It is not an ambiguity-preserving index. For ambiguity-sensitive use, import
every `names.dmp` row into a separate table and retain its name class and taxid.
Keep the original archive as the authoritative snapshot.

NCBI taxonomy is not an automatic SILVA/GTDB/GBIF crosswalk. Mapping another
source needs its identifiers/names and, where available, an explicit crosswalk.
See [Taxonomy Mapping](../taxonomy/mapping.md).

## Query later without a network connection

```python
import sqlite3

with sqlite3.connect("file:human_genes.db?mode=ro", uri=True) as db:
    rows = db.execute(
        "SELECT entrez_id, ensembl_gene_id FROM gene WHERE symbol = ?", ("TP53",),
    ).fetchall()
print(rows)  # [('7157', 'ENSG00000141510')]
```

Use parameterized queries and `fetchall()` so one-to-many matches stay visible.
Read-only mode also prevents accidentally creating an empty database when the
path is wrong. Add indexes for whichever identifier columns you actually query.
For taxonomy, join `taxon_name.taxid` through `merged` to `taxon.taxid`, using
`COALESCE(merged.taxid, taxon_name.taxid)` as the current taxid.

`GeneMapper`, `ChemicalMapper`, and `ProteinMapper` configure online backends;
they do not automatically read these SQLite files or cache all reference data.

## Full ChEMBL/PubChem CID reference

```python
from biodbs.translate import build_chemical_mapping_db

path = build_chemical_mapping_db("mapping.db", source="unichem")
```

This downloads the complete published UniChem ChEMBL (source 1) to PubChem
compound (source 22) export and builds `chemical_mapping(chembl_id, pubchem_cid)`.
It returns a `Path`, stores CIDs as integers, preserves multiple matches in both
directions, removes duplicate pairs, and indexes both identifiers. No additional
dependencies are needed. [ChEMBL documents this bulk crosswalk](https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/general-questions).

Query locally in either direction, keeping all matches:

```python
import sqlite3

with sqlite3.connect("file:mapping.db?mode=ro", uri=True) as db:
    cids = db.execute(
        "SELECT pubchem_cid FROM chemical_mapping WHERE chembl_id=?", ("CHEMBL25",),
    ).fetchall()
    chembl_ids = db.execute(
        "SELECT chembl_id FROM chemical_mapping WHERE pubchem_cid=?", (2244,),
    ).fetchall()
```

Only `source="unichem"` is currently supported. This is a full **published
crosswalk**, not every PubChem CID or every ChEMBL molecule: unmapped identifiers
remain absent. Matching follows UniChem's structure rules and snapshot, so results
can differ from the live online translator. The existing translators and mapper
objects do not automatically use this file.

`chemical_mapping_metadata` stores the source URL, UTC retrieval timestamp,
downloaded archive SHA-256, and distinct row count. The hash identifies the
snapshot; it is not verified against an independently published upstream checksum.
The builder rejects the wrong source header, invalid identifiers, empty exports,
and invalid/truncated gzip files. Source 22's header and numeric-ID validation
guard the expected CID namespace; the builder does not re-query PubChem to verify
every upstream mapping.

The download is temporary and removed after success or failure. Parsing/import
use bounded batches, with one transaction covering every mapping row, index, and
metadata record. Failed imports leave no partial mapping tables; a newly created
empty SQLite file may remain and can be retried. Other tables in the target
database are preserved. Existing `chemical_mapping` or
`chemical_mapping_metadata` objects raise `ValueError` **before downloading**;
refresh into a new file instead of replacing a working reference.

Allow room for the compressed download, the indexed database, and SQLite's
transaction journal. The source archive was approximately 22 MiB compressed
when checked on 2026-10-09; the final SQLite size and build time were not
benchmarked. The fixture tests exercise parsing, both query directions,
deduplication, indexes, rollback, cleanup, and preserving unrelated tables.

## Coverage, validation, and updates

- A complete source export is still only that source's coverage. Unknown inputs
  remain unknown; a full reference is not a guarantee of a mapping for every ID.
- Validate non-empty results and upstream record counts when available. Check
  known mappings after saving and reopening the file; a successful write alone
  does not establish mapping accuracy or completeness.
- Record source URL, retrieval date, source release/update time, row counts, and
  checksums alongside your database. Live upstream data can change between calls.
- Refresh into a new file, validate it, then switch readers to it. Do not replace
  a working reference in place while users are querying it.
- For non-human gene annotations, `biomart_query(dataset=..., attributes=...)`
  without filters requests a whole dataset. Confirm the species dataset and
  attribute names, and validate completeness; it is not the HGNC reference.

## User simulation on 2026-10-09

Using the public APIs on the v0.5.0 development branch, then saving and reopening
an indexed SQLite database:

| Dataset | Rows saved | Fetch + selected export + SQLite write/index time |
| --- | ---: | ---: |
| All approved HGNC human genes | 45,233 (matched `num_found`) | 15.64 s |
| All human KEGG to Entrez mappings | 24,252 | 3.23 s |
| All KEGG compound to ChEBI mappings | 17,191 | 1.30 s |
| All KEGG compound to PubChem SID mappings | 19,527 | 1.42 s |

The combined database, including a two-row taxonomy **fixture**, was 5.75 MiB.
The HGNC timing also included attempting to save one raw record, which failed
because it contained lists. Offline queries with network sockets disabled checked
TP53, BRCA1, water's ChEBI/SID mappings, and the fixture synonym `Bacillus coli`.
SQLite integrity and index-use checks passed. These are spot checks and one-run
timings, not exhaustive accuracy checks or performance guarantees.

The full taxonomy archive's HTTP headers reported 162,293,876 bytes (154.8 MiB)
compressed. The full archive was **not downloaded or benchmarked** in this
simulation; taxonomy loading, mapping, and the SQL export recipe were tested
with the repository fixture. No whole ChEMBL/PubChem export or whole BioMart
dataset was downloaded.
