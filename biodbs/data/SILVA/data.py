"""Fetched data wrappers for SILVA."""

from fnmatch import fnmatch
from typing import Iterator

import pandas as pd

from biodbs.data._base import BaseFetchedData
from biodbs.data.SILVA._data_model import SILVAFile, SILVARelease


class SILVAFileListData(BaseFetchedData):
    """SILVA release file listing."""

    def __init__(self, files: list[SILVAFile]):
        super().__init__(files)
        self.files = files

    def __len__(self) -> int:
        return len(self.files)

    def __iter__(self) -> Iterator[SILVAFile]:
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
            raise ValueError("SILVA data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def names(self) -> list[str]:
        return [item.name for item in self.files]

    def urls(self) -> list[str]:
        return [item.url for item in self.files]

    def filter(self, pattern: str) -> "SILVAFileListData":
        return SILVAFileListData([item for item in self.files if fnmatch(item.name, pattern)])


class SILVAReleaseListData(BaseFetchedData):
    """SILVA archive release listing."""

    def __init__(self, releases: list[SILVARelease]):
        super().__init__(releases)
        self.releases = releases

    def __len__(self) -> int:
        return len(self.releases)

    def __iter__(self) -> Iterator[SILVARelease]:
        return iter(self.releases)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.releases[key]
        for item in self.releases:
            if item.name == key:
                return item
        raise KeyError(key)

    def as_dict(self) -> list[dict]:
        return [item.to_dict() for item in self.releases]

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        if engine != "pandas":
            raise ValueError("SILVA data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def names(self) -> list[str]:
        return [item.name for item in self.releases]

    def urls(self) -> list[str]:
        return [item.url for item in self.releases]


class SILVATextData(BaseFetchedData):
    """Small text file fetched from SILVA."""

    def __init__(self, text: str, url: str = ""):
        super().__init__(text)
        self.text = text
        self.url = url

    def __str__(self) -> str:
        return self.text

    def as_dict(self) -> dict:
        return {"text": self.text, "url": self.url}

