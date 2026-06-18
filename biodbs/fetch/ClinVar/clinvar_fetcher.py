"""ClinVar E-utilities fetcher.

ClinVar is part of NCBI's Entrez system and is accessed via the same
E-utilities base URL used by all Entrez databases::

    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/

Supported endpoints:

- **esearch** — find variation UIDs matching a query.
- **esummary** — retrieve document summaries (JSON) for a list of UIDs.
- **efetch** — download full XML records (VCV or RCV format).
- **elink** — cross-reference to PubMed, MedGen, etc.

Rate limits
-----------
Without an API key: **3 requests/second**.
With an API key:    **10 requests/second**.

The same ``NCBI_API_KEY`` environment variable used by the NCBI Datasets
fetcher is accepted here.  Obtain a key from your NCBI account settings.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional, Union

from biodbs.data.ClinVar.data import ClinVarFetchedData
from biodbs.exceptions import raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

logger = logging.getLogger(__name__)

_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_HOST = "eutils.ncbi.nlm.nih.gov"

_RATE_WITH_KEY = 10
_RATE_WITHOUT_KEY = 3

# Tool / email identifiers recommended by NCBI for programmatic access.
_TOOL = "biodbs"
_EMAIL = "biodbs@users.noreply"


class ClinVar_Fetcher:
    """Fetcher for the ClinVar E-utilities API.

    Wraps the four E-utility endpoints that ClinVar supports (esearch,
    esummary, efetch, elink) with rate limiting and optional API key
    authentication.

    Args:
        api_key: NCBI API key for 10 req/s (vs. 3 req/s without).
            Falls back to the ``NCBI_API_KEY`` environment variable.

    Example::

        fetcher = ClinVar_Fetcher()

        # Search for all pathogenic BRCA1 variants
        uids = fetcher.search("BRCA1[gene] AND pathogenic[clnsig]")

        # Fetch summaries for the first 10
        data = fetcher.fetch_summary(uids[:10])
        print(data.as_dataframe())

        # One-step helper
        data = fetcher.search_gene("TP53", retmax=100)
        for v in data:
            print(v.accession, v.clinical_significance)
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ.get("NCBI_API_KEY")
        rate = _RATE_WITH_KEY if self._api_key else _RATE_WITHOUT_KEY
        get_rate_limiter().set_rate(_HOST, rate)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _base_params(self) -> dict:
        """Common parameters attached to every E-utility request."""
        params: dict = {"tool": _TOOL, "email": _EMAIL}
        if self._api_key:
            params["api_key"] = self._api_key
        return params

    def _get(self, endpoint: str, params: dict) -> object:
        """Execute a GET request against *endpoint* with merged base params."""
        url = f"{_BASE_URL}/{endpoint}"
        merged = {**self._base_params(), **params}
        logger.debug("ClinVar GET %s params=%s", url, merged)
        response = request_with_retry(url, params=merged)
        raise_for_status(response, "ClinVar", url=url)
        return response

    # ------------------------------------------------------------------
    # esearch
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        retmax: int = 500,
        retstart: int = 0,
    ) -> List[str]:
        """Find ClinVar variation UIDs matching an Entrez query.

        Uses the same query language as the ClinVar website, so you can
        test a query interactively before automating it.

        Common field tags:

        - ``BRCA1[gene]`` — variants in a specific gene
        - ``pathogenic[clnsig]`` — by clinical significance
        - ``single_gene[prop]`` — single-gene variants only
        - ``"Breast cancer"[dis]`` — by associated disease

        Args:
            query: Entrez query string (e.g.
                ``"BRCA1[gene] AND pathogenic[clnsig]"``).
            retmax: Maximum UIDs to return (default 500; max 10 000).
            retstart: Zero-based offset for pagination.

        Returns:
            List of variation UID strings.

        Example::

            uids = fetcher.search("TP53[gene] AND pathogenic[clnsig]",
                                  retmax=200)
        """
        response = self._get(
            "esearch.fcgi",
            {
                "db": "clinvar",
                "term": query,
                "retmax": retmax,
                "retstart": retstart,
                "retmode": "json",
            },
        )
        data = response.json()
        esearch_result = data.get("esearchresult", {})
        return esearch_result.get("idlist", [])

    def count(self, query: str) -> int:
        """Return the total number of ClinVar records matching *query*.

        Performs an esearch with ``retmax=0`` so no IDs are transferred.

        Args:
            query: Entrez query string.

        Returns:
            Integer count of matching records.
        """
        response = self._get(
            "esearch.fcgi",
            {"db": "clinvar", "term": query, "retmax": 0, "retmode": "json"},
        )
        result = response.json().get("esearchresult", {})
        return int(result.get("count", 0))

    # ------------------------------------------------------------------
    # esummary
    # ------------------------------------------------------------------

    def fetch_summary(
        self,
        ids: List[Union[str, int]],
        total_count: int = 0,
    ) -> ClinVarFetchedData:
        """Retrieve document summaries for a list of variation UIDs.

        Calls ``esummary`` with ``retmode=json`` to obtain structured data
        including clinical significance, gene associations, conditions,
        and genomic coordinates.

        Args:
            ids: ClinVar variation UIDs (integers or strings).
            total_count: Optional total hit count from a preceding esearch,
                stored on the returned object for reference.

        Returns:
            :class:`ClinVarFetchedData` with one :class:`ClinVarVariant`
            per UID.

        Raises:
            APIError: On HTTP errors.

        Example::

            data = fetcher.fetch_summary(["65533", "14206"])
            for v in data:
                print(v.title, v.clinical_significance)
        """
        if not ids:
            return ClinVarFetchedData({"result": {"uids": []}}, total_count=0)

        id_str = ",".join(str(i) for i in ids)
        response = self._get(
            "esummary.fcgi",
            {"db": "clinvar", "id": id_str, "retmode": "json"},
        )
        return ClinVarFetchedData(response.json(), total_count=total_count)

    # ------------------------------------------------------------------
    # efetch (XML)
    # ------------------------------------------------------------------

    def fetch_vcv(self, accession: str) -> str:
        """Retrieve the full VCV XML record for a variation.

        Args:
            accession: VCV accession with or without version
                (e.g. ``"VCV000014206"`` or ``"VCV000014206.3"``).

        Returns:
            Raw XML string.

        Example::

            xml = fetcher.fetch_vcv("VCV000014206")
        """
        response = self._get(
            "efetch.fcgi",
            {"db": "clinvar", "rettype": "vcv", "id": accession},
        )
        return response.text

    def fetch_rcv(self, accession: str) -> str:
        """Retrieve the full RCV XML record for a variation-condition pair.

        Args:
            accession: RCV accession with or without version
                (e.g. ``"RCV000000606"`` or ``"RCV000000606.3"``).

        Returns:
            Raw XML string.

        Example::

            xml = fetcher.fetch_rcv("RCV000000606")
        """
        response = self._get(
            "efetch.fcgi",
            {"db": "clinvar", "rettype": "clinvarset", "id": accession},
        )
        return response.text

    # ------------------------------------------------------------------
    # elink
    # ------------------------------------------------------------------

    def link_to_pubmed(self, variation_id: Union[str, int]) -> List[str]:
        """Return PubMed UIDs linked to a ClinVar variation.

        Args:
            variation_id: ClinVar variation UID.

        Returns:
            List of PubMed UID strings.
        """
        response = self._get(
            "elink.fcgi",
            {
                "dbfrom": "clinvar",
                "db": "pubmed",
                "id": str(variation_id),
                "retmode": "json",
            },
        )
        data = response.json()
        pmids: List[str] = []
        for linkset in data.get("linksets", []):
            for lsd in linkset.get("linksetdbs", []):
                if lsd.get("dbto") == "pubmed":
                    pmids.extend(str(uid) for uid in lsd.get("links", []))
        return pmids

    # ------------------------------------------------------------------
    # High-level convenience
    # ------------------------------------------------------------------

    def search_gene(
        self,
        gene_symbol: str,
        single_gene: bool = True,
        retmax: int = 500,
        clinical_significance: Optional[str] = None,
    ) -> ClinVarFetchedData:
        """Search for variants in a gene and return summaries in one step.

        Args:
            gene_symbol: HGNC gene symbol (e.g. ``"BRCA1"``).
            single_gene: If ``True`` (default), restrict to variants
                assigned to a single gene (``single_gene[prop]``).
            retmax: Maximum number of variants to return.
            clinical_significance: Optional filter, e.g. ``"pathogenic"``,
                ``"likely pathogenic"``, ``"benign"``.  Maps to the
                ``[clnsig]`` Entrez field tag.

        Returns:
            :class:`ClinVarFetchedData` ready to iterate or convert.

        Example::

            data = fetcher.search_gene("TP53", retmax=200,
                                       clinical_significance="pathogenic")
            print(data.as_dataframe()[["accession", "title",
                                       "clinical_significance"]])
        """
        parts = [f"{gene_symbol}[gene]"]
        if single_gene:
            parts.append("single_gene[prop]")
        if clinical_significance:
            parts.append(f"{clinical_significance}[clnsig]")

        query = " AND ".join(parts)
        total = self.count(query)
        uids = self.search(query, retmax=retmax)
        return self.fetch_summary(uids, total_count=total)

    def search_condition(
        self,
        condition: str,
        retmax: int = 500,
        clinical_significance: Optional[str] = None,
    ) -> ClinVarFetchedData:
        """Search for variants associated with a disease/condition.

        Args:
            condition: Disease or condition name (e.g. ``"Breast cancer"``).
            retmax: Maximum number of variants to return.
            clinical_significance: Optional significance filter.

        Returns:
            :class:`ClinVarFetchedData`.

        Example::

            data = fetcher.search_condition("Lynch syndrome", retmax=100)
        """
        parts = [f'"{condition}"[dis]']
        if clinical_significance:
            parts.append(f"{clinical_significance}[clnsig]")

        query = " AND ".join(parts)
        total = self.count(query)
        uids = self.search(query, retmax=retmax)
        return self.fetch_summary(uids, total_count=total)
