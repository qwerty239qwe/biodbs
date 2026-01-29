from enum import Enum
from pydantic import BaseModel, model_validator, field_validator, ConfigDict
from typing import Dict, Any, Optional, List, Union, Literal


# =============================================================================
# Enums for QuickGO API
# =============================================================================

class QuickGOCategory(Enum):
    """Top-level API categories."""
    ontology = "ontology"
    annotation = "annotation"
    geneproduct = "geneproduct"


class OntologyType(Enum):
    """Ontology types supported by QuickGO."""
    go = "go"   # Gene Ontology
    eco = "eco"  # Evidence & Conclusion Ontology


class GOAspect(Enum):
    """GO aspects (namespaces)."""
    biological_process = "biological_process"
    molecular_function = "molecular_function"
    cellular_component = "cellular_component"


class GOEvidence(Enum):
    """GO evidence codes."""
    # Experimental Evidence
    EXP = "EXP"  # Inferred from Experiment
    IDA = "IDA"  # Inferred from Direct Assay
    IPI = "IPI"  # Inferred from Physical Interaction
    IMP = "IMP"  # Inferred from Mutant Phenotype
    IGI = "IGI"  # Inferred from Genetic Interaction
    IEP = "IEP"  # Inferred from Expression Pattern
    HTP = "HTP"  # Inferred from High Throughput Experiment
    HDA = "HDA"  # Inferred from High Throughput Direct Assay
    HMP = "HMP"  # Inferred from High Throughput Mutant Phenotype
    HGI = "HGI"  # Inferred from High Throughput Genetic Interaction
    HEP = "HEP"  # Inferred from High Throughput Expression Pattern
    # Phylogenetic Evidence
    IBA = "IBA"  # Inferred from Biological aspect of Ancestor
    IBD = "IBD"  # Inferred from Biological aspect of Descendant
    IKR = "IKR"  # Inferred from Key Residues
    IRD = "IRD"  # Inferred from Rapid Divergence
    # Computational Analysis
    ISS = "ISS"  # Inferred from Sequence or structural Similarity
    ISO = "ISO"  # Inferred from Sequence Orthology
    ISA = "ISA"  # Inferred from Sequence Alignment
    ISM = "ISM"  # Inferred from Sequence Model
    IGC = "IGC"  # Inferred from Genomic Context
    RCA = "RCA"  # Inferred from Reviewed Computational Analysis
    # Author Statement
    TAS = "TAS"  # Traceable Author Statement
    NAS = "NAS"  # Non-traceable Author Statement
    # Curator Statement
    IC = "IC"    # Inferred by Curator
    ND = "ND"    # No biological Data available
    # Electronic Annotation
    IEA = "IEA"  # Inferred from Electronic Annotation


class GORelation(Enum):
    """GO term relations."""
    is_a = "is_a"
    part_of = "part_of"
    occurs_in = "occurs_in"
    regulates = "regulates"
    positively_regulates = "positively_regulates"
    negatively_regulates = "negatively_regulates"


class AnnotationQualifier(Enum):
    """Annotation qualifiers (relation between gene product and GO term)."""
    enables = "enables"
    contributes_to = "contributes_to"
    involved_in = "involved_in"
    acts_upstream_of = "acts_upstream_of"
    acts_upstream_of_positive_effect = "acts_upstream_of_positive_effect"
    acts_upstream_of_negative_effect = "acts_upstream_of_negative_effect"
    acts_upstream_of_or_within = "acts_upstream_of_or_within"
    acts_upstream_of_or_within_positive_effect = "acts_upstream_of_or_within_positive_effect"
    acts_upstream_of_or_within_negative_effect = "acts_upstream_of_or_within_negative_effect"
    located_in = "located_in"
    part_of = "part_of"
    is_active_in = "is_active_in"
    colocalizes_with = "colocalizes_with"
    NOT = "NOT"  # Negation


class GOUsage(Enum):
    """How to interpret GO terms in queries."""
    exact = "exact"        # Only the specified term
    descendants = "descendants"  # Term and its descendants
    slim = "slim"          # Map to slim terms


