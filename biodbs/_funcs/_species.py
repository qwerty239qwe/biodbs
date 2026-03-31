"""Shared Species enum and resolver used across biodbs.

Kept in a module with no heavy imports so it can be used by both
the translation layer (biodbs._funcs.translate) and the analysis
layer (biodbs._funcs.analysis) without circular imports.
"""

from enum import Enum
from typing import Union


class Species(Enum):
    """Species with their NCBI taxon IDs and common names.

    Each member carries four pieces of metadata so that any naming
    convention (common name, KEGG code, taxon ID, scientific name) can
    be used interchangeably everywhere in biodbs.

    Attributes:
        taxon_id: NCBI taxonomy ID.
        common_name: Lower-case common name (e.g. ``"human"``).
        kegg_code: Three-letter KEGG organism code (e.g. ``"hsa"``).
        scientific_name: Binomial scientific name (e.g. ``"Homo sapiens"``).

    Examples:
        >>> from biodbs import Species
        >>> translate_gene_ids(["TP53"], from_type=GeneIDType.GENE_SYMBOL,
        ...                    to_type=GeneIDType.ENSEMBL_GENE_ID,
        ...                    species=Species.HUMAN)
        >>> ora_kegg(genes, species=Species.MOUSE)
        >>> ora_go(genes, species=Species.HUMAN)
    """

    HUMAN     = (9606,   "human",     "hsa", "Homo sapiens")
    MOUSE     = (10090,  "mouse",     "mmu", "Mus musculus")
    RAT       = (10116,  "rat",       "rno", "Rattus norvegicus")
    ZEBRAFISH = (7955,   "zebrafish", "dre", "Danio rerio")
    FLY       = (7227,   "fly",       "dme", "Drosophila melanogaster")
    WORM      = (6239,   "worm",      "cel", "Caenorhabditis elegans")
    YEAST     = (559292, "yeast",     "sce", "Saccharomyces cerevisiae")

    def __init__(
        self,
        taxon_id: int,
        common_name: str,
        kegg_code: str,
        scientific_name: str,
    ):
        self.taxon_id = taxon_id
        self.common_name = common_name
        self.kegg_code = kegg_code
        self.scientific_name = scientific_name

    # ------------------------------------------------------------------
    # Class-method constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_taxon_id(cls, taxon_id: int) -> "Species":
        """Look up a Species by its NCBI taxonomy ID.

        Raises:
            ValueError: If *taxon_id* is not in the supported set.
        """
        for sp in cls:
            if sp.taxon_id == taxon_id:
                return sp
        raise ValueError(
            f"Unknown taxon ID: {taxon_id}. "
            f"Supported: {', '.join(f'{s.name}={s.taxon_id}' for s in cls)}"
        )

    @classmethod
    def from_kegg_code(cls, kegg_code: str) -> "Species":
        """Look up a Species by its KEGG three-letter organism code.

        Raises:
            ValueError: If *kegg_code* is not recognised.
        """
        for sp in cls:
            if sp.kegg_code == kegg_code:
                return sp
        raise ValueError(
            f"Unknown KEGG code: {kegg_code!r}. "
            f"Supported: {', '.join(s.kegg_code for s in cls)}"
        )

    @classmethod
    def from_name(cls, name: str) -> "Species":
        """Look up a Species from any of its names.

        Accepts the common name (``"human"``), scientific name
        (``"Homo sapiens"``), KEGG code (``"hsa"``), or the enum
        member name (``"HUMAN"``), all case-insensitive.

        Raises:
            ValueError: If *name* does not match any known species.
        """
        name_lower = name.lower().strip()
        for sp in cls:
            if name_lower in (
                sp.common_name.lower(),
                sp.scientific_name.lower(),
                sp.kegg_code.lower(),
                sp.name.lower(),
            ):
                return sp
        raise ValueError(
            f"Unknown species: {name!r}. "
            f"Supported: {', '.join(s.common_name for s in cls)}"
        )


# ---------------------------------------------------------------------------
# Shared resolver
# ---------------------------------------------------------------------------

def resolve_species(value: Union["Species", str, int]) -> "Species":
    """Resolve any species representation to a :class:`Species` member.

    Accepts:
    - a :class:`Species` instance (returned as-is)
    - an ``int`` NCBI taxon ID (e.g. ``9606``)
    - a ``str``: common name (``"human"``), scientific name
      (``"Homo sapiens"``), KEGG code (``"hsa"``), or enum name
      (``"HUMAN"``), all case-insensitive

    Raises:
        ValueError: If the value cannot be matched to any known species.
        TypeError: If *value* is not a Species, str, or int.

    Examples:
        >>> resolve_species("human")
        <Species.HUMAN: (9606, 'human', 'hsa', 'Homo sapiens')>
        >>> resolve_species(9606)
        <Species.HUMAN: ...>
        >>> resolve_species("hsa")
        <Species.HUMAN: ...>
        >>> resolve_species(Species.HUMAN)
        <Species.HUMAN: ...>
    """
    if isinstance(value, Species):
        return value
    if isinstance(value, int):
        return Species.from_taxon_id(value)
    if isinstance(value, str):
        return Species.from_name(value)
    raise TypeError(
        f"Expected Species, str, or int, got {type(value).__name__!r}"
    )
