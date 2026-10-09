"""Optional reusable configuration for the function-based translation API."""

from dataclasses import dataclass

from biodbs._funcs._species import Species


@dataclass(frozen=True)
class GeneMapper:
    """Gene translation configuration; defaults to NCBI and human.

    ``database`` accepts existing gene backends or ``"kegg"``. ``species``
    accepts the same values as ``translate_gene_ids``. No results are cached.
    """

    database: str = "ncbi"
    species: Species | str | int = Species.HUMAN

    def map(self, ids, from_type, to_type, return_dict=False, *, bulk=False):
        """Translate using this mapper's backend and species."""
        from biodbs._funcs.translate.genes import _translate_gene_ids

        return _translate_gene_ids(
            ids, from_type, to_type, self.species, self.database, return_dict, bulk=bulk
        )


@dataclass(frozen=True)
class ChemicalMapper:
    """Chemical translation configuration.

    ``database="auto"`` retains PubChem for existing ID types and selects
    ChEMBL or KEGG only for their explicit identifier types. Explicit backends
    are ``"pubchem"``, ``"chembl"``, and ``"kegg"``; no fallback is attempted.
    """

    database: str = "auto"

    def map(self, ids, from_type, to_type, return_dict=False, *, bulk=False):
        """Translate using this mapper's routing policy."""
        from biodbs._funcs.translate.chem import _translate_chemical_ids

        return _translate_chemical_ids(
            ids, from_type, to_type, return_dict, database=self.database, bulk=bulk
        )


@dataclass(frozen=True)
class ProteinMapper:
    """UniProt translation configuration; human and reviewed entries by default.

    Organism and review filters apply to gene-name lookup. This object does
    not cache results or change the existing UniProt mapping policy.
    """

    organism: int = 9606
    reviewed_only: bool = True

    def map(self, ids, from_type, to_type, return_dict=False, *, all_matches=False):
        """Translate using this mapper's organism and review filter."""
        from biodbs._funcs.translate.proteins import _translate_protein_ids

        return _translate_protein_ids(
            ids, from_type, to_type, self.organism, return_dict,
            reviewed_only=self.reviewed_only, all_matches=all_matches,
        )
