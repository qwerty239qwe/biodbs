"""Ensembl fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class EnsemblFetchedData(BaseFetchedData):
    """Fetched data from Ensembl REST API.

    Ensembl API returns different response structures depending on endpoint:
        - Single object: {...}
        - List of objects: [...]
        - Nested structure: {"data": [...]} or {"homologies": [...]}

    Attributes:
        results: List of result records (normalized to list format).
        endpoint: The Ensembl endpoint used.
        raw_response: Original API response.
    """

    def __init__(
        self,
        content: Union[dict, list, str],
        endpoint: str = None,
        content_type: str = "json",
    ):
        """Initialize EnsemblFetchedData.

        Args:
            content: Raw API response (dict, list, or str for sequences).
            endpoint: The Ensembl endpoint name for context.
            content_type: Response content type (json, fasta, text).
        """
        super().__init__(content)
        self.endpoint = endpoint
        self.content_type = content_type
        self.raw_response = content

        # Normalize to list of records
        self.results = self._extract_results(content)
        self.text = None
        self.sequence = None

        # Handle text/fasta responses
        if content_type in ("fasta", "text") and isinstance(content, str):
            self.text = content
            if content_type == "fasta":
                self.sequence = self._parse_fasta(content)

    def _extract_results(self, content: Any) -> List[Dict[str, Any]]:
        """Extract results from various Ensembl response formats."""
        if content is None:
            return []

        # String response (sequence, text)
        if isinstance(content, str):
            return []

        # Direct list response
        if isinstance(content, list):
            return content

        # Dict response - look for data in common keys
        if isinstance(content, dict):
            # Homology endpoint
            if "data" in content and isinstance(content["data"], list):
                # Homology response has nested structure
                all_homologies = []
                for item in content["data"]:
                    if "homologies" in item:
                        all_homologies.extend(item["homologies"])
                    else:
                        all_homologies.append(item)
                return all_homologies if all_homologies else content["data"]

            # Gene tree endpoint
            if "tree" in content:
                return [content]

            # Overlap endpoint returns list directly
            # Variation endpoint returns single object
            # Check for common ID fields to identify single-object response
            id_fields = [
                "id", "stable_id", "gene_id", "transcript_id",
                "name", "accession", "assembly_name",
            ]
            if any(field in content for field in id_fields):
                return [content]

            # Mapping response
            if "mappings" in content:
                return content["mappings"]

            # VEP response - array at top level
            # Info endpoints - return as single record
            return [content]

        return []

    def _parse_fasta(self, fasta_text: str) -> List[Dict[str, str]]:
        """Parse FASTA format text into list of sequences."""
        sequences = []
        current_header = None
        current_seq = []

        for line in fasta_text.strip().split("\n"):
            if line.startswith(">"):
                if current_header is not None:
                    sequences.append({
                        "header": current_header,
                        "id": current_header.split()[0].lstrip(">"),
                        "sequence": "".join(current_seq),
                    })
                current_header = line[1:]  # Remove >
                current_seq = []
            else:
                current_seq.append(line.strip())

        # Don't forget the last sequence
        if current_header is not None:
            sequences.append({
                "header": current_header,
                "id": current_header.split()[0],
                "sequence": "".join(current_seq),
            })

        return sequences

    def __iadd__(self, other: "EnsemblFetchedData") -> "EnsemblFetchedData":
        """Concatenate results from another EnsemblFetchedData."""
        self.results.extend(other.results)
        if self.text and other.text:
            self.text = self.text + "\n" + other.text
        if self.sequence and other.sequence:
            self.sequence.extend(other.sequence)
        return self

    def __len__(self) -> int:
        return len(self.results)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return results as list of dicts, optionally filtered to columns."""
        if columns is None:
            return self.results
        return self.format_results(columns=columns)

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
    ):
        """Convert results to a DataFrame.

        Args:
            columns: Columns to include. None means all columns.
            engine: "pandas" or "polars".

        Raises:
            ValueError: If data is not tabular (e.g., sequence/text responses).
        """
        if not self.results:
            if self.text or self.sequence:
                raise ValueError(
                    f"This {self.endpoint} response contains sequence/text data "
                    "which cannot be converted to a DataFrame. "
                    "Use .text, .sequence, or .get_sequences() instead."
                )
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        data = self.as_dict(columns)

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
            if isinstance(record, dict):
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
            if isinstance(record, dict):
                formatted_record = {
                    col: self._get_nested_value(record, col.split("."))
                    for col in columns
                }
                formatted_results.append(formatted_record)
        return formatted_results

    def filter(self, **kwargs) -> "EnsemblFetchedData":
        """Return a new EnsemblFetchedData with records matching the filter.

        Example:
            data.filter(biotype="protein_coding")
            data.filter(start=lambda x: x > 1000000)
        """
        filtered = []
        for record in self.results:
            if not isinstance(record, dict):
                continue
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

        result = EnsemblFetchedData.__new__(EnsemblFetchedData)
        result._content = self._content
        result.endpoint = self.endpoint
        result.content_type = self.content_type
        result.raw_response = self.raw_response
        result.results = filtered
        result.text = self.text
        result.sequence = self.sequence
        return result

    def get_ids(self) -> List[str]:
        """Extract all Ensembl IDs from results."""
        ids = []
        id_fields = ["id", "stable_id", "gene_id", "transcript_id", "protein_id"]
        for record in self.results:
            if isinstance(record, dict):
                for field in id_fields:
                    if field in record:
                        ids.append(record[field])
                        break
        return ids

    def get_sequences(self) -> List[Dict[str, str]]:
        """Get parsed sequences from FASTA response."""
        if self.sequence:
            return self.sequence
        return []

    def get_homologies(self) -> List[Dict[str, Any]]:
        """Get homology data from homology endpoint response."""
        return self.results

    def get_mappings(self) -> List[Dict[str, Any]]:
        """Get coordinate mappings from mapping endpoint response."""
        return self.results

    def get_variants(self) -> List[Dict[str, Any]]:
        """Get variant data from variation/VEP endpoint response."""
        return self.results

    def get_features(self) -> List[Dict[str, Any]]:
        """Get feature data from overlap endpoint response."""
        return self.results


class EnsemblDataManager(BaseDBManager):
    """Data manager for Ensembl data with Ensembl-specific convenience methods."""

    def __init__(
        self,
        storage_path,
        db_name: str = "ensembl",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_ensembl_data(
        self,
        data: EnsemblFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl", "fasta"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save EnsemblFetchedData to storage.

        Args:
            data: The Ensembl data to save.
            filename: Base filename (without extension).
            fmt: Output format.
            key: Optional cache key.
            columns: Optional columns to include (for CSV).
        """
        if fmt == "fasta" and data.text:
            filepath = self.storage_path / f"{filename}.fasta"
            with open(filepath, "w") as f:
                f.write(data.text)
            if key:
                self.update_metadata(key, str(filepath))
            return filepath

        if fmt == "csv" and data.results:
            records = data.as_dict(columns) if columns else data.results
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.results, filename, key=key)
        elif fmt == "jsonl" and data.results:
            return self.stream_json_lines(iter(data.results), filename, key=key)
        else:
            raise ValueError(f"Cannot save format {fmt} for this data type")
