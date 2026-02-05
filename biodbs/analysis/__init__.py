"""Analysis functions for biodbs.

This module provides high-level analysis functions for biological data,
including over-representation analysis (ORA) for pathway/gene set enrichment.

Usage:
    from biodbs.analysis import ora_kegg, ora_go, ora_enrichr, ora_reactome

    # KEGG pathway enrichment - automatic ID translation
    result = ora_kegg(
        genes=["TP53", "BRCA1", "BRCA2", "ATM"],
        organism="hsa",
        from_id_type="symbol"  # Auto-converts to Entrez IDs
    )
    print(result.summary())
    print(result.significant_terms(alpha=0.05).as_dataframe())

    # GO term enrichment - automatic ID translation
    result = ora_go(
        genes=["TP53", "BRCA1", "BRCA2"],
        taxon_id=9606,
        from_id_type="symbol",  # Auto-converts to UniProt IDs
        aspect="biological_process"
    )

    # EnrichR analysis - automatic ID translation
    result = ora_enrichr(
        genes=["ENSG00000141510", "ENSG00000012048"],
        gene_set_library="KEGG_2021_Human",
        from_id_type="ensembl"  # Auto-converts to symbols
    )

    # Reactome pathway analysis - automatic ID translation
    result = ora_reactome(
        genes=["7157", "672", "675"],
        species="Homo sapiens",
        from_id_type="entrez"  # Auto-converts to symbols
    )
    print(result.top_terms(10).as_dataframe())

For more control, use the generic ora() function with custom pathway data:
    from biodbs.analysis import ora, hypergeometric_test

    result = ora(
        genes=my_genes,
        gene_sets=my_pathways,
        background=my_background_genes,
        correction_method="bh"
    )
"""

from biodbs._funcs.analysis import (
    # Core ORA functions
    ora,
    ora_kegg,
    ora_go,
    ora_enrichr,
    ora_reactome,
    ora_reactome_local,
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
    "ora_reactome",
    "ora_reactome_local",
    # Result class
    "ORAResult",
    # Utility functions
    "hypergeometric_test",
    "multiple_test_correction",
]
