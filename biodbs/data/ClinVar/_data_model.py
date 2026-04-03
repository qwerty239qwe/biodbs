"""Data model for ClinVar E-utilities API responses (esummary JSON)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ClinVarVariant:
    """A single ClinVar variant record as parsed from the esummary JSON response.

    Fields are populated from the ``result.<uid>`` object returned by::

        esummary.fcgi?db=clinvar&id=<uid>&retmode=json

    Attributes:
        variation_id: ClinVar variation UID (integer string, e.g. ``"65533"``).
        accession: VCV accession (e.g. ``"VCV000065533"``).
        accession_version: Versioned VCV accession (e.g. ``"VCV000065533.5"``).
        title: Human-readable variant name (e.g.
            ``"NM_007294.4(BRCA1):c.181T>G (p.Cys61Gly)"``).
        variation_type: Variant class (e.g. ``"single nucleotide variant"``).
        clinical_significance: Interpreted clinical significance
            (e.g. ``"Pathogenic"``, ``"Likely benign"``).
        review_status: Evidence review level
            (e.g. ``"reviewed by expert panel"``).
        last_evaluated: ISO date the significance was last evaluated.
        gene_symbols: Approved gene symbols associated with the variant.
        gene_ids: Corresponding NCBI Gene IDs (parallel to *gene_symbols*).
        conditions: Disease/trait names reported in submissions.
        rcv_accessions: List of RCV accessions for this variant.
        protein_change: Protein-level change in one-letter code
            (e.g. ``"Cys61Gly"``).
        chromosome: Chromosome (e.g. ``"17"``).
        start: Genomic start position (GRCh38 preferred, GRCh37 as fallback).
        stop: Genomic stop position.
        assembly: Reference assembly name (e.g. ``"GRCh38"``).
    """

    variation_id: str
    accession: str = ""
    accession_version: str = ""
    title: str = ""
    variation_type: Optional[str] = None
    clinical_significance: Optional[str] = None
    review_status: Optional[str] = None
    last_evaluated: Optional[str] = None
    gene_symbols: List[str] = field(default_factory=list)
    gene_ids: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    rcv_accessions: List[str] = field(default_factory=list)
    protein_change: Optional[str] = None
    chromosome: Optional[str] = None
    start: Optional[int] = None
    stop: Optional[int] = None
    assembly: Optional[str] = None

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_esummary_dict(cls, uid: str, doc: dict) -> "ClinVarVariant":
        """Parse a single ``result.<uid>`` dict from an esummary JSON response.

        Unknown / missing keys are silently ignored so API additions don't
        break existing code.

        Args:
            uid: The UID string (key in the ``result`` object).
            doc: The dict value for that UID.

        Returns:
            A populated :class:`ClinVarVariant`.
        """
        # --- genes ---
        gene_symbols: List[str] = []
        gene_ids: List[str] = []
        for g in doc.get("genes", []):
            sym = g.get("symbol", "")
            gid = str(g.get("geneid", ""))
            if sym:
                gene_symbols.append(sym)
            if gid:
                gene_ids.append(gid)

        # --- clinical significance ---
        clin_sig = doc.get("clinical_significance", {})
        if isinstance(clin_sig, dict):
            significance = clin_sig.get("description")
            review_status = clin_sig.get("review_status")
            last_evaluated = clin_sig.get("last_evaluated")
        else:
            significance = review_status = last_evaluated = None

        # --- conditions / traits ---
        conditions: List[str] = []
        for trait in doc.get("trait_set", []):
            name = trait.get("trait_name", "")
            if name:
                conditions.append(name)

        # --- RCV accessions (pipe-separated string or list) ---
        rcv_raw = doc.get("rcvaccession", "")
        if isinstance(rcv_raw, list):
            rcv_accessions = [r for r in rcv_raw if r]
        elif rcv_raw:
            rcv_accessions = [r.strip() for r in rcv_raw.split("|") if r.strip()]
        else:
            rcv_accessions = []

        # --- variation type ---
        variation_type: Optional[str] = None
        for vs in doc.get("variation_set", []):
            ms = vs.get("measure_set", {})
            vt = ms.get("variation_type") or vs.get("obj_type")
            if vt:
                variation_type = vt
                break
        # fallback: obj_type at top level
        if not variation_type:
            variation_type = doc.get("obj_type")

        # --- genomic location (prefer GRCh38, fallback GRCh37) ---
        chromosome = start = stop = assembly = None
        assembly_set = doc.get("assembly_set", [])
        preferred: Optional[dict] = None
        for asm in assembly_set:
            loc = asm.get("location", {})
            asm_name = (asm.get("assembly_name") or loc.get("asm_name") or "").upper()
            if "GRCH38" in asm_name:
                preferred = (asm, loc)
                break
        if preferred is None and assembly_set:
            preferred = (assembly_set[0], assembly_set[0].get("location", {}))

        if preferred:
            asm_dict, loc = preferred
            chromosome = loc.get("chr") or loc.get("chromosome")
            raw_start = loc.get("start")
            raw_stop = loc.get("stop")
            start = int(raw_start) if raw_start is not None else None
            stop = int(raw_stop) if raw_stop is not None else None
            assembly = asm_dict.get("assembly_name") or loc.get("asm_name")

        return cls(
            variation_id=uid,
            accession=doc.get("accession", ""),
            accession_version=doc.get("accession_version", ""),
            title=doc.get("title", ""),
            variation_type=variation_type,
            clinical_significance=significance,
            review_status=review_status,
            last_evaluated=last_evaluated,
            gene_symbols=gene_symbols,
            gene_ids=gene_ids,
            conditions=conditions,
            rcv_accessions=rcv_accessions,
            protein_change=doc.get("protein_change") or None,
            chromosome=chromosome,
            start=start,
            stop=stop,
            assembly=assembly,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a flat dict representation (all fields, None preserved)."""
        return dataclasses.asdict(self)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_pathogenic(self) -> bool:
        """``True`` if the variant is classified Pathogenic or Likely pathogenic."""
        sig = (self.clinical_significance or "").lower()
        return "pathogenic" in sig and "likely benign" not in sig

    @property
    def primary_gene(self) -> Optional[str]:
        """First gene symbol, or ``None`` if no gene is associated."""
        return self.gene_symbols[0] if self.gene_symbols else None

    def __repr__(self) -> str:
        sig = self.clinical_significance or "?"
        gene = self.primary_gene or "?"
        return (
            f"<ClinVarVariant {self.accession} [{gene}] "
            f"{self.variation_type or 'variant'} — {sig}>"
        )
