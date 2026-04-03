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
    ora_reactome,
    ora_reactome_local,
    # Result classes
    ORAResult,
    ORATermResult,
    Pathway,
    # Enums
    Species,
    GOAspect,
    CorrectionMethod,
    TranslationDatabase,
    PathwayDatabase,
    # Utility functions
    hypergeometric_test,
    multiple_test_correction,
)
from biodbs._funcs.analysis.gmt import load_gmt, save_gmt, fetch_gmt

__all__ = [
    # Core ORA functions
    "ora",
    "ora_kegg",
    "ora_go",
    "ora_enrichr",
    "ora_reactome",
    "ora_reactome_local",
    # Result classes
    "ORAResult",
    "ORATermResult",
    "Pathway",
    # Enums
    "Species",
    "GOAspect",
    "CorrectionMethod",
    "TranslationDatabase",
    "PathwayDatabase",
    # Utility functions
    "hypergeometric_test",
    "multiple_test_correction",
    # GMT I/O
    "load_gmt",
    "save_gmt",
    "fetch_gmt",
]
