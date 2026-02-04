"""Disease Ontology API fetcher following the standardized pattern."""

from typing import Dict, Any, List, Optional
import logging
from urllib.parse import quote

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.fetch._rate_limit import request_with_retry, get_rate_limiter
from biodbs.data.DiseaseOntology._data_model import (
    DOBase,
    DOEndpoint,
    OLSEndpoint,
    DOSearchRequest,
)
from biodbs.data.DiseaseOntology.data import (
    DOFetchedData,
    DOSearchFetchedData,
)

logger = logging.getLogger(__name__)


class DO_APIConfig(BaseAPIConfig):
    """API configuration for Disease Ontology.

    Supports two APIs:
        - Direct DO API: https://disease-ontology.org/api
        - EBI OLS API: https://www.ebi.ac.uk/ols4/api (more comprehensive)
    """

    # Host identifiers for rate limiting
    DO_HOST = "disease-ontology.org"
    OLS_HOST = "www.ebi.ac.uk"

    # Rate limits (requests per second)
    DO_RATE_LIMIT = 10
    OLS_RATE_LIMIT = 10

    def __init__(
        self,
        do_base: str = DOBase.DO_API.value,
        ols_base: str = DOBase.OLS_API.value,
    ):
        super().__init__()
        self._do_base = do_base
        self._ols_base = ols_base

        # Register rate limits with global limiter
        self._register_rate_limits()

    def _register_rate_limits(self):
        """Register rate limits with global rate limiter."""
        limiter = get_rate_limiter()
        limiter.set_rate(self.DO_HOST, self.DO_RATE_LIMIT)
        limiter.set_rate(self.OLS_HOST, self.OLS_RATE_LIMIT)

    def get_do_url(self, endpoint: str) -> str:
        """Build URL for Direct DO API endpoint."""
        return f"{self._do_base}/{endpoint}"

    def get_ols_url(self, endpoint: str) -> str:
        """Build URL for EBI OLS API endpoint."""
        return f"{self._ols_base}/{endpoint}"


