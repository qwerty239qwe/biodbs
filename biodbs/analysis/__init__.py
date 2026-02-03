"""Analysis functions for biodbs.

This module provides high-level analysis functions for biological data,
including over-representation analysis (ORA) for pathway/gene set enrichment.

Usage:
    from biodbs.analysis import ora_kegg, ora_go, ora_enrichr

    # KEGG pathway enrichment analysis
    result = ora_kegg(
        gene_list=["TP53", "BRCA1", "BRCA2", "ATM"],
        organism="hsa",
        id_type="symbol"
    )
    print(result.summary())
    print(result.significant_terms(alpha=0.05).as_dataframe())

    # GO term enrichment analysis
    result = ora_go(
        gene_list=["P04637", "P38398", "P51587"],
        taxon_id=9606,
        aspect="biological_process"
    )

    # EnrichR analysis (uses external service)
    result = ora_enrichr(
        gene_list=["TP53", "BRCA1", "BRCA2"],
        gene_set_library="KEGG_2021_Human"
    )

For more control, use the generic ora() function with custom pathway data:
    from biodbs.analysis import ora, hypergeometric_test

    result = ora(
        gene_list=my_genes,
        pathway_dict=my_pathways,
        background=my_background_genes,
        correction="fdr_bh"
    )
"""

from biodbs._funcs.analysis import (
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
