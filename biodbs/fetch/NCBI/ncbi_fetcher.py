"""NCBI Datasets API fetcher following the standardized pattern."""

from typing import Dict, Any, List, Optional, Union
import logging
import os

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.fetch._rate_limit import request_with_retry, get_rate_limiter
from biodbs.data.NCBI._data_model import (
    NCBIBase,
    NCBIGeneEndpoint,
    NCBITaxonomyEndpoint,
    NCBIGenomeEndpoint,
    NCBIVersionEndpoint,
    GeneDatasetRequest,
    GeneContentType,
)
from biodbs.data.NCBI.data import (
    NCBIGeneFetchedData,
    NCBITaxonomyFetchedData,
    NCBIGenomeFetchedData,
)

logger = logging.getLogger(__name__)


class NCBI_APIConfig(BaseAPIConfig):
    """API configuration for NCBI Datasets.

    Supports API key authentication for higher rate limits:
        - Without API key: 5 requests per second
        - With API key: 10 requests per second

    API key can be provided via:
        - Constructor parameter
        - Environment variable: NCBI_API_KEY
    """

    # Host identifier for rate limiting
    HOST = "api.ncbi.nlm.nih.gov"

    # Rate limits (requests per second)
    RATE_LIMIT_WITH_KEY = 10
    RATE_LIMIT_WITHOUT_KEY = 5

    def __init__(
        self,
        base_url: str = NCBIBase.BASE.value,
        api_key: Optional[str] = None,
    ):
        super().__init__()
        self._base_url = base_url
        self._api_key = api_key or os.environ.get("NCBI_API_KEY")

        # Register rate limit with global limiter
        self._register_rate_limit()

    def _register_rate_limit(self):
        """Register rate limit with global rate limiter."""
        limiter = get_rate_limiter()
        rate = self.RATE_LIMIT_WITH_KEY if self._api_key else self.RATE_LIMIT_WITHOUT_KEY
        limiter.set_rate(self.HOST, rate)

    def get_url(self, endpoint: str) -> str:
        """Build full URL for an endpoint."""
        return f"{self._base_url}/{endpoint}"

    def get_headers(self) -> Dict[str, str]:
        """Get request headers including API key if available."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._api_key:
            headers["api-key"] = self._api_key
        return headers

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self._api_key is not None

    @property
    def rate_limit(self) -> int:
        """Get rate limit based on API key presence."""
        return 10 if self._api_key else 5


class NCBI_Fetcher(BaseDataFetcher):
    """Fetcher for NCBI Datasets API.

    Provides access to NCBI gene, taxonomy, and genome data via the
    Datasets REST API v2.

    Examples::

        fetcher = NCBI_Fetcher()

        # Get gene information by NCBI Gene ID
        genes = fetcher.get_genes_by_id([7157, 672])  # TP53, BRCA1
        print(genes.as_dataframe())

        # Get gene by symbol and taxon
        genes = fetcher.get_genes_by_symbol(["TP53", "BRCA1"], taxon="human")

        # Get taxonomy information
        tax = fetcher.get_taxonomy([9606, 10090])  # Human, mouse
        print(tax.as_dataframe())

        # Translate gene symbols to IDs
        mapping = fetcher.symbol_to_id(["TP53", "BRCA1"], taxon="human")
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize NCBI fetcher.

        Args:
            api_key: NCBI API key for higher rate limits.
                    Can also be set via NCBI_API_KEY environment variable.
        """
        self._api_config = NCBI_APIConfig(api_key=api_key)
        super().__init__(
            self._api_config, NameSpace(GeneDatasetRequest), self._api_config.get_headers()
        )

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API request with rate limiting and automatic retry.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.
            method: HTTP method.
            data: Request body for POST requests.

        Returns:
            JSON response as dictionary.

        Raises:
            ConnectionError: If the request fails after retries.
        """
        url = self._api_config.get_url(endpoint)
        headers = self._api_config.get_headers()

        # Use rate-limited request with retry
        response = request_with_retry(
            url=url,
            method=method,
            params=params,
            headers=headers,
            json=data if method != "GET" else None,
            max_retries=3,
            initial_delay=1.0,
            rate_limit=True,
        )

        if response.status_code != 200:
            raise ConnectionError(
                f"NCBI API request failed. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    # ----- Gene Methods -----

    def get_genes_by_id(
        self,
        gene_ids: List[int],
        returned_content: Optional[str] = None,
        page_size: int = 100,
        query: Optional[str] = None,
        types: Optional[List[str]] = None,
    ) -> NCBIGeneFetchedData:
        """Get gene data reports by NCBI Gene IDs.

        Args:
            gene_ids: List of NCBI Gene IDs (e.g., [7157, 672]).
            returned_content: Content type (COMPLETE, IDS_ONLY, COUNTS_ONLY).
            page_size: Results per page (max 1000).
            query: Additional search query.
            types: Gene type filter (e.g., ["PROTEIN_CODING"]).

        Returns:
            NCBIGeneFetchedData with gene reports.

        Example:
            >>> fetcher = NCBI_Fetcher()
            >>> genes = fetcher.get_genes_by_id([7157, 672])
            >>> print(genes.get_gene_symbols())
            ['TP53', 'BRCA1']
        """
        if not gene_ids:
            return NCBIGeneFetchedData({}, query_ids=[])

        # Build endpoint with gene IDs
        ids_str = ",".join(str(gid) for gid in gene_ids)
        endpoint = NCBIGeneEndpoint.GENE_BY_ID.value.format(gene_ids=ids_str)

        params = {"page_size": page_size}
        if returned_content:
            params["returned_content"] = returned_content
        if query:
            params["query"] = query
        if types:
            params["types"] = types

        data = self._make_request(endpoint, params=params)
        return NCBIGeneFetchedData(data, query_ids=gene_ids)

    def get_genes_by_symbol(
        self,
        symbols: List[str],
        taxon: Union[int, str] = "human",
        returned_content: Optional[str] = None,
        page_size: int = 100,
    ) -> NCBIGeneFetchedData:
        """Get gene data reports by gene symbols and taxon.

        Args:
            symbols: List of gene symbols (e.g., ["TP53", "BRCA1"]).
            taxon: Taxon ID, common name, or scientific name.
            returned_content: Content type.
            page_size: Results per page.

        Returns:
            NCBIGeneFetchedData with gene reports.

        Example:
            >>> fetcher = NCBI_Fetcher()
            >>> genes = fetcher.get_genes_by_symbol(["TP53", "BRCA1"], taxon="human")
            >>> print(genes.to_id_mapping())
            {'TP53': 7157, 'BRCA1': 672}
        """
        if not symbols:
            return NCBIGeneFetchedData({}, query_ids=[])

        symbols_str = ",".join(symbols)
        endpoint = NCBIGeneEndpoint.GENE_BY_SYMBOL.value.format(
            symbols=symbols_str, taxon=str(taxon)
        )

        params = {"page_size": page_size}
        if returned_content:
            params["returned_content"] = returned_content

        data = self._make_request(endpoint, params=params)
        return NCBIGeneFetchedData(data, query_ids=symbols)

    def get_genes_by_accession(
        self,
        accessions: List[str],
        returned_content: Optional[str] = None,
        page_size: int = 100,
    ) -> NCBIGeneFetchedData:
        """Get gene data reports by RefSeq accessions.

        Args:
            accessions: List of RefSeq accessions (e.g., ["NM_000546.6"]).
            returned_content: Content type.
            page_size: Results per page.

        Returns:
            NCBIGeneFetchedData with gene reports.
        """
        if not accessions:
            return NCBIGeneFetchedData({}, query_ids=[])

        acc_str = ",".join(accessions)
        endpoint = NCBIGeneEndpoint.GENE_BY_ACCESSION.value.format(accessions=acc_str)

        params = {"page_size": page_size}
        if returned_content:
            params["returned_content"] = returned_content

        data = self._make_request(endpoint, params=params)
        return NCBIGeneFetchedData(data, query_ids=accessions)

    def get_genes_by_taxon(
        self,
        taxon: Union[int, str],
        query: Optional[str] = None,
        types: Optional[List[str]] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
    ) -> NCBIGeneFetchedData:
        """Get gene data reports by taxon.

        Args:
            taxon: Taxon ID, common name, or scientific name.
            query: Search query for gene name/symbol/description.
            types: Gene type filter.
            page_size: Results per page.
            page_token: Token for pagination.

        Returns:
            NCBIGeneFetchedData with gene reports.

        Example:
            >>> fetcher = NCBI_Fetcher()
            >>> genes = fetcher.get_genes_by_taxon("human", query="kinase")
        """
        endpoint = NCBIGeneEndpoint.GENE_BY_TAXON.value.format(taxon=str(taxon))

        params = {"page_size": page_size}
        if query:
            params["query"] = query
        if types:
            params["types"] = types
        if page_token:
            params["page_token"] = page_token

        data = self._make_request(endpoint, params=params)
        return NCBIGeneFetchedData(data, query_ids=[taxon])

    # ----- Taxonomy Methods -----

    def get_taxonomy(
        self,
        taxons: List[Union[int, str]],
        page_size: int = 100,
    ) -> NCBITaxonomyFetchedData:
        """Get taxonomy data reports.

        Args:
            taxons: List of taxonomy IDs or names.
            page_size: Results per page.

        Returns:
            NCBITaxonomyFetchedData with taxonomy reports.

        Example:
            >>> fetcher = NCBI_Fetcher()
            >>> tax = fetcher.get_taxonomy([9606, 10090])
            >>> print(tax.as_dataframe())
        """
        if not taxons:
            return NCBITaxonomyFetchedData({}, query_taxons=[])

        taxons_str = ",".join(str(t) for t in taxons)
        endpoint = NCBITaxonomyEndpoint.TAXONOMY_BY_TAXON.value.format(taxons=taxons_str)

        params = {"page_size": page_size}
        data = self._make_request(endpoint, params=params)
        return NCBITaxonomyFetchedData(data, query_taxons=taxons)

    # ----- Genome Methods -----

    def get_genome_by_accession(
        self,
        accessions: List[str],
        page_size: int = 100,
    ) -> NCBIGenomeFetchedData:
        """Get genome assembly data reports by accession.

        Args:
            accessions: List of assembly accessions (e.g., ["GCF_000001405.40"]).
            page_size: Results per page.

        Returns:
            NCBIGenomeFetchedData with genome reports.

        Example:
            >>> fetcher = NCBI_Fetcher()
            >>> genomes = fetcher.get_genome_by_accession(["GCF_000001405.40"])
        """
        if not accessions:
            return NCBIGenomeFetchedData({}, query_accessions=[])

        acc_str = ",".join(accessions)
        endpoint = NCBIGenomeEndpoint.GENOME_BY_ACCESSION.value.format(accessions=acc_str)

        params = {"page_size": page_size}
        data = self._make_request(endpoint, params=params)
        return NCBIGenomeFetchedData(data, query_accessions=accessions)

    def get_genome_by_taxon(
        self,
        taxon: Union[int, str],
        page_size: int = 100,
        page_token: Optional[str] = None,
        reference_only: bool = False,
        assembly_source: Optional[str] = None,
    ) -> NCBIGenomeFetchedData:
        """Get genome assembly data reports by taxon.

        Args:
            taxon: Taxon ID, common name, or scientific name.
            page_size: Results per page.
            page_token: Token for pagination.
            reference_only: If True, only return reference genomes.
            assembly_source: Filter by source ("refseq", "genbank", "all").

        Returns:
            NCBIGenomeFetchedData with genome reports.
        """
        endpoint = NCBIGenomeEndpoint.GENOME_BY_TAXON.value.format(taxon=str(taxon))

        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        if reference_only:
            params["filters.reference_only"] = "true"
        if assembly_source:
            params["filters.assembly_source"] = assembly_source

        data = self._make_request(endpoint, params=params)
        return NCBIGenomeFetchedData(data, query_accessions=[str(taxon)])

    # ----- Version Methods -----

    def get_version(self) -> str:
        """Get NCBI Datasets API version.

        Returns:
            Version string.
        """
        endpoint = NCBIVersionEndpoint.VERSION.value
        data = self._make_request(endpoint)
        return data.get("version", "unknown")

    # ----- Convenience Methods for ID Translation -----

    def symbol_to_id(
        self,
        symbols: List[str],
        taxon: Union[int, str] = "human",
    ) -> Dict[str, int]:
        """Convert gene symbols to NCBI Gene IDs.

        Args:
            symbols: List of gene symbols.
            taxon: Taxon for the genes.

        Returns:
            Dictionary mapping symbols to gene IDs.

        Example:
            >>> fetcher = NCBI_Fetcher()
            >>> mapping = fetcher.symbol_to_id(["TP53", "BRCA1"])
            >>> print(mapping)
            {'TP53': 7157, 'BRCA1': 672}
        """
        genes = self.get_genes_by_symbol(symbols, taxon=taxon)
        return genes.to_id_mapping()

    def id_to_symbol(
        self,
        gene_ids: List[int],
    ) -> Dict[int, str]:
        """Convert NCBI Gene IDs to gene symbols.

        Args:
            gene_ids: List of NCBI Gene IDs.

        Returns:
            Dictionary mapping gene IDs to symbols.

        Example:
            >>> fetcher = NCBI_Fetcher()
            >>> mapping = fetcher.id_to_symbol([7157, 672])
            >>> print(mapping)
            {7157: 'TP53', 672: 'BRCA1'}
        """
        genes = self.get_genes_by_id(gene_ids)
        return genes.to_symbol_mapping()

    def get_gene_info(
        self,
        identifiers: List[Union[int, str]],
        taxon: Union[int, str] = "human",
    ) -> NCBIGeneFetchedData:
        """Get gene information by mixed identifiers (IDs or symbols).

        Automatically detects whether input is gene IDs or symbols and
        routes to the appropriate endpoint.

        Args:
            identifiers: List of gene IDs (int) or symbols (str).
            taxon: Taxon for symbol lookups.

        Returns:
            NCBIGeneFetchedData with gene reports.
        """
        # Separate IDs and symbols
        gene_ids = []
        symbols = []

        for ident in identifiers:
            if isinstance(ident, int):
                gene_ids.append(ident)
            elif isinstance(ident, str):
                # Try to parse as integer
                try:
                    gene_ids.append(int(ident))
                except ValueError:
                    symbols.append(ident)

        # Fetch by both methods
        result = NCBIGeneFetchedData({}, query_ids=identifiers)

        if gene_ids:
            id_data = self.get_genes_by_id(gene_ids)
            result += id_data

        if symbols:
            symbol_data = self.get_genes_by_symbol(symbols, taxon=taxon)
            result += symbol_data

        return result


if __name__ == "__main__":
    fetcher = NCBI_Fetcher()

    # Test version
    print("=== API Version ===")
    version = fetcher.get_version()
    print(f"Version: {version}")

    # Test gene by ID
    print("\n=== Gene by ID ===")
    genes = fetcher.get_genes_by_id([7157, 672])
    print(genes.summary())

    # Test gene by symbol
    print("\n=== Gene by Symbol ===")
    genes = fetcher.get_genes_by_symbol(["TP53", "BRCA1"], taxon="human")
    print(f"Found {len(genes)} genes")
    print(f"ID mapping: {genes.to_id_mapping()}")

    # Test taxonomy
    print("\n=== Taxonomy ===")
    tax = fetcher.get_taxonomy([9606, 10090])
    print(tax.as_dataframe())
