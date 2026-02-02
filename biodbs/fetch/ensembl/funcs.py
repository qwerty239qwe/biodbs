"""Convenience functions for Ensembl REST API.

These functions provide easy access to common Ensembl operations
without needing to instantiate the fetcher class directly.
"""

from typing import List, Optional, Union
from biodbs.data.Ensembl.data import EnsemblFetchedData

# Module-level fetcher instance (lazy initialization)
_fetcher = None


def _get_fetcher():
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None:
        from biodbs.fetch.ensembl.ensembl_fetcher import Ensembl_Fetcher
        _fetcher = Ensembl_Fetcher()
    return _fetcher


# =============================================================================
# Lookup Functions
# =============================================================================

def ensembl_lookup(
    id: str,
    species: Optional[str] = None,
    expand: bool = False,
    db_type: str = "core",
) -> EnsemblFetchedData:
    """Look up an Ensembl stable ID.

    Args:
        id: Ensembl stable ID (e.g., "ENSG00000141510" for TP53).
        species: Species name/alias (optional, auto-detected from ID).
        expand: Include connected features (transcripts, exons).
        db_type: Database type ("core" or "otherfeatures").

    Returns:
        EnsemblFetchedData with gene/transcript/protein information.

    Example:
        >>> data = ensembl_lookup("ENSG00000141510", expand=True)
        >>> print(data.results[0]["display_name"])  # TP53
    """
    return _get_fetcher().lookup(id=id, species=species, expand=expand, db_type=db_type)


def ensembl_lookup_batch(
    ids: List[str],
    species: Optional[str] = None,
    expand: bool = False,
) -> EnsemblFetchedData:
    """Look up multiple Ensembl stable IDs in batch.

    Args:
        ids: List of Ensembl stable IDs (max 1000).
        species: Species name/alias.
        expand: Include connected features.

    Returns:
        EnsemblFetchedData with results for each ID.

    Example:
        >>> data = ensembl_lookup_batch(["ENSG00000141510", "ENSG00000012048"])
    """
    return _get_fetcher().lookup_batch(ids=ids, species=species, expand=expand)


def ensembl_lookup_symbol(
    species: str,
    symbol: str,
    expand: bool = False,
) -> EnsemblFetchedData:
    """Look up a gene by symbol.

    Args:
        species: Species name (e.g., "human", "mouse").
        symbol: Gene symbol (e.g., "BRCA2", "TP53").
        expand: Include connected features.

    Returns:
        EnsemblFetchedData with gene information.

    Example:
        >>> data = ensembl_lookup_symbol("human", "TP53")
    """
    return _get_fetcher().lookup_symbol(species=species, symbol=symbol, expand=expand)


# =============================================================================
# Sequence Functions
# =============================================================================

def ensembl_get_sequence(
    id: str,
    sequence_type: str = "genomic",
    species: Optional[str] = None,
    expand_5prime: Optional[int] = None,
    expand_3prime: Optional[int] = None,
    mask: Optional[str] = None,
    format: str = "fasta",
) -> EnsemblFetchedData:
    """Get sequence for an Ensembl stable ID.

    Args:
        id: Ensembl stable ID (gene, transcript, exon, protein).
        sequence_type: Type of sequence ("genomic", "cds", "cdna", "protein").
        species: Species name (optional).
        expand_5prime: Extend upstream (genomic only).
        expand_3prime: Extend downstream (genomic only).
        mask: Mask repeats ("hard" or "soft", genomic only).
        format: Output format ("fasta" or "json").

    Returns:
        EnsemblFetchedData with sequence data.

    Example:
        >>> data = ensembl_get_sequence("ENST00000269305", sequence_type="cds")
        >>> print(data.text)  # FASTA sequence
    """
    return _get_fetcher().get_sequence(
        id=id,
        sequence_type=sequence_type,
        species=species,
        expand_5prime=expand_5prime,
        expand_3prime=expand_3prime,
        mask=mask,
        format=format,
    )


def ensembl_get_sequence_batch(
    ids: List[str],
    sequence_type: str = "genomic",
    species: Optional[str] = None,
    format: str = "fasta",
) -> EnsemblFetchedData:
    """Get sequences for multiple Ensembl IDs in batch.

    Args:
        ids: List of Ensembl stable IDs (max 50).
        sequence_type: Type of sequence.
        species: Species name.
        format: Output format.

    Returns:
        EnsemblFetchedData with sequences.
    """
    return _get_fetcher().get_sequence_batch(
        ids=ids,
        sequence_type=sequence_type,
        species=species,
        format=format,
    )


