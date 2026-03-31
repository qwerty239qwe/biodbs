"""Data model for HGNC REST API responses."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HGNCEntry:
    """A single HGNC gene entry as returned by the /fetch endpoint.

    All fields except ``hgnc_id`` and ``symbol`` are optional because
    HGNC records vary in completeness.

    Attributes:
        hgnc_id: HGNC identifier (e.g. "HGNC:11998").
        symbol: Approved gene symbol (e.g. "TP53").
        name: Full gene name.
        status: Approval status ("Approved", "Entry Withdrawn", etc.).
        location: Chromosomal location (e.g. "17p13.1").
        locus_type: Gene type (e.g. "gene with protein product").
        locus_group: Broader locus group (e.g. "protein-coding gene").
        alias_symbol: Alternative symbols.
        alias_name: Alternative full names.
        prev_symbol: Previous symbols.
        prev_name: Previous names.
        gene_group: Gene family/group names.
        gene_group_id: Gene family/group IDs.
        date_approved_reserved: ISO date the entry was approved.
        date_modified: ISO date of last modification.
        date_symbol_changed: ISO date of last symbol change.
        date_name_changed: ISO date of last name change.
        ensembl_gene_id: Ensembl stable gene ID (e.g. "ENSG00000141510").
        entrez_id: NCBI Gene ID (e.g. "7157").
        uniprot_ids: UniProt accession(s).
        refseq_accession: RefSeq accession(s).
        omim_id: OMIM ID(s).
        ccds_id: CCDS ID(s).
        ena: ENA/GenBank accession(s).
        pubmed_id: PubMed ID(s).
        mgd_id: Mouse Genome Database ID(s).
        rgd_id: Rat Genome Database ID(s).
        enzyme_id: Enzyme Commission number(s).
        vega_id: Vega gene ID.
        ucsc_id: UCSC genome browser ID.
        cosmic: COSMIC gene symbol.
        mirbase: miRBase accession.
        iuphar: Guide to Pharmacology target ID.
        agr: Alliance of Genome Resources ID.
        uuid: Internal HGNC UUID.
    """

    hgnc_id: str
    symbol: str
    name: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    locus_type: Optional[str] = None
    locus_group: Optional[str] = None
    alias_symbol: List[str] = field(default_factory=list)
    alias_name: List[str] = field(default_factory=list)
    prev_symbol: List[str] = field(default_factory=list)
    prev_name: List[str] = field(default_factory=list)
    gene_group: List[str] = field(default_factory=list)
    gene_group_id: List[int] = field(default_factory=list)
    date_approved_reserved: Optional[str] = None
    date_modified: Optional[str] = None
    date_symbol_changed: Optional[str] = None
    date_name_changed: Optional[str] = None
    ensembl_gene_id: Optional[str] = None
    entrez_id: Optional[str] = None
    uniprot_ids: List[str] = field(default_factory=list)
    refseq_accession: List[str] = field(default_factory=list)
    omim_id: List[str] = field(default_factory=list)
    ccds_id: List[str] = field(default_factory=list)
    ena: List[str] = field(default_factory=list)
    pubmed_id: List[int] = field(default_factory=list)
    mgd_id: List[str] = field(default_factory=list)
    rgd_id: List[str] = field(default_factory=list)
    enzyme_id: List[str] = field(default_factory=list)
    vega_id: Optional[str] = None
    ucsc_id: Optional[str] = None
    cosmic: Optional[str] = None
    mirbase: Optional[str] = None
    iuphar: Optional[str] = None
    agr: Optional[str] = None
    uuid: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "HGNCEntry":
        """Construct an HGNCEntry from a raw API response dict.

        Unknown keys are silently ignored so future API additions don't
        break existing code.
        """
        # Fields that HGNC returns as lists
        list_fields = {
            "alias_symbol", "alias_name", "prev_symbol", "prev_name",
            "gene_group", "gene_group_id", "uniprot_ids", "refseq_accession",
            "omim_id", "ccds_id", "ena", "pubmed_id", "mgd_id", "rgd_id",
            "enzyme_id",
        }
        kwargs = {}
        for f in cls.__dataclass_fields__:
            val = data.get(f)
            if val is None:
                continue
            if f in list_fields:
                kwargs[f] = val if isinstance(val, list) else [val]
            else:
                kwargs[f] = val
        return cls(**kwargs)

    def to_dict(self) -> dict:
        """Return a plain dict representation (non-None fields only)."""
        import dataclasses
        return {
            k: v for k, v in dataclasses.asdict(self).items()
            if v is not None and v != []
        }


# Searchable fields supported by the HGNC REST API /search endpoint.
HGNC_SEARCHABLE_FIELDS = frozenset({
    "symbol", "name", "hgnc_id", "status", "location",
    "alias_symbol", "alias_name", "prev_symbol", "prev_name",
    "ensembl_gene_id", "entrez_id", "refseq_accession", "uniprot_ids",
    "omim_id", "ccds_id", "ena", "locus_type", "locus_group",
    "curator_notes", "mgd_id", "rgd_id", "vega_id", "ucsc_id",
    "symbol_report_tag",
})

# Fields returned by /fetch (stored fields — superset of search fields).
HGNC_STORED_FIELDS = frozenset({
    "hgnc_id", "symbol", "name", "status", "location",
    "alias_symbol", "alias_name", "prev_symbol", "prev_name",
    "locus_type", "locus_group", "gene_group", "gene_group_id",
    "date_approved_reserved", "date_modified", "date_symbol_changed",
    "date_name_changed",
    "ensembl_gene_id", "entrez_id", "uniprot_ids", "refseq_accession",
    "omim_id", "ccds_id", "ena", "rna_central_id", "pubmed_id",
    "enzyme_id", "mgd_id", "rgd_id", "vega_id", "ucsc_id",
    "cosmic", "mirbase", "iuphar", "agr", "uuid",
    "lncipedia", "merops", "cd", "horde_id", "bioparadigms_slc",
    "symbol_report_tag", "lsdb", "imgt",
})