class GeneProductType(Enum):
    """Types of gene products."""
    protein = "protein"
    miRNA = "miRNA"
    complex = "complex"


class GeneProductDatabase(Enum):
    """Gene product source databases."""
    UniProtKB = "UniProtKB"
    RNAcentral = "RNAcentral"
    ComplexPortal = "ComplexPortal"


class DownloadFormat(Enum):
    """Download formats for annotations."""
    tsv = "tsv"
    gaf = "gaf"
    gpad = "gpad"


# =============================================================================
# Ontology Endpoint Enums
# =============================================================================

class OntologyEndpoint(Enum):
    """Ontology API endpoints."""
    about = "about"
    search = "search"
    terms = "terms"
    slim = "slim"
    terms_by_id = "terms/{ids}"
    terms_ancestors = "terms/{ids}/ancestors"
    terms_descendants = "terms/{ids}/descendants"
    terms_children = "terms/{ids}/children"
    terms_chart = "terms/{ids}/chart"
    terms_chart_coords = "terms/{ids}/chart/coords"
    terms_complete = "terms/{ids}/complete"
    terms_constraints = "terms/{ids}/constraints"
    terms_graph = "terms/graph"


class AnnotationEndpoint(Enum):
    """Annotation API endpoints."""
    search = "search"
    download = "downloadSearch"
    stats = "stats"


class GeneProductEndpoint(Enum):
    """Gene Product API endpoints."""
    search = "search"


# =============================================================================
# Pydantic Models for Request Validation
# =============================================================================

class QuickGOBaseModel(BaseModel):
    """Base model for QuickGO API requests."""
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    # Pagination
    limit: Optional[int] = None
    page: Optional[int] = None

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 10000):
            raise ValueError("limit must be between 1 and 10000")
        return v

    @field_validator("page")
    @classmethod
    def validate_page(cls, v):
        if v is not None and v < 1:
            raise ValueError("page must be >= 1")
        return v


class OntologySearchModel(QuickGOBaseModel):
    """Model for ontology search requests (GO/ECO term search)."""
    ontology: OntologyType = OntologyType.go
    query: str  # Search query string

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("query cannot be empty")
        return v.strip()


class OntologyTermsModel(QuickGOBaseModel):
    """Model for fetching GO/ECO terms by ID."""
    ontology: OntologyType = OntologyType.go
    ids: Union[str, List[str]]  # GO:XXXXXXX or ECO:XXXXXXX format

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v):
        if isinstance(v, str):
            v = [v]
        for id_ in v:
            if not (id_.startswith("GO:") or id_.startswith("ECO:")):
                raise ValueError(
                    f"Invalid term ID format: {id_}. Must start with GO: or ECO:"
                )
        return v


class OntologyAncestorsDescendantsModel(OntologyTermsModel):
    """Model for ancestor/descendant queries."""
    relations: Optional[List[GORelation]] = None

    @model_validator(mode="after")
    def set_default_relations(self):
        if self.relations is None:
            self.relations = [
                GORelation.is_a,
                GORelation.part_of,
                GORelation.occurs_in,
                GORelation.regulates,
            ]
        return self


class OntologySlimModel(QuickGOBaseModel):
    """Model for GO slim mapping."""
    ontology: OntologyType = OntologyType.go
    slimsToIds: Union[str, List[str]]  # Target slim term IDs
    slimsFromIds: Optional[Union[str, List[str]]] = None  # Source term IDs
    relations: Optional[List[GORelation]] = None


class OntologyGraphModel(QuickGOBaseModel):
    """Model for term graph queries."""
    ontology: OntologyType = OntologyType.go
    startIds: Union[str, List[str]]  # Starting term IDs
    stopIds: Optional[Union[str, List[str]]] = None  # Optional stop term IDs
    relations: Optional[List[GORelation]] = None


