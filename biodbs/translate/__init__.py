"""ID translation functions for biodbs.

This module provides convenience functions for translating between different
biological identifier systems (gene IDs, chemical IDs, protein IDs).

Usage:
    from biodbs.translate import translate_gene_ids, translate_chemical_ids

    # Gene ID translation
    result = translate_gene_ids(
        ["TP53", "BRCA1"],
        from_type="external_gene_name",
        to_type="ensembl_gene_id"
    )

    # Chemical ID translation
    result = translate_chemical_ids(
        ["aspirin", "ibuprofen"],
        from_type="name",
        to_type="cid"
    )

    # Cross-database translation
    result = translate_chembl_to_pubchem(["CHEMBL25"])
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
