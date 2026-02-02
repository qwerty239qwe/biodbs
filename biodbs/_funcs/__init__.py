"""Utility functions for biodbs.

This module provides convenience functions for common operations like
ID translation between different biological databases.

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

__all__ = [
    # Gene translation
    "translate_gene_ids",
    "translate_gene_ids_kegg",
    # Chemical translation
    "translate_chemical_ids",
    "translate_chemical_ids_kegg",
    "translate_chembl_to_pubchem",
    "translate_pubchem_to_chembl",
]
