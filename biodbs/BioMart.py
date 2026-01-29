"""
BioMart module (deprecated).

This module is kept for backward compatibility.
"""
from biodbs.deprecated import (
    BIOMART_HOSTS as HOSTS,
    BIOMART_DEFAULT_HOST as DEFAULT_HOST,
    BIOMART_DEFAULT_MART_NAME as DEFAULT_MART_NAME,
    BIOMART_DEFAULT_DATASET_NAME as DEFAULT_DATASET_NAME,
    biomart_get_full_url_from_host as get_full_url_from_host,
    _biomart_rsp_to_df as _rsp_to_df,
    _biomart_find_contained_rows as find_contained_rows,
    _biomart_find_matched_rows as find_matched_rows,
    _biomart_xml_to_tabular as xml_to_tabular,
    BioMartServer as Server,
    BioMartMart as Mart,
    BioMartDataset as Dataset,
)

__all__ = [
    "HOSTS", "DEFAULT_HOST", "DEFAULT_MART_NAME", "DEFAULT_DATASET_NAME",
    "get_full_url_from_host", "_rsp_to_df", "find_contained_rows",
    "find_matched_rows", "xml_to_tabular", "Server", "Mart", "Dataset",
]