class DO_Fetcher(BaseDataFetcher):
    """Fetcher for Disease Ontology API.

    Provides access to disease ontology data via two APIs:
        - Direct DO API for basic metadata
        - EBI Ontology Lookup Service (OLS) for comprehensive queries

    Examples::

        fetcher = DO_Fetcher()

        # Get disease term by DOID
        term = fetcher.get_term("DOID:162")  # Cancer
        print(term.as_dataframe())

        # Search for diseases
        results = fetcher.search("cancer")
        print(results.get_doids())

        # Get term hierarchy
        parents = fetcher.get_parents("DOID:162")
        children = fetcher.get_children("DOID:162")

        # Get cross-references
        term = fetcher.get_term("DOID:162")
        print(term.terms[0].mesh_id)  # Get MeSH ID
        print(term.terms[0].umls_cui)  # Get UMLS CUI
    """

    def __init__(self):
        """Initialize Disease Ontology fetcher."""
        self._api_config = DO_APIConfig()
        super().__init__(
            self._api_config, NameSpace(DOSearchRequest), {}
        )

    def _make_do_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the direct DO API with rate limiting and retry.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response as dictionary.

        Raises:
            ConnectionError: If the request fails after retries.
        """
        url = self._api_config.get_do_url(endpoint)
        headers = {"Accept": "application/json"}

        response = request_with_retry(
            url=url,
            method="GET",
            params=params,
            headers=headers,
            max_retries=3,
            initial_delay=1.0,
            rate_limit=True,
        )

        if response.status_code != 200:
            raise ConnectionError(
                f"DO API request failed. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def _make_ols_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the EBI OLS API with rate limiting and retry.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response as dictionary.

        Raises:
            ConnectionError: If the request fails after retries.
        """
        url = self._api_config.get_ols_url(endpoint)
        headers = {"Accept": "application/json"}

        response = request_with_retry(
            url=url,
            method="GET",
            params=params,
            headers=headers,
            max_retries=3,
            initial_delay=1.0,
            rate_limit=True,
        )

        if response.status_code != 200:
            raise ConnectionError(
                f"OLS API request failed. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def _normalize_doid(self, doid: str) -> str:
        """Normalize DOID format to DOID:XXXXX format.

        Args:
            doid: Disease ontology ID in various formats.

        Returns:
            Normalized DOID (e.g., "DOID:162").
        """
        doid = doid.strip()
        if doid.startswith("DOID:"):
            return doid
        elif doid.startswith("DOID_"):
            return doid.replace("DOID_", "DOID:")
        elif doid.isdigit():
            return f"DOID:{doid}"
        return doid

    def _doid_to_iri(self, doid: str) -> str:
        """Convert DOID to IRI format for OLS API.

        Args:
            doid: Disease ontology ID.

        Returns:
            IRI format URL.
        """
        doid = self._normalize_doid(doid)
        numeric = doid.split(":")[1] if ":" in doid else doid
        return f"http://purl.obolibrary.org/obo/DOID_{numeric}"

    def _encode_iri(self, iri: str) -> str:
        """Double URL-encode IRI for OLS API endpoints.

        Args:
            iri: IRI URL to encode.

        Returns:
            Double URL-encoded IRI.
        """
        return quote(quote(iri, safe=""), safe="")

    # ----- Term Methods -----

    def get_term(
        self,
        doid: str,
        use_ols: bool = True,
    ) -> DOFetchedData:
        """Get a disease term by DOID.

        Args:
            doid: Disease Ontology ID (e.g., "DOID:162", "162", "DOID_162").
            use_ols: If True, use OLS API for more detailed data.

        Returns:
            DOFetchedData with the disease term.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> term = fetcher.get_term("DOID:162")  # Cancer
            >>> print(term.terms[0].name)
            'cancer'
        """
        doid = self._normalize_doid(doid)

        if use_ols:
            # Use OLS API for detailed term data
            iri = self._doid_to_iri(doid)
            encoded_iri = self._encode_iri(iri)
            endpoint = OLSEndpoint.TERM_BY_IRI.value.format(encoded_iri=encoded_iri)
            data = self._make_ols_request(endpoint)
            return DOFetchedData(data, query_ids=[doid])
        else:
            # Use direct DO API
            numeric = doid.split(":")[1] if ":" in doid else doid
            endpoint = DOEndpoint.METADATA.value.format(doid=numeric)
            data = self._make_do_request(endpoint)
            return DOFetchedData(data, query_ids=[doid])

    def get_terms(
        self,
        doids: List[str],
        use_ols: bool = True,
    ) -> DOFetchedData:
        """Get multiple disease terms by DOIDs.

        Args:
            doids: List of Disease Ontology IDs.
            use_ols: If True, use OLS API for more detailed data.

        Returns:
            DOFetchedData with all disease terms.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> terms = fetcher.get_terms(["DOID:162", "DOID:10283"])
            >>> print(terms.get_names())
        """
        if not doids:
            return DOFetchedData([], query_ids=[])

        result = DOFetchedData([], query_ids=doids)

        for doid in doids:
            try:
                term_data = self.get_term(doid, use_ols=use_ols)
                result += term_data
            except ConnectionError as e:
                logger.warning(f"Failed to fetch term {doid}: {e}")

        return result

    def get_all_terms(
        self,
        page: int = 0,
        page_size: int = 100,
    ) -> DOFetchedData:
        """Get all disease terms from the ontology (paginated).

        Args:
            page: Page number (0-indexed).
            page_size: Number of terms per page.

        Returns:
            DOFetchedData with disease terms.
        """
        endpoint = OLSEndpoint.TERMS.value
        params = {
            "page": page,
            "size": page_size,
        }
        data = self._make_ols_request(endpoint, params=params)
        return DOFetchedData(data, query_ids=[])

    # ----- Search Methods -----

    def search(
        self,
        query: str,
        exact: bool = False,
        rows: int = 20,
        start: int = 0,
        obsoletes: bool = False,
    ) -> DOSearchFetchedData:
        """Search for disease terms.

        Args:
            query: Search query string.
            exact: If True, search for exact matches only.
            rows: Maximum number of results to return.
            start: Starting offset for pagination.
            obsoletes: If True, include obsolete terms.

        Returns:
            DOSearchFetchedData with search results.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> results = fetcher.search("breast cancer")
            >>> print(results.get_doids())
        """
        request = DOSearchRequest(
            query=query,
            ontology="doid",
            exact=exact,
            rows=rows,
            start=start,
        )

        params = request.get_params()
        if not obsoletes:
            params["obsoletes"] = "false"

        data = self._make_ols_request(OLSEndpoint.SEARCH.value, params=params)
        return DOSearchFetchedData(data, query=query)

    def search_by_xref(
        self,
        database: str,
        external_id: str,
    ) -> DOSearchFetchedData:
        """Search for disease terms by external database reference.

        Args:
            database: Database name (e.g., "MESH", "UMLS_CUI", "ICD10CM").
            external_id: ID in the external database.

        Returns:
            DOSearchFetchedData with matching terms.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> results = fetcher.search_by_xref("MESH", "D001943")  # Breast cancer
        """
        # Search using the xref format
        query = f"{database}:{external_id}"
        return self.search(query, exact=True)

    # ----- Hierarchy Methods -----

    def get_parents(self, doid: str) -> DOFetchedData:
        """Get parent terms of a disease.

        Args:
            doid: Disease Ontology ID.

        Returns:
            DOFetchedData with parent terms.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> parents = fetcher.get_parents("DOID:1612")  # Breast cancer
            >>> for term in parents.terms:
            ...     print(f"{term.doid}: {term.name}")
        """
        doid = self._normalize_doid(doid)
        iri = self._doid_to_iri(doid)
        encoded_iri = self._encode_iri(iri)
        endpoint = OLSEndpoint.PARENTS.value.format(encoded_iri=encoded_iri)
        data = self._make_ols_request(endpoint)
        return DOFetchedData(data, query_ids=[doid])

    def get_children(self, doid: str) -> DOFetchedData:
        """Get child terms of a disease.

        Args:
            doid: Disease Ontology ID.

        Returns:
            DOFetchedData with child terms.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> children = fetcher.get_children("DOID:162")  # Cancer
            >>> print(f"Cancer has {len(children)} child terms")
        """
        doid = self._normalize_doid(doid)
        iri = self._doid_to_iri(doid)
        encoded_iri = self._encode_iri(iri)
        endpoint = OLSEndpoint.CHILDREN.value.format(encoded_iri=encoded_iri)
        data = self._make_ols_request(endpoint)
        return DOFetchedData(data, query_ids=[doid])

    def get_ancestors(self, doid: str) -> DOFetchedData:
        """Get all ancestor terms of a disease.

        Args:
            doid: Disease Ontology ID.

        Returns:
            DOFetchedData with ancestor terms.
        """
        doid = self._normalize_doid(doid)
        iri = self._doid_to_iri(doid)
        encoded_iri = self._encode_iri(iri)
        endpoint = OLSEndpoint.ANCESTORS.value.format(encoded_iri=encoded_iri)
        data = self._make_ols_request(endpoint)
        return DOFetchedData(data, query_ids=[doid])

    def get_descendants(self, doid: str) -> DOFetchedData:
        """Get all descendant terms of a disease.

        Args:
            doid: Disease Ontology ID.

        Returns:
            DOFetchedData with descendant terms.
        """
        doid = self._normalize_doid(doid)
        iri = self._doid_to_iri(doid)
        encoded_iri = self._encode_iri(iri)
        endpoint = OLSEndpoint.DESCENDANTS.value.format(encoded_iri=encoded_iri)
        data = self._make_ols_request(endpoint)
        return DOFetchedData(data, query_ids=[doid])

    def get_hierarchical_parents(self, doid: str) -> DOFetchedData:
        """Get hierarchical parent terms (includes part_of relationships).

        Args:
            doid: Disease Ontology ID.

        Returns:
            DOFetchedData with hierarchical parent terms.
        """
        doid = self._normalize_doid(doid)
        iri = self._doid_to_iri(doid)
        encoded_iri = self._encode_iri(iri)
        endpoint = OLSEndpoint.HIERARCHICAL_PARENTS.value.format(encoded_iri=encoded_iri)
        data = self._make_ols_request(endpoint)
        return DOFetchedData(data, query_ids=[doid])

    def get_hierarchical_children(self, doid: str) -> DOFetchedData:
        """Get hierarchical child terms (includes part_of relationships).

        Args:
            doid: Disease Ontology ID.

        Returns:
            DOFetchedData with hierarchical child terms.
        """
        doid = self._normalize_doid(doid)
        iri = self._doid_to_iri(doid)
        encoded_iri = self._encode_iri(iri)
        endpoint = OLSEndpoint.HIERARCHICAL_CHILDREN.value.format(encoded_iri=encoded_iri)
        data = self._make_ols_request(endpoint)
        return DOFetchedData(data, query_ids=[doid])

    # ----- Ontology Info Methods -----

    def get_ontology_info(self) -> Dict[str, Any]:
        """Get Disease Ontology metadata.

        Returns:
            Dictionary with ontology information.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> info = fetcher.get_ontology_info()
            >>> print(info.get("config", {}).get("title"))
        """
        endpoint = OLSEndpoint.ONTOLOGY_INFO.value
        return self._make_ols_request(endpoint)

    # ----- Cross-reference Methods -----

    def doid_to_mesh(self, doids: List[str]) -> Dict[str, Optional[str]]:
        """Convert DOIDs to MeSH IDs.

        Args:
            doids: List of Disease Ontology IDs.

        Returns:
            Dictionary mapping DOIDs to MeSH IDs.

        Example:
            >>> fetcher = DO_Fetcher()
            >>> mapping = fetcher.doid_to_mesh(["DOID:162", "DOID:1612"])
            >>> print(mapping)
        """
        terms = self.get_terms(doids)
        return {t.doid: t.mesh_id for t in terms.terms}

    def doid_to_umls(self, doids: List[str]) -> Dict[str, Optional[str]]:
        """Convert DOIDs to UMLS CUIs.

        Args:
            doids: List of Disease Ontology IDs.

        Returns:
            Dictionary mapping DOIDs to UMLS CUIs.
        """
        terms = self.get_terms(doids)
        return {t.doid: t.umls_cui for t in terms.terms}

    def doid_to_icd10(self, doids: List[str]) -> Dict[str, Optional[str]]:
        """Convert DOIDs to ICD-10 codes.

        Args:
            doids: List of Disease Ontology IDs.

        Returns:
            Dictionary mapping DOIDs to ICD-10 codes.
        """
        terms = self.get_terms(doids)
        return {t.doid: t.icd10_code for t in terms.terms}


if __name__ == "__main__":
    fetcher = DO_Fetcher()

    # Test ontology info
    print("=== Ontology Info ===")
    info = fetcher.get_ontology_info()
    config = info.get("config", {})
    print(f"Title: {config.get('title')}")
    print(f"Version: {config.get('version')}")

    # Test get term
    print("\n=== Get Term ===")
    term = fetcher.get_term("DOID:162")  # Cancer
    print(term.summary())

    # Test search
    print("\n=== Search ===")
    results = fetcher.search("breast cancer", rows=5)
    print(f"Found {len(results)} results for 'breast cancer'")
    for r in results.results[:3]:
        print(f"  {r.doid}: {r.name}")

    # Test hierarchy
    print("\n=== Hierarchy ===")
    children = fetcher.get_children("DOID:162")
    print(f"Cancer has {len(children)} direct children")

    # Test cross-references
    print("\n=== Cross-references ===")
    term = fetcher.get_term("DOID:1612")  # Breast cancer
    if term.terms:
        t = term.terms[0]
        print(f"DOID: {t.doid}")
        print(f"Name: {t.name}")
        print(f"MeSH: {t.mesh_id}")
        print(f"UMLS: {t.umls_cui}")
        print(f"ICD-10: {t.icd10_code}")
