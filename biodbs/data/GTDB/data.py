"""Fetched data wrappers for GTDB."""

from __future__ import annotations

import csv
from fnmatch import fnmatch
from io import StringIO
from typing import Iterator

import pandas as pd

from biodbs.data._base import BaseFetchedData
from biodbs.data.GTDB._data_model import GTDBFile


class GTDBFileListData(BaseFetchedData):
    """GTDB release file listing."""

    def __init__(self, files: list[GTDBFile]):
        super().__init__(files)
        self.files = files

    def __len__(self) -> int:
        return len(self.files)

    def __iter__(self) -> Iterator[GTDBFile]:
        return iter(self.files)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.files[key]
        for item in self.files:
            if item.name == key:
                return item
        raise KeyError(key)

    def as_dict(self) -> list[dict]:
        return [item.to_dict() for item in self.files]

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        if engine != "pandas":
            raise ValueError("GTDB data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def names(self) -> list[str]:
        return [item.name for item in self.files]

    def urls(self) -> list[str]:
        return [item.url for item in self.files]

    def filter(self, pattern: str) -> "GTDBFileListData":
        return GTDBFileListData([item for item in self.files if fnmatch(item.name, pattern)])


class GTDBTableData(BaseFetchedData):
    """Tabular GTDB release data."""

    def __init__(
        self,
        text: str,
        url: str = "",
        delimiter: str = "\t",
        fieldnames: list[str] | None = None,
    ):
        rows = (
            list(csv.DictReader(StringIO(text), delimiter=delimiter, fieldnames=fieldnames))
            if text.strip()
            else []
        )
        super().__init__(rows)
        self.text = text
        self.url = url
        self.delimiter = delimiter
        self.fieldnames = fieldnames
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[dict]:
        return iter(self.rows)

    def __getitem__(self, key):
        return self.rows[key]

    def as_dict(self) -> list[dict]:
        return self.rows

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        if engine != "pandas":
            raise ValueError("GTDB data currently supports engine='pandas' only.")
        return pd.DataFrame(self.rows)


class GTDBTextData(BaseFetchedData):
    """Small text file fetched from GTDB."""

    def __init__(self, text: str, url: str = ""):
        super().__init__(text)
        self.text = text
        self.url = url

    def __str__(self) -> str:
        return self.text

    def as_dict(self) -> dict:
        return {"text": self.text, "url": self.url}
