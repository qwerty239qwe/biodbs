# Changelog

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
