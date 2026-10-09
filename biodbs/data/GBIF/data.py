"""List wrapper for GBIF matches."""

from __future__ import annotations

from typing import Iterator

import pandas as pd

from biodbs.data._base import BaseFetchedData
from biodbs.data.GBIF._data_model import GBIFMatch


class GBIFMatchListData(BaseFetchedData):
    """List wrapper for a batch of GBIF backbone name matches."""

    def __init__(self, matches: list[GBIFMatch]):
        super().__init__(matches)
        self._matches = matches

    def __len__(self) -> int:
        return len(self._matches)

    def __iter__(self) -> Iterator[GBIFMatch]:
        return iter(self._matches)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._matches[key]
        for match in self._matches:
            if match.query == key:
                return match
        raise KeyError(key)

    def names(self) -> list[str]:
        return [match.query for match in self._matches]

    def as_dict(self) -> list[dict]:
        return [match.to_dict() for match in self._matches]

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        if engine != "pandas":
            raise ValueError("GBIF data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())
