from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.FDA._data_model import FDAModel
from biodbs.data.FDA.data import FDAFetchedData, FDADataManager

from typing import Literal, Optional, Union
from pathlib import Path
import logging

import requests

logger = logging.getLogger(__name__)


class FDANameSpace(NameSpace):
    def __init__(self):
        model = FDAModel
        super().__init__(model)
    

class FDA_APIConfig(BaseAPIConfig):
    def __init__(self):
        super().__init__(url_format="https://api.fda.gov/{category}/{endpoint}.json")
        

class FDA_Fetcher(BaseDataFetcher):
    """Fetcher for openFDA API.

    The openFDA API provides access to FDA data including:

    - Drug adverse events (drug/event)
    - Drug product labeling (drug/label)
    - Drug recalls and enforcement (drug/enforcement)
    - Device adverse events and recalls
    - Food recalls and enforcement

    Rate limits:

    - Without API key: 240 requests/min, 1,000 requests/day per IP
    - With API key: 240 requests/min, 120,000 requests/day per key

    Example:
        ```python
        fetcher = FDA_Fetcher()

        # Search drug adverse events
        events = fetcher.get(
            category="drug",
            endpoint="event",
            search={"patient.drug.medicinalproduct": "aspirin"},
            limit=10
        )
        df = events.as_dataframe(columns=["receivedate", "patient.patientsex"])

        # Get drug labels
        labels = fetcher.get(
            category="drug",
            endpoint="label",
            search={"openfda.brand_name": "TYLENOL"},
            limit=5
        )
        ```
    """

    def __init__(self, api_key: str = None, limit: int = None, **data_manager_kws):
        """Initialize FDA fetcher.

        Args:
            api_key: openFDA API key for higher rate limits (optional).
            limit: Default limit for queries. If None, uses API default.
            **data_manager_kws: Keyword arguments for FDADataManager
                (e.g., storage_path for stream_to_storage method).
        """
        super().__init__(FDA_APIConfig(), FDANameSpace(), {})
        self._api_key = api_key
        self._limit = limit
        self._data_manager = FDADataManager(**data_manager_kws)

    def get(self, category, endpoint, stream=None, **kwargs):
        """Fetch data from openFDA API.

        Args:
            category: FDA category (e.g., "drug", "device", "food").
            endpoint: Category endpoint (e.g., "event", "label", "enforcement").
            stream: If True, stream the response (for large downloads).
            **kwargs: Query parameters including:
                - search: Search query dict (e.g., {"field": "value"}).
                - limit: Maximum records to return (1-1000).
                - skip: Number of records to skip for pagination.
                - sort: Sort field and direction.
                - count: Field to count occurrences of.
                - api_key: Override default API key.

        Returns:
            FDAFetchedData with query results.

        Example:
            >>> fetcher = FDA_Fetcher()
            >>> data = fetcher.get(
            ...     category="drug",
            ...     endpoint="event",
            ...     search={"patient.drug.medicinalproduct": "aspirin"},
            ...     limit=10
            ... )
            >>> print(data)
            <FDAFetchedData results=10>
        """
        kwargs["api_key"] = self._api_key if kwargs.get("api_key") is None else kwargs.get("api_key")
        kwargs["limit"] = self._limit if kwargs.get("limit") is None else kwargs.get("limit")

        is_valid, err_msg = self._namespace.validate(category=category, 
                                                     endpoint=endpoint, 
                                                     search=kwargs.get("search"),
                                                     limit=kwargs.get("limit"),
                                                     sort=kwargs.get("sort"),
                                                     count=kwargs.get("count"),
                                                     skip=kwargs.get("skip"))
        if not is_valid:
            raise ValueError(err_msg)
        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url

        response = requests.get(url, params=kwargs, stream=stream)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to fetch data from FDA API. Status code: {response.status_code}, Message: {response.text}")
        
        return FDAFetchedData(response.json())
    
    def _fetch_page(self, url: str, **params) -> FDAFetchedData:
        """Thread-safe page fetch — no shared state mutation."""
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ConnectionError(
                f"FDA API error {response.status_code}: {response.text}"
            )
        return FDAFetchedData(response.json())

    def _resolve_url(self, category, endpoint, **kwargs):
        """Validate params once and return the resolved base URL."""
        is_valid, err_msg = self._namespace.validate(
            category=category,
            endpoint=endpoint,
            search=kwargs.get("search"),
            limit=kwargs.get("limit"),
            sort=kwargs.get("sort"),
            count=kwargs.get("count"),
            skip=kwargs.get("skip"),
        )
        if not is_valid:
            raise ValueError(err_msg)
        self._api_config.update_params(**self._namespace.valid_params)
        return self._api_config.api_url

    def get_all(
        self,
        category,
        endpoint,
        method: Literal["concat", "stream_to_storage"] = "concat",
        batch_size: int = 1000,
        max_records: Optional[int] = None,
        rate_limit_per_second: int = 4,
        **kwargs,
    ) -> Union[FDAFetchedData, Path]:
        """Fetch multiple pages of results concurrently.

        Uses :meth:`schedule_process` to dispatch page requests across
        threads while staying within the FDA rate limit.

        Args:
            category: FDA category (e.g. ``"drug"``).
            endpoint: FDA endpoint (e.g. ``"event"``).
            method: ``"concat"`` accumulates all results in memory and returns
                a single :class:`FDAFetchedData`.  ``"stream_to_storage"``
                streams each batch to the data manager as JSON Lines and
                returns the output file :class:`Path`.
            batch_size: Records per request (max 1000).
            max_records: Total records to fetch.  ``None`` means fetch all
                available records.
            rate_limit_per_second: Max concurrent requests per second
                (FDA default: 240/min ≈ 4/sec).
            **kwargs: Forwarded to the API (``search``, ``sort``, etc.).

        Note — openFDA rate limits:
            Without an API key: 240 req/min, 1 000 req/day per IP.
            With an API key: 240 req/min, 120 000 req/day per key.
        """
        if batch_size > 1000:
            raise ValueError("Upper limit = 1000 per request")
        if method not in ("concat", "stream_to_storage"):
            raise ValueError(f"Unknown method: {method!r}")

        # -- resolve URL and apply defaults --------------------------------
        req_kwargs = dict(kwargs)
        req_kwargs["api_key"] = (
            self._api_key if req_kwargs.get("api_key") is None else req_kwargs["api_key"]
        )
        req_kwargs["limit"] = (
            self._limit if req_kwargs.get("limit") is None else req_kwargs["limit"]
        )
        url = self._resolve_url(category, endpoint, **req_kwargs)

        # -- first request: discover total ---------------------------------
        first_params = {**req_kwargs, "limit": batch_size, "skip": 0}
        first_page = self._fetch_page(url, **first_params)

        if not first_page.results:
            return FDAFetchedData({"meta": {}, "results": []})

        total_available = (
            first_page.metadata.get("results", {}).get("total")
            or len(first_page.results)
        )
        target = (
            min(max_records, total_available)
            if max_records is not None
            else total_available
        )
        first_count = len(first_page.results)

        # -- compute remaining page offsets --------------------------------
        offsets = list(range(first_count, target, batch_size))
        if not offsets:
            # First page already covers everything.
            if max_records is not None:
                first_page.results = first_page.results[:target]
            return self._finalise(method, [first_page], category, endpoint)

        page_kwargs_list = [
            {**req_kwargs, "limit": min(batch_size, target - offset), "skip": offset}
            for offset in offsets
        ]

        # -- concurrent fetch via schedule_process -------------------------
        logger.info(
            "Fetching %d remaining pages concurrently (rate=%d/s)",
            len(page_kwargs_list),
            rate_limit_per_second,
        )

        def _fetch(page_params):
            return self._fetch_page(url, **page_params)

        remaining_pages: list = self.schedule_process(
            get_func=_fetch,
            args_list=[(kw,) for kw in page_kwargs_list],
            rate_limit_per_second=rate_limit_per_second,
            return_exceptions=True,
        )

        # -- collect results in order --------------------------------------
        all_pages: list[FDAFetchedData] = [first_page]
        for i, page in enumerate(remaining_pages):
            if isinstance(page, Exception):
                logger.warning(
                    "Page at skip=%d failed: %s", offsets[i], page
                )
                continue
            if page.results:
                all_pages.append(page)

        return self._finalise(method, all_pages, category, endpoint, target)

    def _finalise(
        self,
        method: str,
        pages: list[FDAFetchedData],
        category: str,
        endpoint: str,
        max_records: Optional[int] = None,
    ) -> Union[FDAFetchedData, Path]:
        """Combine fetched pages into the requested output format."""
        filename = f"{category}_{endpoint}"

        if method == "concat":
            result = pages[0]
            for page in pages[1:]:
                result += page
            if max_records is not None:
                result.results = result.results[:max_records]
            return result

        # stream_to_storage
        for page in pages:
            self._data_manager.stream_json_lines(
                iter(page.results), filename, key=filename,
            )
        self._data_manager.flush_metadata()
        return self._data_manager.storage_path / f"{filename}.jsonl"


if __name__ == "__main__":
    fetcher = FDA_Fetcher(storage_path="./temp")
    params = dict(search={"receivedate": "[20040101+TO+20081231]"}, limit=3)
    data = fetcher.get(category="drug", endpoint="event", **params)

    print(data.show_valid_columns())
    print(data.format_results(columns=["receivedate", "patient.patientonsetage", 
                                       "patient.patientsex", "patient.drug.medicinalproduct", 
                                       "patient.drug.drugindication"]))
    
    print(data.as_dataframe(columns=["receivedate", "patient.patientonsetage"],))

    batch_data = fetcher.get_all(category="drug", endpoint="event", max_records=4500, **params)
    print(batch_data.as_dataframe(columns=["receivedate", "patient.patientonsetage"],))
    print(f"#results: {len(batch_data.results)}")