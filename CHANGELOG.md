# Changelog

## 0.5.0

Adds a taxonomic ID **canonical / mapping table**: resolve organism names and
per-database lineage strings to one hub identifier (NCBI Taxonomy `taxid`) and join
any two reference databases on it.

- New `biodbs.taxonomy` API: `TaxonomyMapper` (`map_names`, `map_lineage`, `resolve`),
  `load_taxdump` (parse `new_taxdump.tar.gz` into an in-memory hub table), and
  `merge_on_hub` (cross-database join). Output is a pandas DataFrame keyed on
  `hub_taxid`.
- Added `biodbs.translate.translate_taxon_names` (also available at the top level)
  as a thin wrapper over a configured `TaxonomyMapper.map_names`. Existing
  taxonomy imports remain unchanged; offline regression checks cover the wrapper.
- Unify ChEMBL/PubChem and KEGG chemical conversion under `translate_chemical_ids`,
  and KEGG gene conversion under `translate_gene_ids`. Keep explicit SID/CID types,
  structure checks, and legacy helper output contracts.
- Add optional `GeneMapper`, `ChemicalMapper`, and `ProteinMapper` configuration
  objects. Ordinary calls retain their effective defaults; explicit mapper conflicts
  raise. Protein helpers share the main translator, with optional `all_matches`
  and review filters. Main KEGG routes require `bulk=True` for empty-input bulk
  queries; legacy KEGG wrappers retain their historical whole-database behavior.
- Allow taxonomic name translation without a mapper using online NCBI resolution;
  taxdumps are never downloaded automatically.
- Added the **GBIF** backbone fetcher (`gbif_match_name`/`gbif_match_names`) as the
  all-life canonical-name and synonym authority.
- Added `ncbi_taxonomy_name_to_id` (name → taxid via E-utilities esearch).
- Added `gtdb_ncbi_crosswalk` (GTDB species → NCBI taxid, majority vote from GTDB
  metadata) so GTDB lineage strings join the hub directly.

### Reliability fixes

- Fix MIDORI2 downloads after the upstream migration to Zenodo, resolving explicit
  releases from both the current and legacy archives. Preserve legacy version
  spellings and explicit direct-file mirrors. Verify the published bundle MD5,
  extract only the requested gzip file atomically, and remove temporary files;
  failed overwrites preserve existing output. Default `build_url` now requires a
  metadata lookup and returns the containing ZIP URL. Each uncached download needs
  temporary space for the full bundle plus the requested file. Add offline and
  bounded-download live regression checks; see the [MIDORI2 guide](docs/fetch/midori2.md).
- Surface Ensembl and ChEMBL/PubChem outages in live translator-quality checks
  before translators convert them to missing mappings. Keep exact-ID assertions
  strict for successful responses and add offline guard regression cases.
- Isolate PubChem PUG REST/View and QuickGO request parameters during concurrent
  fetching. Reuse per-thread HTTP connections in the retry helper, QuickGO, and
  Ensembl; close failed retry responses and bound QuickGO/Ensembl request timeouts.
- Separate batch request start rates from maximum in-flight concurrency (default
  10). Fetch QuickGO annotations in 200-record pages and validate the service limit.
- Batch chemical properties for up to 100 unique CIDs, deduplicate input lookups,
  match responses by CID, and isolate failed compounds with individual fallbacks.
- Isolate GO JSON caches by species, aspect, and evidence filters. Cache full
  fetched gene sets before term-size filtering and ignore old ambiguous cache keys.
- Add 71 offline fetching/chemical/cache regression cases, including actual
  loopback HTTP connection reuse and request-count comparisons on mock data.
- Discover current SILVA classifiers in live checks and documentation rather than
  relying on a retired release folder. Keep binary-header and MD5-listing checks.
- Give whole-organism QuickGO ORA checks a separate, longer CI job, and use GO IDs
  when annotation names are missing so pathway caches can be written and reused.
- Correct Ensembl symbol translation namespaces and stable-ID identity mappings.
- Read all UniProt mapping and explicit-ID NCBI gene-report pages.
- Preserve duplicate multi-target rows and chemical dictionary input keys; omit
  missing BioMart IDs instead of returning NaN mappings.
- Fetch each unique HGNC input once for all targets. Keep RefSeq protein and mRNA
  namespaces distinct; reject unsupported HGNC protein aliases and avoid guessing
  NCBI accession-to-gene associations.
