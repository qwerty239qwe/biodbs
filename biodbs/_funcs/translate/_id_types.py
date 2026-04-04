"""Universal ID type aliases for gene identifier translation.

This module defines a single :class:`GeneIDType` enum whose members represent
universal concepts (e.g. "gene symbol", "Entrez ID") that get automatically
resolved to the native field name required by each backend database.

Why this exists
---------------
Every database has its own vocabulary for the same concept:

    ==================  =================  ============  ===========  ===============  ==============
    Universal alias     BioMart            NCBI           UniProt      Ensembl REST     HGNC
    ==================  =================  ============  ===========  ===============  ==============
    gene_symbol         external_gene_name symbol         Gene_Name    HGNC             symbol
    hgnc_id             hgnc_id            —              —            —                hgnc_id
    entrez_id           entrezgene_id      gene_id        GeneID       EntrezGene       entrez_id
    ensembl_gene_id     ensembl_gene_id    ensembl_gene.. Ensembl      ensembl_gene_id  ensembl_gene_id
    uniprot_id          uniprot_gn_id      uniprot        UniProtKB_AC-ID  Uniprot_gn   uniprot_ids
    refseq_mrna         refseq_mrna        refseq_acc..   —            RefSeq_mRNA      refseq_accession
    ensembl_protein_id  ensembl_peptide_id —              —            —                —
    ==================  =================  ============  ===========  ===============  ==============

Usage
-----
    from biodbs.translate import GeneIDType

    result = translate_gene_ids(
        ["TP53", "BRCA1"],
        from_type=GeneIDType.GENE_SYMBOL,
        to_type=GeneIDType.ENSEMBL_GENE_ID,
    )

Raw database-native strings are always accepted too — if a value is not in
the alias map it is passed through unchanged, so existing code keeps working.
"""

from enum import Enum


# ---------------------------------------------------------------------------
# Universal alias enum
# ---------------------------------------------------------------------------

class GeneIDType(str, Enum):
    """Universal gene / protein identifier types.

    Use these members as ``from_type`` / ``to_type`` in :func:`translate_gene_ids`
    instead of database-specific field names.  The correct native name for the
    chosen database is resolved automatically.

    Raw native strings (e.g. ``"external_gene_name"``, ``"Gene_Name"``) are
    still accepted everywhere and passed through unchanged.

    Examples:
        >>> from biodbs.translate import GeneIDType
        >>> translate_gene_ids(["TP53"], from_type=GeneIDType.GENE_SYMBOL,
        ...                    to_type=GeneIDType.ENSEMBL_GENE_ID)
        >>> translate_gene_ids(["TP53"], from_type="gene_symbol",   # same
        ...                    to_type="ensembl_gene_id")
    """

    GENE_SYMBOL         = "gene_symbol"           # HGNC symbol, e.g. "TP53"
    ENSEMBL_GENE_ID     = "ensembl_gene_id"        # e.g. "ENSG00000141510"
    ENSEMBL_TRANSCRIPT_ID = "ensembl_transcript_id" # e.g. "ENST00000269305"
    ENSEMBL_PROTEIN_ID  = "ensembl_protein_id"     # e.g. "ENSP00000269305"
    ENTREZ_ID           = "entrez_id"              # NCBI Entrez Gene ID, e.g. "7157"
    HGNC_ID             = "hgnc_id"                # e.g. "HGNC:11998"
    HGNC_SYMBOL         = "hgnc_symbol"            # HGNC-curated symbol
    UNIPROT_ID          = "uniprot_id"             # UniProt accession, e.g. "P04637"
    REFSEQ_MRNA         = "refseq_mrna"            # e.g. "NM_000546"
    REFSEQ_PROTEIN      = "refseq_protein"         # e.g. "NP_000537"
    PDB_ID              = "pdb_id"                 # PDB structure ID


# ---------------------------------------------------------------------------
# Database-native name maps  (key = GeneIDType value, value = native name)
# ---------------------------------------------------------------------------

BIOMART_ID_MAP: dict[str, str] = {
    GeneIDType.GENE_SYMBOL:          "external_gene_name",
    GeneIDType.ENSEMBL_GENE_ID:      "ensembl_gene_id",
    GeneIDType.ENSEMBL_TRANSCRIPT_ID: "ensembl_transcript_id",
    GeneIDType.ENSEMBL_PROTEIN_ID:   "ensembl_peptide_id",
    GeneIDType.ENTREZ_ID:            "entrezgene_id",
    GeneIDType.HGNC_ID:              "hgnc_id",
    GeneIDType.HGNC_SYMBOL:          "hgnc_symbol",
    GeneIDType.UNIPROT_ID:           "uniprot_gn_id",
    GeneIDType.REFSEQ_MRNA:          "refseq_mrna",
    GeneIDType.REFSEQ_PROTEIN:       "refseq_peptide",
}

NCBI_ID_MAP: dict[str, str] = {
    GeneIDType.GENE_SYMBOL:     "symbol",
    GeneIDType.ENSEMBL_GENE_ID: "ensembl_gene_id",
    GeneIDType.ENTREZ_ID:       "gene_id",
    GeneIDType.UNIPROT_ID:      "uniprot",
    GeneIDType.REFSEQ_MRNA:     "refseq_accession",
    GeneIDType.REFSEQ_PROTEIN:  "refseq_accession",
}

