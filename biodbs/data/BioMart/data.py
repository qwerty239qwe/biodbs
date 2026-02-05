"""BioMart fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from typing import Literal, Optional, List, Dict, Any
import pandas as pd
import polars as pl
import xml.etree.ElementTree as ET
from functools import reduce


def _xml_to_dataframe(xml_text: str, tag: Optional[str] = None, how: str = "union") -> pd.DataFrame:
    """Convert XML response to DataFrame.

    Args:
        xml_text: XML string from BioMart response.
        tag: Optional tag to filter elements.
        how: Method to combine attribute keys ("union" or "intersection").

    Returns:
        DataFrame with XML attributes as columns.
    """
    try:
        tree = ET.fromstring(xml_text)
    except ET.ParseError:
        return pd.DataFrame()

    child_keys = [set(ch.attrib.keys()) for ch in tree.iter(tag)]
    if len(child_keys) == 0:
        return pd.DataFrame()

    to_gets = reduce(getattr(set, how), child_keys)
    data = {key: [ch.attrib.get(key) for ch in tree.iter(tag)] for key in to_gets}
    return pd.DataFrame(data).dropna(how="all")


def _tsv_to_dataframe(tsv_text: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Convert TSV response to DataFrame.

    Args:
        tsv_text: TSV string from BioMart response.
        columns: Optional column names. If None, first row is used as header.

    Returns:
        DataFrame with parsed data.
    """
    lines = tsv_text.strip().split("\n")
    if not lines or not lines[0]:
        return pd.DataFrame()

    if columns is None:
        # First line is header
        columns = lines[0].split("\t")
        data_lines = lines[1:]
    else:
        data_lines = lines

    rows = [line.split("\t") for line in data_lines if line.strip()]
    if not rows:
        return pd.DataFrame(columns=columns)

    # Ensure all rows have the same number of columns
    max_cols = max(len(row) for row in rows)
    if len(columns) < max_cols:
        columns = columns + [f"col_{i}" for i in range(len(columns), max_cols)]

    padded_rows = [row + [""] * (len(columns) - len(row)) for row in rows]
    return pd.DataFrame(padded_rows, columns=columns)


