"""UniProt REST API fetcher following the standardized pattern."""

from typing import Dict, Any, List, Optional, Union
import logging
import time
import re

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.fetch._rate_limit import request_with_retry, get_rate_limiter
from biodbs.exceptions import raise_for_status
from biodbs.data.uniprot._data_model import (
    UniProtBase,
    UniProtEndpoint,
    UniProtSearchRequest,
)
from biodbs.data.uniprot.data import (
    UniProtFetchedData,
    UniProtSearchResult,
)

logger = logging.getLogger(__name__)


class UniProt_APIConfig(BaseAPIConfig):
    """API configuration for UniProt REST API.

    UniProt has rate limits but they are generally generous for
    programmatic access. The API supports various output formats.
    """

    # Host identifier for rate limiting
    HOST = "rest.uniprot.org"

    # Rate limit (requests per second) - UniProt is relatively generous
    RATE_LIMIT = 10

    def __init__(
        self,
        base_url: str = UniProtBase.BASE.value,
    ):
        super().__init__()
        self._base_url = base_url

        # Register rate limit with global limiter
        self._register_rate_limit()

    def _register_rate_limit(self):
        """Register rate limit with global rate limiter."""
        limiter = get_rate_limiter()
        limiter.set_rate(self.HOST, self.RATE_LIMIT)

    def get_url(self, endpoint: str) -> str:
        """Build full URL for an endpoint."""
        return f"{self._base_url}/{endpoint}"

    def get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Accept": "application/json",
        }


