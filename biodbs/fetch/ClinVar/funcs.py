"""Convenience functions for ClinVar data fetching."""

from __future__ import annotations

from typing import List, Optional, Union

from biodbs.data.ClinVar.data import ClinVarFetchedData
from biodbs.fetch.ClinVar.clinvar_fetcher import ClinVar_Fetcher

_fetcher: Optional[ClinVar_Fetcher] = None


def _get_fetcher() -> ClinVar_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = ClinVar_Fetcher()
    return _fetcher


def clinvar_search(
    query: str,
    retmax: int = 500,
    retstart: int = 0,
) -> List[str]:
    """Find ClinVar variation UIDs matching an Entrez query.

    Uses the same query language as the ClinVar website.  Common field tags:

    - ``BRCA1[gene]`` — gene name
    - ``pathogenic[clnsig]`` — clinical significance
    - ``"Breast cancer"[dis]`` — disease
    - ``single_gene[prop]`` — single-gene variants

    Args:
        query: Entrez query string.
        retmax: Maximum UIDs to return (default 500).
        retstart: Offset for pagination.

    Returns:
        List of variation UID strings.

    Example::

        uids = clinvar_search("BRCA1[gene] AND pathogenic[clnsig]")
        data = clinvar_fetch_by_id(uids[:20])
    """
    return _get_fetcher().search(query, retmax=retmax, retstart=retstart)


def clinvar_count(query: str) -> int:
    """Return the total number of ClinVar records matching *query*.

    Args:
        query: Entrez query string.

    Returns:
        Integer count.

    Example::

        n = clinvar_count("TP53[gene] AND pathogenic[clnsig]")
        print(f"TP53 has {n} pathogenic variants in ClinVar")
    """
    return _get_fetcher().count(query)


def clinvar_fetch_by_id(
    ids: List[Union[str, int]],
) -> ClinVarFetchedData:
    """Fetch ClinVar summaries for a list of variation UIDs.

    Args:
        ids: ClinVar variation UIDs (integers or strings).

    Returns:
        :class:`~biodbs.data.ClinVar.data.ClinVarFetchedData`.

    Example::

        data = clinvar_fetch_by_id([65533, 14206])
        print(data.as_dataframe())
    """
    return _get_fetcher().fetch_summary(ids)


def clinvar_search_gene(
    gene_symbol: str,
    retmax: int = 500,
    single_gene: bool = True,
    clinical_significance: Optional[str] = None,
) -> ClinVarFetchedData:
    """Search and fetch ClinVar variants for a gene in one step.

    Args:
        gene_symbol: HGNC gene symbol (e.g. ``"BRCA1"``).
        retmax: Maximum variants to return.
        single_gene: If ``True`` (default), restrict to single-gene variants.
        clinical_significance: Optional filter (e.g. ``"pathogenic"``).

    Returns:
        :class:`~biodbs.data.ClinVar.data.ClinVarFetchedData`.

    Example::

        data = clinvar_search_gene("TP53", retmax=200,
                                   clinical_significance="pathogenic")
        df = data.as_dataframe()
    """
    return _get_fetcher().search_gene(
        gene_symbol,
        single_gene=single_gene,
        retmax=retmax,
        clinical_significance=clinical_significance,
    )


def clinvar_search_condition(
    condition: str,
    retmax: int = 500,
    clinical_significance: Optional[str] = None,
) -> ClinVarFetchedData:
    """Search and fetch ClinVar variants for a disease/condition.

    Args:
        condition: Disease or condition name (e.g. ``"Lynch syndrome"``).
        retmax: Maximum variants to return.
        clinical_significance: Optional significance filter.

    Returns:
        :class:`~biodbs.data.ClinVar.data.ClinVarFetchedData`.

    Example::

        data = clinvar_search_condition("Breast cancer",
                                        clinical_significance="pathogenic")
    """
    return _get_fetcher().search_condition(
        condition,
        retmax=retmax,
        clinical_significance=clinical_significance,
    )


def clinvar_fetch_vcv(accession: str) -> str:
    """Retrieve the full VCV XML record for a variation.

    Args:
        accession: VCV accession (e.g. ``"VCV000014206"`` or
            ``"VCV000014206.3"``).

    Returns:
        Raw XML string.

    Example::

        xml = clinvar_fetch_vcv("VCV000014206")
    """
    return _get_fetcher().fetch_vcv(accession)


def clinvar_fetch_rcv(accession: str) -> str:
    """Retrieve the full RCV XML record for a variation-condition pair.

    Args:
        accession: RCV accession (e.g. ``"RCV000000606"``).

    Returns:
        Raw XML string.

    Example::

        xml = clinvar_fetch_rcv("RCV000000606")
    """
    return _get_fetcher().fetch_rcv(accession)


def clinvar_link_pubmed(variation_id: Union[str, int]) -> List[str]:
    """Return PubMed UIDs linked to a ClinVar variation.

    Args:
        variation_id: ClinVar variation UID.

    Returns:
        List of PubMed UID strings.

    Example::

        pmids = clinvar_link_pubmed(65533)
    """
    return _get_fetcher().link_to_pubmed(variation_id)
