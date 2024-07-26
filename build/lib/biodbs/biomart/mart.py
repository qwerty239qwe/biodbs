import pandas as pd
from biodbs.biomart.enum import BiomartHost, BiomartDatabase, BiomartMart
from biodbs.biomart.utils import *
from biodbs.utils import *


class Server:
    """
    A biomart server contains many mart
    """
    def __init__(self, host=BiomartHost.main):
        self.host = host
        self._mart_df = None

    @property
    def marts(self) -> list:
        if not isinstance(self._mart_df, pd.DataFrame):
            _ = self.list_marts()
        return self._mart_df["name"].to_list()

    @property
    def mart_df(self) -> pd.DataFrame:
        if not isinstance(self._mart_df, pd.DataFrame):
            _ = self.list_marts()
        return self._mart_df

    def list_marts(self):
        if not isinstance(self._mart_df, pd.DataFrame):
            rsp = get_rsp(self.host, query={"type": "registry"})
            self._mart_df = xml_to_tabular(rsp.text)
        return self._mart_df


class Mart:
    """
    A mart contains many datasets
    """
    def __init__(self,
                 mart_name: str | BiomartMart = BiomartMart.default,
                 host: str | BiomartHost = BiomartHost.main):
        self.host = host
        self.mart_name = mart_name
        self._datasets = None

    @property
    def datasets(self):
        if not isinstance(self._datasets, pd.DataFrame):
            self._datasets = self._get_datasets()
        return self._datasets["dataset"]

    def _get_datasets(self):
        query = {"type": "datasets", "mart": self.mart_name}
        columns = ["col_0", "dataset", "description", "col_1",
                   "version", "col_2", "col_3", "virtual_schema", "col_5"]
        df = response_to_df(get_rsp(self.host, query), columns)[["dataset", "description",
                                                                "version", "virtual_schema"]].dropna(how="all")
        return df

    def list_datasets(self,
                      contain: str = None,
                      ignore_case: bool = True,
                      pattern: str = None):
        if not isinstance(self._datasets, pd.DataFrame):
            self._datasets = self._get_datasets()

        if contain:
            df = find_contained_rows(df=self._datasets,
                                     contain=contain,
                                     cols=["dataset", "description"],
                                     ignore_case=ignore_case)
        elif pattern:
            df = find_matched_rows(df=self._datasets,
                                   pattern=pattern,
                                   cols=["dataset", "description"])
        else:
            df = self._datasets
        return df


