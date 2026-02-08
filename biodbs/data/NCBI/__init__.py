"""NCBI Datasets data models and containers."""

from biodbs.data.NCBI._data_model import (
    NCBIBase,
    NCBIGeneEndpoint,
    NCBITaxonomyEndpoint,
    NCBIGenomeEndpoint,
    NCBIVersionEndpoint,
    GeneType,
    SortDirection,
    GeneContentType,
    GeneReport,
    TaxonomyReport,
    GenomeReport,
    GeneDatasetRequest,
    TaxonomyDatasetRequest,
)
from biodbs.data.NCBI.data import (
    NCBIGeneFetchedData,
    NCBITaxonomyFetchedData,
    NCBIGenomeFetchedData,
    NCBIDataManager,
)

__all__ = [
    # Base URLs and Endpoints
    "NCBIBase",
    "NCBIGeneEndpoint",
    "NCBITaxonomyEndpoint",
    "NCBIGenomeEndpoint",
    "NCBIVersionEndpoint",
    # Enums
    "GeneType",
    "SortDirection",
    "GeneContentType",
    # Data Models
    "GeneReport",
    "TaxonomyReport",
    "GenomeReport",
    # Request Models
    "GeneDatasetRequest",
    "TaxonomyDatasetRequest",
    # Data Containers
    "NCBIGeneFetchedData",
    "NCBITaxonomyFetchedData",
    "NCBIGenomeFetchedData",
    "NCBIDataManager",
]
