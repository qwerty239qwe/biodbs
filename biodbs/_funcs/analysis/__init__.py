"""Analysis functions for biodbs.

This module provides statistical analysis functions for biological data,
including over-representation analysis (ORA) for gene set enrichment.
"""

from biodbs._funcs.analysis.ora import (
    # Core ORA functions
    ora,
    ora_kegg,
    ora_go,
    ora_enrichr,
    # Result class
    ORAResult,
    # Utility functions
    hypergeometric_test,
    multiple_test_correction,
)

__all__ = [
    # Core ORA functions
    "ora",
    "ora_kegg",
    "ora_go",
    "ora_enrichr",
    # Result class
    "ORAResult",
    # Utility functions
    "hypergeometric_test",
    "multiple_test_correction",
]