class OntologyChartModel(OntologyTermsModel):
    """Model for chart generation."""
    base64: bool = False
    showKey: bool = True
    showIds: bool = True
    showSlimColours: bool = False
    showChildren: bool = True
    termBoxWidth: Optional[int] = None
    termBoxHeight: Optional[int] = None
    fontSize: Optional[int] = None


class AnnotationSearchModel(QuickGOBaseModel):
    """Model for annotation search requests.

    Supports filtering by GO terms, gene products, taxonomy, evidence, etc.
    """
    # GO term filters
    goId: Optional[Union[str, List[str]]] = None
    goUsage: Optional[GOUsage] = None
    goUsageRelationships: Optional[List[GORelation]] = None

    # Gene product filters
    geneProductId: Optional[Union[str, List[str]]] = None
    geneProductType: Optional[GeneProductType] = None
    geneProductSubset: Optional[str] = None

    # Taxonomy filters
    taxonId: Optional[Union[int, List[int]]] = None
    taxonUsage: Optional[Literal["exact", "descendants"]] = None

    # Annotation filters
    aspect: Optional[GOAspect] = None
    evidenceCode: Optional[Union[str, List[str]]] = None  # ECO IDs
    goEvidence: Optional[Union[GOEvidence, List[GOEvidence]]] = None
    qualifier: Optional[Union[AnnotationQualifier, List[AnnotationQualifier]]] = None
    assignedBy: Optional[Union[str, List[str]]] = None

    # Reference and extension filters
    reference: Optional[Union[str, List[str]]] = None
    withFrom: Optional[Union[str, List[str]]] = None
    extension: Optional[str] = None

    # Target sets
    targetSet: Optional[Union[str, List[str]]] = None

    # Output control
    includeFields: Optional[List[str]] = None
    excludeFields: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_at_least_one_filter(self):
        filter_fields = [
            self.goId, self.geneProductId, self.taxonId,
            self.aspect, self.evidenceCode, self.goEvidence,
            self.qualifier, self.assignedBy, self.reference,
        ]
        if all(f is None for f in filter_fields):
            # Allow empty search for browsing, but warn
            pass
        return self


class AnnotationDownloadModel(AnnotationSearchModel):
    """Model for annotation download requests."""
    downloadFormat: DownloadFormat = DownloadFormat.tsv

    # TSV-specific options
    selectedFields: Optional[List[str]] = None

    # Available fields for TSV download
    AVAILABLE_FIELDS: List[str] = [
        "geneProductDb", "geneProductId", "symbol", "qualifier",
        "goId", "goName", "goAspect", "evidenceCode", "goEvidence",
        "reference", "withFrom", "taxonId", "taxonName",
        "assignedBy", "extensions", "date", "synonyms", "name",
    ]


class AnnotationStatsModel(QuickGOBaseModel):
    """Model for annotation statistics requests."""
    # At least one filter required
    goId: Optional[Union[str, List[str]]] = None
    geneProductId: Optional[Union[str, List[str]]] = None
    taxonId: Optional[Union[int, List[int]]] = None
    aspect: Optional[GOAspect] = None
    evidenceCode: Optional[Union[str, List[str]]] = None
    goEvidence: Optional[Union[GOEvidence, List[GOEvidence]]] = None
    assignedBy: Optional[Union[str, List[str]]] = None


class GeneProductSearchModel(QuickGOBaseModel):
    """Model for gene product search requests."""
    query: str  # Search query (symbol, name, ID)
    taxonId: Optional[Union[int, List[int]]] = None
    type: Optional[GeneProductType] = None
    dbSubset: Optional[str] = None  # e.g., "Swiss-Prot", "TrEMBL"
    proteome: Optional[str] = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("query cannot be empty")
        return v.strip()


# =============================================================================
# Main QuickGO Model
# =============================================================================

