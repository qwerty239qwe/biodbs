"""Pydantic models for EnrichR API requests and responses."""

from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class EnrichRBase(str, Enum):
    """EnrichR base URLs for different organisms."""

    HUMAN = "https://maayanlab.cloud/Enrichr"
    MOUSE = "https://maayanlab.cloud/Enrichr"  # Same as human
    FLY = "https://maayanlab.cloud/FlyEnrichr"
    YEAST = "https://maayanlab.cloud/YeastEnrichr"
    WORM = "https://maayanlab.cloud/WormEnrichr"
    FISH = "https://maayanlab.cloud/FishEnrichr"

    # Speed API for background enrichment
    SPEED = "https://maayanlab.cloud/speedrichr"


class EnrichRCategory(int, Enum):
    """EnrichR gene set library categories."""

    TRANSCRIPTION = 1
    PATHWAYS = 2
    ONTOLOGIES = 3
    DISEASES_DRUGS = 4
    CELL_TYPES = 5
    MISC = 6
    LEGACY = 7
    CROWD = 8


class EnrichREndpoint(str, Enum):
    """EnrichR API endpoints."""

    ADD_LIST = "addList"
    ENRICH = "enrich"
    EXPORT = "export"
    VIEW = "view"
    DATASET_STATISTICS = "datasetStatistics"
    GEN_MAP = "genemap"

    # Speed API endpoints (for background enrichment)
    SPEED_ADD_LIST = "api/addList"
    SPEED_ADD_BACKGROUND = "api/addbackground"
    SPEED_BACKGROUND_ENRICH = "api/backgroundenrich"


class LibraryStatistics(BaseModel):
    """Statistics for a gene set library."""

    libraryName: str
    numTerms: int
    geneCoverage: int
    genesPerTerm: float
    link: str = ""
    categoryId: Optional[int] = None
    appyter: Optional[str] = None


class CategoryInfo(BaseModel):
    """Category information."""

    name: str
    categoryId: int


class EnrichRLibraryModel(BaseModel):
    """Model for querying available libraries."""

    organism: str = "human"

    @field_validator("organism")
    @classmethod
    def validate_organism(cls, v: str) -> str:
        valid_organisms = {"human", "mouse", "fly", "yeast", "worm", "fish"}
        if v.lower() not in valid_organisms:
            raise ValueError(f"Invalid organism: {v}. Valid: {valid_organisms}")
        return v

    def get_base_url(self) -> str:
        """Get the base URL for the organism."""
        organism_map = {
            "human": EnrichRBase.HUMAN.value,
            "mouse": EnrichRBase.HUMAN.value,  # Same endpoint
            "fly": EnrichRBase.FLY.value,
            "yeast": EnrichRBase.YEAST.value,
            "worm": EnrichRBase.WORM.value,
            "fish": EnrichRBase.FISH.value,
        }
        return organism_map.get(self.organism.lower(), EnrichRBase.HUMAN.value)


class EnrichRAddListModel(BaseModel):
    """Model for adding a gene list to EnrichR."""

    genes: List[str] = Field(..., min_length=1, description="List of gene symbols")
    description: str = Field(default="biodbs gene list", description="Description for the gene list")
    organism: str = Field(default="human", description="Organism (human, mouse, fly, yeast, worm, fish)")

    @field_validator("organism")
    @classmethod
    def validate_organism(cls, v: str) -> str:
        valid_organisms = {"human", "mouse", "fly", "yeast", "worm", "fish"}
        if v.lower() not in valid_organisms:
            raise ValueError(f"Invalid organism: {v}. Valid: {valid_organisms}")
        return v

    def get_gene_string(self) -> str:
        """Get genes as newline-separated string for API."""
        return "\n".join(self.genes)

    def get_base_url(self) -> str:
        """Get the base URL for the organism."""
        organism_map = {
            "human": EnrichRBase.HUMAN.value,
            "mouse": EnrichRBase.HUMAN.value,
            "fly": EnrichRBase.FLY.value,
            "yeast": EnrichRBase.YEAST.value,
            "worm": EnrichRBase.WORM.value,
            "fish": EnrichRBase.FISH.value,
        }
        return organism_map.get(self.organism.lower(), EnrichRBase.HUMAN.value)


class AddListResponse(BaseModel):
    """Response from addList endpoint."""

    userListId: int
    shortId: Optional[str] = None


