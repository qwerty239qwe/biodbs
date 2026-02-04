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

    # Protein ID translation (via UniProt)
    result = translate_protein_ids(
        ["P04637", "P00533"],
        from_type="UniProtKB_AC-ID",
        to_type="GeneID"
    )

    # Gene to UniProt mapping
    result = translate_gene_to_uniprot(["TP53", "BRCA1"])

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
    # Protein translation
    translate_protein_ids,
    translate_gene_to_uniprot,
    translate_uniprot_to_gene,
    translate_uniprot_to_pdb,
    translate_uniprot_to_ensembl,
    translate_uniprot_to_refseq,
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
    # Protein translation
    "translate_protein_ids",
    "translate_gene_to_uniprot",
    "translate_uniprot_to_gene",
    "translate_uniprot_to_pdb",
    "translate_uniprot_to_ensembl",
    "translate_uniprot_to_refseq",
]
