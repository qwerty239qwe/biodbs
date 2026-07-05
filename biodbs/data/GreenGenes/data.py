"""Fetched data wrappers for GreenGenes."""

from fnmatch import fnmatch
from typing import Iterator

import pandas as pd

from biodbs.data._base import BaseFetchedData
from biodbs.data.GreenGenes._data_model import GreenGenesFile, GreenGenesRelease


class GreenGenesFileListData(BaseFetchedData):
    """GreenGenes release file listing."""

    def __init__(self, files: list[GreenGenesFile]):
        super().__init__(files)
        self.files = files

    def __len__(self) -> int:
        return len(self.files)

    def __iter__(self) -> Iterator[GreenGenesFile]:
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
            raise ValueError("GreenGenes data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def names(self) -> list[str]:
        return [item.name for item in self.files]

    def urls(self) -> list[str]:
        return [item.url for item in self.files]

    def filter(self, pattern: str) -> "GreenGenesFileListData":
        return GreenGenesFileListData([item for item in self.files if fnmatch(item.name, pattern)])


class GreenGenesReleaseListData(BaseFetchedData):
    """GreenGenes release listing."""

    def __init__(self, releases: list[GreenGenesRelease]):
        super().__init__(releases)
        self.releases = releases

    def __len__(self) -> int:
        return len(self.releases)

    def __iter__(self) -> Iterator[GreenGenesRelease]:
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
            raise ValueError("GreenGenes data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def names(self) -> list[str]:
        return [item.name for item in self.releases]

    def urls(self) -> list[str]:
        return [item.url for item in self.releases]
