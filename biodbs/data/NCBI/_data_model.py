"""Pydantic models for NCBI Datasets API requests and responses."""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class NCBIBase(str, Enum):
    """NCBI Datasets API base URL."""

    BASE = "https://api.ncbi.nlm.nih.gov/datasets/v2"


class NCBIGeneEndpoint(str, Enum):
    """NCBI Gene endpoints."""

    # Gene data reports
    GENE_BY_ID = "gene/id/{gene_ids}/dataset_report"
    GENE_BY_ACCESSION = "gene/accession/{accessions}/dataset_report"
    GENE_BY_SYMBOL = "gene/symbol/{symbols}/taxon/{taxon}/dataset_report"
    GENE_BY_TAXON = "gene/taxon/{taxon}/dataset_report"

    # Gene downloads
    GENE_DOWNLOAD_BY_ID = "gene/id/{gene_ids}/download"
    GENE_DOWNLOAD_BY_SYMBOL = "gene/symbol/{symbols}/taxon/{taxon}/download"

    # Gene dataset reports (POST)
    GENE_DATASET_REPORT = "gene/dataset_report"


class NCBITaxonomyEndpoint(str, Enum):
    """NCBI Taxonomy endpoints."""

    TAXONOMY_BY_TAXON = "taxonomy/taxon/{taxons}/dataset_report"
    TAXONOMY_DOWNLOAD = "taxonomy/taxon/{tax_ids}/download"
    TAXONOMY_DATASET_REPORT = "taxonomy/dataset_report"
    TAXONOMY_NAME_REPORT = "taxonomy/taxon/{taxons}/name_report"


class NCBIGenomeEndpoint(str, Enum):
    """NCBI Genome endpoints."""

    GENOME_BY_ACCESSION = "genome/accession/{accessions}/dataset_report"
    GENOME_BY_TAXON = "genome/taxon/{taxon}/dataset_report"
    GENOME_DOWNLOAD = "genome/accession/{accessions}/download"


class NCBIVersionEndpoint(str, Enum):
    """NCBI Version endpoints."""

    VERSION = "version"


class GeneType(str, Enum):
    """Gene type filter values."""

    PROTEIN_CODING = "PROTEIN_CODING"
    PSEUDO = "PSEUDO"
    NCRNA = "ncRNA"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class SortDirection(str, Enum):
    """Sort direction options."""

    ASC = "asc"
    DESC = "desc"


class GeneContentType(str, Enum):
    """Gene data report content type options."""

    COMPLETE = "COMPLETE"
    IDS_ONLY = "IDS_ONLY"
    COUNTS_ONLY = "COUNTS_ONLY"


# ----- Gene Models -----


class GeneLocation(BaseModel):
    """Gene genomic location information."""

    chromosome: Optional[str] = Field(default=None, description="Chromosome name")
    start: Optional[int] = Field(default=None, description="Start position")
    stop: Optional[int] = Field(default=None, description="Stop position")
    strand: Optional[str] = Field(default=None, description="Strand (+/-)")
    accession_version: Optional[str] = Field(
        default=None, description="Accession version"
    )
    assembly_accession: Optional[str] = Field(
        default=None, description="Assembly accession"
    )
    assembly_name: Optional[str] = Field(default=None, description="Assembly name")


class TranscriptInfo(BaseModel):
    """Transcript information."""

    accession_version: Optional[str] = Field(default=None, description="Transcript accession")
    name: Optional[str] = Field(default=None, description="Transcript name")
    length: Optional[int] = Field(default=None, description="Transcript length")
    protein: Optional[Dict[str, Any]] = Field(default=None, description="Protein info")


class GeneAnnotation(BaseModel):
    """Gene annotation information."""

    release_date: Optional[str] = Field(default=None, description="Release date")
    release_name: Optional[str] = Field(default=None, description="Release name")


