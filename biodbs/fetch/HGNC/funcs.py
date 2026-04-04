"""Convenience functions for HGNC data fetching."""

from typing import Optional
from biodbs.data.HGNC.data import HGNCFetchedData
from biodbs.fetch.HGNC.hgnc_fetcher import HGNC_Fetcher

_fetcher: Optional[HGNC_Fetcher] = None


def _get_fetcher() -> HGNC_Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = HGNC_Fetcher()
    return _fetcher


def hgnc_info() -> dict:
    """Return HGNC service metadata.

    Includes the database last-modified timestamp, total document count,
    and the lists of searchable and stored fields.

    Returns:
        Raw JSON dict from the ``/info`` endpoint.

    Example::

        info = hgnc_info()
        print(info["response"]["numDoc"])
    """
    return _get_fetcher().info()


def hgnc_fetch(field: str, term: str) -> HGNCFetchedData:
    """Exact-match lookup by any HGNC stored field.

    Returns full gene records.  No wildcard expansion — use
    :func:`hgnc_search` for wildcard queries.

    Args:
        field: HGNC field name (e.g. ``"symbol"``, ``"hgnc_id"``,
            ``"ensembl_gene_id"``, ``"entrez_id"``, ``"uniprot_ids"``).
        term: Exact value to match.

    Returns:
        :class:`HGNCFetchedData` containing :class:`HGNCEntry` records.

    Example::

        data = hgnc_fetch("symbol", "TP53")
        entry = data[0]
        print(entry.hgnc_id, entry.entrez_id, entry.ensembl_gene_id)
    """
    return _get_fetcher().fetch(field, term)


def hgnc_search(query_or_field: str, term: Optional[str] = None) -> HGNCFetchedData:
    """Wildcard / boolean search across HGNC records.

    Returns lightweight summaries (``hgnc_id``, ``symbol``, ``score``).
    Use :func:`hgnc_fetch` to retrieve full records.

    Args:
        query_or_field: Full Solr query string, OR a field name when *term*
            is also given.
        term: Search term for the given field (supports ``*`` and ``?``).

    Returns:
        :class:`HGNCFetchedData` with ``is_search=True``.

    Example::

        # All approved TP53 family members
        hits = hgnc_search("symbol", "TP53*")
        print(hits.symbols())

        # Boolean query
        hits = hgnc_search("status:Approved+AND+locus_group:non-coding+RNA")
    """
    return _get_fetcher().search(query_or_field, term)


def hgnc_fetch_by_symbol(symbol: str) -> HGNCFetchedData:
    """Fetch a gene entry by its approved HGNC symbol.

    Args:
        symbol: Approved gene symbol (e.g. ``"TP53"``, ``"BRCA1"``).

    Returns:
        :class:`HGNCFetchedData` with the matching gene entry (usually
        one record; zero if the symbol is not found).

    Example::

        data = hgnc_fetch_by_symbol("EGFR")
        entry = data[0]
        print(entry.name)  # "epidermal growth factor receptor"
    """
    return _get_fetcher().fetch("symbol", symbol)


def hgnc_fetch_by_hgnc_id(hgnc_id: str) -> HGNCFetchedData:
    """Fetch a gene entry by its HGNC ID.

    Args:
        hgnc_id: HGNC identifier in the form ``"HGNC:NNNN"``
            (e.g. ``"HGNC:11998"`` for TP53).

    Returns:
        :class:`HGNCFetchedData` with the matching gene entry.

    Example::

        data = hgnc_fetch_by_hgnc_id("HGNC:11998")
        print(data[0].symbol)  # "TP53"
    """
    return _get_fetcher().fetch("hgnc_id", hgnc_id)


def hgnc_fetch_by_entrez_id(entrez_id: str) -> HGNCFetchedData:
    """Fetch a gene entry by NCBI Entrez Gene ID.

    Args:
        entrez_id: NCBI Gene ID as a string (e.g. ``"7157"`` for TP53).

    Returns:
        :class:`HGNCFetchedData` with the matching gene entry.

    Example::

        data = hgnc_fetch_by_entrez_id("7157")
        print(data[0].symbol)  # "TP53"
    """
    return _get_fetcher().fetch("entrez_id", entrez_id)


def hgnc_fetch_by_ensembl_id(ensembl_id: str) -> HGNCFetchedData:
    """Fetch a gene entry by Ensembl stable gene ID.

    Args:
        ensembl_id: Ensembl gene ID (e.g. ``"ENSG00000141510"``).

    Returns:
        :class:`HGNCFetchedData` with the matching gene entry.

    Example::

        data = hgnc_fetch_by_ensembl_id("ENSG00000141510")
        print(data[0].symbol)  # "TP53"
    """
    return _get_fetcher().fetch("ensembl_gene_id", ensembl_id)


def hgnc_fetch_by_uniprot_id(uniprot_id: str) -> HGNCFetchedData:
    """Fetch a gene entry by UniProt accession.

    Args:
        uniprot_id: UniProt accession (e.g. ``"P04637"``).

    Returns:
        :class:`HGNCFetchedData` with the matching gene entry.

    Example::

        data = hgnc_fetch_by_uniprot_id("P04637")
        print(data[0].symbol)  # "TP53"
    """
    return _get_fetcher().fetch("uniprot_ids", uniprot_id)


def hgnc_fetch_by_refseq(refseq_accession: str) -> HGNCFetchedData:
    """Fetch a gene entry by RefSeq accession.

    Args:
        refseq_accession: RefSeq accession (e.g. ``"NM_000546"``).

    Returns:
        :class:`HGNCFetchedData` with the matching gene entry.

    Example::

        data = hgnc_fetch_by_refseq("NM_000546")
        print(data[0].symbol)  # "TP53"
    """
    return _get_fetcher().fetch("refseq_accession", refseq_accession)


def hgnc_search_symbol(query: str) -> HGNCFetchedData:
    """Search HGNC gene symbols using wildcard patterns.

    Returns lightweight summaries; use :func:`hgnc_fetch_by_symbol` for
    full records once you have exact symbols.

    Args:
        query: Symbol query supporting ``*`` (any chars) and ``?`` (one char).
            Examples: ``"ZNF*"``, ``"BRCA?"``

    Returns:
        :class:`HGNCFetchedData` with ``is_search=True``.

    Example::

        hits = hgnc_search_symbol("TP53*")
        print(hits.symbols())
        # ['TP53', 'TP53AIP1', 'TP53BP1', 'TP53BP2', ...]
    """
    return _get_fetcher().search("symbol", query)
