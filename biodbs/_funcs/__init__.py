"""Utility functions for biodbs.

This module provides convenience functions for common operations like
ID translation between different biological databases and enrichment analysis.

Usage:
    from biodbs._funcs import translate_gene_ids, translate_chemical_ids

    # Translate gene symbols to Ensembl IDs
    result = translate_gene_ids(
        ["TP53", "BRCA1"],
        from_type="external_gene_name",
        to_type="ensembl_gene_id"
    )

    # Translate compound names to PubChem CIDs
    result = translate_chemical_ids(
        ["aspirin", "ibuprofen"],
        from_type="name",
        to_type="cid"
    )

    # Over-representation analysis
    from biodbs._funcs import ora_kegg, ora_go

    # KEGG pathway enrichment
    result = ora_kegg(["TP53", "BRCA1", "BRCA2"], id_type="symbol")
    print(result.summary())

    # GO enrichment
    result = ora_go(["P04637", "P38398"], taxon_id=9606)
    print(result.significant_terms().as_dataframe())
"""

from biodbs._funcs.translate import (
    # Gene translation
    translate_gene_ids,
    translate_gene_ids_kegg,
    # Chemical translation
    translate_chemical_ids,
    translate_chemical_ids_kegg,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
)

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
    # Gene translation
    "translate_gene_ids",
    "translate_gene_ids_kegg",
    # Chemical translation
    "translate_chemical_ids",
    "translate_chemical_ids_kegg",
    "translate_chembl_to_pubchem",
    "translate_pubchem_to_chembl",
    # Over-representation analysis
    "ora",
    "ora_kegg",
    "ora_go",
    "ora_enrichr",
    "ORAResult",
    "hypergeometric_test",
    "multiple_test_correction",
]
