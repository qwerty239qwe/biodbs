# Plan: RESCRIPt-parity database fetchers for biodbs

## Goal
Add fetchers for the databases biodbs doesn't yet cover, matching RESCRIPt's
reach: **UNITE, PR2, MIDORI2, EUKARYOME, BOLD, GreenGenes**.
(SILVA done, NCBI done, GTDB in progress already present.)

RESCRIPt's fetch actions cover: SILVA, NCBI, GTDB, UNITE, PR2, MIDORI2,
EUKARYOME. GreenGenes has no dedicated RESCRIPt action (it lives in the
separate `q2-greengenes2` plugin) and BOLD is tutorial-only — both are still
fetchable as biodbs modules (GreenGenes = static FTP releases, BOLD = public
API), so they are included here.

## Shared template (per DB — copy the existing SILVA/GTDB quad)
Every DB except BOLD is a static-release download, same shape as the existing
SILVA/GTDB fetchers. For each `<DB>`:

1. **`biodbs/data/<DB>/`**
   - `_data_model.py` — release/file dataclasses (mirror `SILVARelease`, `SILVAFile`)
   - `data.py` — `BaseFetchedData` subclasses (`<DB>SequenceData`, `<DB>TaxonomyData`, list data)
   - `__init__.py` — re-exports
2. **`biodbs/fetch/<DB>/`**
   - `funcs.py` — URL builders + parse the release listing (pure funcs, fully unit-testable)
   - `<db>_fetcher.py` — `<DB>_Fetcher(BaseDataFetcher)` with `list_releases()`, `get_sequences()`, `get_taxonomy()`, `download_*()`
   - `__init__.py`
3. **`tests/test_fetch/<db>/`** — `test_<db>_funcs.py` (URL/parse, mocked),
   `test_<db>_fetcher.py` (mocked HTTP), `test_<db>_data.py`; live calls behind
   the `integration` marker
4. **Register** — export from `biodbs/fetch/__init__.py` + `biodbs/__init__.py`
5. **Docs** — `docs/fetch/<db>.md`, a section in `docs/api/fetch.md`, nav entry in `mkdocs.yml`

Reuse existing infra: `BaseDataFetcher.schedule_process` (rate-limited bulk
download), `RateLimiter` singleton, `raise_for_status`/custom exceptions,
`configure_rate_limits_for_ci` in `tests/conftest.py` (add each new host).

## Per-DB specifics (the only part that differs)

| DB | Listing source | Download / parse notes |
|----|----------------|------------------------|
All URL patterns below are verified against RESCRIPt's own source (`get_*.py`),
which is authoritative — RESCRIPt already implements EUKARYOME/MIDORI2/UNITE/PR2.
**None of them scrape HTML**; they build static direct URLs or hit a REST API.

| DB | Listing source | Download / parse notes |
|----|----------------|------------------------|
| **PR2** *(done)* | GitHub Releases API: `api.github.com/repos/pr2database/pr2database/releases` | JSON to asset URLs. No scraping. Version = release tag. Implemented. |
| **GreenGenes** | Open HTTP dir listing: `http://ftp.microbio.me/greengenes_release/` | Parse the directory index (real dirs: `gg_13_8_otus/`, `gg_13_5/`, `2022.10/`, `2024.09/`, `current/`). `.fasta` + `_otu_taxonomy.txt`. GreenGenes2 lives in `q2-greengenes2`, not RESCRIPt core. |
| **EUKARYOME** | Static direct URL (no scraping) | `https://sisu.ut.ee/wp-content/uploads/sites/643/General_EUK_{gene}_v{ver}.zip`, `gene ∈ {SSU,LSU,ITS,longread}`, `ver` default `2.0`. Host is `sisu.ut.ee`. Gotcha: some zips contain a **nested 7z** needing a 2nd extract step. |
| **MIDORI2** | Static direct URL (no scraping) | `https://www.reference-midori.info/download/Databases/{GenBankNNN_YYYY-MM-DD}/{QIIME\|QIIME_sp}/{uniq\|longest}/MIDORI2_{UNIQ\|LONGEST}_NUC_{SP_\|}GB{NNN}_{gene}_QIIME.{fasta\|taxon}.gz`. Version is the **full** string (e.g. `GenBank271_2026-04-07`), not `GB260`. Two files per gene: `.fasta.gz` + `.taxon.gz` sidecar. |
| **UNITE** *(fiddliest of the static set)* | PlutoF JSON REST API | `https://api.plutof.ut.ee/v1/public/dois/?format=vnd.api%2Bjson&identifier={DOI}`, driven by a **maintained `version→taxon_group→singletons→DOI` mapping dict** (the real maintenance burden). Response yields media URL → download `.tgz` → extract → keep files containing `_dev` → select by `cluster_id`. Params: version (10.0/9.0/8.3/8.2), taxon_group (fungi/eukaryotes), cluster_id (99/97/dynamic), singletons (bool). |
| **BOLD** *(deferred — high risk)* | Portal API `https://portal.boldsystems.org/api/` | **Legacy `index.php/API_Public/combined` is dead (404).** Current flow is token-based multi-step: `/api/query/preprocessor` → `/api/query` (returns token) → `/api/documents/<id>/download`, BCDM/DwC TSV/FASTA, 1M-record cap. **No RESCRIPt precedent** — needs fresh design; prototype before committing. |

## Execution order & checkpoints
Build one DB fully (TDD: funcs to data to fetcher to docs) and get it merged
before the next, in this order for rising difficulty:

**PR2 ✅ → GreenGenes ✅ → EUKARYOME ✅ → MIDORI2 ✅ → UNITE ✅ → BOLD (deferred)**

- GreenGenes: one directory-index parse, static download.
- EUKARYOME / MIDORI2: pure static-URL builders — simplest of all (no listing at
  all, just construct the URL from params). Arguably simpler than GreenGenes.
- UNITE: PlutoF REST API + a maintained DOI mapping table + archive extraction —
  the fiddliest of the static set.
- BOLD: deferred until the Portal API multi-step token flow is prototyped.

## Risks / notes
- The genuinely reusable helper is **"download archive (zip/tgz/7z) → extract →
  (fasta, taxonomy)"**, shared by EUKARYOME/MIDORI2/UNITE — extract it after the
  *second* DB needs it, not before. (There is no HTML scraping to share.)
- Extra deps: **7z extraction** for EUKARYOME's nested archives; MIDORI2's
  `.taxon.gz` sidecar taxonomy handling.
- UNITE's DOI mapping dict is the maintenance point — keep it in `funcs.py` where
  it is easy to update per release.
- License/citation differs per DB — surface each DB's citation string in its data
  model / docs (RESCRIPt does this).
- Large downloads — stream to disk (as FDA/others do), don't hold in memory.

Skipped for now: no shared archive-extract helper up front (YAGNI — extract after
2nd consumer); BOLD deferred (dead legacy endpoint, no RESCRIPt precedent, needs a
prototyped multi-step flow).

## Sources
- RESCRIPt (authoritative fetch logic): https://github.com/bokulich-lab/RESCRIPt/tree/master/rescript
  (`get_eukaryome.py`, `get_midori2.py`, `get_unite.py`, `get_gtdb.py`)
- GreenGenes: http://ftp.microbio.me/greengenes_release/
- EUKARYOME files: https://sisu.ut.ee/wp-content/uploads/sites/643/
- MIDORI2: https://www.reference-midori.info/download/Databases/
- UNITE via PlutoF API: https://api.plutof.ut.ee/v1/public/dois/
- PR2 releases: https://github.com/pr2database/pr2database/releases
- BOLD Portal API: https://portal.boldsystems.org/api/
