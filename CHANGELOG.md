# Changelog

## 0.4.1

- Fixed SILVA file and classifier downloads after SILVA's site migration: files
  are now fetched from `fileadmin/silva_databases/current/` (the `current-release/`
  paths became CMS browse pages that were being saved as HTML). A download that
  receives an HTML page now raises a clear error instead of silently saving it.
- `download_classifier` now takes the nested path below the classifier directory,
  matching SILVA's per-release/marker layout.
- Fixed SILVA listings (`list_current_files`, `list_archive_releases`), which
  returned nothing because SILVA's CMS uses root-relative links; they now browse
  the release tree correctly.
- `download_file` now treats a suffix-less destination (e.g. `"data/silva"`) as a
  directory instead of a filename, and streams to a temporary file that is moved
  into place only on success, so an interrupted download is no longer cached as a
  valid file.

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
