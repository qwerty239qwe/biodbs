# LPSN

The LPSN API provides nomenclature and taxonomy records for prokaryotic names.

LPSN requires a free API account. biodbs uses the LPSN web API directly with `requests`; it does not depend on the official `lpsn` Python package or `python-keycloak`.

## Credentials

Use either a bearer token:

```bash
export BIODBS_LPSN_TOKEN="..."
```

Or username and password:

```bash
export BIODBS_LPSN_USERNAME="you@example.org"
export BIODBS_LPSN_PASSWORD="..."
```

## Fetch Records

```python
from biodbs.fetch.LPSN import LPSN_Fetcher

fetcher = LPSN_Fetcher()
data = fetcher.fetch([520424, 4948, 17724])

for entry in data:
    print(entry.id, entry.full_name, entry.category)
```

The LPSN `/fetch` endpoint accepts up to 100 IDs at a time. biodbs chunks longer ID lists automatically.

## Advanced Search

```python
hits = fetcher.advanced_search(category="species", riskgroup="1")
print(hits.ids())
```

Pythonic keyword names are converted to API parameter names:

```python
hits = fetcher.advanced_search(
    taxon_name="Bacillus",
    validly_published="yes",
    correct_name="yes",
)
```

## Flexible Search

```python
hits = fetcher.flexible_search({"category": "species"})
```

To get full records after search:

```python
records = fetcher.search_and_fetch(category="species", riskgroup="1")
```

## Convenience Functions

```python
from biodbs.fetch import lpsn_fetch, lpsn_advanced_search

records = lpsn_fetch([520424, 4948])
hits = lpsn_advanced_search(category="species")
```

## Notes

LPSN data is subject to LPSN copyright and usage terms. Some taxonomy fields reflect current LPSN opinions and may change over time.