class QuickGOModel(BaseModel):
    """Main model for QuickGO API request validation.

    Examples::

        # Search GO terms
        QuickGOModel(
            category="ontology",
            ontology="go",
            endpoint="search",
            query="apoptosis"
        )

        # Get GO term by ID
        QuickGOModel(
            category="ontology",
            ontology="go",
            endpoint="terms/{ids}",
            ids=["GO:0008150", "GO:0003674"]
        )

        # Search annotations
        QuickGOModel(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",
            taxonId=9606,
            goEvidence=["IDA", "IMP"]
        )

        # Download annotations
        QuickGOModel(
            category="annotation",
            endpoint="downloadSearch",
            goId="GO:0006915",
            downloadFormat="gaf"
        )

        # Search gene products
        QuickGOModel(
            category="geneproduct",
            endpoint="search",
            query="TP53"
        )
    """
    model_config = ConfigDict(use_enum_values=True, extra="allow")

    # Required fields
    category: QuickGOCategory
    endpoint: str

    # Ontology-specific
    ontology: Optional[OntologyType] = OntologyType.go
    ids: Optional[Union[str, List[str]]] = None

    # Search/query
    query: Optional[str] = None

    # GO term filters
    goId: Optional[Union[str, List[str]]] = None
    goUsage: Optional[GOUsage] = None
    goUsageRelationships: Optional[List[GORelation]] = None

    # Gene product filters
    geneProductId: Optional[Union[str, List[str]]] = None
    geneProductType: Optional[GeneProductType] = None

    # Taxonomy
    taxonId: Optional[Union[int, List[int]]] = None
    taxonUsage: Optional[Literal["exact", "descendants"]] = None

    # Evidence and annotation
    aspect: Optional[GOAspect] = None
    evidenceCode: Optional[Union[str, List[str]]] = None
    goEvidence: Optional[Union[GOEvidence, List[GOEvidence]]] = None
    qualifier: Optional[Union[AnnotationQualifier, List[AnnotationQualifier]]] = None
    assignedBy: Optional[Union[str, List[str]]] = None

    # Relations
    relations: Optional[List[GORelation]] = None
    startIds: Optional[Union[str, List[str]]] = None
    stopIds: Optional[Union[str, List[str]]] = None

    # Slim
    slimsToIds: Optional[Union[str, List[str]]] = None
    slimsFromIds: Optional[Union[str, List[str]]] = None

    # Chart options
    base64: Optional[bool] = None
    showKey: Optional[bool] = None
    showIds: Optional[bool] = None
    showSlimColours: Optional[bool] = None
    showChildren: Optional[bool] = None
    termBoxWidth: Optional[int] = None
    termBoxHeight: Optional[int] = None
    fontSize: Optional[int] = None

    # Download options
    downloadFormat: Optional[DownloadFormat] = None
    selectedFields: Optional[List[str]] = None
    includeFields: Optional[List[str]] = None
    excludeFields: Optional[List[str]] = None

    # Pagination
    limit: Optional[int] = None
    page: Optional[int] = None

    @model_validator(mode="after")
    def validate_category_requirements(self):
        cat = QuickGOCategory(self.category) if isinstance(self.category, str) else self.category

        if cat == QuickGOCategory.ontology:
            # Ontology endpoints require ontology type
            if self.ontology is None:
                self.ontology = OntologyType.go

            # Search requires query
            if self.endpoint == "search" and not self.query:
                raise ValueError("Ontology search requires 'query' parameter")

            # Terms endpoints require ids (except search, about, terms list)
            if "{ids}" in self.endpoint and not self.ids:
                raise ValueError(f"Endpoint '{self.endpoint}' requires 'ids' parameter")

            # Graph requires startIds
            if self.endpoint == "terms/graph" and not self.startIds:
                raise ValueError("terms/graph endpoint requires 'startIds' parameter")

            # Slim requires slimsToIds
            if self.endpoint == "slim" and not self.slimsToIds:
                raise ValueError("slim endpoint requires 'slimsToIds' parameter")

        elif cat == QuickGOCategory.geneproduct:
            # Gene product search requires query
            if self.endpoint == "search" and not self.query:
                raise ValueError("Gene product search requires 'query' parameter")

        return self

    @field_validator("ids", "goId", "geneProductId", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 10000):
            raise ValueError("limit must be between 1 and 10000")
        return v

    def build_path(self) -> str:
        """Build the URL path for this request."""
        cat = self.category if isinstance(self.category, str) else self.category.value
        ont = self.ontology if isinstance(self.ontology, str) else (
            self.ontology.value if self.ontology else "go"
        )

        if cat == "ontology":
            base = f"{ont}/{self.endpoint}"
            if self.ids and "{ids}" in base:
                ids_str = ",".join(self.ids) if isinstance(self.ids, list) else self.ids
                base = base.replace("{ids}", ids_str)
            return base
        elif cat == "annotation":
            return self.endpoint
        elif cat == "geneproduct":
            return self.endpoint
        return self.endpoint

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for the request."""
        params = {}

        # Pagination
        if self.limit is not None:
            params["limit"] = self.limit
        if self.page is not None:
            params["page"] = self.page

        # Search query
        if self.query:
            params["query"] = self.query

        # GO filters
        if self.goId:
            params["goId"] = ",".join(self.goId) if isinstance(self.goId, list) else self.goId
        if self.goUsage:
            params["goUsage"] = self.goUsage
        if self.goUsageRelationships:
            params["goUsageRelationships"] = ",".join(
                r if isinstance(r, str) else r.value for r in self.goUsageRelationships
            )

        # Gene product filters
        if self.geneProductId:
            params["geneProductId"] = ",".join(self.geneProductId) if isinstance(
                self.geneProductId, list) else self.geneProductId
        if self.geneProductType:
            params["geneProductType"] = self.geneProductType

        # Taxonomy
        if self.taxonId:
            params["taxonId"] = ",".join(map(str, self.taxonId)) if isinstance(
                self.taxonId, list) else self.taxonId
        if self.taxonUsage:
            params["taxonUsage"] = self.taxonUsage

        # Evidence
        if self.aspect:
            params["aspect"] = self.aspect
        if self.evidenceCode:
            params["evidenceCode"] = ",".join(self.evidenceCode) if isinstance(
                self.evidenceCode, list) else self.evidenceCode
        if self.goEvidence:
            evs = self.goEvidence if isinstance(self.goEvidence, list) else [self.goEvidence]
            params["goEvidence"] = ",".join(e if isinstance(e, str) else e.value for e in evs)
        if self.qualifier:
            qs = self.qualifier if isinstance(self.qualifier, list) else [self.qualifier]
            params["qualifier"] = ",".join(q if isinstance(q, str) else q.value for q in qs)
        if self.assignedBy:
            params["assignedBy"] = ",".join(self.assignedBy) if isinstance(
                self.assignedBy, list) else self.assignedBy

        # Relations
        if self.relations:
            params["relations"] = ",".join(
                r if isinstance(r, str) else r.value for r in self.relations
            )
        if self.startIds:
            params["startIds"] = ",".join(self.startIds) if isinstance(
                self.startIds, list) else self.startIds
        if self.stopIds:
            params["stopIds"] = ",".join(self.stopIds) if isinstance(
                self.stopIds, list) else self.stopIds

        # Slim
        if self.slimsToIds:
            params["slimsToIds"] = ",".join(self.slimsToIds) if isinstance(
                self.slimsToIds, list) else self.slimsToIds
        if self.slimsFromIds:
            params["slimsFromIds"] = ",".join(self.slimsFromIds) if isinstance(
                self.slimsFromIds, list) else self.slimsFromIds

        # Chart options
        for field in ["base64", "showKey", "showIds", "showSlimColours",
                      "showChildren", "termBoxWidth", "termBoxHeight", "fontSize"]:
            val = getattr(self, field, None)
            if val is not None:
                params[field] = val

        # Download options
        if self.downloadFormat:
            params["downloadFormat"] = self.downloadFormat
        if self.selectedFields:
            params["selectedFields"] = ",".join(self.selectedFields)
        if self.includeFields:
            params["includeFields"] = ",".join(self.includeFields)
        if self.excludeFields:
            params["excludeFields"] = ",".join(self.excludeFields)

        return params