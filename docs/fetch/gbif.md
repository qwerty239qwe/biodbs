# GBIF

The GBIF backbone taxonomy is a canonical name registry spanning all of life. biodbs
uses it to resolve a scientific name to its **canonical name**, rank, and
accepted/synonym status — the name-canonicalisation authority behind the taxonomy
mapping table (see [Taxonomy Mapping](../taxonomy/mapping.md)).

```python
from biodbs.fetch import gbif_match_name

match = gbif_match_name("Escherichia coli")
print(match.canonical_name, match.rank, match.status)  # Escherichia coli SPECIES ACCEPTED
```

`match.match_type` is `EXACT`, `FUZZY`, `HIGHERRANK`, or `NONE`; `match.is_synonym`
flags names GBIF treats as synonyms. Pass `strict=True` to reject fuzzy matches.
