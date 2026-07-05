"""GTDB data wrappers."""

from biodbs.data.GTDB._data_model import GTDBFile
from biodbs.data.GTDB.data import GTDBFileListData, GTDBTableData, GTDBTextData

__all__ = [
    "GTDBFile",
    "GTDBFileListData",
    "GTDBTableData",
    "GTDBTextData",
]
