"""
KEGG module (deprecated).

This module is kept for backward compatibility. New code should use:
    from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher
"""
import warnings
warnings.warn(
    "biodbs.KEGG is deprecated and will be removed in a future release. "
    "Use 'from biodbs.fetch.KEGG.funcs import ...' or 'from biodbs.fetch.KEGG.kegg_fetcher import KEGG_Fetcher' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from biodbs.deprecated import (
    KEGGDatabase as Database,
    KEGG_DEFAULT_HOST as DEFAULT_HOST,
    KEGG_ALIAS_NAME_DICT as ALIAS_NAME_DICT,
    kegg_list_database as list_database,
    KEGGdb,
)

__all__ = ["Database", "DEFAULT_HOST", "ALIAS_NAME_DICT", "list_database", "KEGGdb"]
