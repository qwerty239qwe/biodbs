from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.exceptions import raise_for_status
from biodbs.data.QuickGO._data_model import QuickGOModel, QuickGOCategory
from biodbs.data.QuickGO.data import QuickGOFetchedData, QuickGODataManager
from typing import Dict, Any, List, Literal, Optional, Union
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)


def _build_quickgo_url(params: Dict[str, Any]) -> str:
    """Build QuickGO API URL from validated parameters.

    QuickGO API structure:
        https://www.ebi.ac.uk/QuickGO/services/{category}/{path}?{query_params}

    The path and query params are built by QuickGOModel.build_path() and
    build_query_params() respectively.
    """
    base_url = "https://www.ebi.ac.uk/QuickGO/services"
    category = params.get("category")

    if isinstance(category, QuickGOCategory):
        category = category.value

    path = params.get("_path", "")
    return f"{base_url}/{category}/{path}"


class QuickGONameSpace(NameSpace):
    """Namespace that validates parameters via QuickGOModel."""

    def __init__(self):
        super().__init__(QuickGOModel)

    def validate(self, **kwargs):
        """Validate and also compute derived fields (path, query params)."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            # Build path and query params from the validated model
            model = QuickGOModel(**kwargs)
            self._valid_params["_path"] = model.build_path()
            self._valid_params["_query_params"] = model.build_query_params()
        return is_valid, err_msg


class QuickGO_APIConfig(BaseAPIConfig):
    """API config for QuickGO API using a custom URL builder.

    QuickGO URLs vary by category and endpoint, so a simple format string
    doesn't work. Instead, _build_quickgo_url constructs the URL from
    validated params.
    """

    def __init__(self):
        super().__init__(url_builder=_build_quickgo_url)


class QuickGO_Fetcher(BaseDataFetcher):
    """Fetcher for QuickGO API (GO annotations, ontology, gene products).

    QuickGO provides access to:

    - Gene Ontology term information
    - GO annotations for genes/proteins
    - Gene product information
    - Annotation downloads in various formats (GAF, GPAD, TSV)

    Categories:

    - **ontology**: GO term search and retrieval
    - **annotation**: GO annotation search and download
    - **geneproduct**: Gene product information

    Example:
        ```python
        fetcher = QuickGO_Fetcher()

        # Search GO terms
        data = fetcher.get(
            category="ontology",
            endpoint="search",
            query="apoptosis"
        )

        # Get GO term by ID
        data = fetcher.get(
            category="ontology",
            endpoint="terms/{ids}",
            ids=["GO:0008150", "GO:0003674"]
        )

        # Search annotations for human
        data = fetcher.get(
            category="annotation",
            endpoint="search",
            goId="GO:0006915",  # apoptotic process
            taxonId=9606
        )
        df = data.as_dataframe()
        ```
    """

    DEFAULT_LIMIT = 100

    def __init__(self, **data_manager_kws: Any):
        """Initialize QuickGO fetcher.

        Args:
            **data_manager_kws: Keyword arguments for QuickGODataManager
                (e.g., storage_path for stream_to_storage method).
        """
        super().__init__(QuickGO_APIConfig(), QuickGONameSpace(), {})
        self._data_manager = (
            QuickGODataManager(**data_manager_kws)
            if data_manager_kws
            else None
        )

    def get(
        self,
        category: str,
        endpoint: str,
        **kwargs: Any,
    ) -> QuickGOFetchedData:
        """Fetch data from QuickGO API.

        Args:
            category: QuickGO category (ontology, annotation, geneproduct).
            endpoint: API endpoint (search, terms/{ids}, downloadSearch, etc.).
            **kwargs: Endpoint-specific parameters.

        Returns:
            QuickGOFetchedData with parsed results.
        """
        is_valid, err_msg = self._namespace.validate(
            category=category, endpoint=endpoint, **kwargs
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url
        query_params = self._namespace.valid_params.get("_query_params", {})
        download_format = kwargs.get("downloadFormat")

        # Set Accept header for download requests
        headers = {}
        if endpoint == "downloadSearch" and download_format:
            accept_map = {
                "tsv": "text/tsv",
                "gaf": "text/gaf",
                "gpad": "text/gpad",
            }
            headers["Accept"] = accept_map.get(download_format, "text/tsv")

        response = requests.get(url, params=query_params, headers=headers)
        if response.status_code != 200:
            raise_for_status(response, "QuickGO", url=url)

        # Handle different response types
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            content = response.json()
        else:
            content = response.text

        return QuickGOFetchedData(
            content, endpoint=endpoint, download_format=download_format
        )

    def _fetch_page(
        self,
        url: str,
        query_params: Dict[str, Any],
        endpoint: str,
        download_format: Optional[str] = None,
    ) -> QuickGOFetchedData:
        """Thread-safe fetch for a single page."""
        response = requests.get(url, params=query_params)
        if response.status_code != 200:
            raise_for_status(response, "QuickGO", url=url)

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            content = response.json()
        else:
            content = response.text

        return QuickGOFetchedData(
            content, endpoint=endpoint, download_format=download_format
        )

    def get_all(
        self,
        category: str,
        endpoint: str,
        method: Literal["concat", "stream_to_storage"] = "concat",
        limit_per_page: int = DEFAULT_LIMIT,
        max_records: Optional[int] = None,
        rate_limit_per_second: int = 5,
        **kwargs: Any,
    ) -> Union[QuickGOFetchedData, Path]:
        """Fetch multiple pages of results concurrently.

        Args:
            category: QuickGO category (ontology, annotation, geneproduct).
            endpoint: API endpoint (search, etc.). Note: downloadSearch
                doesn't support pagination, use get() directly.
            method: ``"concat"`` returns a single QuickGOFetchedData.
                ``"stream_to_storage"`` streams each batch to storage and
                returns the output file Path.
            limit_per_page: Records per request (default 100, max 10000).
            max_records: Total records to fetch. None means fetch all.
            rate_limit_per_second: Max concurrent requests per second.
            **kwargs: Forwarded to the API (goId, taxonId, etc.).

        Returns:
            Combined QuickGOFetchedData or Path to output file.
        """
        if endpoint == "downloadSearch":
            raise ValueError(
                "downloadSearch doesn't support pagination. Use get() instead."
            )

        if method == "stream_to_storage" and self._data_manager is None:
            raise ValueError(
                "stream_to_storage requires storage_path in QuickGO_Fetcher constructor"
            )

        # Validate and build URL
        kwargs["limit"] = limit_per_page
        kwargs["page"] = 1

        is_valid, err_msg = self._namespace.validate(
            category=category, endpoint=endpoint, **kwargs
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._api_config.update_params(**self._namespace.valid_params)
        base_url = self._api_config.api_url
        base_query_params = self._namespace.valid_params.get("_query_params", {})
        download_format = kwargs.get("downloadFormat")

        # First request to discover total
        first_params = {**base_query_params, "limit": limit_per_page, "page": 1}
        first_page = self._fetch_page(base_url, first_params, endpoint, download_format)

        if not first_page.results:
            return QuickGOFetchedData({}, endpoint=endpoint, download_format=download_format)

        # Get total from metadata
        total_available = first_page.get_total_hits()
        target = (
            min(max_records, total_available)
            if max_records is not None
            else total_available
        )
        first_count = len(first_page.results)

        # Compute remaining pages
        if first_count >= target:
            return self._finalise_quickgo(method, [first_page], category, endpoint)

        # QuickGO uses 1-based page numbers
        remaining_pages_needed = (target - first_count + limit_per_page - 1) // limit_per_page
        page_numbers = list(range(2, 2 + remaining_pages_needed))

        logger.info(
            "Fetching %d more pages concurrently (rate=%d/s)",
            len(page_numbers),
            rate_limit_per_second,
        )

        def _fetch(page_num):
            params = {**base_query_params, "limit": limit_per_page, "page": page_num}
            return self._fetch_page(base_url, params, endpoint, download_format)

        remaining_results: list = self.schedule_process(
            get_func=_fetch,
            args_list=[(p,) for p in page_numbers],
            rate_limit_per_second=rate_limit_per_second,
            return_exceptions=True,
        )

        # Collect results
        all_pages: List[QuickGOFetchedData] = [first_page]
        for i, result in enumerate(remaining_results):
            if isinstance(result, Exception):
                logger.warning("Page %d failed: %s", page_numbers[i], result)
                continue
            if result.results:
                all_pages.append(result)

        return self._finalise_quickgo(method, all_pages, category, endpoint, target)

    def _finalise_quickgo(
        self,
        method: str,
        pages: List[QuickGOFetchedData],
        category: str,
        endpoint: str,
        max_records: Optional[int] = None,
    ) -> Union[QuickGOFetchedData, Path]:
        """Combine fetched pages into the requested output format."""
        filename = f"quickgo_{category}_{endpoint.replace('/', '_')}"

        if method == "concat":
            result = pages[0]
            for page in pages[1:]:
                result += page
            if max_records is not None:
                result.results = result.results[:max_records]
            return result

        # stream_to_storage
        for page in pages:
            if page.results:
                self._data_manager.stream_json_lines(
                    iter(page.results), filename, key=filename
                )

        self._data_manager.flush_metadata()
        return self._data_manager.storage_path / f"{filename}.jsonl"


if __name__ == "__main__":
    fetcher = QuickGO_Fetcher()

    # Test ontology search
    print("=== Ontology Search ===")
    data = fetcher.get(category="ontology", endpoint="search", query="apoptosis", limit=5)
    print(f"Found {len(data.results)} results")
    print(data.show_columns())

    # Test get GO term by ID
    print("\n=== Get GO Term ===")
    data = fetcher.get(category="ontology", endpoint="terms/{ids}", ids=["GO:0008150"])
    print(f"Found {len(data.results)} results")
    if data.results:
        print(f"Term: {data.results[0].get('name', 'N/A')}")

    # Test annotation search
    print("\n=== Annotation Search ===")
    data = fetcher.get(
        category="annotation",
        endpoint="search",
        goId="GO:0006915",
        taxonId=9606,
        limit=10
    )
    print(f"Found {len(data.results)} results (total: {data.get_total_hits()})")
    print(data.show_columns())