- Verify ChEMBL–PubChem mappings by structure, and document KEGG PubChem SIDs.
- Add exact-ID and request-count translator regression checks, with live reference
  tests in integration CI and documented backend limitations.
- Prevent unresolved taxonomy IDs from joining to each other, while preserving
  unmatched rows in left, right, and outer joins.
- Classify offline taxdump matches as accepted scientific names or synonyms.
- Use atomic downloads for GTDB, HOMD, and GreenGenes, preserving existing files
  when replacement downloads fail.
- Fix retries for real HTTP error responses and enforce batch request rates
  using a shared monotonic start schedule; reject non-positive rates.
- Isolate live Disease Ontology, NCBI, and UniProt tests from the unit suite and
  include them in integration CI. Add 74 regression cases for these fixes.

## 0.4.1

Fixes SILVA discovery/download integrity after SILVA's site migration and adds
fetch-only access to the exact HOMD, MOMD, and NCBI artifacts used by FOMC-inspired
oral-microbiome pipelines.

### SILVA fixes

- Fixed SILVA file and classifier downloads after SILVA's site migration: files
  are now fetched from `fileadmin/silva_databases/current/` (the `current-release/`
  paths became CMS browse pages that were being saved as HTML). A download that
  receives an HTML page now raises a clear error instead of silently saving it.
- Fixed SILVA listings (`list_current_files`, `list_archive_releases`), which
  returned nothing because SILVA's CMS uses root-relative links; listings now
  return both sub-directories and downloadable file leaves (with `is_dir`), so
  classifier filenames and their `.md5` sidecars are discoverable.
- `download_classifier` now takes the nested path below the classifier directory
  and verifies the download against SILVA's published `.md5` by default
  (`verify=False` to skip); `download_file` gained an opt-in `verify_md5`.
- `download_file` now treats a suffix-less destination (e.g. `"data/silva"`) as a
  directory instead of a filename.

### New fetch capabilities

- Added a shared atomic downloader: every large download streams to a temporary
  file and is moved into place only after the transfer (and any published MD5)
  succeeds, so an interrupted download is never cached as a valid file.
- **HOMD/MOMD** — `list_16s_refseq`, `download_16s_refseq`, and the new
  `download_16s_taxonomy` are now version- and source-aware (`version="15.22"`,
  `source="homd"|"momd"`), selecting the unaligned `.fasta` and `.qiime.taxonomy`
  for a pinned release. MOMD is served from its own `momd.org` host.
- **NCBI** — added `download_blast_database` (e.g. `16S_ribosomal_RNA`) and
  `download_taxdump` (`new_taxdump`), both MD5-verified against NCBI's sidecars.
- Added the [FOMC Reference Sources](docs/fetch/fomc-references.md) fetch-only recipe and
  live contract tests (SILVA leaf/MD5 discovery, HOMD/MOMD listings, NCBI archive
  reachability) with `homd` and `ncbi` added to the CI integration matrix.

## 0.4.0

- Added reference-database fetchers matching the databases supported by RESCRIPt:
  - **PR2** — Protist Ribosomal Reference release files via the GitHub Releases API.
  - **GreenGenes** — release-directory browsing and downloads over `ftp.microbio.me`.
  - **EUKARYOME** — eukaryote-wide rRNA (SSU/LSU/ITS/longread) reference archives.
  - **MIDORI2** — QIIME-formatted mitochondrial reference files (fasta + taxon sidecar).
  - **UNITE** — fungal/eukaryote ITS release archives resolved via the PlutoF DOI API.
- Added the **GTDB** and **HOMD** fetchers.
- Each fetcher ships offline (mocked) unit tests and live integration tests, plus
  API docs and user guides.
- Routed PubChem requests through the shared rate-limited `request_with_retry`
  helper so the configured per-host rate limit and 429 backoff take effect.
- Hardened live integration CI by rerunning only failed tests
  (`pytest-rerunfailures`) to absorb third-party API throttling of CI IP ranges.
- BOLD is not yet included: its legacy API endpoint is retired and the current
  Portal API needs a multi-step token flow (tracked in `docs/dev/rescript-parity-plan.md`).

## 0.3.1

- Isolated live KEGG and QuickGO API tests behind the `integration` marker.
- Added offline mocked KEGG coverage for URL construction across REST operations.
- Replaced broad JSON parsing exception handlers in fetch utilities with explicit decode-related handling.
- Established an enforceable `ruff check .` baseline with targeted ignores for intentional public re-export modules and deprecated compatibility code.
- Documented the offline test gate and live integration test command for contributors.
