"""Pydantic models for Disease Ontology API requests and responses."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class DOBase(str, Enum):
    """Disease Ontology base URLs."""

    # Direct Disease Ontology API
    DO_API = "https://disease-ontology.org/api"
    # EBI Ontology Lookup Service (more comprehensive)
    OLS_API = "https://www.ebi.ac.uk/ols4/api"


class DOEndpoint(str, Enum):
    """Disease Ontology direct API endpoints."""

    # Metadata endpoint
    METADATA = "metadata/{doid}/"


class OLSEndpoint(str, Enum):
    """EBI OLS API endpoints for Disease Ontology."""

    # Ontology info
    ONTOLOGY_INFO = "ontologies/doid"

    # Term endpoints
    TERMS = "ontologies/doid/terms"
    TERM_BY_IRI = "ontologies/doid/terms/{encoded_iri}"
    TERM_BY_SHORT = "ontologies/doid/terms?short_form={short_form}"

    # Hierarchy endpoints
    PARENTS = "ontologies/doid/terms/{encoded_iri}/parents"
    CHILDREN = "ontologies/doid/terms/{encoded_iri}/children"
    ANCESTORS = "ontologies/doid/terms/{encoded_iri}/ancestors"
    DESCENDANTS = "ontologies/doid/terms/{encoded_iri}/descendants"
    HIERARCHICAL_PARENTS = "ontologies/doid/terms/{encoded_iri}/hierarchicalParents"
    HIERARCHICAL_CHILDREN = "ontologies/doid/terms/{encoded_iri}/hierarchicalChildren"

    # Search
    SEARCH = "search"


# ----- Cross-reference Models -----


class XRef(BaseModel):
    """External cross-reference."""

    database: Optional[str] = Field(default=None, description="Database name")
    id: Optional[str] = Field(default=None, description="ID in external database")
    description: Optional[str] = Field(default=None, description="Description")
    url: Optional[str] = Field(default=None, description="URL to external resource")

    @property
    def full_id(self) -> str:
        """Get full ID as database:id format."""
        if self.database and self.id:
            return f"{self.database}:{self.id}"
        return self.id or ""


# ----- Disease Term Models -----


class DiseaseTerm(BaseModel):
    """Disease Ontology term model.

    Represents a disease term from the Disease Ontology.
    """

    doid: str = Field(..., description="Disease Ontology ID (e.g., DOID:162)")
    name: str = Field(..., description="Disease name")
    definition: Optional[str] = Field(default=None, description="Disease definition")
    synonyms: Optional[List[str]] = Field(default=None, description="Synonyms")
    xrefs: Optional[List[str]] = Field(
        default=None, description="Cross-references as strings"
    )
    subsets: Optional[List[str]] = Field(default=None, description="Ontology subsets")
    is_obsolete: bool = Field(default=False, description="Whether term is obsolete")
    has_children: bool = Field(default=False, description="Whether term has children")
    is_root: bool = Field(default=False, description="Whether term is a root term")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def id(self) -> str:
        """Alias for doid."""
        return self.doid

    @property
    def numeric_id(self) -> int:
        """Get numeric part of DOID."""
        if ":" in self.doid:
            return int(self.doid.split(":")[1])
        return int(self.doid.replace("DOID_", "").replace("DOID", ""))

    def get_xref(self, database: str) -> Optional[str]:
        """Get cross-reference for a specific database.

        Args:
            database: Database name (e.g., "MESH", "UMLS_CUI", "ICD10CM").

        Returns:
            ID in the specified database, or None.
        """
        if not self.xrefs:
            return None
        db_upper = database.upper()
        for xref in self.xrefs:
            if xref.upper().startswith(db_upper + ":"):
                return xref.split(":", 1)[1]
        return None

    @property
    def mesh_id(self) -> Optional[str]:
        """Get MeSH ID if available."""
        return self.get_xref("MESH")

    @property
    def umls_cui(self) -> Optional[str]:
        """Get UMLS CUI if available."""
        return self.get_xref("UMLS_CUI")

    @property
    def icd10_code(self) -> Optional[str]:
        """Get ICD-10 code if available."""
        return self.get_xref("ICD10CM")

    @property
    def nci_code(self) -> Optional[str]:
        """Get NCI Thesaurus code if available."""
        return self.get_xref("NCI")


class DiseaseTermDetailed(DiseaseTerm):
    """Detailed disease term with additional OLS fields."""

    iri: Optional[str] = Field(default=None, description="Full IRI")
    short_form: Optional[str] = Field(default=None, description="Short form (DOID_123)")
    ontology_name: str = Field(default="doid", description="Ontology name")
    ontology_prefix: str = Field(default="DOID", description="Ontology prefix")
    annotation: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional annotations"
    )
    obo_xrefs: Optional[List[XRef]] = Field(
        default=None, description="Detailed cross-references"
    )
    in_subset: Optional[List[str]] = Field(
        default=None, description="Ontology subsets"
    )

    model_config = ConfigDict(populate_by_name=True)


class DiseaseRelationship(BaseModel):
    """Relationship between disease terms."""

    relationship_type: str = Field(..., description="Type of relationship (is_a, etc.)")
    target_doid: str = Field(..., description="Target disease DOID")
    target_name: str = Field(..., description="Target disease name")


class OntologyInfo(BaseModel):
    """Disease Ontology metadata."""

    ontology_id: str = Field(default="doid", description="Ontology ID")
    title: str = Field(default="Human Disease Ontology", description="Ontology title")
    description: Optional[str] = Field(default=None, description="Description")
    version: Optional[str] = Field(default=None, description="Version string")
    number_of_terms: int = Field(default=0, description="Number of terms")
    loaded: Optional[str] = Field(default=None, description="Last loaded timestamp")
    homepage: Optional[str] = Field(
        default="https://disease-ontology.org", description="Homepage URL"
    )

    model_config = ConfigDict(populate_by_name=True)


# ----- Search Models -----


class SearchResult(BaseModel):
    """Search result from OLS."""

    iri: str = Field(..., description="Term IRI")
    doid: str = Field(..., alias="obo_id", description="DOID")
    name: str = Field(..., alias="label", description="Disease name")
    description: Optional[List[str]] = Field(default=None, description="Descriptions")
    synonyms: Optional[List[str]] = Field(default=None, description="Synonyms")
    ontology_name: str = Field(default="doid", description="Ontology name")
    short_form: Optional[str] = Field(default=None, description="Short form")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def definition(self) -> Optional[str]:
        """Get first description as definition."""
        if self.description:
            return self.description[0]
        return None


# ----- Request Models -----


class DOSearchRequest(BaseModel):
    """Request model for disease search."""

    query: str = Field(..., min_length=1, description="Search query")
    ontology: str = Field(default="doid", description="Ontology to search")
    exact: bool = Field(default=False, description="Exact match only")
    rows: int = Field(default=20, description="Number of results")
    start: int = Field(default=0, description="Starting offset")

    def get_params(self) -> Dict[str, Any]:
        """Get query parameters for API request."""
        params = {
            "q": self.query,
            "ontology": self.ontology,
            "rows": self.rows,
            "start": self.start,
        }
        if self.exact:
            params["exact"] = "true"
        return params
