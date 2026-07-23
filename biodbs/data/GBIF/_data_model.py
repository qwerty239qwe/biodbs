"""Data model for GBIF backbone name matches."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GBIFMatch:
    """One GBIF ``/species/match`` result."""

    query: str
    usage_key: int | None = None
    canonical_name: str | None = None
    rank: str | None = None
    status: str | None = None          # ACCEPTED / SYNONYM / DOUBTFUL / ...
    match_type: str | None = None      # EXACT / FUZZY / HIGHERRANK / NONE
    confidence: int | None = None
    is_synonym: bool = False

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "usage_key": self.usage_key,
            "canonical_name": self.canonical_name,
            "rank": self.rank,
            "status": self.status,
            "match_type": self.match_type,
            "confidence": self.confidence,
            "is_synonym": self.is_synonym,
        }
