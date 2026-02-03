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
        id (str): Ensembl stable ID (e.g., "ENSG00000141510").
        species (Optional[str]): Species name (optional, auto-detected from ID).
        expand (bool): If True, include connected features (transcripts, exons).
        db_type (str): Database type ("core" or "otherfeatures").

    Returns:
        EnsemblFetchedData containing gene/transcript/protein information.

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
        ids (List[str]): List of Ensembl stable IDs (max 1000).
        species (Optional[str]): Species name/alias.
        expand (bool): If True, include connected features.

    Returns:
        EnsemblFetchedData containing results for each ID.

    Example:
        >>> data = ensembl_lookup_batch(["ENSG00000141510", "ENSG00000012048"])
        >>> print(len(data.results))
    """
    return _get_fetcher().lookup_batch(ids=ids, species=species, expand=expand)


def ensembl_lookup_symbol(
    species: str,
    symbol: str,
    expand: bool = False,
) -> EnsemblFetchedData:
    """Look up a gene by symbol.

    Args:
        species (str): Species name (e.g., "human", "mouse").
        symbol (str): Gene symbol (e.g., "BRCA2", "TP53").
        expand (bool): If True, include connected features.

    Returns:
        EnsemblFetchedData containing gene information.

    Example:
        >>> data = ensembl_lookup_symbol("human", "TP53")
        >>> print(data.results[0]["id"])  # ENSG00000141510
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
        id (str): Ensembl stable ID (gene, transcript, exon, protein).
        sequence_type (str): Type of sequence ("genomic", "cds", "cdna", "protein").
        species (Optional[str]): Species name (optional).
        expand_5prime (Optional[int]): Extend upstream (genomic only).
        expand_3prime (Optional[int]): Extend downstream (genomic only).
        mask (Optional[str]): Mask repeats ("hard" or "soft", genomic only).
        format (str): Output format ("fasta" or "json").

    Returns:
        EnsemblFetchedData containing sequence data.

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
        ids (List[str]): List of Ensembl stable IDs (max 50).
        sequence_type (str): Type of sequence ("genomic", "cds", "cdna", "protein").
        species (Optional[str]): Species name.
        format (str): Output format ("fasta" or "json").

    Returns:
        EnsemblFetchedData containing sequences for all requested IDs.

    Example:
        >>> data = ensembl_get_sequence_batch(["ENST00000269305", "ENST00000366667"])
        >>> print(data.text)  # FASTA sequences
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
        species (str): Species name (e.g., "human").
        region (str): Genomic region (e.g., "X:1000000..1000100:1").
        expand_5prime (Optional[int]): Extend upstream.
        expand_3prime (Optional[int]): Extend downstream.
        mask (Optional[str]): Mask repeats ("hard" or "soft").
        format (str): Output format ("fasta" or "json").

    Returns:
        EnsemblFetchedData containing the genomic sequence.

    Example:
        >>> data = ensembl_get_sequence_region("human", "7:140424943-140424963:1")
        >>> print(data.text)  # FASTA sequence
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
        id (str): Ensembl stable ID.
        feature (Union[str, List[str]]): Feature type(s) to retrieve (gene, transcript, exon, etc.).
        species (Optional[str]): Species name.
        biotype (Optional[str]): Filter by biotype (e.g., "protein_coding").

    Returns:
        EnsemblFetchedData containing overlapping features.

    Example:
        >>> data = ensembl_get_overlap_id("ENSG00000141510", feature=["transcript", "exon"])
        >>> print(len(data.results))
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
        species (str): Species name (e.g., "human").
        region (str): Genomic region (e.g., "7:140424943-140624564", max 5Mb).
        feature (Union[str, List[str]]): Feature type(s) to retrieve.
        biotype (Optional[str]): Filter by biotype.
        variant_set (Optional[str]): Variant set restriction (e.g., "ClinVar").

    Returns:
        EnsemblFetchedData containing overlapping features.

    Example:
        >>> data = ensembl_get_overlap_region(
        ...     "human", "7:140424943-140624564",
        ...     feature=["gene", "transcript"]
        ... )
        >>> print(len(data.results))
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
        id (str): Ensembl stable ID.
        species (Optional[str]): Species name.
        external_db (Optional[str]): Filter by external database (e.g., "HGNC", "UniProt").
        all_levels (bool): If True, find all linked features.

    Returns:
        EnsemblFetchedData containing cross-references.

    Example:
        >>> data = ensembl_get_xrefs("ENSG00000141510", external_db="HGNC")
        >>> print(data.results[0]["display_id"])
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
        species (str): Species name.
        symbol (str): External symbol (e.g., gene name "BRCA2").
        external_db (Optional[str]): Filter by external database.
        object_type (Optional[str]): Filter by feature type (e.g., "gene").

    Returns:
        EnsemblFetchedData containing matching Ensembl objects.

    Example:
        >>> data = ensembl_get_xrefs_symbol("human", "BRCA2")
        >>> print(data.results[0]["id"])
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
        species (str): Source species name (e.g., "human").
        id (str): Ensembl gene ID.
        homology_type (str): Type of homology ("orthologues", "paralogues", "all").
        target_species (Optional[str]): Filter by target species.
        sequence (str): Sequence type ("none", "cdna", "protein").

    Returns:
        EnsemblFetchedData containing homology data.

    Example:
        >>> data = ensembl_get_homology("human", "ENSG00000141510", target_species="mouse")
        >>> print(data.results[0]["homologies"])
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
        species (str): Source species name.
        symbol (str): Gene symbol.
        homology_type (str): Type of homology ("orthologues", "paralogues", "all").
        target_species (Optional[str]): Filter by target species.

    Returns:
        EnsemblFetchedData containing homology data.

    Example:
        >>> data = ensembl_get_homology_symbol("human", "TP53", target_species="mouse")
        >>> print(data.results[0]["homologies"])
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
        species (str): Species name.
        id (str): Variant ID (e.g., "rs56116432").
        genotypes (bool): If True, include individual genotypes.
        pops (bool): If True, include population allele frequencies.
        phenotypes (bool): If True, include phenotypes.

    Returns:
        EnsemblFetchedData containing variant data.

    Example:
        >>> data = ensembl_get_variation("human", "rs56116432", pops=True)
        >>> print(data.results[0]["MAF"])
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
        species (str): Species name.
        hgvs_notation (str): HGVS notation (e.g., "ENST00000366667:c.803C>T").
        canonical (bool): If True, only return canonical transcript.
        hgvs (bool): If True, add HGVS nomenclature.
        protein (bool): If True, include protein position and amino acid changes.

    Returns:
        EnsemblFetchedData containing VEP results.

    Example:
        >>> data = ensembl_vep_hgvs("human", "ENST00000366667:c.803C>T")
        >>> print(data.results[0]["transcript_consequences"])
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
        species (str): Species name.
        id (str): Variant ID (e.g., rsID).
        canonical (bool): If True, only return canonical transcript.
        hgvs (bool): If True, add HGVS nomenclature.
        protein (bool): If True, include protein position.

    Returns:
        EnsemblFetchedData containing VEP results.

    Example:
        >>> data = ensembl_vep_id("human", "rs56116432")
        >>> print(data.results[0]["most_severe_consequence"])
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
        species (str): Species name.
        region (str): Genomic region (e.g., "9:22125503-22125502:1").
        allele (str): Variant allele (e.g., "C", "DUP").
        canonical (bool): If True, only return canonical transcript.
        hgvs (bool): If True, add HGVS nomenclature.
        protein (bool): If True, include protein position.

    Returns:
        EnsemblFetchedData containing VEP results.

    Example:
        >>> data = ensembl_vep_region("human", "9:22125503-22125502:1", "C")
        >>> print(data.results[0]["most_severe_consequence"])
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
        species (str): Species name.
        asm_one (str): Source assembly version (e.g., "GRCh37").
        region (str): Genomic region to map (e.g., "X:1000000..1000100:1").
        asm_two (str): Target assembly version (e.g., "GRCh38").

    Returns:
        EnsemblFetchedData containing mapped coordinates.

    Example:
        >>> data = ensembl_map_assembly("human", "GRCh37", "X:1000000..1000100:1", "GRCh38")
        >>> print(data.results[0]["mapped"])
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
        species (str): Species name.
        gene (str): Gene name or Ensembl ID.
        include_associated (bool): If True, include phenotypes from associated variants.
        include_overlap (bool): If True, include phenotypes from overlapping features.

    Returns:
        EnsemblFetchedData containing phenotype data.

    Example:
        >>> data = ensembl_get_phenotype_gene("human", "BRCA2")
        >>> print(data.results[0]["description"])
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
        species (str): Species name.
        region (str): Genomic region.

    Returns:
        EnsemblFetchedData containing phenotype data.

    Example:
        >>> data = ensembl_get_phenotype_region("human", "9:22125503-22130000")
        >>> print(len(data.results))
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
        id (str): Ontology term ID (e.g., "GO:0005667").
        simple (bool): If True, don't fetch parent/child terms.

    Returns:
        EnsemblFetchedData containing ontology term data.

    Example:
        >>> data = ensembl_get_ontology_term("GO:0005667")
        >>> print(data.results[0]["name"])
    """
    return _get_fetcher().get_ontology_term(id=id, simple=simple)


def ensembl_get_ontology_ancestors(
    id: str,
    ontology: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get ancestor terms for an ontology term.

    Args:
        id (str): Ontology term ID.
        ontology (Optional[str]): Filter by ontology.

    Returns:
        EnsemblFetchedData containing ancestor terms.

    Example:
        >>> data = ensembl_get_ontology_ancestors("GO:0005667")
        >>> print(len(data.results))
    """
    return _get_fetcher().get_ontology_ancestors(id=id, ontology=ontology)


