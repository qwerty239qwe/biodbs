"""ClinVar fetched data class."""

from __future__ import annotations

from typing import List

import pandas as pd

from biodbs.data._base import BaseFetchedData
from biodbs.data.ClinVar._data_model import ClinVarVariant


class ClinVarFetchedData(BaseFetchedData):
    """Fetched data from the ClinVar E-utilities API (esummary).

    Wraps the JSON response from::

        esummary.fcgi?db=clinvar&id=<ids>&retmode=json

    Attributes:
        results: Parsed :class:`ClinVarVariant` objects, one per UID.
        uids: The UIDs returned by the API, in order.
        total_count: Total hits reported by a preceding esearch (if known).
    """

    def __init__(self, content: dict, total_count: int = 0):
        super().__init__(content)
        result = content.get("result", {})
        self.uids: List[str] = result.get("uids", [])
        self.total_count: int = total_count

        self.results: List[ClinVarVariant] = [
            ClinVarVariant.from_esummary_dict(uid, result[uid])
            for uid in self.uids
            if uid in result
        ]

    # ------------------------------------------------------------------
    # Sequence protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.results[key]
        if isinstance(key, str):
            return self._get_by_id(key)
        raise TypeError(
            f"Indices must be integers, slices, or strings, not {type(key).__name__}"
        )

    def __repr__(self) -> str:
        return (
            f"<ClinVarFetchedData: {len(self.results)} variants"
            + (f" (of {self.total_count} found)" if self.total_count else "")
            + ">"
        )

    # ------------------------------------------------------------------
    # ID lookup
    # ------------------------------------------------------------------

    def _get_by_id(self, id_value: str) -> ClinVarVariant:
        """Look up a variant by variation ID, VCV accession, or RCV accession.

        Raises:
            KeyError: If no matching variant is found.
        """
        id_lower = id_value.lower()
        for v in self.results:
            if (
                v.variation_id == id_value
                or v.accession.lower() == id_lower
                or v.accession_version.lower() == id_lower
                or id_value in v.rcv_accessions
            ):
                return v
        raise KeyError(id_value)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def variation_ids(self) -> List[str]:
        """Return all variation IDs."""
        return [v.variation_id for v in self.results]

    def accessions(self) -> List[str]:
        """Return all VCV accessions."""
        return [v.accession for v in self.results]

    def gene_symbols(self) -> List[str]:
        """Return all unique gene symbols across all variants."""
        seen = set()
        out = []
        for v in self.results:
            for sym in v.gene_symbols:
                if sym not in seen:
                    seen.add(sym)
                    out.append(sym)
        return out

    def pathogenic(self) -> "ClinVarFetchedData":
        """Return a new instance containing only pathogenic/likely pathogenic variants."""
        filtered = {
            "result": {
                "uids": [v.variation_id for v in self.results if v.is_pathogenic],
                **{
                    v.variation_id: self._content.get("result", {}).get(v.variation_id, {})
                    for v in self.results
                    if v.is_pathogenic
                },
            }
        }
        return ClinVarFetchedData(filtered, total_count=sum(1 for v in self.results if v.is_pathogenic))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def as_dict(self) -> List[dict]:
        """Return a list of flat dicts, one per variant."""
        return [v.to_dict() for v in self.results]

    def as_dataframe(self) -> pd.DataFrame:
        """Convert variants to a :class:`~pandas.DataFrame`.

        Returns:
            DataFrame with one row per variant, columns matching
            :class:`ClinVarVariant` fields.
        """
        records = self.as_dict()
        df = pd.DataFrame(records)
        # Expand list columns to semicolon-separated strings for tabular display
        for col in ("gene_symbols", "gene_ids", "conditions", "rcv_accessions"):
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: ";".join(x) if isinstance(x, list) else x
                )
        return df
