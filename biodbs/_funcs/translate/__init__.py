"""Translation/conversion functions for biological identifiers."""

from biodbs._funcs._species import Species, resolve_species
from biodbs._funcs.translate._id_types import GeneIDType, TranslationDatabase
from biodbs._funcs.translate.genes import (
    translate_gene_ids,
    translate_gene_ids_kegg,
)
from biodbs._funcs.translate.chem import (
    translate_chemical_ids,
    translate_chemical_ids_kegg,
    translate_chembl_to_pubchem,
    translate_pubchem_to_chembl,
)
from biodbs._funcs.translate.proteins import (
    translate_protein_ids,
    translate_gene_to_uniprot,
    translate_uniprot_to_gene,
    translate_uniprot_to_pdb,
    translate_uniprot_to_ensembl,
    translate_uniprot_to_refseq,
)

__all__ = [
    # Species
    "Species",
    "resolve_species",
    # ID type and database enums
    "GeneIDType",
    "TranslationDatabase",
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