class GeneReport(BaseModel):
    """NCBI Gene report model.

    Represents a gene data report from the NCBI Datasets API.
    """

    gene_id: int = Field(..., alias="geneId", description="NCBI Gene ID")
    symbol: Optional[str] = Field(default=None, description="Gene symbol")
    description: Optional[str] = Field(default=None, description="Gene description/name")
    tax_id: Optional[int] = Field(default=None, alias="taxId", description="Taxonomy ID")
    taxname: Optional[str] = Field(default=None, description="Taxonomy name")
    common_name: Optional[str] = Field(default=None, alias="commonName", description="Common name")
    gene_type: Optional[str] = Field(default=None, alias="type", description="Gene type")
    synonyms: Optional[List[str]] = Field(default=None, description="Gene synonyms/aliases")
    chromosomes: Optional[List[str]] = Field(default=None, description="Chromosome locations")
    genomic_ranges: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="genomicRanges", description="Genomic location ranges"
    )
    reference_standards: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="referenceStandards", description="Reference standards"
    )
    transcripts: Optional[List[TranscriptInfo]] = Field(
        default=None, description="Transcript list"
    )
    swiss_prot_accessions: Optional[List[str]] = Field(
        default=None, alias="swissProtAccessions", description="UniProt/SwissProt accessions"
    )
    ensembl_gene_ids: Optional[List[str]] = Field(
        default=None, alias="ensemblGeneIds", description="Ensembl gene IDs"
    )
    omim_ids: Optional[List[str]] = Field(
        default=None, alias="omimIds", description="OMIM IDs"
    )
    orientation: Optional[str] = Field(default=None, description="Gene orientation")
    annotations: Optional[List[GeneAnnotation]] = Field(
        default=None, description="Annotations"
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def entrez_id(self) -> int:
        """Alias for gene_id (NCBI Entrez Gene ID)."""
        return self.gene_id

    @property
    def location_str(self) -> str:
        """Get a human-readable location string."""
        if self.chromosomes:
            return ", ".join(self.chromosomes)
        return ""


# ----- Taxonomy Models -----


class TaxonomyRank(str, Enum):
    """Taxonomy rank levels."""

    SUPERKINGDOM = "superkingdom"
    KINGDOM = "kingdom"
    PHYLUM = "phylum"
    CLASS = "class"
    ORDER = "order"
    FAMILY = "family"
    GENUS = "genus"
    SPECIES = "species"
    SUBSPECIES = "subspecies"
    NO_RANK = "no rank"


class TaxonomyReport(BaseModel):
    """NCBI Taxonomy report model."""

    tax_id: int = Field(..., description="Taxonomy ID")
    rank: Optional[str] = Field(default=None, description="Taxonomic rank")
    current_scientific_name: Optional[Dict[str, Any]] = Field(
        default=None, description="Current scientific name info"
    )
    curator_common_name: Optional[str] = Field(
        default=None, description="Curator common name"
    )
    group_name: Optional[str] = Field(default=None, description="Group name")
    classification: Optional[Dict[str, Any]] = Field(
        default=None, description="Taxonomic classification"
    )
    parents: Optional[List[int]] = Field(
        default=None, description="Parent taxonomy IDs"
    )
    children: Optional[List[int]] = Field(
        default=None, description="Child taxonomy IDs"
    )
    counts: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Resource counts"
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def organism_name(self) -> str:
        """Get scientific name."""
        if self.current_scientific_name:
            return self.current_scientific_name.get("name", "")
        return ""

    @property
    def scientific_name(self) -> str:
        """Alias for organism_name."""
        return self.organism_name

    @property
    def common_name(self) -> str:
        """Get common name."""
        return self.curator_common_name or ""

    @property
    def parent_tax_id(self) -> Optional[int]:
        """Get parent taxonomy ID."""
        if self.parents:
            return self.parents[-1] if self.parents else None
        return None


# ----- Genome Models -----


class AssemblyLevel(str, Enum):
    """Genome assembly level."""

    COMPLETE_GENOME = "complete_genome"
    CHROMOSOME = "chromosome"
    SCAFFOLD = "scaffold"
    CONTIG = "contig"


class GenomeReport(BaseModel):
    """NCBI Genome assembly report model."""

    accession: str = Field(..., description="Assembly accession")
    organism_name: Optional[str] = Field(
        default=None, alias="organismName", description="Organism name"
    )
    organism_tax_id: Optional[int] = Field(
        default=None, alias="organismTaxId", description="Organism taxonomy ID"
    )
    assembly_info: Optional[Dict[str, Any]] = Field(
        default=None, alias="assemblyInfo", description="Assembly information"
    )
    assembly_stats: Optional[Dict[str, Any]] = Field(
        default=None, alias="assemblyStats", description="Assembly statistics"
    )
    annotation_info: Optional[Dict[str, Any]] = Field(
        default=None, alias="annotationInfo", description="Annotation information"
    )
    organelle_info: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="organelleInfo", description="Organelle information"
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def assembly_name(self) -> str:
        """Get assembly name."""
        if self.assembly_info:
            return self.assembly_info.get("assemblyName", "")
        return ""

    @property
    def assembly_level(self) -> str:
        """Get assembly level."""
        if self.assembly_info:
            return self.assembly_info.get("assemblyLevel", "")
        return ""


# ----- Request Models -----


class GeneDatasetRequest(BaseModel):
    """Request model for gene dataset reports."""

    gene_ids: Optional[List[int]] = Field(
        default=None, description="List of NCBI Gene IDs"
    )
    accessions: Optional[List[str]] = Field(
        default=None, description="List of RefSeq accessions"
    )
    symbols: Optional[List[str]] = Field(
        default=None, description="List of gene symbols"
    )
    taxon: Optional[str] = Field(
        default=None, description="Taxon (ID, name, or scientific name)"
    )
    returned_content: Optional[str] = Field(
        default=None, description="Content type to return"
    )
    page_size: int = Field(default=100, description="Results per page")
    page_token: Optional[str] = Field(default=None, description="Page token")
    query: Optional[str] = Field(
        default=None, description="Search query for symbol, name, alias"
    )
    types: Optional[List[str]] = Field(default=None, description="Gene type filter")

    def get_params(self) -> Dict[str, Any]:
        """Get query parameters for API request."""
        params = {"page_size": self.page_size}
        if self.returned_content:
            params["returned_content"] = self.returned_content
        if self.page_token:
            params["page_token"] = self.page_token
        if self.query:
            params["query"] = self.query
        if self.types:
            params["types"] = self.types
        return params


class TaxonomyDatasetRequest(BaseModel):
    """Request model for taxonomy dataset reports."""

    taxons: List[Union[int, str]] = Field(..., description="List of taxonomy IDs or names")
    page_size: int = Field(default=100, description="Results per page")
    page_token: Optional[str] = Field(default=None, description="Page token")

    def get_params(self) -> Dict[str, Any]:
        """Get query parameters for API request."""
        params = {"page_size": self.page_size}
        if self.page_token:
            params["page_token"] = self.page_token
        return params
