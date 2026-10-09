"""Public taxonomy mapping API.

Build a canonical / cross-database taxon mapping table around NCBI taxid:

    >>> from biodbs.taxonomy import TaxonomyMapper
    >>> from biodbs.fetch.NCBI import NCBI_Fetcher
    >>> from biodbs.fetch.GBIF import GBIF_Fetcher
    >>> mapper = TaxonomyMapper(ncbi_fetcher=NCBI_Fetcher(), gbif_fetcher=GBIF_Fetcher())
    >>> df = mapper.map_names(["Escherichia coli"])
"""

from biodbs._funcs.taxonomy import (
    MAPPING_COLUMNS,
    NCBITaxonomy,
    TaxonRecord,
    TaxonomyMapper,
    load_taxdump,
    merge_on_hub,
)

__all__ = [
    "MAPPING_COLUMNS",
    "NCBITaxonomy",
    "TaxonRecord",
    "TaxonomyMapper",
    "load_taxdump",
    "merge_on_hub",
]