def ensembl_get_sequence_region(
    species: str,
    region: str,
    expand_5prime: Optional[int] = None,
    expand_3prime: Optional[int] = None,
    mask: Optional[str] = None,
    format: str = "fasta",
) -> EnsemblFetchedData:
    """Get genomic sequence for a region.

    Args:
        species: Species name (e.g., "human").
        region: Genomic region (e.g., "X:1000000..1000100:1").
        expand_5prime: Extend upstream.
        expand_3prime: Extend downstream.
        mask: Mask repeats ("hard" or "soft").
        format: Output format ("fasta" or "json").

    Returns:
        EnsemblFetchedData with sequence.

    Example:
        >>> data = ensembl_get_sequence_region("human", "7:140424943-140424963:1")
    """
    return _get_fetcher().get_sequence_region(
        species=species,
        region=region,
        expand_5prime=expand_5prime,
        expand_3prime=expand_3prime,
        mask=mask,
        format=format,
    )


# =============================================================================
# Overlap Functions
# =============================================================================

def ensembl_get_overlap_id(
    id: str,
    feature: Union[str, List[str]],
    species: Optional[str] = None,
    biotype: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get features overlapping an Ensembl ID.

    Args:
        id: Ensembl stable ID.
        feature: Feature type(s) to retrieve (gene, transcript, exon, etc.).
        species: Species name.
        biotype: Filter by biotype (e.g., "protein_coding").

    Returns:
        EnsemblFetchedData with overlapping features.

    Example:
        >>> data = ensembl_get_overlap_id("ENSG00000141510", feature=["transcript", "exon"])
    """
    return _get_fetcher().get_overlap_id(
        id=id,
        feature=feature,
        species=species,
        biotype=biotype,
    )


def ensembl_get_overlap_region(
    species: str,
    region: str,
    feature: Union[str, List[str]],
    biotype: Optional[str] = None,
    variant_set: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get features overlapping a genomic region.

    Args:
        species: Species name (e.g., "human").
        region: Genomic region (e.g., "7:140424943-140624564", max 5Mb).
        feature: Feature type(s) to retrieve.
        biotype: Filter by biotype.
        variant_set: Variant set restriction (e.g., "ClinVar").

    Returns:
        EnsemblFetchedData with overlapping features.

    Example:
        >>> data = ensembl_get_overlap_region(
        ...     "human", "7:140424943-140624564",
        ...     feature=["gene", "transcript"]
        ... )
    """
    return _get_fetcher().get_overlap_region(
        species=species,
        region=region,
        feature=feature,
        biotype=biotype,
        variant_set=variant_set,
    )


# =============================================================================
# Cross Reference Functions
# =============================================================================

def ensembl_get_xrefs(
    id: str,
    species: Optional[str] = None,
    external_db: Optional[str] = None,
    all_levels: bool = False,
) -> EnsemblFetchedData:
    """Get external cross-references for an Ensembl ID.

    Args:
        id: Ensembl stable ID.
        species: Species name.
        external_db: Filter by external database (e.g., "HGNC", "UniProt").
        all_levels: Find all linked features.

    Returns:
        EnsemblFetchedData with cross-references.

    Example:
        >>> data = ensembl_get_xrefs("ENSG00000141510", external_db="HGNC")
    """
    return _get_fetcher().get_xrefs(
        id=id,
        species=species,
        external_db=external_db,
        all_levels=all_levels,
    )


def ensembl_get_xrefs_symbol(
    species: str,
    symbol: str,
    external_db: Optional[str] = None,
    object_type: Optional[str] = None,
) -> EnsemblFetchedData:
    """Look up Ensembl objects by external symbol.

    Args:
        species: Species name.
        symbol: External symbol (e.g., gene name "BRCA2").
        external_db: Filter by external database.
        object_type: Filter by feature type (e.g., "gene").

    Returns:
        EnsemblFetchedData with matching Ensembl objects.

    Example:
        >>> data = ensembl_get_xrefs_symbol("human", "BRCA2")
    """
    return _get_fetcher().get_xrefs_symbol(
        species=species,
        symbol=symbol,
        external_db=external_db,
        object_type=object_type,
    )


# =============================================================================
# Homology Functions
# =============================================================================

def ensembl_get_homology(
    species: str,
    id: str,
    homology_type: str = "all",
    target_species: Optional[str] = None,
    sequence: str = "protein",
) -> EnsemblFetchedData:
    """Get homology information for a gene.

    Args:
        species: Source species name (e.g., "human").
        id: Ensembl gene ID.
        homology_type: Type of homology ("orthologues", "paralogues", "all").
        target_species: Filter by target species.
        sequence: Sequence type ("none", "cdna", "protein").

    Returns:
        EnsemblFetchedData with homology data.

    Example:
        >>> data = ensembl_get_homology("human", "ENSG00000141510", target_species="mouse")
    """
    return _get_fetcher().get_homology(
        species=species,
        id=id,
        homology_type=homology_type,
        target_species=target_species,
        sequence=sequence,
    )


def ensembl_get_homology_symbol(
    species: str,
    symbol: str,
    homology_type: str = "all",
    target_species: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get homology information for a gene by symbol.

    Args:
        species: Source species name.
        symbol: Gene symbol.
        homology_type: Type of homology.
        target_species: Filter by target species.

    Returns:
        EnsemblFetchedData with homology data.

    Example:
        >>> data = ensembl_get_homology_symbol("human", "TP53", target_species="mouse")
    """
    return _get_fetcher().get_homology_symbol(
        species=species,
        symbol=symbol,
        homology_type=homology_type,
        target_species=target_species,
    )


# =============================================================================
# Variation Functions
# =============================================================================

def ensembl_get_variation(
    species: str,
    id: str,
    genotypes: bool = False,
    pops: bool = False,
    phenotypes: bool = False,
) -> EnsemblFetchedData:
    """Get variant information by rsID.

    Args:
        species: Species name.
        id: Variant ID (e.g., "rs56116432").
        genotypes: Include individual genotypes.
        pops: Include population allele frequencies.
        phenotypes: Include phenotypes.

    Returns:
        EnsemblFetchedData with variant data.

    Example:
        >>> data = ensembl_get_variation("human", "rs56116432", pops=True)
    """
    return _get_fetcher().get_variation(
        species=species,
        id=id,
        genotypes=genotypes,
        pops=pops,
        phenotypes=phenotypes,
    )


# =============================================================================
# VEP (Variant Effect Predictor) Functions
# =============================================================================

def ensembl_vep_hgvs(
    species: str,
    hgvs_notation: str,
    canonical: bool = False,
    hgvs: bool = True,
    protein: bool = True,
) -> EnsemblFetchedData:
    """Get variant consequences using HGVS notation.

    Args:
        species: Species name.
        hgvs_notation: HGVS notation (e.g., "ENST00000366667:c.803C>T").
        canonical: Only return canonical transcript.
        hgvs: Add HGVS nomenclature.
        protein: Include protein position and amino acid changes.

    Returns:
        EnsemblFetchedData with VEP results.

    Example:
        >>> data = ensembl_vep_hgvs("human", "ENST00000366667:c.803C>T")
    """
    return _get_fetcher().get_vep_hgvs(
        species=species,
        hgvs_notation=hgvs_notation,
        canonical=canonical,
        hgvs=hgvs,
        protein=protein,
    )


def ensembl_vep_id(
    species: str,
    id: str,
    canonical: bool = False,
    hgvs: bool = True,
    protein: bool = True,
) -> EnsemblFetchedData:
    """Get variant consequences using variant ID.

    Args:
        species: Species name.
        id: Variant ID (e.g., rsID).
        canonical: Only return canonical transcript.
        hgvs: Add HGVS nomenclature.
        protein: Include protein position.

    Returns:
        EnsemblFetchedData with VEP results.

    Example:
        >>> data = ensembl_vep_id("human", "rs56116432")
    """
    return _get_fetcher().get_vep_id(
        species=species,
        id=id,
        canonical=canonical,
        hgvs=hgvs,
        protein=protein,
    )


def ensembl_vep_region(
    species: str,
    region: str,
    allele: str,
    canonical: bool = False,
    hgvs: bool = True,
    protein: bool = True,
) -> EnsemblFetchedData:
    """Get variant consequences using genomic coordinates.

    Args:
        species: Species name.
        region: Genomic region (e.g., "9:22125503-22125502:1").
        allele: Variant allele (e.g., "C", "DUP").
        canonical: Only return canonical transcript.
        hgvs: Add HGVS nomenclature.
        protein: Include protein position.

    Returns:
        EnsemblFetchedData with VEP results.

    Example:
        >>> data = ensembl_vep_region("human", "9:22125503-22125502:1", "C")
    """
    return _get_fetcher().get_vep_region(
        species=species,
        region=region,
        allele=allele,
        canonical=canonical,
        hgvs=hgvs,
        protein=protein,
    )


# =============================================================================
# Mapping Functions
# =============================================================================

def ensembl_map_assembly(
    species: str,
    asm_one: str,
    region: str,
    asm_two: str,
) -> EnsemblFetchedData:
    """Map coordinates between assemblies.

    Args:
        species: Species name.
        asm_one: Source assembly version (e.g., "GRCh37").
        region: Genomic region to map (e.g., "X:1000000..1000100:1").
        asm_two: Target assembly version (e.g., "GRCh38").

    Returns:
        EnsemblFetchedData with mapped coordinates.

    Example:
        >>> data = ensembl_map_assembly("human", "GRCh37", "X:1000000..1000100:1", "GRCh38")
    """
    return _get_fetcher().map_assembly(
        species=species,
        asm_one=asm_one,
        region=region,
        asm_two=asm_two,
    )


# =============================================================================
# Phenotype Functions
# =============================================================================

def ensembl_get_phenotype_gene(
    species: str,
    gene: str,
    include_associated: bool = False,
    include_overlap: bool = False,
) -> EnsemblFetchedData:
    """Get phenotypes associated with a gene.

    Args:
        species: Species name.
        gene: Gene name or Ensembl ID.
        include_associated: Include phenotypes from associated variants.
        include_overlap: Include phenotypes from overlapping features.

    Returns:
        EnsemblFetchedData with phenotype data.

    Example:
        >>> data = ensembl_get_phenotype_gene("human", "BRCA2")
    """
    return _get_fetcher().get_phenotype_gene(
        species=species,
        gene=gene,
        include_associated=include_associated,
        include_overlap=include_overlap,
    )


def ensembl_get_phenotype_region(
    species: str,
    region: str,
) -> EnsemblFetchedData:
    """Get phenotypes in a genomic region.

    Args:
        species: Species name.
        region: Genomic region.

    Returns:
        EnsemblFetchedData with phenotype data.

    Example:
        >>> data = ensembl_get_phenotype_region("human", "9:22125503-22130000")
    """
    return _get_fetcher().get_phenotype_region(
        species=species,
        region=region,
    )


# =============================================================================
# Ontology Functions
# =============================================================================

def ensembl_get_ontology_term(
    id: str,
    simple: bool = False,
) -> EnsemblFetchedData:
    """Get ontology term information.

    Args:
        id: Ontology term ID (e.g., "GO:0005667").
        simple: Don't fetch parent/child terms.

    Returns:
        EnsemblFetchedData with ontology term data.

    Example:
        >>> data = ensembl_get_ontology_term("GO:0005667")
    """
    return _get_fetcher().get_ontology_term(id=id, simple=simple)


def ensembl_get_ontology_ancestors(
    id: str,
    ontology: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get ancestor terms for an ontology term.

    Args:
        id: Ontology term ID.
        ontology: Filter by ontology.

    Returns:
        EnsemblFetchedData with ancestor terms.

    Example:
        >>> data = ensembl_get_ontology_ancestors("GO:0005667")
    """
    return _get_fetcher().get_ontology_ancestors(id=id, ontology=ontology)


def ensembl_get_ontology_descendants(
    id: str,
    ontology: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get descendant terms for an ontology term.

    Args:
        id: Ontology term ID.
        ontology: Filter by ontology.

    Returns:
        EnsemblFetchedData with descendant terms.

    Example:
        >>> data = ensembl_get_ontology_descendants("GO:0005667")
    """
    return _get_fetcher().get_ontology_descendants(id=id, ontology=ontology)


# =============================================================================
# Gene Tree Functions
# =============================================================================

def ensembl_get_genetree(
    id: str,
    sequence: str = "protein",
    aligned: bool = False,
) -> EnsemblFetchedData:
    """Get gene tree by tree ID.

    Args:
        id: Gene tree ID (e.g., "ENSGT00390000003602").
        sequence: Sequence type ("none", "cdna", "protein").
        aligned: Include aligned sequences.

    Returns:
        EnsemblFetchedData with gene tree data.

    Example:
        >>> data = ensembl_get_genetree("ENSGT00390000003602")
    """
    return _get_fetcher().get_genetree(id=id, sequence=sequence, aligned=aligned)


def ensembl_get_genetree_member(
    species: str,
    id: str,
    sequence: str = "protein",
) -> EnsemblFetchedData:
    """Get gene tree containing a gene ID.

    Args:
        species: Species name.
        id: Ensembl gene ID.
        sequence: Sequence type.

    Returns:
        EnsemblFetchedData with gene tree data.

    Example:
        >>> data = ensembl_get_genetree_member("human", "ENSG00000141510")
    """
    return _get_fetcher().get_genetree_member(species=species, id=id, sequence=sequence)


# =============================================================================
# Information Functions
# =============================================================================

def ensembl_get_assembly_info(
    species: str,
) -> EnsemblFetchedData:
    """Get assembly information for a species.

    Args:
        species: Species name.

    Returns:
        EnsemblFetchedData with assembly information.

    Example:
        >>> data = ensembl_get_assembly_info("human")
        >>> print(data.results[0]["assembly_name"])  # GRCh38
    """
    return _get_fetcher().get_assembly_info(species=species)


def ensembl_get_species_info(
    division: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get information about available species.

    Args:
        division: Filter by Ensembl division (e.g., "EnsemblVertebrates").

    Returns:
        EnsemblFetchedData with species information.

    Example:
        >>> data = ensembl_get_species_info()
    """
    return _get_fetcher().get_species_info(division=division)