UNIPROT_ID_MAP: dict[str, str] = {
    GeneIDType.GENE_SYMBOL:     "Gene_Name",
    GeneIDType.ENSEMBL_GENE_ID: "Ensembl",
    GeneIDType.ENTREZ_ID:       "GeneID",
    GeneIDType.UNIPROT_ID:      "UniProtKB_AC-ID",
    GeneIDType.REFSEQ_PROTEIN:  "RefSeq_Protein",
    GeneIDType.PDB_ID:          "PDB",
}

ENSEMBL_ID_MAP: dict[str, str] = {
    GeneIDType.GENE_SYMBOL:     "HGNC",
    GeneIDType.ENSEMBL_GENE_ID: "ensembl_gene_id",
    GeneIDType.ENTREZ_ID:       "EntrezGene",
    GeneIDType.UNIPROT_ID:      "Uniprot_gn",
    GeneIDType.REFSEQ_MRNA:     "RefSeq_mRNA",
    GeneIDType.REFSEQ_PROTEIN:  "RefSeq_peptide",
}

# HGNC field names used by the /fetch endpoint.
HGNC_ID_MAP: dict[str, str] = {
    GeneIDType.GENE_SYMBOL:     "symbol",
    GeneIDType.HGNC_ID:         "hgnc_id",
    GeneIDType.HGNC_SYMBOL:     "symbol",
    GeneIDType.ENTREZ_ID:       "entrez_id",
    GeneIDType.ENSEMBL_GENE_ID: "ensembl_gene_id",
    GeneIDType.UNIPROT_ID:      "uniprot_ids",
    GeneIDType.REFSEQ_MRNA:     "refseq_accession",
    GeneIDType.REFSEQ_PROTEIN:  "refseq_accession",
}

_DB_MAPS: dict[str, dict[str, str]] = {
    "biomart": BIOMART_ID_MAP,
    "ncbi":    NCBI_ID_MAP,
    "uniprot": UNIPROT_ID_MAP,
    "ensembl": ENSEMBL_ID_MAP,
    "hgnc":    HGNC_ID_MAP,
}


# ---------------------------------------------------------------------------
# Resolution helper
# ---------------------------------------------------------------------------

def resolve_id_type(id_type: str, database: str) -> str:
    """Resolve a :class:`GeneIDType` member (or any string) to the native
    field name used by *database*.

    If *id_type* is not in the alias map it is returned unchanged, so
    database-native strings always work without modification.

    Args:
        id_type: A :class:`GeneIDType` value (e.g. ``"gene_symbol"``) or a
            raw database-native string (e.g. ``"external_gene_name"``).
        database: One of ``"biomart"``, ``"ncbi"``, ``"uniprot"``,
            ``"ensembl"``.

    Returns:
        The database-native field name.

    Examples:
        >>> resolve_id_type("gene_symbol", "biomart")
        'external_gene_name'
        >>> resolve_id_type(GeneIDType.GENE_SYMBOL, "ncbi")
        'symbol'
        >>> resolve_id_type("external_gene_name", "biomart")  # native pass-through
        'external_gene_name'
        >>> resolve_id_type("symbol", "ncbi")                 # native pass-through
        'symbol'
    """
    db_map = _DB_MAPS.get(database, {})
    # Extract the actual string value from enum members (.value) so that
    # str(GeneIDType.GENE_SYMBOL) == "GeneIDType.GENE_SYMBOL" in Python 3.10
    # doesn't fool the lookup.
    key = id_type.value if hasattr(id_type, "value") else str(id_type)
    return db_map.get(key, key)


# ---------------------------------------------------------------------------
# Database enum  (also used by biodbs.analysis — kept here to avoid circular
# imports since translate is imported by analysis)
# ---------------------------------------------------------------------------

class TranslationDatabase(str, Enum):
    """Databases available for gene ID translation.

    Use these as the ``database`` parameter in :func:`translate_gene_ids` and
    the ``translation_database`` parameter in ORA functions.

    Members:
        NCBI:    NCBI Datasets API.  Most stable; best for symbol ↔ Entrez ↔
                 Ensembl translations.  *Default for translate_gene_ids.*
        ENSEMBL: Ensembl REST API (xrefs endpoint).  More stable than BioMart;
                 natural choice when working with Ensembl IDs.
        UNIPROT: UniProt ID-mapping API.  Best for protein-centric translations
                 (UniProt accession, PDB, RefSeq protein).
        BIOMART: BioMart / Ensembl query interface.  Supports the widest range
                 of ID types but is less reliable than the other options.
        HGNC:    HGNC REST API.  Authoritative for human gene nomenclature;
                 best for translations involving HGNC IDs, approved symbols,
                 aliases, and previous symbols.  **Human only.**

    Examples:
        >>> from biodbs.translate import TranslationDatabase, translate_gene_ids
        >>> translate_gene_ids(["TP53"], from_type="gene_symbol",
        ...                    to_type="ensembl_gene_id",
        ...                    database=TranslationDatabase.NCBI)
        >>> # Raw strings still work for backwards compatibility
        >>> translate_gene_ids(["TP53"], from_type="gene_symbol",
        ...                    to_type="ensembl_gene_id",
        ...                    database="ncbi")
    """

    NCBI    = "ncbi"
    ENSEMBL = "ensembl"
    UNIPROT = "uniprot"
    BIOMART = "biomart"
    HGNC    = "hgnc"