class EnrichREnrichModel(BaseModel):
    """Model for enrichment analysis request."""

    user_list_id: int = Field(..., description="User list ID from addList response")
    gene_set_library: str = Field(..., description="Name of the gene set library")
    organism: str = Field(default="human", description="Organism")

    def get_base_url(self) -> str:
        """Get the base URL for the organism."""
        organism_map = {
            "human": EnrichRBase.HUMAN.value,
            "mouse": EnrichRBase.HUMAN.value,
            "fly": EnrichRBase.FLY.value,
            "yeast": EnrichRBase.YEAST.value,
            "worm": EnrichRBase.WORM.value,
            "fish": EnrichRBase.FISH.value,
        }
        return organism_map.get(self.organism.lower(), EnrichRBase.HUMAN.value)


class EnrichRBackgroundModel(BaseModel):
    """Model for background enrichment analysis."""

    genes: List[str] = Field(..., min_length=1, description="Query gene list")
    background: List[str] = Field(..., min_length=1, description="Background gene list")
    gene_set_library: str = Field(..., description="Name of the gene set library")
    description: str = Field(default="biodbs gene list", description="Description")

    def get_gene_string(self) -> str:
        """Get genes as newline-separated string."""
        return "\n".join(self.genes)

    def get_background_string(self) -> str:
        """Get background genes as newline-separated string."""
        return "\n".join(self.background)


class EnrichmentTerm(BaseModel):
    """A single enrichment result term."""

    rank: int = Field(..., description="Rank by combined score")
    term_name: str = Field(..., description="Term/pathway name")
    p_value: float = Field(..., description="Raw p-value")
    z_score: float = Field(..., description="Z-score")
    combined_score: float = Field(..., description="Combined score (log(p) * z)")
    overlapping_genes: List[str] = Field(default_factory=list, description="Genes overlapping with term")
    adjusted_p_value: float = Field(..., description="Adjusted p-value (BH)")
    old_p_value: Optional[float] = Field(default=None, description="Old p-value (deprecated)")
    old_adjusted_p_value: Optional[float] = Field(default=None, description="Old adjusted p-value")
    odds_ratio: Optional[float] = Field(default=None, description="Odds ratio")

    @classmethod
    def _parse_genes(cls, genes_data: Any) -> List[str]:
        """Parse overlapping genes from various formats."""
        if not genes_data:
            return []
        if isinstance(genes_data, list):
            return genes_data
        if isinstance(genes_data, str):
            return genes_data.split(";") if genes_data else []
        return []

    @classmethod
    def from_api_row(cls, row: List[Any], rank: int = 0) -> "EnrichmentTerm":
        """Create from API response row.

        API returns: [Rank, Term name, P-value, Z-score, Combined score,
                      Overlapping genes (list or ;-separated), Adjusted P-value,
                      Old P-value, Old Adjusted P-value]

        Or for newer API: [Rank, Term, P-value, Odds Ratio, Combined Score,
                          Genes, Adjusted P-value]
        """
        # Handle different response formats
        if len(row) >= 9:
            # Old format with 9 columns
            return cls(
                rank=int(row[0]) if row[0] else rank,
                term_name=str(row[1]),
                p_value=float(row[2]) if row[2] else 1.0,
                z_score=float(row[3]) if row[3] else 0.0,
                combined_score=float(row[4]) if row[4] else 0.0,
                overlapping_genes=cls._parse_genes(row[5]),
                adjusted_p_value=float(row[6]) if row[6] else 1.0,
                old_p_value=float(row[7]) if row[7] else None,
                old_adjusted_p_value=float(row[8]) if row[8] else None,
            )
        elif len(row) >= 7:
            # Newer format with odds ratio
            return cls(
                rank=int(row[0]) if row[0] else rank,
                term_name=str(row[1]),
                p_value=float(row[2]) if row[2] else 1.0,
                odds_ratio=float(row[3]) if row[3] else None,
                combined_score=float(row[4]) if row[4] else 0.0,
                overlapping_genes=cls._parse_genes(row[5]),
                adjusted_p_value=float(row[6]) if row[6] else 1.0,
                z_score=0.0,  # Not provided in this format
            )
        else:
            raise ValueError(f"Unexpected row format with {len(row)} columns")


class EnrichmentResult(BaseModel):
    """Enrichment results for a gene set library."""

    library_name: str
    terms: List[EnrichmentTerm] = Field(default_factory=list)

    def significant_terms(self, p_threshold: float = 0.05, use_adjusted: bool = True) -> List[EnrichmentTerm]:
        """Get terms below the p-value threshold."""
        if use_adjusted:
            return [t for t in self.terms if t.adjusted_p_value < p_threshold]
        return [t for t in self.terms if t.p_value < p_threshold]

    def top_terms(self, n: int = 10) -> List[EnrichmentTerm]:
        """Get top N terms by combined score."""
        return sorted(self.terms, key=lambda x: x.combined_score, reverse=True)[:n]
