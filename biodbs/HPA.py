"""
HPA (Human Protein Atlas) module (deprecated).

This module is kept for backward compatibility.
"""
import warnings
warnings.warn(
    "biodbs.HPA is deprecated and will be removed in a future release. "
    "Use 'from biodbs.fetch.HPA.funcs import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from biodbs.deprecated import (
    HPA_DEFAULT_HOST as DEFAULT_HOST,
    HPA_DOWNLOADABLE_DATA as DOWNLOADABLE_DATA,
    HPAdb,
)

__all__ = ["DEFAULT_HOST", "DOWNLOADABLE_DATA", "HPAdb"]
