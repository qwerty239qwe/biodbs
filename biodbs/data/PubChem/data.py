"""PubChem fetched data and data manager classes for both PUG REST and PUG View APIs."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from biodbs.data.PubChem.utils import parse_cmp, clean_value
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class PUGRestFetchedData(BaseFetchedData):
    """Fetched data from PubChem PUG REST API.

    PUG REST returns different JSON structures depending on the request:

    For compound records:
        {"PC_Compounds": [{...}, {...}]}

    For properties:
        {"PropertyTable": {"Properties": [{...}, {...}]}}

    For synonyms:
        {"InformationList": {"Information": [{...}]}}

    For CIDs/SIDs:
        {"IdentifierList": {"CID": [...]}} or {"IdentifierList": {"SID": [...]}}

    Attributes:
        results: List of result records (normalized).
        raw_content: Original API response.
        domain: The PubChem domain (compound, substance, etc.).
        operation: The operation performed.
    """

    def __init__(
        self,
        content: Union[dict, list, bytes],
        domain: str = None,
        operation: str = None,
    ):
        super().__init__(content)
        self.domain = domain
        self.operation = operation
        self.raw_content = content

        if isinstance(content, bytes):
            self.results = []
            self.binary_data = content
        else:
            self.binary_data = None
            self.results = self._extract_results(content)

    def _extract_results(self, content: dict) -> List[Dict[str, Any]]:
        """Extract results from various PUG REST response formats."""
        if not isinstance(content, dict):
            return []

        # PC_Compounds format (full compound records)
        if "PC_Compounds" in content:
            return content["PC_Compounds"]

        # PropertyTable format
        if "PropertyTable" in content:
            return content["PropertyTable"].get("Properties", [])

        # InformationList format (synonyms, descriptions)
        if "InformationList" in content:
            return content["InformationList"].get("Information", [])

        # IdentifierList format (CIDs, SIDs, AIDs)
        if "IdentifierList" in content:
            id_list = content["IdentifierList"]
            if "CID" in id_list:
                return [{"CID": cid} for cid in id_list["CID"]]
            elif "SID" in id_list:
                return [{"SID": sid} for sid in id_list["SID"]]
            elif "AID" in id_list:
                return [{"AID": aid} for aid in id_list["AID"]]

        # Assay format
        if "PC_AssayContainer" in content:
            return content["PC_AssayContainer"]

        # Table format
        if "Table" in content:
            table = content["Table"]
            columns = table.get("Columns", {}).get("Column", [])
            rows = table.get("Row", [])
            results = []
            for row in rows:
                cells = row.get("Cell", [])
                record = {col: cell for col, cell in zip(columns, cells)}
                results.append(record)
            return results

        # Waiting/Fault
        if "Waiting" in content or "Fault" in content:
            return []

        # Single record wrapped
        if len(content) == 1:
            key = list(content.keys())[0]
            value = content[key]
            if isinstance(value, list):
                return value
            elif isinstance(value, dict):
                return [value]

        return []

    def __iadd__(self, other: "PUGRestFetchedData") -> "PUGRestFetchedData":
        self.results.extend(other.results)
        return self

    def __len__(self) -> int:
        return len(self.results)

    def get_cids(self) -> List[int]:
        """Extract all CIDs from results."""
        cids = []
        for record in self.results:
            if "CID" in record:
                cids.append(record["CID"])
            elif "id" in record and "id" in record["id"]:
                cid_info = record["id"]["id"]
                if "cid" in cid_info:
                    cids.append(cid_info["cid"])
        return cids

    def get_sids(self) -> List[int]:
        return [r["SID"] for r in self.results if "SID" in r]

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if columns is None:
            return self.results
        return self.format_results(columns=columns)

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
    ):
        data = self.as_dict(columns)
        if not data:
            return pd.DataFrame() if engine == "pandas" else pl.DataFrame()
        return pd.DataFrame(data) if engine == "pandas" else pl.DataFrame(data)

    def _get_nested_value(self, data_dict: dict, keys: List[str]) -> Any:
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
        col_set = set()
        for record in self.results:
            col_set.update(self._show_valid_columns_helper(record))
        return sorted(col_set)

    def format_results(self, columns: List[str], safe_check: bool = True) -> List[Dict[str, Any]]:
        if safe_check:
            valid_columns = self.show_columns()
            for col in columns:
                if col not in valid_columns:
                    raise ValueError(f"Column '{col}' is not valid. Valid columns: {valid_columns}")
        return [
            {col: self._get_nested_value(record, col.split(".")) for col in columns}
            for record in self.results
        ]

    def filter(self, **kwargs) -> "PUGRestFetchedData":
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

        result = PUGRestFetchedData.__new__(PUGRestFetchedData)
        result._content = self._content
        result.domain = self.domain
        result.operation = self.operation
        result.raw_content = self.raw_content
        result.results = filtered
        result.binary_data = None
        return result

    def has_error(self) -> bool:
        if isinstance(self.raw_content, dict):
            return "Fault" in self.raw_content
        return False

    def get_error_message(self) -> Optional[str]:
        if isinstance(self.raw_content, dict) and "Fault" in self.raw_content:
            return self.raw_content["Fault"].get("Message", str(self.raw_content["Fault"]))
        return None

    def to_sdf(self, file_path: str):
        if self.binary_data:
            with open(file_path, "wb") as f:
                f.write(self.binary_data)
        elif isinstance(self.raw_content, str):
            with open(file_path, "w") as f:
                f.write(self.raw_content)

    def to_image(self, file_path: str):
        if self.binary_data:
            with open(file_path, "wb") as f:
                f.write(self.binary_data)


class PUGViewFetchedData(BaseFetchedData):
    """Fetched data from PubChem PUG View API.

    PUG View returns hierarchical annotation data with structure:
        {
            "Record": {
                "RecordType": "CID",
                "RecordNumber": 2244,
                "Section": [
                    {
                        "TOCHeading": "Names and Identifiers",
                        "Section": [...],
                        "Information": [...]
                    },
                    ...
                ]
            }
        }

    This class provides methods to navigate and extract data from this hierarchy.

    Attributes:
        record: The raw Record dict.
        sections: Top-level sections.
        record_type: Type of record (CID, SID, etc.).
        record_id: The record identifier.
    """

    def __init__(self, content: dict, record_type: str = None):
        super().__init__(content)
        self.raw_content = content
        self.record_type = record_type

        if isinstance(content, dict) and "Record" in content:
            self.record = content["Record"]
            self.sections = self.record.get("Section", [])
            self.record_id = self.record.get("RecordNumber")
        else:
            self.record = {}
            self.sections = []
            self.record_id = None

    def get_section(self, heading: str) -> Optional[Dict]:
        """Get a top-level section by heading name."""
        for section in self.sections:
            if section.get("TOCHeading") == heading:
                return section
        return None

    def get_all_headings(self) -> List[str]:
        """Get all top-level section headings."""
        return [s.get("TOCHeading", "") for s in self.sections]

    def get_parsed_data(self) -> Dict:
        """Parse the hierarchical structure into a cleaner dict format.

        Uses the parse_cmp and clean_value utilities.
        """
        if self.sections:
            return clean_value(parse_cmp(self.sections))
        return {}

    def get_information(self, heading: str) -> List[Dict]:
        """Get Information entries from a specific section."""
        section = self.get_section(heading)
        if section:
            return section.get("Information", [])
        return []

    def get_subsections(self, heading: str) -> List[Dict]:
        """Get subsections from a specific top-level section."""
        section = self.get_section(heading)
        if section:
            return section.get("Section", [])
        return []

    def find_value(self, *path: str) -> Any:
        """Navigate through the section hierarchy to find a value.

        Args:
            *path: Sequence of section headings to navigate.

        Example:
            data.find_value("Names and Identifiers", "Computed Descriptors", "IUPAC Name")
        """
        current = self.sections
        for heading in path:
            found = None
            for item in current:
                if item.get("TOCHeading") == heading:
                    found = item
                    break
            if found is None:
                return None
            # Try to get nested sections or information
            if "Section" in found:
                current = found["Section"]
            elif "Information" in found:
                return found["Information"]
            else:
                return found
        return current

    def as_dict(self) -> Dict:
        """Return the parsed data as a dictionary."""
        return self.get_parsed_data()

    def has_error(self) -> bool:
        if isinstance(self.raw_content, dict):
            return "Fault" in self.raw_content
        return False

    def get_error_message(self) -> Optional[str]:
        if isinstance(self.raw_content, dict) and "Fault" in self.raw_content:
            return self.raw_content["Fault"].get("Message", str(self.raw_content["Fault"]))
        return None


# Backwards compatibility alias
PubChemFetchedData = PUGRestFetchedData


class PubChemDataManager(BaseDBManager):
    """Data manager for PubChem data."""

    def __init__(
        self,
        storage_path,
        db_name: str = "pubchem",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_rest_data(
        self,
        data: PUGRestFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl", "sdf"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save PUG REST data to storage."""
        if fmt == "csv" and data.results:
            records = data.as_dict(columns) if columns else data.results
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.results, filename, key=key)
        elif fmt == "jsonl" and data.results:
            return self.stream_json_lines(iter(data.results), filename, key=key)
        elif fmt == "sdf" and data.binary_data:
            filepath = self.storage_path / f"{filename}.sdf"
            with open(filepath, "wb") as f:
                f.write(data.binary_data)
            if key:
                self._update_metadata(key, filepath=str(filepath), format="sdf")
            return filepath
        else:
            raise ValueError(f"Cannot save format {fmt} for this data")

    def save_view_data(
        self,
        data: PUGViewFetchedData,
        filename: str,
        key: Optional[str] = None,
    ):
        """Save PUG View data to storage."""
        parsed = data.get_parsed_data()
        return self.save_json(parsed, filename, key=key)
