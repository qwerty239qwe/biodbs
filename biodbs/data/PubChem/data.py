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

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        n = len(self.results)
        parts = [f"PUGRestFetchedData({n} results"]
        if self.domain:
            parts.append(f", domain='{self.domain}'")
        if self.operation:
            parts.append(f", operation='{self.operation}'")
        parts.append(")")
        cids = self.get_cids()
        if cids:
            parts.append(f"\n  CIDs: {cids[:5]}{'...' if len(cids) > 5 else ''}")
        return "".join(parts)

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

    def get_properties_df(self, engine: Literal["pandas", "polars"] = "pandas"):
        """Extract compound properties into a clean DataFrame.

        This method extracts the nested 'props' field from PC_Compounds records
        and returns a flat DataFrame with common molecular properties.

        Returns:
            DataFrame with columns: CID, and various property columns like
            MolecularWeight, MolecularFormula, InChI, SMILES, etc.

        Example:
            >>> data = pubchem_get_compounds([2244, 5988])
            >>> df = data.get_properties_df()
            >>> print(df[['CID', 'MolecularFormula', 'MolecularWeight']])
        """
        records = []
        for result in self.results:
            record = {}

            # Extract CID
            if "id" in result and "id" in result["id"]:
                record["CID"] = result["id"]["id"].get("cid")
            elif "CID" in result:
                record["CID"] = result["CID"]

            # Extract properties from 'props' list
            props = result.get("props", [])
            for prop in props:
                urn = prop.get("urn", {})
                value = prop.get("value", {})

                # Get property name from urn
                label = urn.get("label", "")
                name = urn.get("name", "")

                # Get the actual value (can be in different fields)
                val = None
                for val_key in ["sval", "ival", "fval", "binary"]:
                    if val_key in value:
                        val = value[val_key]
                        break

                if label and val is not None:
                    # Create column name from label (and name if different)
                    col_name = label
                    if name and name != label:
                        col_name = f"{label}_{name}"
                    # Clean column name
                    col_name = col_name.replace(" ", "_").replace("-", "_")
                    record[col_name] = val

            # Extract counts
            count = result.get("count", {})
            for count_key, count_val in count.items():
                record[f"count_{count_key}"] = count_val

            # Extract charge
            if "charge" in result:
                record["charge"] = result["charge"]

            records.append(record)

        if not records:
            return pd.DataFrame() if engine == "pandas" else pl.DataFrame()

        return pd.DataFrame(records) if engine == "pandas" else pl.DataFrame(records)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if columns is None:
            return self.results
        return self.format_results(columns=columns)

    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = "",
        sep: str = ".",
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                # Handle lists - if all items are dicts, try to flatten
                if v and all(isinstance(item, dict) for item in v):
                    # For lists of dicts, we can't easily flatten, keep as-is
                    items.append((new_key, v))
                else:
                    items.append((new_key, v))
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
            flatten: If True, flatten nested dictionaries into dot-separated column names.
                     e.g., {'id': {'cid': 2244}} becomes {'id.cid': 2244}

        Raises:
            ValueError: If the data is binary (e.g., SDF, image) and cannot be converted.

        Example:
            >>> data = pubchem_get_compounds([2244, 5988])
            >>> # Without flatten - nested dicts in columns
            >>> df = data.as_dataframe()
            >>> # With flatten - flat columns like 'id.id.cid'
            >>> df = data.as_dataframe(flatten=True)
        """
        # Check for binary data that can't be converted
        if self.binary_data and not self.results:
            raise ValueError(
                "This PubChem response contains binary data (e.g., SDF, image) which cannot be "
                "converted to a DataFrame. Use .binary_data, .to_sdf(path), or .to_image(path) instead."
            )

        data = self.as_dict(columns)
        if not data:
            return pd.DataFrame() if engine == "pandas" else pl.DataFrame()

        if flatten:
            data = [self._flatten_dict(record) for record in data]

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

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        parts = [f"PUGViewFetchedData("]
        if self.record_type:
            parts.append(f"type='{self.record_type}'")
        if self.record_id:
            parts.append(f", id={self.record_id}")
        parts.append(f", {len(self.sections)} sections)")
        if self.sections:
            headings = [s.get("TOCHeading", "") for s in self.sections[:3]]
            parts.append(f"\n  Sections: {headings}{'...' if len(self.sections) > 3 else ''}")
        return "".join(parts)

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

    def as_dataframe(self, *args, **kwargs):
        """PUG View data is hierarchical and cannot be converted to a DataFrame.

        Raises:
            ValueError: Always, as PUG View data is not tabular.

        Use ``as_dict()`` or ``get_parsed_data()`` to access the data as a
        nested dictionary, or use ``get_section()`` and ``find_value()``
        to navigate the hierarchy.
        """
        raise ValueError(
            "PUG View data is hierarchical and cannot be converted to a DataFrame. "
            "Use .as_dict() or .get_parsed_data() to get the data as a dictionary, "
            "or use .get_section() and .find_value() to navigate the hierarchy."
        )

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
