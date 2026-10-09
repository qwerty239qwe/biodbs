"""Taxonomic name translation using the shared taxonomy mapper."""

from typing import Iterable

import pandas as pd

from biodbs._funcs.taxonomy import TaxonomyMapper


def translate_taxon_names(
    names: Iterable[str],
    *,
    mapper: TaxonomyMapper | None = None,
    source: str = "name",
) -> pd.DataFrame:
    """Resolve taxonomic names to NCBI taxids and canonical-name metadata.

    Args:
        names: Iterable of taxonomic names, not a single string. Input order
            and duplicate names are preserved.
        mapper: Optional configured taxonomy mapper. Supply a loaded taxdump for offline
            resolution, or NCBI/GBIF fetchers for online resolution/enrichment.
            Without a mapper, use online NCBI name-to-taxid resolution only.
            A taxdump is never downloaded automatically.
        source: Source label passed to ``TaxonomyMapper.map_names``. Use
            ``"gtdb"`` to consult the mapper's GTDB species-name crosswalk.

    Returns:
        The mapper's standard mapping DataFrame, including ``query``,
        ``hub_taxid``, ``canonical_name``, rank, lineage, and match status.
        Unresolved names remain as rows with missing taxids; empty input
        returns an empty DataFrame with the same columns.

    Raises:
        TypeError: If names is a single string or bytes object.

    Note:
        Fetcher errors propagate unchanged. For database lineage strings,
        use ``mapper.map_lineage`` instead.
    """
    if isinstance(names, (str, bytes)):
        raise TypeError("names must be an iterable of taxonomic names, not a single string")
    if mapper is None:
        from biodbs.fetch.NCBI import NCBI_Fetcher

        mapper = TaxonomyMapper(ncbi_fetcher=NCBI_Fetcher(), use_gbif=False)
    return mapper.map_names(names, source=source)
