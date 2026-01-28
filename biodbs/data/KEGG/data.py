from biodbs.data._base import BaseFetchedData, BaseDBManager
from typing import Literal, Optional, Union, List, Dict, Any
import pandas as pd
import polars as pl
import re


# Column names for different KEGG operations (tab-separated responses)
KEGG_TABULAR_COLUMNS = {
    "list": ["entry_id", "description"],
    "find": ["entry_id", "description"],
    "conv": ["source_id", "target_id"],
    "link": ["source_id", "target_id"],
    "ddi": ["drug1", "drug2", "interaction_type"],
}


class KEGGFetchedData(BaseFetchedData):
    """Fetched data from KEGG REST API.

    Handles multiple response formats:
        - **Tabular** (list, find, conv, link, ddi): Tab-separated values
          parsed into list of dicts with appropriate column names.
        - **Text** (info, get flat file): Raw text, with optional flat-file
          parsing for GET responses.
        - **JSON** (get with json option): Parsed JSON dict.
        - **Binary** (get with image option): Raw bytes.

    Attributes:
        operation: The KEGG operation that produced this data.
        format: The response format (``"tabular"``, ``"text"``, ``"json"``,
            ``"binary"``, ``"flat_file"``).
        records: For tabular data, list of dicts. For flat_file, list of
            parsed entry dicts.
        text: For text/flat_file formats, the raw text.
        json_data: For JSON format, the parsed dict.
        binary_data: For binary format (images), the raw bytes.
    """

    def __init__(
        self,
        content: Union[str, bytes, dict],
        operation: str,
        get_option: Optional[str] = None,
    ):
        super().__init__(content)
        self.operation = operation
        self.get_option = get_option

        # Determine format and parse accordingly
        self.format: str = self._detect_format()
        self.records: List[Dict[str, Any]] = []
        self.text: Optional[str] = None
        self.json_data: Optional[dict] = None
        self.binary_data: Optional[bytes] = None

        self._parse_content()

    def _detect_format(self) -> str:
        """Detect the response format based on operation and options."""
        if self.operation in ("list", "find", "conv", "link", "ddi"):
            return "tabular"
        elif self.operation == "info":
            return "text"
        elif self.operation == "get":
            if self.get_option == "json":
                return "json"
            elif self.get_option == "image":
                return "binary"
            elif self.get_option in ("aaseq", "ntseq"):
                return "fasta"
            elif self.get_option in ("mol", "kcf", "kgml"):
                return "text"
            else:
                return "flat_file"
        return "text"

    def _parse_content(self):
        """Parse content based on detected format."""
        content = self._content

        if self.format == "tabular":
            self._parse_tabular(content)
        elif self.format == "json":
            if isinstance(content, dict):
                self.json_data = content
            else:
                import json
                self.json_data = json.loads(content)
        elif self.format == "binary":
            self.binary_data = content if isinstance(content, bytes) else content.encode()
        elif self.format == "flat_file":
            self.text = content
            self._parse_flat_file(content)
        elif self.format == "fasta":
            self.text = content
            self._parse_fasta(content)
        else:
            self.text = content

    def _parse_tabular(self, content: str):
        """Parse tab-separated KEGG response."""
        columns = KEGG_TABULAR_COLUMNS.get(self.operation, ["col1", "col2"])
        lines = content.strip().split("\n") if content.strip() else []

        for line in lines:
            if not line.strip():
                continue
            parts = line.split("\t")
            record = {}
            for i, col in enumerate(columns):
                record[col] = parts[i] if i < len(parts) else None
            # Handle extra columns for ddi which may have variable format
            if len(parts) > len(columns):
                record["extra"] = parts[len(columns):]
            self.records.append(record)

    def _parse_flat_file(self, content: str):
        """Parse KEGG flat file format into structured records.

        KEGG flat files have format:
            FIELD       value
                        continuation
            FIELD2      value2
            ///
        """
        entries = content.split("///")
        for entry_text in entries:
            entry_text = entry_text.strip()
            if not entry_text:
                continue

            record: Dict[str, Any] = {}
            current_field = None
            current_value: List[str] = []

            for line in entry_text.split("\n"):
                if not line:
                    continue

                # Check if line starts a new field (12 char field name)
                if line[:12].strip():
                    # Save previous field
                    if current_field:
                        record[current_field] = self._process_field_value(
                            current_field, current_value
                        )
                    # Start new field
                    current_field = line[:12].strip()
                    current_value = [line[12:].strip()] if line[12:].strip() else []
                else:
                    # Continuation of previous field
                    if current_field and line[12:].strip():
                        current_value.append(line[12:].strip())

            # Save last field
            if current_field:
                record[current_field] = self._process_field_value(
                    current_field, current_value
                )

            if record:
                self.records.append(record)

    def _process_field_value(
        self, field: str, values: List[str]
    ) -> Union[str, List[str]]:
        """Process field values - join or keep as list based on field type."""
        # Fields that should remain as lists
        list_fields = {
            "PATHWAY", "MODULE", "DISEASE", "DRUG", "DBLINKS",
            "GENE", "ORTHOLOGY", "REFERENCE", "COMPOUND", "REACTION",
        }
        if field in list_fields:
            return values
        return "\n".join(values) if len(values) > 1 else (values[0] if values else "")

    def _parse_fasta(self, content: str):
        """Parse FASTA format sequences."""
        entries = content.split(">")
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            lines = entry.split("\n")
            header = lines[0]
            sequence = "".join(lines[1:])
            # Parse header: typically "entry_id description"
            parts = header.split(None, 1)
            record = {
                "entry_id": parts[0] if parts else "",
                "description": parts[1] if len(parts) > 1 else "",
                "sequence": sequence,
            }
            self.records.append(record)

    def __iadd__(self, other: "KEGGFetchedData") -> "KEGGFetchedData":
        """Concatenate records from another KEGGFetchedData."""
        if self.format != other.format:
            raise ValueError(
                f"Cannot concatenate different formats: {self.format} vs {other.format}"
            )
        self.records.extend(other.records)
        if self.text and other.text:
            self.text += "\n" + other.text
        return self

    def __len__(self) -> int:
        return len(self.records)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return records as list of dicts, optionally filtered to columns."""
        if not columns:
            return self.records
        return [{col: r.get(col) for col in columns} for r in self.records]

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
    ):
        """Convert records to a DataFrame.

        Args:
            columns: Columns to include. None means all columns.
            engine: ``"pandas"`` or ``"polars"``.
        """
        data = self.as_dict(columns)
        if not data:
            # Return empty dataframe with expected columns
            cols = columns or (KEGG_TABULAR_COLUMNS.get(self.operation, []))
            if engine == "pandas":
                return pd.DataFrame(columns=cols)
            return pl.DataFrame(schema={c: pl.Utf8 for c in cols})

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def show_columns(self) -> List[str]:
        """Return list of available column names."""
        if not self.records:
            return KEGG_TABULAR_COLUMNS.get(self.operation, [])
        cols = set()
        for r in self.records:
            cols.update(r.keys())
        return sorted(cols)

    def filter(self, **kwargs) -> "KEGGFetchedData":
        """Return a new KEGGFetchedData with records matching the filter.

        Example:
            data.filter(entry_id="hsa:10458")
            data.filter(entry_id=lambda x: x.startswith("hsa:"))
        """
        filtered = []
        for record in self.records:
            match = True
            for key, value in kwargs.items():
                if key not in record:
                    match = False
                    break
                if callable(value):
                    if not value(record[key]):
                        match = False
                        break
                elif record[key] != value:
                    match = False
                    break
            if match:
                filtered.append(record)

        result = KEGGFetchedData.__new__(KEGGFetchedData)
        result._content = self._content
        result.operation = self.operation
        result.get_option = self.get_option
        result.format = self.format
        result.records = filtered
        result.text = self.text
        result.json_data = self.json_data
        result.binary_data = self.binary_data
        return result

    def to_text(self, file_path: str, mode: str = "w"):
        """Save raw text content to file."""
        if self.text:
            with open(file_path, mode) as f:
                f.write(self.text)
        elif self.format == "tabular":
            # Reconstruct TSV
            with open(file_path, mode) as f:
                for record in self.records:
                    line = "\t".join(str(v) for v in record.values())
                    f.write(line + "\n")

    def to_binary(self, file_path: str):
        """Save binary content (e.g., image) to file."""
        if self.binary_data:
            with open(file_path, "wb") as f:
                f.write(self.binary_data)

    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific entry by ID."""
        for record in self.records:
            if record.get("entry_id") == entry_id or record.get("ENTRY", "").startswith(entry_id):
                return record
        return None


class KEGGDataManager(BaseDBManager):
    """Data manager for KEGG data with KEGG-specific convenience methods."""

    def __init__(
        self,
        storage_path,
        db_name: str = "kegg",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_kegg_data(
        self,
        data: KEGGFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl", "text"] = "csv",
        key: Optional[str] = None,
    ):
        """Save KEGGFetchedData to storage.

        Args:
            data: The KEGG data to save.
            filename: Base filename (without extension).
            fmt: Output format.
            key: Optional cache key.
        """
        if fmt == "csv" and data.records:
            return self.save_csv(data.records, filename, key=key)
        elif fmt == "json":
            content = data.json_data if data.json_data else data.records
            return self.save_json(content, filename, key=key)
        elif fmt == "jsonl" and data.records:
            return self.stream_json_lines(iter(data.records), filename, key=key)
        elif fmt == "text" and data.text:
            filepath = self.storage_path / f"{filename}.txt"
            filepath.write_text(data.text, encoding="utf-8")
            if key:
                self._update_metadata(key, filepath=str(filepath), format="text")
            return filepath
        else:
            raise ValueError(f"Cannot save format {fmt} for data type {data.format}")