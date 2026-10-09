"""GBIF backbone taxonomy name-matching fetcher."""

from __future__ import annotations

from urllib.parse import urljoin

from biodbs.data.GBIF import GBIFMatch, GBIFMatchListData
from biodbs.exceptions import raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_BASE_URL = "https://api.gbif.org/v1/"
_HOST = "api.gbif.org"

get_rate_limiter().set_rate(_HOST, 10)


class GBIF_Fetcher:
    """Resolve names against the GBIF backbone taxonomy (canonical names + synonyms)."""

    def __init__(self, base_url: str = _BASE_URL):
        self.base_url = base_url

    def match_name(self, name: str, *, strict: bool = False) -> GBIFMatch:
        """Match a single name via GBIF ``/species/match``."""
        url = urljoin(self.base_url, "species/match")
        response = request_with_retry(
            url,
            params={"name": name, "strict": str(strict).lower()},
        )
        raise_for_status(response, "GBIF", url=url)
        payload = response.json()
        return GBIFMatch(
            query=name,
            usage_key=payload.get("usageKey"),
            canonical_name=payload.get("canonicalName"),
            rank=payload.get("rank"),
            status=payload.get("status"),
            match_type=payload.get("matchType"),
            confidence=payload.get("confidence"),
            is_synonym=bool(payload.get("synonym", False)),
        )

    def match_names(self, names: list[str], *, strict: bool = False) -> GBIFMatchListData:
        """Match many names; one request per name (GBIF has no batch match endpoint)."""
        return GBIFMatchListData([self.match_name(name, strict=strict) for name in names])
