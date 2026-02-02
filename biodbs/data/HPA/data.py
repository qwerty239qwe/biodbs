"""Human Protein Atlas fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class HPAFetchedData(BaseFetchedData):
    """Fetched data from Human Protein Atlas API.

    HPA returns different data structures depending on the endpoint:

    For individual gene entries (JSON):
        [
            {
                "Ensembl": "ENSG00000134057",
                "Gene": "CCNB1",
                "Gene synonym": ["CCNB", "CCNB1-202"],
                "Gene description": "cyclin B1",
                ...
            }
        ]

    For search_download API (JSON):
        [
            {"Gene": "TP53", "Ensembl": "ENSG00000141510", ...},
            {"Gene": "TP53I3", "Ensembl": "ENSG00000115129", ...},
            ...
        ]

    Attributes:
        results: List of result records (normalized).
        raw_content: Original API response.
        format: The response format (json, tsv, xml).
        query_type: The type of query (entry, search, search_download).
    """

    def __init__(
        self,
        content: Union[dict, list, str, bytes],
        format: str = "json",
        query_type: str = "entry",
    ):
        super().__init__(content)
        self.format = format
        self.query_type = query_type
        self.raw_content = content

        if isinstance(content, bytes):
            self.results = []
            self.binary_data = content
        elif isinstance(content, str):
            # TSV or XML as string
            self.results = []
            self.text_data = content
            if format == "tsv":
                self.results = self._parse_tsv(content)
        else:
            self.binary_data = None
            self.text_data = None
            self.results = self._extract_results(content)

    def _extract_results(self, content: Union[dict, list]) -> List[Dict[str, Any]]:
        """Extract results from HPA response formats."""
        if isinstance(content, list):
            return content
        if isinstance(content, dict):
            # Single entry wrapped in a dict
            return [content]
        return []

    def _parse_tsv(self, content: str) -> List[Dict[str, Any]]:
        """Parse TSV content into list of dicts."""
        lines = content.strip().split("\n")
        if not lines:
            return []

        headers = lines[0].split("\t")
        results = []
        for line in lines[1:]:
            if not line.strip():
                continue
            values = line.split("\t")
            record = {h: v for h, v in zip(headers, values)}
            results.append(record)
        return results

    def __iadd__(self, other: "HPAFetchedData") -> "HPAFetchedData":
        """Concatenate results from another HPAFetchedData."""
        self.results.extend(other.results)
        return self

    def __len__(self) -> int:
        return len(self.results)

    def get_ensembl_ids(self) -> List[str]:
        """Extract all Ensembl IDs from results."""
        ids = []
        for record in self.results:
            if "Ensembl" in record:
                ids.append(record["Ensembl"])
            elif "eg" in record:
                ids.append(record["eg"])
        return ids

    def get_gene_names(self) -> List[str]:
        """Extract all gene names from results."""
        names = []
        for record in self.results:
            if "Gene" in record:
                names.append(record["Gene"])
            elif "g" in record:
                names.append(record["g"])
        return names

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return results as list of dictionaries."""
        if columns is None:
            return self.results
        return self.format_results(columns=columns)

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
    ):
        """Convert results to DataFrame.

        Args:
            columns: Columns to include. None means all columns.
            engine: "pandas" or "polars".

        Raises:
            ValueError: If the data is binary or unparsed text that cannot be converted.
        """
        # Check for non-tabular data
        if not self.results:
            if hasattr(self, 'binary_data') and self.binary_data:
                raise ValueError(
                    "This HPA response contains binary data which cannot be converted to a DataFrame."
                )
            elif hasattr(self, 'text_data') and self.text_data and self.format == "xml":
                raise ValueError(
                    "This HPA XML response was not parsed into tabular records. "
                    "Use .text_data attribute to access the raw XML content."
                )

        data = self.as_dict(columns)
        if not data:
            return pd.DataFrame() if engine == "pandas" else pl.DataFrame()
        return pd.DataFrame(data) if engine == "pandas" else pl.DataFrame(data)

    def _get_nested_value(self, data_dict: dict, keys: List[str]) -> Any:
        """Navigate nested dict structure."""
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
        """Recursively collect column names."""
        col_list = []
        if not isinstance(record, dict):
            return col_list
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
        """Show all available columns in the results."""
        col_set = set()
        for record in self.results:
            col_set.update(self._show_valid_columns_helper(record))
        return sorted(col_set)

    def format_results(self, columns: List[str], safe_check: bool = True) -> List[Dict[str, Any]]:
        """Format results to include only specified columns."""
        if safe_check:
            valid_columns = self.show_columns()
            for col in columns:
                if col not in valid_columns:
                    raise ValueError(f"Column '{col}' is not valid. Valid columns: {valid_columns}")
        return [
            {col: self._get_nested_value(record, col.split(".")) for col in columns}
            for record in self.results
        ]

    def filter(self, **kwargs) -> "HPAFetchedData":
        """Filter results based on field values."""
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

        result = HPAFetchedData.__new__(HPAFetchedData)
        result._content = self._content
        result.format = self.format
        result.query_type = self.query_type
        result.raw_content = self.raw_content
        result.results = filtered
        result.binary_data = None
        result.text_data = None
        return result

    def get_expression_data(self, tissue: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract expression data from results.

        Args:
            tissue: Optional tissue name to filter by.

        Returns:
            List of expression data records.
        """
        expression_data = []
        for record in self.results:
            expr_record = {
                "Gene": record.get("Gene", record.get("g")),
                "Ensembl": record.get("Ensembl", record.get("eg")),
            }

            # Collect all RNA expression fields
            for key, value in record.items():
                if key.startswith("rna_") or key.startswith("RNA"):
                    if tissue is None or tissue.lower() in key.lower():
                        expr_record[key] = value

            if len(expr_record) > 2:  # Has expression data beyond gene info
                expression_data.append(expr_record)

        return expression_data

    def get_subcellular_location(self) -> List[Dict[str, Any]]:
        """Extract subcellular location data from results."""
        location_data = []
        for record in self.results:
            loc_record = {
                "Gene": record.get("Gene", record.get("g")),
                "Ensembl": record.get("Ensembl", record.get("eg")),
            }

            # Subcellular location fields
            location_fields = [
                "Subcellular location", "scl",
                "Subcellular main location", "scml",
                "Subcellular additional location", "scal",
            ]
            for field in location_fields:
                if field in record:
                    loc_record[field] = record[field]

            if len(loc_record) > 2:
                location_data.append(loc_record)

        return location_data

    def has_error(self) -> bool:
        """Check if response contains an error."""
        if isinstance(self.raw_content, dict):
            return "error" in self.raw_content or "Error" in self.raw_content
        return False

    def get_error_message(self) -> Optional[str]:
        """Get error message if present."""
        if isinstance(self.raw_content, dict):
            return self.raw_content.get("error") or self.raw_content.get("Error")
        return None


class HPADataManager(BaseDBManager):
    """Data manager for Human Protein Atlas data."""

    def __init__(
        self,
        storage_path,
        db_name: str = "hpa",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_hpa_data(
        self,
        data: HPAFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl", "tsv"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save HPA data to storage.

        Args:
            data: HPAFetchedData object.
            filename: Output filename (without extension).
            fmt: Output format.
            key: Optional cache key.
            columns: Optional list of columns to include.

        Returns:
            Path to saved file.
        """
        if fmt == "csv" and data.results:
            records = data.as_dict(columns) if columns else data.results
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.results, filename, key=key)
        elif fmt == "jsonl" and data.results:
            return self.stream_json_lines(iter(data.results), filename, key=key)
        elif fmt == "tsv" and data.text_data:
            filepath = self.storage_path / f"{filename}.tsv"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(data.text_data)
            if key:
                self._update_metadata(key, filepath=str(filepath), format="tsv")
            return filepath
        else:
            raise ValueError(f"Cannot save format {fmt} for this data")

    def save_expression_data(
        self,
        data: HPAFetchedData,
        filename: str,
        tissue: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """Save expression data to storage.

        Args:
            data: HPAFetchedData object.
            filename: Output filename (without extension).
            tissue: Optional tissue to filter by.
            key: Optional cache key.

        Returns:
            Path to saved file.
        """
        expression = data.get_expression_data(tissue=tissue)
        if not expression:
            raise ValueError("No expression data found")
        return self.save_json(expression, filename, key=key)

    def save_subcellular_data(
        self,
        data: HPAFetchedData,
        filename: str,
        key: Optional[str] = None,
    ):
        """Save subcellular location data to storage.

        Args:
            data: HPAFetchedData object.
            filename: Output filename (without extension).
            key: Optional cache key.

        Returns:
            Path to saved file.
        """
        locations = data.get_subcellular_location()
        if not locations:
            raise ValueError("No subcellular location data found")
        return self.save_json(locations, filename, key=key)