class BioMartRegistryData(BaseFetchedData):
    """Fetched data from BioMart registry (list of marts)."""

    def __init__(self, content: str):
        super().__init__(content)
        self.raw_content = content
        self._df = _xml_to_dataframe(content)

    @property
    def marts(self) -> List[str]:
        """Get list of mart names."""
        if "name" in self._df.columns:
            return self._df["name"].dropna().tolist()
        return []

    def as_dataframe(self, engine: Literal["pandas", "polars"] = "pandas"):
        """Convert to DataFrame."""
        if engine == "polars":
            return pl.from_pandas(self._df)
        return self._df

    def as_dict(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries."""
        return self._df.to_dict(orient="records")

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"BioMartRegistryData({len(self._df)} marts)"


class BioMartDatasetsData(BaseFetchedData):
    """Fetched data from BioMart datasets list."""

    def __init__(self, content: str):
        super().__init__(content)
        self.raw_content = content
        columns = [
            "col_0", "dataset", "description", "col_1",
            "version", "col_2", "col_3", "virtual_schema", "col_5"
        ]
        df = _tsv_to_dataframe(content, columns=columns)
        if df.empty:
            self._df = pd.DataFrame(columns=["dataset", "description", "version", "virtual_schema"])
        else:
            self._df = df[["dataset", "description", "version", "virtual_schema"]].dropna(how="all")

    @property
    def datasets(self) -> List[str]:
        """Get list of dataset names."""
        if "dataset" in self._df.columns:
            return self._df["dataset"].dropna().tolist()
        return []

    def search(
        self,
        contain: Optional[str] = None,
        pattern: Optional[str] = None,
        ignore_case: bool = True,
    ) -> pd.DataFrame:
        """Search datasets by name or description.

        Args:
            contain: String to search for (substring match).
            pattern: Regex pattern to match.
            ignore_case: Whether to ignore case for contain search.

        Returns:
            Filtered DataFrame.
        """
        df = self._df.copy()
        if contain:
            contain_str = contain.lower() if ignore_case else contain
            mask = (
                df["dataset"].str.lower().str.contains(contain_str, na=False) |
                df["description"].str.lower().str.contains(contain_str, na=False)
            ) if ignore_case else (
                df["dataset"].str.contains(contain, na=False) |
                df["description"].str.contains(contain, na=False)
            )
            return df[mask]
        if pattern:
            mask = (
                df["dataset"].str.match(pattern, na=False) |
                df["description"].str.match(pattern, na=False)
            )
            return df[mask]
        return df

    def as_dataframe(self, engine: Literal["pandas", "polars"] = "pandas"):
        """Convert to DataFrame."""
        if engine == "polars":
            return pl.from_pandas(self._df)
        return self._df

    def as_dict(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries."""
        return self._df.to_dict(orient="records")

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"BioMartDatasetsData({len(self._df)} datasets)"


class BioMartConfigData(BaseFetchedData):
    """Fetched data from BioMart dataset configuration (filters and attributes)."""

    def __init__(self, content: str):
        super().__init__(content)
        self.raw_content = content
        self._filters_df, self._attributes_df = self._parse_config(content)

    def _parse_config(self, xml_text: str):
        """Parse configuration XML into filters and attributes DataFrames."""
        try:
            tree = ET.fromstring(xml_text)
        except ET.ParseError:
            return pd.DataFrame(), pd.DataFrame()

        # Parse filters
        filter_dfs = []
        for filter_desc in tree.iter("FilterDescription"):
            filter_df = _xml_to_dataframe(
                ET.tostring(filter_desc, encoding="unicode"),
                tag="Option"
            )
            if not filter_df.empty:
                if "internalName" in filter_df.columns:
                    filter_df = filter_df.rename(columns={"internalName": "name"})
                filter_dfs.append(filter_df)

        filters_df = pd.concat(filter_dfs, ignore_index=True) if filter_dfs else pd.DataFrame()

        # Parse attributes
        attr_dfs = []
        for page in tree.iter("AttributePage"):
            page_df = _xml_to_dataframe(
                ET.tostring(page, encoding="unicode"),
                tag="AttributeDescription"
            )
            if not page_df.empty:
                page_df["pageName"] = page.get("internalName")
                page_df["outFormats"] = page.get("outFormats")
                if "internalName" in page_df.columns:
                    page_df = page_df.rename(columns={"internalName": "name"})
                attr_dfs.append(page_df)

        attrs_df = pd.concat(attr_dfs, ignore_index=True) if attr_dfs else pd.DataFrame()

        return filters_df, attrs_df

    @property
    def filter_names(self) -> List[str]:
        """Get list of available filter names."""
        if "name" in self._filters_df.columns:
            return self._filters_df["name"].dropna().tolist()
        return []

    @property
    def attribute_names(self) -> List[str]:
        """Get list of available attribute names."""
        if "name" in self._attributes_df.columns:
            return self._attributes_df["name"].dropna().tolist()
        return []

    def get_filters(
        self,
        contain: Optional[str] = None,
        pattern: Optional[str] = None,
        ignore_case: bool = True,
    ) -> pd.DataFrame:
        """Get filters, optionally filtered by search criteria."""
        df = self._filters_df.copy()
        search_cols = ["name", "displayName", "description"]
        search_cols = [c for c in search_cols if c in df.columns]

        if contain and search_cols:
            contain_str = contain.lower() if ignore_case else contain
            masks = [
                df[col].str.lower().str.contains(contain_str, na=False)
                if ignore_case else df[col].str.contains(contain, na=False)
                for col in search_cols
            ]
            return df[reduce(lambda a, b: a | b, masks)]
        if pattern and search_cols:
            masks = [df[col].str.match(pattern, na=False) for col in search_cols]
            return df[reduce(lambda a, b: a | b, masks)]
        return df

    def get_attributes(
        self,
        contain: Optional[str] = None,
        pattern: Optional[str] = None,
        ignore_case: bool = True,
    ) -> pd.DataFrame:
        """Get attributes, optionally filtered by search criteria."""
        df = self._attributes_df.copy()
        search_cols = ["name", "displayName", "description"]
        search_cols = [c for c in search_cols if c in df.columns]

        if contain and search_cols:
            contain_str = contain.lower() if ignore_case else contain
            masks = [
                df[col].str.lower().str.contains(contain_str, na=False)
                if ignore_case else df[col].str.contains(contain, na=False)
                for col in search_cols
            ]
            return df[reduce(lambda a, b: a | b, masks)]
        if pattern and search_cols:
            masks = [df[col].str.match(pattern, na=False) for col in search_cols]
            return df[reduce(lambda a, b: a | b, masks)]
        return df

    def as_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return filters and attributes as dict."""
        return {
            "filters": self._filters_df.to_dict(orient="records"),
            "attributes": self._attributes_df.to_dict(orient="records"),
        }

    def __len__(self) -> int:
        return len(self._filters_df) + len(self._attributes_df)

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"BioMartConfigData({len(self._filters_df)} filters, {len(self._attributes_df)} attributes)"


class BioMartQueryData(BaseFetchedData):
    """Fetched data from BioMart query results."""

    def __init__(
        self,
        content: str,
        columns: Optional[List[str]] = None,
        has_header: bool = True,
    ):
        super().__init__(content)
        self.raw_content = content
        self.columns = columns
        self.has_header = has_header
        self._df = self._parse_results(content, columns, has_header)

    def _parse_results(
        self,
        content: str,
        columns: Optional[List[str]],
        has_header: bool,
    ) -> pd.DataFrame:
        """Parse query results into DataFrame."""
        if not content or not content.strip():
            return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

        # Check for error messages
        if content.startswith("Query ERROR") or content.startswith("Error"):
            return pd.DataFrame()

        lines = content.strip().split("\n")
        if not lines:
            return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

        if has_header:
            # Skip the header line
            if columns is None:
                # First line is header, use it as column names
                columns = lines[0].split("\t")
            data_lines = lines[1:]
        else:
            data_lines = lines

        rows = [line.split("\t") for line in data_lines if line.strip()]
        if not rows:
            return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

        # Handle column count mismatch
        if columns:
            max_cols = max(len(row) for row in rows)
            if len(columns) < max_cols:
                columns = list(columns) + [f"col_{i}" for i in range(len(columns), max_cols)]
            padded_rows = [row + [""] * (len(columns) - len(row)) for row in rows]
            return pd.DataFrame(padded_rows, columns=columns)
        else:
            return pd.DataFrame(rows)

    @property
    def results(self) -> List[Dict[str, Any]]:
        """Get results as list of dictionaries."""
        return self._df.to_dict(orient="records")

    def __iadd__(self, other: "BioMartQueryData") -> "BioMartQueryData":
        """Concatenate results from another BioMartQueryData."""
        self._df = pd.concat([self._df, other._df], ignore_index=True)
        return self

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        n = len(self._df)
        cols = list(self._df.columns)[:3]
        parts = [f"BioMartQueryData({n} rows"]
        if cols:
            parts.append(f", columns={cols}{'...' if len(self._df.columns) > 3 else ''}")
        parts.append(")")
        return "".join(parts)

    def as_dataframe(self, engine: Literal["pandas", "polars"] = "pandas"):
        """Convert to DataFrame."""
        if engine == "polars":
            return pl.from_pandas(self._df)
        return self._df

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries."""
        if columns:
            return self._df[columns].to_dict(orient="records")
        return self._df.to_dict(orient="records")

    def show_columns(self) -> List[str]:
        """Get list of column names."""
        return list(self._df.columns)

    def filter(self, **kwargs) -> "BioMartQueryData":
        """Filter results based on column values.

        Args:
            **kwargs: Column name and value pairs for filtering.
                     Values can be scalars or callables.

        Returns:
            Filtered BioMartQueryData.
        """
        df = self._df.copy()
        for col, value in kwargs.items():
            if col not in df.columns:
                continue
            if callable(value):
                mask = df[col].apply(value)
            else:
                mask = df[col] == value
            df = df[mask]

        result = BioMartQueryData.__new__(BioMartQueryData)
        result._content = self._content
        result.raw_content = self.raw_content
        result.columns = self.columns
        result.has_header = self.has_header
        result._df = df
        return result

    def drop_duplicates(self) -> "BioMartQueryData":
        """Remove duplicate rows."""
        result = BioMartQueryData.__new__(BioMartQueryData)
        result._content = self._content
        result.raw_content = self.raw_content
        result.columns = self.columns
        result.has_header = self.has_header
        result._df = self._df.drop_duplicates()
        return result

    def has_error(self) -> bool:
        """Check if query returned an error."""
        if isinstance(self.raw_content, str):
            return (
                self.raw_content.startswith("Query ERROR") or
                self.raw_content.startswith("Error") or
                "Exception" in self.raw_content
            )
        return False

    def get_error_message(self) -> Optional[str]:
        """Get error message if present."""
        if self.has_error():
            return self.raw_content[:500]  # Return first 500 chars of error
        return None


class BioMartDataManager(BaseDBManager):
    """Data manager for BioMart data."""

    def __init__(
        self,
        storage_path,
        db_name: str = "biomart",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_query_data(
        self,
        data: BioMartQueryData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl", "tsv", "parquet"] = "csv",
        key: Optional[str] = None,
    ):
        """Save query data to storage.

        Args:
            data: BioMartQueryData object.
            filename: Output filename (without extension).
            fmt: Output format.
            key: Optional cache key.

        Returns:
            Path to saved file.
        """
        df = data.as_dataframe()
        if df.empty:
            raise ValueError("Cannot save empty data")

        if fmt == "csv":
            return self.save_csv(df.to_dict(orient="records"), filename, key=key)
        elif fmt == "json":
            return self.save_json(df.to_dict(orient="records"), filename, key=key)
        elif fmt == "jsonl":
            return self.stream_json_lines(
                iter(df.to_dict(orient="records")), filename, key=key
            )
        elif fmt == "tsv":
            filepath = self.storage_path / f"{filename}.tsv"
            df.to_csv(filepath, sep="\t", index=False)
            if key:
                self._update_metadata(key, filepath=str(filepath), format="tsv")
            return filepath
        elif fmt == "parquet":
            filepath = self.storage_path / f"{filename}.parquet"
            df.to_parquet(filepath, index=False)
            if key:
                self._update_metadata(key, filepath=str(filepath), format="parquet")
            return filepath
        else:
            raise ValueError(f"Unknown format: {fmt}")

    def save_config_data(
        self,
        data: BioMartConfigData,
        dataset_name: str,
        key: Optional[str] = None,
    ):
        """Save dataset configuration to storage.

        Args:
            data: BioMartConfigData object.
            dataset_name: Dataset name for filename.
            key: Optional cache key.

        Returns:
            Dict with paths to saved files.
        """
        filters_path = self.save_json(
            data.get_filters().to_dict(orient="records"),
            f"{dataset_name}_filters",
            key=f"{key}_filters" if key else None,
        )
        attrs_path = self.save_json(
            data.get_attributes().to_dict(orient="records"),
            f"{dataset_name}_attributes",
            key=f"{key}_attributes" if key else None,
        )
        return {"filters": filters_path, "attributes": attrs_path}
