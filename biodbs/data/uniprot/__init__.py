"""UniProt data models and containers."""

from biodbs.data.uniprot._data_model import (
    UniProtBase,
    UniProtEndpoint,
    EntryType,
    ProteinExistence,
    CommentType,
    FeatureType,
    Evidence,
    Gene,
    GeneName,
    Organism,
    ProteinDescription,
    ProteinName,
    ProteinNameValue,
    Sequence,
    Feature,
    FeatureLocation,
    Comment,
    CrossReference,
    Keyword,
    EntryAudit,
    UniProtEntry,
    UniProtSearchRequest,
    IDMappingRequest,
)
from biodbs.data.uniprot.data import (
    UniProtFetchedData,
    UniProtSearchResult,
    UniProtDataManager,
)

__all__ = [
    # Base URLs and Endpoints
    "UniProtBase",
    "UniProtEndpoint",
    # Enums
    "EntryType",
    "ProteinExistence",
    "CommentType",
    "FeatureType",
    # Data Models
    "Evidence",
    "Gene",
    "GeneName",
    "Organism",
    "ProteinDescription",
    "ProteinName",
    "ProteinNameValue",
    "Sequence",
    "Feature",
    "FeatureLocation",
    "Comment",
    "CrossReference",
    "Keyword",
    "EntryAudit",
    "UniProtEntry",
    # Request Models
    "UniProtSearchRequest",
    "IDMappingRequest",
    # Data Containers
    "UniProtFetchedData",
    "UniProtSearchResult",
    "UniProtDataManager",
]
