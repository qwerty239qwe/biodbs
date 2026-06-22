"""Fetched data wrappers for LPSN."""

from typing import Any, Iterator

import pandas as pd

from biodbs.data._base import BaseFetchedData
from biodbs.data.LPSN._data_model import LPSNEntry


class LPSNFetchedData(BaseFetchedData):
    """Fetched LPSN taxon records."""

    def __init__(self, content: dict[str, Any] | list[dict[str, Any]]):
        super().__init__(content)
        records = content.get("results", []) if isinstance(content, dict) else content
        self.results = [LPSNEntry.from_dict(item) for item in records]
        self.count = content.get("count", len(self.results)) if isinstance(content, dict) else len(self.results)
        self.next = content.get("next") if isinstance(content, dict) else None
        self.previous = content.get("previous") if isinstance(content, dict) else None

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self) -> Iterator[LPSNEntry]:
        return iter(self.results)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.results[key]
        if isinstance(key, str):
            return self._get_by_id_or_name(key)
        raise TypeError(f"Unsupported key type: {type(key).__name__}")

    def _get_by_id_or_name(self, value: str) -> LPSNEntry:
        value_lower = value.lower()
        for entry in self.results:
            if str(entry.id) == value or (entry.full_name and entry.full_name.lower() == value_lower):
                return entry
        raise KeyError(value)

    def as_dict(self) -> list[dict[str, Any]]:
        """Return records as dictionaries."""
        return [entry.to_dict() for entry in self.results]

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        """Convert records to a pandas DataFrame."""
        if engine != "pandas":
            raise ValueError("LPSN data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def ids(self) -> list[int]:
        """Return LPSN IDs in this response."""
        return [entry.id for entry in self.results if entry.id is not None]

    def names(self) -> list[str]:
        """Return taxon full names in this response."""
        return [entry.full_name for entry in self.results if entry.full_name]


class LPSNSearchData(BaseFetchedData):
    """LPSN search result IDs."""

    def __init__(self, content: dict[str, Any]):
        super().__init__(content)
        self.results = list(content.get("results", []))
        self.count = content.get("count", len(self.results))
        self.next = content.get("next")
        self.previous = content.get("previous")

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, key):
        return self.results[key]

    def as_dict(self) -> list[dict[str, Any]]:
        """Return IDs as dictionaries for DataFrame compatibility."""
        return [{"id": item} for item in self.results]

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        """Convert IDs to a pandas DataFrame."""
        if engine != "pandas":
            raise ValueError("LPSN data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def ids(self) -> list[int]:
        """Return search result IDs."""
        return [int(item) for item in self.results]
