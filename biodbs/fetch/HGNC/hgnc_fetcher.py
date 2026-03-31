"""HGNC REST API fetcher."""

import logging
from typing import Optional
from urllib.parse import quote

from biodbs.data.HGNC.data import HGNCFetchedData
from biodbs.data.HGNC._data_model import HGNC_SEARCHABLE_FIELDS
from biodbs.exceptions import raise_for_status, APIValidationError
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

logger = logging.getLogger(__name__)

_BASE_URL = "https://rest.genenames.org"
_HOST = "rest.genenames.org"
_HEADERS = {"Accept": "application/json"}

# Register HGNC's stated rate limit with the global limiter.
get_rate_limiter().set_rate(_HOST, 10)


class HGNC_Fetcher:
    """Fetcher for the HGNC REST API (rest.genenames.org).

    The HGNC (HUGO Gene Nomenclature Committee) REST API provides authoritative
    human gene nomenclature data: approved symbols, names, aliases, previous
    symbols, and cross-references to Ensembl, NCBI Gene, UniProt, OMIM, etc.

    Three endpoints are exposed:

    - **info** — service metadata (last update, document count, field lists).
    - **fetch** — exact-match lookup by any stored field; returns full records.
    - **search** — wildcard / boolean query; returns lightweight summaries
      (``hgnc_id``, ``symbol``, ``score`` only).

    Rate limit: 10 requests per second (enforced automatically).

    Example::

        fetcher = HGNC_Fetcher()

        # Exact lookup by symbol
        data = fetcher.fetch("symbol", "TP53")
        entry = data[0]          # HGNCEntry
        print(entry.hgnc_id)     # "HGNC:11998"
        print(entry.entrez_id)   # "7157"

        # Wildcard search
        hits = fetcher.search("symbol", "ZNF*")
        print(hits.num_found)    # many zinc-finger genes

        # Service metadata
        info = fetcher.info()
        print(info["response"]["numDoc"])
    """

    def info(self) -> dict:
        """Retrieve HGNC service metadata.

        Returns the raw parsed JSON dict which contains:
            - ``lastModified``: timestamp of last database update
            - ``numDoc``: total number of records
            - ``searchableFields``: list of fields that can be queried
            - ``storedFields``: list of fields returned by fetch

        Returns:
            Raw JSON dict from ``/info``.

        Raises:
            APIError: On HTTP errors.
        """
        url = f"{_BASE_URL}/info"
        response = request_with_retry(url, headers=_HEADERS)
        raise_for_status(response, "HGNC", url=url)
        return response.json()

    def fetch(self, field: str, term: str) -> HGNCFetchedData:
        """Exact-match lookup by any stored field.

        Returns full gene records for all entries where *field* exactly
        equals *term*.  No wildcard expansion is performed.

        Args:
            field: HGNC stored field name (e.g. ``"symbol"``, ``"hgnc_id"``,
                ``"ensembl_gene_id"``, ``"entrez_id"``, ``"uniprot_ids"``).
            term: Exact value to match.

        Returns:
            :class:`HGNCFetchedData` containing full :class:`HGNCEntry` records.

        Raises:
            APIValidationError: If the field name is not recognised (HTTP 400).
            APIError: On other HTTP errors.

        Example::

            data = fetcher.fetch("symbol", "BRCA1")
            print(data[0].ensembl_gene_id)  # ENSG00000012048
        """
        encoded_term = quote(str(term), safe="")
        url = f"{_BASE_URL}/fetch/{field}/{encoded_term}"
        logger.debug("HGNC fetch: %s", url)
        response = request_with_retry(url, headers=_HEADERS)
        raise_for_status(response, "HGNC", url=url)
        return HGNCFetchedData(response.json(), is_search=False)

    def search(self, query_or_field: str, term: Optional[str] = None) -> HGNCFetchedData:
        """Wildcard / boolean search.

        Two calling styles are supported:

        1. **Free-form query**: ``search("symbol:ZNF* AND status:Approved")``
        2. **Field + term**: ``search("symbol", "ZNF*")``

        Wildcard characters:
            - ``*`` — zero or more characters
            - ``?`` — exactly one character

        Boolean operators: ``AND``, ``OR``, ``NOT``
        (URL-encoded as ``+AND+``, ``+OR+``, ``+NOT+`` internally).

        Note:
            Search responses contain only ``hgnc_id``, ``symbol``, and
            ``score``.  Use :meth:`fetch` to retrieve complete records.

        Args:
            query_or_field: A full Solr query string, OR a field name when
                *term* is also provided.
            term: The search term for the given field.  Leave ``None`` when
                passing a full query string as the first argument.

        Returns:
            :class:`HGNCFetchedData` with ``is_search=True``; items are plain
            dicts with ``hgnc_id``, ``symbol``, ``score``.

        Raises:
            APIValidationError: On an invalid query (HTTP 400).
            APIError: On other HTTP errors.

        Example::

            # All ZNF genes
            hits = fetcher.search("symbol", "ZNF*")

            # Approved genes on chromosome 17
            hits = fetcher.search("status:Approved+AND+location:17*")
        """
        if term is not None:
            if query_or_field not in HGNC_SEARCHABLE_FIELDS:
                logger.warning(
                    "Field %r may not be searchable. "
                    "Valid searchable fields: %s",
                    query_or_field,
                    sorted(HGNC_SEARCHABLE_FIELDS),
                )
            encoded_term = quote(str(term), safe="*?")
            url = f"{_BASE_URL}/search/{query_or_field}/{encoded_term}"
        else:
            encoded_query = quote(str(query_or_field), safe="*?:+")
            url = f"{_BASE_URL}/search/{encoded_query}"

        logger.debug("HGNC search: %s", url)
        response = request_with_retry(url, headers=_HEADERS)
        raise_for_status(response, "HGNC", url=url)
        return HGNCFetchedData(response.json(), is_search=True)
