"""Fetched data wrappers for PR2."""

from fnmatch import fnmatch
from typing import Iterator

import pandas as pd

from biodbs.data._base import BaseFetchedData
from biodbs.data.PR2._data_model import PR2Asset, PR2Release


class PR2AssetListData(BaseFetchedData):
    """PR2 release asset listing."""

    def __init__(self, assets: list[PR2Asset]):
        super().__init__(assets)
        self.assets = assets

    def __len__(self) -> int:
        return len(self.assets)

    def __iter__(self) -> Iterator[PR2Asset]:
        return iter(self.assets)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.assets[key]
        for item in self.assets:
            if item.name == key:
                return item
        raise KeyError(key)

    def as_dict(self) -> list[dict]:
        return [item.to_dict() for item in self.assets]

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        if engine != "pandas":
            raise ValueError("PR2 data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def names(self) -> list[str]:
        return [item.name for item in self.assets]

    def urls(self) -> list[str]:
        return [item.url for item in self.assets]

    def filter(self, pattern: str) -> "PR2AssetListData":
        return PR2AssetListData([item for item in self.assets if fnmatch(item.name, pattern)])


class PR2ReleaseListData(BaseFetchedData):
    """PR2 release listing."""

    def __init__(self, releases: list[PR2Release]):
        super().__init__(releases)
        self.releases = releases

    def __len__(self) -> int:
        return len(self.releases)

    def __iter__(self) -> Iterator[PR2Release]:
        return iter(self.releases)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.releases[key]
        for item in self.releases:
            if item.tag == key:
                return item
        raise KeyError(key)

    def as_dict(self) -> list[dict]:
        return [item.to_dict() for item in self.releases]

    def as_dataframe(self, engine: str = "pandas") -> pd.DataFrame:
        if engine != "pandas":
            raise ValueError("PR2 data currently supports engine='pandas' only.")
        return pd.DataFrame(self.as_dict())

    def names(self) -> list[str]:
        return [item.tag for item in self.releases]
