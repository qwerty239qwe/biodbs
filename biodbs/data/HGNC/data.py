"""HGNC fetched data class."""

from biodbs.data._base import BaseFetchedData
from biodbs.data.HGNC._data_model import HGNCEntry
from typing import List, Optional, Dict, Any, Union
import pandas as pd


class HGNCFetchedData(BaseFetchedData):
    """Fetched data from the HGNC REST API.

    Wraps responses from both the ``/fetch`` and ``/search`` endpoints.

    - ``/fetch`` returns full gene records; each item is an :class:`HGNCEntry`.
    - ``/search`` returns lightweight summaries (hgnc_id, symbol, score only);
      items are plain dicts since full records are not returned.

    Attributes:
        results: List of records.  Full :class:`HGNCEntry` objects for
            fetch responses; plain dicts for search responses.
        num_found: Total number of matching records reported by the API.
        is_search: ``True`` when the data came from a ``/search`` request.
    """

    def __init__(
        self,
        content: dict,
        is_search: bool = False,
    ):
        super().__init__(content)
        self.is_search = is_search

        response = content.get("response", {})
        self.num_found: int = response.get("numFound", 0)
        docs: List[dict] = response.get("docs", [])

        if is_search:
            # Search returns lightweight dicts (hgnc_id, symbol, score)
            self.results: List[Union[HGNCEntry, dict]] = docs
        else:
            # Fetch returns full records — parse into HGNCEntry objects
            self.results = [HGNCEntry.from_dict(d) for d in docs]

    # ------------------------------------------------------------------
    # Sequence protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.results)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.results[key]
        if isinstance(key, str):
            return self._get_by_id(key)
        raise TypeError(
            f"Indices must be integers, slices, or strings, not {type(key).__name__}"
        )

    def __iter__(self):
        return iter(self.results)

    def __repr__(self) -> str:
        kind = "search hits" if self.is_search else "gene entries"
        return f"<HGNCFetchedData: {len(self.results)} {kind} (of {self.num_found} found)>"

    # ------------------------------------------------------------------
    # ID lookup
    # ------------------------------------------------------------------

    def _get_by_id(self, id_value: str) -> Union[HGNCEntry, dict]:
        """Return a record by HGNC ID or gene symbol (case-insensitive).

        For fetch responses, matches against :attr:`HGNCEntry.hgnc_id` and
        :attr:`HGNCEntry.symbol`.  For search responses, matches against the
        ``hgnc_id`` and ``symbol`` keys of the summary dicts.

        Raises:
            KeyError: If no matching record is found.
        """
        id_lower = id_value.lower()
        for item in self.results:
            if isinstance(item, HGNCEntry):
                if item.hgnc_id == id_value or (
                    item.symbol and item.symbol.lower() == id_lower
                ):
                    return item
            else:
                if item.get("hgnc_id") == id_value or (
                    item.get("symbol", "").lower() == id_lower
                ):
                    return item
        raise KeyError(id_value)

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def as_dict(self) -> List[Dict[str, Any]]:
        """Return records as a list of plain dicts."""
        if self.is_search:
            return list(self.results)
        return [entry.to_dict() for entry in self.results]

    def as_dataframe(self, engine: str = "pandas") -> "pd.DataFrame":
        """Convert records to a DataFrame.

        Args:
            engine: Only ``"pandas"`` is supported.

        Returns:
            DataFrame with one row per gene record.
        """
        records = self.as_dict()
        if engine == "pandas":
            return pd.DataFrame(records)
        raise ValueError(f"Unsupported engine: {engine!r}. Use 'pandas'.")

    def symbols(self) -> List[str]:
        """Return all gene symbols in this response."""
        if self.is_search:
            return [r.get("symbol", "") for r in self.results if r.get("symbol")]
        return [e.symbol for e in self.results if e.symbol]

    def hgnc_ids(self) -> List[str]:
        """Return all HGNC IDs in this response."""
        if self.is_search:
            return [r.get("hgnc_id", "") for r in self.results if r.get("hgnc_id")]
        return [e.hgnc_id for e in self.results if e.hgnc_id]
