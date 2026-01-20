from biodbs.data._base import BaseFetchedData
from typing import Literal
import pandas as pd
import polars as pl
from copy import deepcopy


class FDAFetchedData(BaseFetchedData):
    def __init__(self, content):
        super().__init__(content)
        self.metadata = content.get("meta", {})
        self.results = content.get("results", [])

    def __iadd__(self, data: "FDAFetchedData"):
        self.results.extend(data.results)
    
    def as_dict(self, columns=None,):
        if columns is not None:
            return self.format_results(columns=columns)
        return self.results

    def as_dataframe(self, columns, engine: Literal["pandas", "polars"] = "pandas"):
        formatted_results = self.format_results(columns=columns)
        return pd.DataFrame(formatted_results) if engine == "pandas" else pl.DataFrame(formatted_results)

    def _show_valid_columns_helper(self, record, parent_key=""):
        col_list = []
        for key, value in record.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                col_list.extend(self._show_valid_columns_helper(value, full_key))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                col_list.extend(self._show_valid_columns_helper(value[0], full_key))
            else:
                col_list.append(full_key)
        return col_list

    def show_valid_columns(self):
        col_list = []
        for record in self.results:
            col_list.extend(self._show_valid_columns_helper(record))
        unique_cols = sorted(set(col_list))
        return unique_cols
    
    def _get_nested_value(self, data_dict, keys):
        for key in keys:
            if isinstance(data_dict, list):
                data_dict = [self._get_nested_value(item, [key]) for item in data_dict]
            else:
                data_dict = data_dict.get(key, None)
            if data_dict is None:
                return None
        return data_dict
    
    def format_results(self, 
                       columns=None,
                       safe_check=True):
        columns_to_keep = [] if columns is None else columns
        if safe_check:
            valid_columns = self.show_valid_columns()
            for col in columns_to_keep:
                if col not in valid_columns:
                    raise ValueError(f"Column '{col}' is not a valid column. Valid columns are: {valid_columns}")

        formatted_results = []
        for record in self.results:
            formatted_record = {
                col: self._get_nested_value(record, col.split("."))
                for col in columns_to_keep
            }
            formatted_results.append(formatted_record)
        return formatted_results
    
    def trim(self, columns: list):
        raise NotImplementedError("This method should be implemented in subclass.")
    
