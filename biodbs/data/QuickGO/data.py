from biodbs.data._base import BaseFetchedData, BaseDBManager
from typing import Literal, Optional, Union, List, Dict, Any
import pandas as pd
import polars as pl


class QuickGOFetchedData(BaseFetchedData):
    """Fetched data from QuickGO API.

    Handles multiple response formats:
        - **JSON** (search, terms): Standard JSON response with results array.
        - **TSV** (download with tsv format): Tab-separated values.
        - **GAF** (download with gaf format): GO Annotation File format.
        - **GPAD** (download with gpad format): Gene Product Association Data.

    Attributes:
        format: The response format (``"json"``, ``"tsv"``, ``"gaf"``, ``"gpad"``).
        results: List of result records (parsed from JSON or tabular data).
        metadata: Response metadata (pageInfo, numberOfHits, etc.).
        text: Raw text for non-JSON formats.
    """

    def __init__(
        self,
        content: Union[str, bytes, dict],
        endpoint: str,
        download_format: Optional[str] = None,
    ):
        super().__init__(content)
        self.endpoint = endpoint
        self.download_format = download_format

        # Determine format and parse
        self.format: str = self._detect_format()
        self.results: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.text: Optional[str] = None

        self._parse_content()

    def _detect_format(self) -> str:
        """Detect the response format based on content and download_format."""
        if self.download_format:
            return self.download_format  # tsv, gaf, gpad
        if isinstance(self._content, dict):
            return "json"
        if isinstance(self._content, bytes):
            return "binary"
        # Try to detect from text content
        content = self._content
        if content.strip().startswith("{") or content.strip().startswith("["):
            return "json"
        return "text"

    def _parse_content(self):
        """Parse content based on detected format."""
        content = self._content

        if self.format == "json":
            self._parse_json(content)
        elif self.format == "tsv":
            self._parse_tsv(content)
        elif self.format == "gaf":
            self._parse_gaf(content)
        elif self.format == "gpad":
            self._parse_gpad(content)
        else:
            self.text = content if isinstance(content, str) else content.decode("utf-8")

    def _parse_json(self, content: Union[str, dict]):
        """Parse JSON response from QuickGO API."""
        if isinstance(content, str):
            import json
            content = json.loads(content)

        # QuickGO responses have different structures depending on endpoint
        if "results" in content:
            self.results = content["results"]
            self.metadata = {k: v for k, v in content.items() if k != "results"}
        elif "searchHits" in content:
            # Gene product search format
            self.results = content["searchHits"]
            self.metadata = {k: v for k, v in content.items() if k != "searchHits"}
        elif isinstance(content, list):
            self.results = content
        else:
            # Single result or other format
            self.results = [content] if content else []
            self.metadata = {}

    def _parse_tsv(self, content: Union[str, bytes]):
        """Parse TSV download format."""
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        self.text = content

        lines = content.strip().split("\n")
        if not lines:
            return

        # First line is header
        headers = lines[0].split("\t")
        for line in lines[1:]:
            if not line.strip() or line.startswith("!"):
                continue
            parts = line.split("\t")
            record = {}
            for i, header in enumerate(headers):
                record[header] = parts[i] if i < len(parts) else None
            self.results.append(record)

    def _parse_gaf(self, content: Union[str, bytes]):
        """Parse GAF (GO Annotation File) format.

        GAF 2.2 columns:
        1. DB, 2. DB_Object_ID, 3. DB_Object_Symbol, 4. Qualifier,
        5. GO_ID, 6. DB:Reference, 7. Evidence_Code, 8. With/From,
        9. Aspect, 10. DB_Object_Name, 11. DB_Object_Synonym,
        12. DB_Object_Type, 13. Taxon, 14. Date, 15. Assigned_By,
        16. Annotation_Extension, 17. Gene_Product_Form_ID
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        self.text = content

        gaf_columns = [
            "db", "db_object_id", "db_object_symbol", "qualifier",
            "go_id", "db_reference", "evidence_code", "with_from",
            "aspect", "db_object_name", "db_object_synonym",
            "db_object_type", "taxon", "date", "assigned_by",
            "annotation_extension", "gene_product_form_id"
        ]

        for line in content.strip().split("\n"):
            if not line.strip() or line.startswith("!"):
                continue
            parts = line.split("\t")
            record = {}
            for i, col in enumerate(gaf_columns):
                record[col] = parts[i] if i < len(parts) else None
            self.results.append(record)

    def _parse_gpad(self, content: Union[str, bytes]):
        """Parse GPAD (Gene Product Association Data) format.

        GPAD 2.0 columns:
        1. DB_Object_ID, 2. Negation, 3. Relation, 4. GO_ID,
        5. Reference, 6. Evidence_Code, 7. With/From, 8. Interacting_Taxon_ID,
        9. Date, 10. Assigned_By, 11. Annotation_Extension, 12. Annotation_Properties
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        self.text = content

        gpad_columns = [
            "db_object_id", "negation", "relation", "go_id",
            "reference", "evidence_code", "with_from", "interacting_taxon_id",
            "date", "assigned_by", "annotation_extension", "annotation_properties"
        ]

        for line in content.strip().split("\n"):
            if not line.strip() or line.startswith("!"):
                continue
            parts = line.split("\t")
            record = {}
            for i, col in enumerate(gpad_columns):
                record[col] = parts[i] if i < len(parts) else None
            self.results.append(record)

    def __iadd__(self, other: "QuickGOFetchedData") -> "QuickGOFetchedData":
        """Concatenate results from another QuickGOFetchedData."""
        if self.format != other.format:
            raise ValueError(
                f"Cannot concatenate different formats: {self.format} vs {other.format}"
            )
        self.results.extend(other.results)
        if self.text and other.text:
            self.text += "\n" + other.text
        return self

    def __len__(self) -> int:
        return len(self.results)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return results as list of dicts, optionally filtered to columns."""
        if not columns:
            return self.results
        return [{col: r.get(col) for col in columns} for r in self.results]

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
    ):
        """Convert results to a DataFrame.

        Args:
            columns: Columns to include. None means all columns.
            engine: ``"pandas"`` or ``"polars"``.
        """
        data = self.as_dict(columns)
        if not data:
            cols = columns or []
            if engine == "pandas":
                return pd.DataFrame(columns=cols)
            return pl.DataFrame(schema={c: pl.Utf8 for c in cols})

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def show_columns(self) -> List[str]:
        """Return list of available column names."""
        if not self.results:
            return []
        cols = set()
        for r in self.results:
            cols.update(r.keys())
        return sorted(cols)

    def filter(self, **kwargs) -> "QuickGOFetchedData":
        """Return a new QuickGOFetchedData with records matching the filter.

        Example:
            data.filter(go_id="GO:0008150")
            data.filter(evidence_code=lambda x: x in ["IDA", "IMP"])
        """
        filtered = []
        for record in self.results:
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

        result = QuickGOFetchedData.__new__(QuickGOFetchedData)
        result._content = self._content
        result.endpoint = self.endpoint
        result.download_format = self.download_format
        result.format = self.format
        result.results = filtered
        result.metadata = self.metadata
        result.text = self.text
        return result

    def get_page_info(self) -> Dict[str, Any]:
        """Get pagination info from metadata."""
        return self.metadata.get("pageInfo", {})

    def get_total_hits(self) -> int:
        """Get total number of hits from metadata."""
        return self.metadata.get("numberOfHits", len(self.results))


class QuickGODataManager(BaseDBManager):
    """Data manager for QuickGO data with QuickGO-specific convenience methods."""

    def __init__(
        self,
        storage_path,
        db_name: str = "quickgo",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_quickgo_data(
        self,
        data: QuickGOFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl", "gaf", "gpad", "tsv"] = "csv",
        key: Optional[str] = None,
    ):
        """Save QuickGOFetchedData to storage.

        Args:
            data: The QuickGO data to save.
            filename: Base filename (without extension).
            fmt: Output format.
            key: Optional cache key.
        """
        if fmt == "csv" and data.results:
            return self.save_csv(data.results, filename, key=key)
        elif fmt == "json":
            content = data.results if data.results else data.metadata
            return self.save_json(content, filename, key=key)
        elif fmt == "jsonl" and data.results:
            return self.stream_json_lines(iter(data.results), filename, key=key)
        elif fmt in ("gaf", "gpad", "tsv") and data.text:
            filepath = self.storage_path / f"{filename}.{fmt}"
            filepath.write_text(data.text, encoding="utf-8")
            if key:
                self._update_metadata(key, filepath=str(filepath), format=fmt)
            return filepath
        else:
            raise ValueError(f"Cannot save format {fmt} for data type {data.format}")
