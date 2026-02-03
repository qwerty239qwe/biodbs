"""ChEMBL fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class ChEMBLFetchedData(BaseFetchedData):
    """Fetched data from ChEMBL REST API.

    ChEMBL API returns JSON with structure:
        {
            "page_meta": {
                "limit": 20,
                "next": "/chembl/api/data/molecule?offset=20&limit=20&format=json",
                "offset": 0,
                "previous": null,
                "total_count": 2157379
            },
            "{resource_name}s": [...]  # e.g., "molecules", "activities"
        }

    For single-entry lookups, the response is just the object directly.

    Attributes:
        metadata: Pagination metadata from page_meta.
        results: List of result records.
        resource: The ChEMBL resource type.
    """

    def __init__(self, content: Union[dict, list], resource: str = None):
        """Initialize ChEMBLFetchedData.

        Args:
            content: Raw API response (dict or list).
            resource: The ChEMBL resource name for context.
        """
        super().__init__(content)
        self.resource = resource

        # Handle different response formats
        if isinstance(content, dict):
            self.metadata = content.get("page_meta", {})
            # Find the results list - it's named as plural of resource
            self.results = self._extract_results(content)
        elif isinstance(content, list):
            # Direct list response
            self.metadata = {}
            self.results = content
        else:
            self.metadata = {}
            self.results = []

    def _extract_results(self, content: dict) -> List[Dict[str, Any]]:
        """Extract results from ChEMBL response.

        ChEMBL uses plural resource names as keys (e.g., "molecules", "activities").
        For single-entry lookups, the object is returned directly.
        """
        # Check for page_meta to determine if it's a list response
        if "page_meta" in content:
            # Find the results key (usually plural of resource)
            for key, value in content.items():
                if key != "page_meta" and isinstance(value, list):
                    return value
            return []
        else:
            # Single entry lookup - returns the object directly
            # Detect by checking for common ChEMBL ID fields
            id_fields = [
                "molecule_chembl_id", "target_chembl_id", "assay_chembl_id",
                "document_chembl_id", "cell_chembl_id", "tissue_chembl_id",
                "activity_id", "drugind_id", "mec_id",
            ]
            if content and any(field in content for field in id_fields):
                return [content]
        return []

    def __iadd__(self, other: "ChEMBLFetchedData") -> "ChEMBLFetchedData":
        """Concatenate results from another ChEMBLFetchedData."""
        self.results.extend(other.results)
        return self

    def __len__(self) -> int:
        return len(self.results)

    def get_total_count(self) -> Optional[int]:
        """Get total count from pagination metadata."""
        return self.metadata.get("total_count")

    def get_next_offset(self) -> Optional[int]:
        """Get offset for next page, if available."""
        next_url = self.metadata.get("next")
        if next_url:
            # Parse offset from URL
            import re
            match = re.search(r"offset=(\d+)", next_url)
            if match:
                return int(match.group(1))
        return None

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return results as list of dicts, optionally filtered to columns."""
        if columns is None:
            return self.results
        return self.format_results(columns=columns)

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary into dot-separated keys.

        Args:
            d: Dictionary to flatten.
            parent_key: Prefix for keys (used in recursion).
            sep: Separator between nested keys.

        Returns:
            Flattened dictionary with dot-separated keys.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
        flatten: bool = False,
    ):
        """Convert results to a DataFrame.

        Args:
            columns: Columns to include. None means all columns.
            engine: "pandas" or "polars".
            flatten: If True, flatten nested dictionaries into dot-separated columns.
        """
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if flatten:
            data = [self._flatten_dict(record) for record in data]

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def _get_nested_value(self, data_dict: dict, keys: List[str]) -> Any:
        """Get value from nested dict using dot-separated keys."""
        for key in keys:
            if isinstance(data_dict, list):
                data_dict = [self._get_nested_value(item, [key]) for item in data_dict]
            elif isinstance(data_dict, dict):
                data_dict = data_dict.get(key)
            else:
                return None
            if data_dict is None:
                return None
        return data_dict

    def _show_valid_columns_helper(self, record: dict, parent_key: str = "") -> List[str]:
        """Recursively collect column names from nested structure."""
        col_list = []
        for key, value in record.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                col_list.extend(self._show_valid_columns_helper(value, full_key))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                col_list.extend(self._show_valid_columns_helper(value[0], full_key))
            else:
                col_list.append(full_key)
        return col_list

    def show_columns(self) -> List[str]:
        """Return list of available column names (including nested)."""
        col_set = set()
        for record in self.results:
            col_set.update(self._show_valid_columns_helper(record))
        return sorted(col_set)

    def format_results(
        self,
        columns: List[str],
        safe_check: bool = True
    ) -> List[Dict[str, Any]]:
        """Format results with only specified columns.

        Args:
            columns: List of column names (supports dot notation for nested).
            safe_check: If True, validate columns exist.
        """
        if safe_check:
            valid_columns = self.show_columns()
            for col in columns:
                if col not in valid_columns:
                    raise ValueError(
                        f"Column '{col}' is not valid. "
                        f"Valid columns are: {valid_columns}"
                    )

        formatted_results = []
        for record in self.results:
            formatted_record = {
                col: self._get_nested_value(record, col.split("."))
                for col in columns
            }
            formatted_results.append(formatted_record)
        return formatted_results

    def filter(self, **kwargs) -> "ChEMBLFetchedData":
        """Return a new ChEMBLFetchedData with records matching the filter.

        Example:
            data.filter(molecule_chembl_id="CHEMBL25")
            data.filter(pchembl_value=lambda x: x is not None and x > 5)
        """
        filtered = []
        for record in self.results:
            match = True
            for key, value in kwargs.items():
                record_value = self._get_nested_value(record, key.split("."))
                if callable(value):
                    if not value(record_value):
                        match = False
                        break
                elif record_value != value:
                    match = False
                    break
            if match:
                filtered.append(record)

        result = ChEMBLFetchedData.__new__(ChEMBLFetchedData)
        result._content = self._content
        result.resource = self.resource
        result.metadata = self.metadata
        result.results = filtered
        return result

    def get_chembl_ids(self) -> List[str]:
        """Extract all ChEMBL IDs from results."""
        ids = []
        # Try common ID field names
        id_fields = [
            "molecule_chembl_id",
            "target_chembl_id",
            "assay_chembl_id",
            "document_chembl_id",
            "cell_chembl_id",
            "tissue_chembl_id",
        ]
        for record in self.results:
            for field in id_fields:
                if field in record:
                    ids.append(record[field])
                    break
        return ids


class ChEMBLDataManager(BaseDBManager):
    """Data manager for ChEMBL data with ChEMBL-specific convenience methods."""

    def __init__(
        self,
        storage_path,
        db_name: str = "chembl",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_chembl_data(
        self,
        data: ChEMBLFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save ChEMBLFetchedData to storage.

        Args:
            data: The ChEMBL data to save.
            filename: Base filename (without extension).
            fmt: Output format.
            key: Optional cache key.
            columns: Optional columns to include (for CSV).
        """
        if fmt == "csv" and data.results:
            records = data.as_dict(columns) if columns else data.results
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.results, filename, key=key)
        elif fmt == "jsonl" and data.results:
            return self.stream_json_lines(iter(data.results), filename, key=key)
        else:
            raise ValueError(f"Cannot save format {fmt} for empty data")
