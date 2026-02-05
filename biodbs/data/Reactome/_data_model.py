"""Pydantic models for Reactome API requests and responses."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReactomeBase(str, Enum):
    """Reactome base URLs."""

    ANALYSIS = "https://reactome.org/AnalysisService"
    CONTENT = "https://reactome.org/ContentService"


class ReactomeAnalysisEndpoint(str, Enum):
    """Reactome Analysis Service endpoints."""

    # Identifier analysis
    IDENTIFIER = "identifier/{id}"
    IDENTIFIER_PROJECTION = "identifier/{id}/projection"
    IDENTIFIERS = "identifiers/"
    IDENTIFIERS_PROJECTION = "identifiers/projection"
    IDENTIFIERS_FORM = "identifiers/form"
    IDENTIFIERS_URL = "identifiers/url"

    # Token-based retrieval
    TOKEN = "token/{token}"
    TOKEN_FILTER_SPECIES = "token/{token}/filter/species/{species}"
    TOKEN_FILTER_PATHWAYS = "token/{token}/filter/pathways"
    TOKEN_FOUND_ALL = "token/{token}/found/all"
    TOKEN_FOUND_ENTITIES = "token/{token}/found/entities/{pathway}"
    TOKEN_NOT_FOUND = "token/{token}/notFound"
    TOKEN_PATHWAYS_BINNED = "token/{token}/pathways/binned"

    # Download
    DOWNLOAD_JSON = "download/{token}/result.json"
    DOWNLOAD_CSV = "download/{token}/pathways/{resource}/{filename}.csv"
    DOWNLOAD_FOUND_CSV = "download/{token}/entities/found/{resource}/{filename}.csv"
    DOWNLOAD_NOT_FOUND_CSV = "download/{token}/entities/notfound/{filename}.csv"

    # Mapping
    MAPPING = "mapping/"
    MAPPING_PROJECTION = "mapping/projection"

    # Species comparison
    SPECIES_COMPARISON = "species/homoSapiens/{species}"

    # Database info
    DATABASE_NAME = "database/name"
    DATABASE_VERSION = "database/version"


class ReactomeContentEndpoint(str, Enum):
    """Reactome Content Service endpoints."""

    # Pathways
    PATHWAYS_TOP = "data/pathways/top/{species}"
    EVENTS_HIERARCHY = "data/eventsHierarchy/{species}"
    PATHWAY_CONTAINED_EVENTS = "data/pathway/{id}/containedEvents"
    PATHWAYS_LOW_ENTITY = "data/pathways/low/entity/{id}"
    PATHWAYS_LOW_DIAGRAM = "data/pathways/low/diagram/entity/{id}"
    PATHWAYS_LOW_ENTITY_ALL_FORMS = "data/pathways/low/entity/{id}/allForms"

    # Species
    SPECIES_ALL = "data/species/all"
    SPECIES_MAIN = "data/species/main"

    # Query
    QUERY = "data/query/{id}"
    QUERY_IDS = "data/query/ids"
    QUERY_ENHANCED = "data/query/enhanced/{id}"

    # Mapping
    MAPPING_PATHWAYS = "data/mapping/{resource}/{identifier}/pathways"
    MAPPING_REACTIONS = "data/mapping/{resource}/{identifier}/reactions"

    # Participants (for getting pathway members)
    PARTICIPANTS = "data/participants/{id}"
    PARTICIPANTS_PHYSICAL_ENTITIES = "data/participants/{id}/participatingPhysicalEntities"
    PARTICIPANTS_REFERENCE_ENTITIES = "data/participants/{id}/referenceEntities"

    # Events
    EVENT_ANCESTORS = "data/event/{id}/ancestors"

    # Entities
    COMPLEX_SUBUNITS = "data/complex/{id}/subunits"
    ENTITY_COMPONENT_OF = "data/entity/{id}/componentOf"
    ENTITY_OTHER_FORMS = "data/entity/{id}/otherForms"

    # Database
    DATABASE_NAME = "data/database/name"
    DATABASE_VERSION = "data/database/version"

    # Diseases
    DISEASES = "data/diseases"
    DISEASES_DOID = "data/diseases/doid"

    # Schema
    SCHEMA_MODEL = "data/schema/model"
    SCHEMA_CLASS = "data/schema/{className}"
    SCHEMA_CLASS_COUNT = "data/schema/{className}/count"


class EntityStatistics(BaseModel):
    """Statistics for entities in a pathway."""

    curatedFound: int = Field(default=0, description="Number of curated entities found")
    curatedTotal: int = Field(default=0, description="Total curated entities")
    curatedInteractorsFound: int = Field(default=0, description="Curated interactors found")
    curatedInteractorsTotal: int = Field(default=0, description="Total curated interactors")
    found: int = Field(default=0, description="Total entities found")
    total: int = Field(default=0, description="Total entities in pathway")
    ratio: float = Field(default=0.0, description="Ratio of found to total")
    pValue: float = Field(default=1.0, description="P-value for enrichment")
    fdr: float = Field(default=1.0, description="False discovery rate")
    exp: Optional[List[float]] = Field(default=None, description="Expression values")


class ReactionStatistics(BaseModel):
    """Statistics for reactions in a pathway."""

    found: int = Field(default=0, description="Reactions with found entities")
    total: int = Field(default=0, description="Total reactions in pathway")
    ratio: float = Field(default=0.0, description="Ratio of found to total")


class SpeciesSummary(BaseModel):
    """Summary of species in analysis results."""

    dbId: int = Field(..., description="Database ID")
    taxId: str = Field(..., description="Taxonomy ID")
    name: str = Field(..., description="Species name")
    pathways: int = Field(default=0, description="Number of pathways")
    filtered: int = Field(default=0, description="Filtered pathways")


class ResourceSummary(BaseModel):
    """Summary of resources in analysis results."""

    resource: str = Field(..., description="Resource name (TOTAL, UNIPROT, etc.)")
    pathways: int = Field(default=0, description="Number of pathways")
    filtered: int = Field(default=0, description="Filtered pathways")


class PathwaySummary(BaseModel):
    """Summary of a pathway in analysis results."""

    stId: str = Field(..., description="Stable identifier (e.g., R-HSA-123)")
    dbId: int = Field(..., description="Database ID")
    name: str = Field(..., description="Pathway name")
    species: Optional[SpeciesSummary] = Field(default=None, description="Species info")
    llp: bool = Field(default=False, description="Is lowest level pathway")
    inDisease: bool = Field(default=False, description="Is disease pathway")
    entities: Optional[EntityStatistics] = Field(default=None, description="Entity statistics")
    reactions: Optional[ReactionStatistics] = Field(default=None, description="Reaction statistics")

    @property
    def p_value(self) -> float:
        """Get p-value from entity statistics."""
        if self.entities:
            return self.entities.pValue
        return 1.0

    @property
    def fdr(self) -> float:
        """Get FDR from entity statistics."""
        if self.entities:
            return self.entities.fdr
        return 1.0

    @property
    def found_entities(self) -> int:
        """Get number of found entities."""
        if self.entities:
            return self.entities.found
        return 0

    @property
    def total_entities(self) -> int:
        """Get total number of entities."""
        if self.entities:
            return self.entities.total
        return 0


class AnalysisIdentifier(BaseModel):
    """An identifier in analysis results."""

    id: str = Field(..., description="Identifier")
    mapsTo: Optional[List[Dict[str, Any]]] = Field(default=None, description="Mapped entities")
    exp: Optional[List[float]] = Field(default=None, description="Expression values")


class FoundEntity(BaseModel):
    """A found entity in a pathway."""

    id: str = Field(..., description="Entity identifier")
    stId: str = Field(..., description="Stable identifier")
    name: str = Field(default="", description="Entity name")
    mapsFrom: Optional[List[str]] = Field(default=None, description="Input identifiers")
    exp: Optional[List[float]] = Field(default=None, description="Expression values")


class AnalysisRequestModel(BaseModel):
    """Model for analysis request parameters."""

    identifiers: List[str] = Field(..., min_length=1, description="List of identifiers")
    species: Optional[str] = Field(default=None, description="Species name (e.g., 'Homo sapiens')")
    interactors: bool = Field(default=False, description="Include interactors")
    pageSize: int = Field(default=20, description="Results per page")
    page: int = Field(default=1, description="Page number")
    sortBy: str = Field(default="ENTITIES_FDR", description="Sort field")
    order: str = Field(default="ASC", description="Sort order (ASC/DESC)")
    resource: str = Field(default="TOTAL", description="Resource filter")
    pValue: float = Field(default=1.0, description="P-value cutoff")
    includeDisease: bool = Field(default=True, description="Include disease pathways")
    min_entities: Optional[int] = Field(default=None, description="Minimum pathway size")
    max_entities: Optional[int] = Field(default=None, description="Maximum pathway size")

    def get_params(self) -> Dict[str, Any]:
        """Get query parameters for API request."""
        params = {
            "interactors": str(self.interactors).lower(),
            "pageSize": self.pageSize,
            "page": self.page,
            "sortBy": self.sortBy,
            "order": self.order,
            "resource": self.resource,
            "pValue": self.pValue,
            "includeDisease": str(self.includeDisease).lower(),
        }
        if self.species:
            params["species"] = self.species
        if self.min_entities is not None:
            params["min"] = self.min_entities
        if self.max_entities is not None:
            params["max"] = self.max_entities
        return params

    def get_identifiers_string(self) -> str:
        """Get identifiers as newline-separated string."""
        return "\n".join(self.identifiers)


class SpeciesInfo(BaseModel):
    """Species information from Content Service."""

    dbId: int = Field(..., description="Database ID")
    taxId: str = Field(default="", description="Taxonomy ID")
    displayName: str = Field(..., description="Display name")
    shortName: str = Field(default="", description="Short name (e.g., 'H. sapiens')")
    abbreviation: str = Field(default="", description="Abbreviation (e.g., 'HSA')")