def ensembl_get_ontology_descendants(
    id: str,
    ontology: Optional[str] = None,
) -> EnsemblFetchedData:
    """Get descendant terms for an ontology term.

    Args:
        id (str): Ontology term ID.
        ontology (Optional[str]): Filter by ontology.

    Returns:
        EnsemblFetchedData containing descendant terms.

    Example:
        >>> data = ensembl_get_ontology_descendants("GO:0005667")
        >>> print(len(data.results))
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
        id (str): Gene tree ID (e.g., "ENSGT00390000003602").
        sequence (str): Sequence type ("none", "cdna", "protein").
        aligned (bool): If True, include aligned sequences.

    Returns:
        EnsemblFetchedData containing gene tree data.

    Example:
        >>> data = ensembl_get_genetree("ENSGT00390000003602")
        >>> print(data.results[0]["tree"])
    """
    return _get_fetcher().get_genetree(id=id, sequence=sequence, aligned=aligned)


def ensembl_get_genetree_member(
    species: str,
    id: str,
    sequence: str = "protein",
) -> EnsemblFetchedData:
    """Get gene tree containing a gene ID.

    Args:
        species (str): Species name.
        id (str): Ensembl gene ID.
        sequence (str): Sequence type ("none", "cdna", "protein").

    Returns:
        EnsemblFetchedData containing gene tree data.

    Example:
        >>> data = ensembl_get_genetree_member("human", "ENSG00000141510")
        >>> print(data.results[0]["tree"])
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
        species (str): Species name.

    Returns:
        EnsemblFetchedData containing assembly information.

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
        division (Optional[str]): Filter by Ensembl division (e.g., "EnsemblVertebrates").

    Returns:
        EnsemblFetchedData containing species information.

    Example:
        >>> data = ensembl_get_species_info()
        >>> print(len(data.results))
    """
    return _get_fetcher().get_species_info(division=division)