class UniProt_Fetcher(BaseDataFetcher):
    """Fetcher for UniProt REST API.

    Provides access to UniProtKB protein data including:

    - Entry retrieval by accession
    - Search by query
    - ID mapping between databases
    - Batch retrieval

    Example:
        ```python
        fetcher = UniProt_Fetcher()

        # Get protein by accession
        entry = fetcher.get_entry("P05067")  # APP protein
        print(entry.entries[0].protein_name)

        # Search for proteins
        results = fetcher.search("gene:TP53 AND organism_id:9606")
        print(results.as_dataframe())

        # Get multiple entries
        entries = fetcher.get_entries(["P05067", "P04637", "P00533"])

        # Map IDs
        mapping = fetcher.map_ids(
            ["P05067", "P04637"],
            from_db="UniProtKB_AC-ID",
            to_db="GeneID"
        )
        ```
    """

    def __init__(self):
        """Initialize UniProt fetcher."""
        self._api_config = UniProt_APIConfig()
        super().__init__(
            self._api_config, NameSpace(UniProtSearchRequest), self._api_config.get_headers()
        )

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        accept: str = "application/json",
    ) -> Any:
        """Make an API request with rate limiting and automatic retry.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.
            method: HTTP method.
            data: Form data for POST requests.
            accept: Accept header value.

        Returns:
            JSON response or text depending on accept header.

        Raises:
            ConnectionError: If the request fails after retries.
        """
        url = self._api_config.get_url(endpoint)
        headers = {"Accept": accept}

        if method == "POST" and data:
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        response = request_with_retry(
            url=url,
            method=method,
            params=params,
            headers=headers,
            data=data,
            max_retries=3,
            initial_delay=1.0,
            rate_limit=True,
        )

        if response.status_code not in (200, 303):
            raise_for_status(response, "UniProt", url=url)

        # Handle redirect for ID mapping
        if response.status_code == 303:
            return {"redirect": response.headers.get("Location")}

        if "application/json" in accept:
            return response.json()
        return response.text

    def _extract_next_cursor(self, response_headers: Dict) -> Optional[str]:
        """Extract next cursor from Link header.

        Args:
            response_headers: Response headers.

        Returns:
            Next cursor value or None.
        """
        link = response_headers.get("Link", "")
        if 'rel="next"' in link:
            match = re.search(r'cursor=([^&>]+)', link)
            if match:
                return match.group(1)
        return None

    # ----- Entry Retrieval Methods -----

    def get_entry(
        self,
        accession: str,
        fields: Optional[str] = None,
    ) -> UniProtFetchedData:
        """Get a UniProt entry by accession.

        Args:
            accession: UniProt accession (e.g., "P05067").
            fields: Comma-separated list of fields to return.

        Returns:
            UniProtFetchedData with the entry.

        Example:
            ```python
            fetcher = UniProt_Fetcher()
            entry = fetcher.get_entry("P05067")
            print(entry.entries[0].protein_name)
            ```
        """
        endpoint = UniProtEndpoint.ENTRY.value.format(accession=accession)
        params = {}
        if fields:
            params["fields"] = fields

        data = self._make_request(endpoint, params=params)
        return UniProtFetchedData(data, query_ids=[accession])

    def get_entries(
        self,
        accessions: List[str],
        fields: Optional[str] = None,
    ) -> UniProtFetchedData:
        """Get multiple UniProt entries by accessions.

        Args:
            accessions: List of UniProt accessions.
            fields: Comma-separated list of fields to return.

        Returns:
            UniProtFetchedData with all entries.

        Example:
            ```python
            fetcher = UniProt_Fetcher()
            entries = fetcher.get_entries(["P05067", "P04637", "P00533"])
            print(entries.get_gene_names())
            ```
        """
        if not accessions:
            return UniProtFetchedData([], query_ids=[])

        # Use search with accession query for batch retrieval
        accession_query = " OR ".join(f"accession:{acc}" for acc in accessions)
        return self.search(accession_query, fields=fields, size=len(accessions))

    # ----- Search Methods -----

    def search(
        self,
        query: str,
        fields: Optional[str] = None,
        sort: Optional[str] = None,
        size: int = 25,
        include_isoform: bool = False,
        cursor: Optional[str] = None,
    ) -> UniProtSearchResult:
        """Search UniProtKB.

        Args:
            query: Search query (e.g., "gene:TP53 AND organism_id:9606").
            fields: Comma-separated list of fields to return.
            sort: Sort field and direction (e.g., "accession desc").
            size: Number of results per page (max 500).
            include_isoform: Include isoforms in results.
            cursor: Cursor for pagination.

        Returns:
            UniProtSearchResult with matching entries.

        Example:
            ```python
            fetcher = UniProt_Fetcher()
            results = fetcher.search("gene:BRCA1 AND reviewed:true")
            print(results.as_dataframe())
            ```
        """
        params = {
            "query": query,
            "size": min(size, 500),
        }
        if fields:
            params["fields"] = fields
        if sort:
            params["sort"] = sort
        if include_isoform:
            params["includeIsoform"] = "true"
        if cursor:
            params["cursor"] = cursor

        response = request_with_retry(
            url=self._api_config.get_url(UniProtEndpoint.SEARCH.value),
            method="GET",
            params=params,
            headers={"Accept": "application/json"},
            max_retries=3,
            rate_limit=True,
        )

        if response.status_code != 200:
            raise_for_status(response, "UniProt", url=self._api_config.get_url(UniProtEndpoint.SEARCH.value))

        # Extract next cursor from headers
        next_cursor = self._extract_next_cursor(dict(response.headers))

        data = response.json()
        return UniProtSearchResult(data, query=query, next_cursor=next_cursor)

    def search_all(
        self,
        query: str,
        fields: Optional[str] = None,
        sort: Optional[str] = None,
        max_results: int = 10000,
        include_isoform: bool = False,
    ) -> UniProtFetchedData:
        """Search and retrieve all results with pagination.

        Args:
            query: Search query.
            fields: Fields to return.
            sort: Sort field and direction.
            max_results: Maximum results to retrieve.
            include_isoform: Include isoforms.

        Returns:
            UniProtFetchedData with all matching entries.
        """
        all_entries = []
        cursor = None
        retrieved = 0

        while retrieved < max_results:
            batch_size = min(500, max_results - retrieved)
            result = self.search(
                query=query,
                fields=fields,
                sort=sort,
                size=batch_size,
                include_isoform=include_isoform,
                cursor=cursor,
            )

            all_entries.extend(result.entries)
            retrieved += len(result.entries)

            if not result.has_next or len(result.entries) == 0:
                break

            cursor = result.next_cursor

        # Create combined result
        combined = UniProtFetchedData([], query_ids=[query])
        combined.entries = all_entries
        combined.total_count = len(all_entries)
        return combined

    # ----- Convenience Search Methods -----

    def search_by_gene(
        self,
        gene_name: str,
        organism: Optional[Union[int, str]] = None,
        reviewed_only: bool = False,
        size: int = 25,
    ) -> UniProtSearchResult:
        """Search by gene name.

        Args:
            gene_name: Gene name to search.
            organism: Organism tax ID or name.
            reviewed_only: Only return reviewed entries.
            size: Results per page.

        Returns:
            UniProtSearchResult with matching entries.

        Example:
            ```python
            fetcher = UniProt_Fetcher()
            results = fetcher.search_by_gene("TP53", organism=9606, reviewed_only=True)
            ```
        """
        query_parts = [f"gene:{gene_name}"]
        if organism:
            if isinstance(organism, int):
                query_parts.append(f"organism_id:{organism}")
            else:
                query_parts.append(f"organism_name:{organism}")
        if reviewed_only:
            query_parts.append("reviewed:true")

        query = " AND ".join(query_parts)
        return self.search(query, size=size)

    def search_by_organism(
        self,
        organism: Union[int, str],
        reviewed_only: bool = False,
        size: int = 25,
    ) -> UniProtSearchResult:
        """Search by organism.

        Args:
            organism: Organism tax ID or name.
            reviewed_only: Only return reviewed entries.
            size: Results per page.

        Returns:
            UniProtSearchResult with matching entries.
        """
        if isinstance(organism, int):
            query = f"organism_id:{organism}"
        else:
            query = f"organism_name:{organism}"

        if reviewed_only:
            query += " AND reviewed:true"

        return self.search(query, size=size)

    def search_by_keyword(
        self,
        keyword: str,
        organism: Optional[Union[int, str]] = None,
        reviewed_only: bool = False,
        size: int = 25,
    ) -> UniProtSearchResult:
        """Search by keyword.

        Args:
            keyword: Keyword to search (e.g., "kinase", "receptor").
            organism: Optional organism filter.
            reviewed_only: Only return reviewed entries.
            size: Results per page.

        Returns:
            UniProtSearchResult with matching entries.
        """
        query_parts = [f"keyword:{keyword}"]
        if organism:
            if isinstance(organism, int):
                query_parts.append(f"organism_id:{organism}")
            else:
                query_parts.append(f"organism_name:{organism}")
        if reviewed_only:
            query_parts.append("reviewed:true")

        query = " AND ".join(query_parts)
        return self.search(query, size=size)

    # ----- ID Mapping Methods -----

    def map_ids(
        self,
        ids: List[str],
        from_db: str = "UniProtKB_AC-ID",
        to_db: str = "UniProtKB",
        poll_interval: float = 1.0,
        max_wait: float = 60.0,
    ) -> Dict[str, List[str]]:
        """Map IDs between databases.

        Args:
            ids: List of IDs to map.
            from_db: Source database (e.g., "UniProtKB_AC-ID", "Gene_Name", "GeneID").
            to_db: Target database (e.g., "UniProtKB", "GeneID", "PDB").
            poll_interval: Seconds between status checks.
            max_wait: Maximum seconds to wait for job completion.

        Returns:
            Dictionary mapping input IDs to lists of output IDs.

        Example:
            ```python
            fetcher = UniProt_Fetcher()
            mapping = fetcher.map_ids(
                ["P05067", "P04637"],
                from_db="UniProtKB_AC-ID",
                to_db="GeneID"
            )
            ```
        """
        if not ids:
            return {}

        # Submit mapping job
        data = {
            "ids": ",".join(ids),
            "from": from_db,
            "to": to_db,
        }

        response = request_with_retry(
            url=self._api_config.get_url(UniProtEndpoint.IDMAPPING_RUN.value),
            method="POST",
            data=data,
            headers={"Accept": "application/json"},
            max_retries=3,
            rate_limit=True,
        )

        if response.status_code != 200:
            raise_for_status(response, "UniProt", url=self._api_config.get_url(UniProtEndpoint.IDMAPPING_RUN.value))

        job_id = response.json().get("jobId")
        if not job_id:
            raise ConnectionError("No job ID returned from ID mapping")

        # Poll for job completion and get redirect URL
        import requests as req
        start_time = time.time()
        results_url = None

        while time.time() - start_time < max_wait:
            status_endpoint = UniProtEndpoint.IDMAPPING_STATUS.value.format(job_id=job_id)
            # Use requests directly with allow_redirects=False to capture redirect
            status_response = req.get(
                self._api_config.get_url(status_endpoint),
                headers={"Accept": "application/json"},
                allow_redirects=False,
                timeout=30.0,
            )

            if status_response.status_code == 303:
                # Job complete, get results URL from redirect
                results_url = status_response.headers.get("Location")
                break
            elif status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("jobStatus") == "FINISHED":
                    # Use generic results endpoint
                    results_url = f"https://rest.uniprot.org/idmapping/results/{job_id}"
                    break
                elif status_data.get("jobStatus") == "ERROR":
                    raise ConnectionError(f"ID mapping job failed: {status_data}")

            time.sleep(poll_interval)
        else:
            raise ConnectionError(f"ID mapping job timed out after {max_wait} seconds")

        if not results_url:
            raise ConnectionError("Failed to get results URL from ID mapping")

        # Get results using the redirect URL
        results_response = request_with_retry(
            url=results_url,
            method="GET",
            headers={"Accept": "application/json"},
            max_retries=3,
            rate_limit=True,
        )

        if results_response.status_code != 200:
            raise_for_status(results_response, "UniProt", url=results_url)

        results_data = results_response.json()

        # Parse results into mapping
        mapping: Dict[str, List[str]] = {id_: [] for id_ in ids}
        for result in results_data.get("results", []):
            from_id = result.get("from")
            to_entry = result.get("to")
            if from_id and to_entry:
                if isinstance(to_entry, dict):
                    # UniProtKB entry
                    to_id = to_entry.get("primaryAccession", to_entry.get("id"))
                else:
                    to_id = str(to_entry)
                if to_id and from_id in mapping:
                    mapping[from_id].append(to_id)

        return mapping

    # ----- Convenience Methods -----

    def gene_to_uniprot(
        self,
        gene_names: List[str],
        organism: int = 9606,
        reviewed_only: bool = True,
    ) -> Dict[str, str]:
        """Map gene names to UniProt accessions.

        Uses concurrent requests for efficient batch processing.

        Args:
            gene_names: List of gene names.
            organism: Organism tax ID (default human).
            reviewed_only: Only return reviewed entries.

        Returns:
            Dictionary mapping gene names to accessions.

        Example:
            ```python
            fetcher = UniProt_Fetcher()
            mapping = fetcher.gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
            ```
        """
        if not gene_names:
            return {}

        def _search_gene(gene: str) -> tuple:
            """Search for a single gene and return (gene, accession) tuple."""
            results = self.search_by_gene(
                gene, organism=organism, reviewed_only=reviewed_only, size=1
            )
            if results.entries:
                return (gene, results.entries[0].primaryAccession)
            return (gene, None)

        # Use schedule_process for concurrent requests
        results = self.schedule_process(
            get_func=_search_gene,
            args_list=[(gene,) for gene in gene_names],
            rate_limit_per_second=self._api_config.RATE_LIMIT,
            return_exceptions=True,
        )

        # Build mapping from results, skipping failures
        mapping = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            gene, accession = result
            if accession:
                mapping[gene] = accession

        return mapping

    def uniprot_to_gene(
        self,
        accessions: List[str],
    ) -> Dict[str, str]:
        """Map UniProt accessions to gene names.

        Args:
            accessions: List of UniProt accessions.

        Returns:
            Dictionary mapping accessions to gene names.
        """
        entries = self.get_entries(accessions)
        return entries.to_gene_mapping()

    def get_sequences(
        self,
        accessions: List[str],
    ) -> Dict[str, str]:
        """Get protein sequences for accessions.

        Args:
            accessions: List of UniProt accessions.

        Returns:
            Dictionary mapping accessions to sequences.
        """
        entries = self.get_entries(accessions, fields="accession,sequence")
        return entries.get_sequences()


if __name__ == "__main__":
    fetcher = UniProt_Fetcher()

    # Test get entry
    print("=== Get Entry ===")
    entry = fetcher.get_entry("P05067")
    print(entry.summary())

    # Test search
    print("\n=== Search ===")
    results = fetcher.search("gene:TP53 AND organism_id:9606 AND reviewed:true", size=5)
    print(f"Found {len(results)} results")
    for e in results.entries[:3]:
        print(f"  {e.primaryAccession}: {e.gene_name} - {e.protein_name}")

    # Test search by gene
    print("\n=== Search by Gene ===")
    results = fetcher.search_by_gene("BRCA1", organism=9606, reviewed_only=True)
    print(f"BRCA1 results: {len(results)} entries")

    # Test gene to uniprot mapping
    print("\n=== Gene to UniProt ===")
    mapping = fetcher.gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
    for gene, acc in mapping.items():
        print(f"  {gene} -> {acc}")
