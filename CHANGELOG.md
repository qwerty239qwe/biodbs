# Changelog

## 0.3.1

- Isolated live KEGG and QuickGO API tests behind the `integration` marker.
- Added offline mocked KEGG coverage for URL construction across REST operations.
- Replaced broad JSON parsing exception handlers in fetch utilities with explicit decode-related handling.
- Established an enforceable `ruff check .` baseline with targeted ignores for intentional public re-export modules and deprecated compatibility code.
- Documented the offline test gate and live integration test command for contributors.
