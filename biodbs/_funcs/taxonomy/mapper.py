"""Build a canonical / cross-database taxon mapping table around NCBI taxid."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import pandas as pd

MAPPING_COLUMNS = [
    "query",
    "source",
    "source_id",
    "hub_taxid",
    "canonical_name",
    "rank",
    "name_status",
    "match_type",
    "lineage",
]


@dataclass
class TaxonRecord:
    query: str
    source: str = "name"
    source_id: str | None = None
    hub_taxid: int | None = None
    canonical_name: str | None = None
    rank: str | None = None
    name_status: str = "unmatched"       # accepted / synonym / unmatched
    match_type: str = "none"             # taxdump / ncbi / gtdb-crosswalk / none
    lineage: str | None = None


class TaxonomyMapper:
    """Resolve names / lineage strings to NCBI taxid and canonical names.

    Args:
        taxdump: optional loaded :class:`NCBITaxonomy` for offline bulk resolution.
        ncbi_fetcher: optional object exposing ``taxonomy_name_to_id`` for online
            fallback (typically ``biodbs.fetch.NCBI.NCBI_Fetcher``).
        gbif_fetcher: optional object exposing ``match_name`` for canonical names.
        gtdb_crosswalk: optional ``{gtdb_species_name: ncbi_taxid}`` for lineage joins.
        use_gbif: set False to skip canonical-name enrichment.
    """

    def __init__(
        self,
        taxdump=None,
        ncbi_fetcher=None,
        gbif_fetcher=None,
        gtdb_crosswalk: dict[str, int] | None = None,
        use_gbif: bool = True,
    ):
        self.taxdump = taxdump
        self.ncbi_fetcher = ncbi_fetcher
        self.gbif_fetcher = gbif_fetcher
        self.gtdb_crosswalk = gtdb_crosswalk or {}
        self.use_gbif = use_gbif

    def resolve(self, name: str, source: str = "name", source_id: str | None = None) -> TaxonRecord:
        record = TaxonRecord(query=name, source=source, source_id=source_id)

        # 1. hub taxid: GTDB crosswalk (lineage sources) -> taxdump -> online NCBI
        if source == "gtdb" and name in self.gtdb_crosswalk:
            record.hub_taxid = self.gtdb_crosswalk[name]
            record.match_type = "gtdb-crosswalk"
        elif self.taxdump is not None and self.taxdump.taxid_for_name(name) is not None:
            record.hub_taxid = self.taxdump.taxid_for_name(name)
            record.match_type = "taxdump"
        elif self.ncbi_fetcher is not None:
            hit = self.ncbi_fetcher.taxonomy_name_to_id([name]).get(name)
            if hit is not None:
                record.hub_taxid = hit
                record.match_type = "ncbi"

        # 2. rank + lineage from taxdump when available
        if record.hub_taxid is not None and self.taxdump is not None:
            record.rank = self.taxdump.rank(record.hub_taxid)
            lineage = self.taxdump.lineage(record.hub_taxid)
            if lineage:
                record.lineage = ";".join(f"{rank}:{taxon}" for rank, taxon in lineage)

        # 3. canonical name + accepted/synonym status from GBIF
        if self.use_gbif and self.gbif_fetcher is not None:
            match = self.gbif_fetcher.match_name(name)
            if match.canonical_name:
                record.canonical_name = match.canonical_name
                record.rank = record.rank or (match.rank.lower() if match.rank else None)
                if match.status == "ACCEPTED":
                    record.name_status = "accepted"
                elif match.is_synonym or match.status == "SYNONYM":
                    record.name_status = "synonym"

        # Classify offline matches against the taxdump's scientific name.
        if record.name_status == "unmatched" and record.match_type == "taxdump":
            scientific_name = self.taxdump.name(record.hub_taxid)
            if scientific_name:
                record.name_status = (
                    "accepted" if name.strip().lower() == scientific_name.lower() else "synonym"
                )
            record.canonical_name = record.canonical_name or scientific_name

        return record

    def map_names(self, names: Iterable[str], source: str = "name") -> pd.DataFrame:
        records = [self.resolve(name, source=source) for name in names]
        return self._to_frame(records)

    def map_lineage(self, lineages: Iterable[str], source: str = "gtdb") -> pd.DataFrame:
        records = []
        for lineage in lineages:
            species = self._leaf_species(lineage)
            record = self.resolve(species, source=source, source_id=lineage)
            record.query = lineage
            records.append(record)
        return self._to_frame(records)

    @staticmethod
    def _leaf_species(lineage: str) -> str:
        if "s__" in lineage:
            return lineage.rsplit("s__", 1)[-1].strip()
        return lineage.split(";")[-1].strip()

    @staticmethod
    def _to_frame(records: list[TaxonRecord]) -> pd.DataFrame:
        frame = pd.DataFrame([asdict(r) for r in records])
        return frame.reindex(columns=MAPPING_COLUMNS)


def merge_on_hub(
    left: pd.DataFrame,
    right: pd.DataFrame,
    how: str = "outer",
    suffixes: tuple[str, str] = ("_a", "_b"),
) -> pd.DataFrame:
    """Join on ``hub_taxid``; unresolved IDs never match each other."""
    # pandas matches null keys; unresolved taxa must remain separate rows.
    null_key = object()  # A unique column label cannot overwrite caller data.
    left, right = left.copy(), right.copy()
    left[null_key] = left["hub_taxid"].isna()
    right[null_key] = False
    return left.merge(right, on=["hub_taxid", null_key], how=how, suffixes=suffixes).drop(columns=[null_key])
