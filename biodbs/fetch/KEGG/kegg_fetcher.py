from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.KEGG._data_model import (
    KEGGModel, KEGGOperation, KEGGDatabase,
)
from biodbs.data.KEGG.data import KEGGFetchedData, KEGGDataManager
from biodbs.utils import get_rsp
from typing import Dict, Any, List, Literal, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def _build_kegg_url(params: Dict[str, Any]) -> str:
    """Build KEGG REST API URL from validated parameters.

    This function is passed to :class:`BaseAPIConfig` as ``url_builder``.
    Parameters are validated by :class:`KEGGModel` before this is called.
    """
    base_url = "https://rest.kegg.jp"
    op = params.get("operation")

    if op == KEGGOperation.info.value:
        return f"{base_url}/info/{params['database']}"

    elif op == KEGGOperation.list.value:
        if params.get("dbentries"):
            entries = "+".join(params["dbentries"])
            return f"{base_url}/list/{entries}"
        elif params.get("organism") and params.get("database") == KEGGDatabase.pathway.value:
            return f"{base_url}/list/pathway/{params['organism']}"
        elif params.get("brite_option"):
            return f"{base_url}/list/brite/{params['brite_option']}"
        else:
            return f"{base_url}/list/{params['database']}"

    elif op == KEGGOperation.find.value:
        url = f"{base_url}/find/{params['database']}/{params['query']}"
        if params.get("find_option"):
            url += f"/{params['find_option']}"
        return url

    elif op == KEGGOperation.get.value:
        entries = "+".join(params["dbentries"])
        url = f"{base_url}/get/{entries}"
        if params.get("get_option"):
            url += f"/{params['get_option']}"
        return url

    elif op == KEGGOperation.conv.value:
        if params.get("dbentries"):
            entries = "+".join(params["dbentries"])
            return f"{base_url}/conv/{params['target_db']}/{entries}"
        else:
            return f"{base_url}/conv/{params['target_db']}/{params['source_db']}"

    elif op == KEGGOperation.link.value:
        if params.get("dbentries"):
            entries = "+".join(params["dbentries"])
            url = f"{base_url}/link/{params['target_db']}/{entries}"
        else:
            url = f"{base_url}/link/{params['target_db']}/{params['source_db']}"
        if params.get("rdf_option"):
            url += f"/{params['rdf_option']}"
        return url

    elif op == KEGGOperation.ddi.value:
        entries = "+".join(params["dbentries"])
        return f"{base_url}/ddi/{entries}"

    else:
        raise ValueError(f"Unsupported operation: {op}")


class KEGGNameSpace(NameSpace):
    """Namespace that validates parameters via :class:`KEGGModel`."""

    def __init__(self):
        super().__init__(KEGGModel)


class KEGG_APIConfig(BaseAPIConfig):
    """API config for KEGG REST API using a custom URL builder.

    KEGG URLs vary by operation, so a simple format string doesn't work.
    Instead, :func:`_build_kegg_url` constructs the URL from validated params.
    """

    def __init__(self):
        super().__init__(url_builder=_build_kegg_url)


class KEGG_Fetcher(BaseDataFetcher):
    # Default batch size for operations that use dbentries
    DEFAULT_BATCH_SIZE = 10  # KEGG API limit

    def __init__(self, **data_manager_kws):
        super().__init__(KEGG_APIConfig(), KEGGNameSpace(), {})
        self._data_manager = (
            KEGGDataManager(**data_manager_kws)
            if data_manager_kws
            else None
        )

    def get(self, operation: str, **kwargs) -> KEGGFetchedData:
        """Fetch data from KEGG REST API.

        Args:
            operation: KEGG operation (info, list, find, get, conv, link, ddi).
            **kwargs: Operation-specific parameters (database, query, dbentries, etc.).

        Returns:
            KEGGFetchedData with parsed results.
        """
        is_valid, err_msg = self._namespace.validate(operation=operation, **kwargs)
        if not is_valid:
            raise ValueError(err_msg)
        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url
        get_option = kwargs.get("get_option")

        response = get_rsp(url)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to fetch data from KEGG API. Status code: {response.status_code}, Message: {response.text}"
            )

        # Handle binary responses (images)
        if get_option == "image":
            content = response.content
        # Handle JSON responses
        elif get_option == "json":
            content = response.json()
        else:
            content = response.text

        return KEGGFetchedData(content, operation=operation, get_option=get_option)

    def _fetch_batch(
        self,
        operation: str,
        dbentries: List[str],
        get_option: Optional[str] = None,
        **kwargs,
    ) -> KEGGFetchedData:
        """Thread-safe fetch for a batch of entries.

        Builds URL directly without mutating shared state.
        """
        # Build params for this batch
        params = {
            "operation": operation,
            "dbentries": dbentries,
            **kwargs,
        }
        if get_option:
            params["get_option"] = get_option

        # Validate
        is_valid, err_msg = self._namespace.validate(**params)
        if not is_valid:
            raise ValueError(err_msg)

        # Build URL using the url_builder directly
        url = _build_kegg_url(self._namespace.valid_params)

        response = get_rsp(url)
        if response.status_code != 200:
            raise ConnectionError(
                f"KEGG API error {response.status_code}: {response.text}"
            )

        if get_option == "image":
            content = response.content
        elif get_option == "json":
            content = response.json()
        else:
            content = response.text

        return KEGGFetchedData(content, operation=operation, get_option=get_option)

    def get_all(
        self,
        operation: str,
        dbentries: List[str],
        method: Literal["concat", "stream_to_storage"] = "concat",
        batch_size: int = DEFAULT_BATCH_SIZE,
        rate_limit_per_second: int = 3,
        get_option: Optional[str] = None,
        **kwargs,
    ) -> Union[KEGGFetchedData, Path]:
        """Fetch data for many entries by batching and concurrent requests.

        KEGG limits certain operations (get, conv, link, ddi) to a small
        number of entries per request.  This method splits a large entry
        list into batches and fetches them concurrently.

        Args:
            operation: KEGG operation (``get``, ``conv``, ``link``, ``ddi``).
            dbentries: List of database entry IDs to fetch.
            method: ``"concat"`` returns a single :class:`KEGGFetchedData`.
                ``"stream_to_storage"`` writes batches to storage and returns
                the output file :class:`Path` (requires ``storage_path`` in
                constructor).
            batch_size: Entries per request (default 10, KEGG's limit).
            rate_limit_per_second: Max requests per second (default 3 to be
                conservative with KEGG).
            get_option: For ``get`` operation, the output format (aaseq,
                ntseq, image, json, etc.).
            **kwargs: Additional parameters (target_db for conv/link, etc.).

        Returns:
            Combined KEGGFetchedData or Path to output file.

        Example::

            fetcher = KEGG_Fetcher(storage_path="./data")
            genes = ["hsa:10458", "hsa:7157", "hsa:672", ...]  # 100+ genes
            data = fetcher.get_all("get", genes)
            print(len(data.records))
        """
        if operation not in ("get", "conv", "link", "ddi"):
            raise ValueError(
                f"get_all only supports operations with dbentries: get, conv, link, ddi. "
                f"Got: {operation}"
            )
        if method == "stream_to_storage" and self._data_manager is None:
            raise ValueError(
                "stream_to_storage requires storage_path in KEGG_Fetcher constructor"
            )
        if not dbentries:
            return KEGGFetchedData("", operation=operation, get_option=get_option)

        # Split entries into batches
        batches = [
            dbentries[i : i + batch_size]
            for i in range(0, len(dbentries), batch_size)
        ]

        logger.info(
            "Fetching %d entries in %d batches (rate=%d/s)",
            len(dbentries),
            len(batches),
            rate_limit_per_second,
        )

        # Fetch first batch to establish format
        first_batch = self._fetch_batch(
            operation, batches[0], get_option=get_option, **kwargs
        )

        if len(batches) == 1:
            return self._finalise_kegg(
                method, [first_batch], operation, get_option
            )

        # Concurrent fetch remaining batches
        def _fetch(batch_entries):
            return self._fetch_batch(
                operation, batch_entries, get_option=get_option, **kwargs
            )

        remaining_results: list = self.schedule_process(
            get_func=_fetch,
            args_list=[(batch,) for batch in batches[1:]],
            rate_limit_per_second=rate_limit_per_second,
            return_exceptions=True,
        )

        # Collect results
        all_batches: List[KEGGFetchedData] = [first_batch]
        for i, result in enumerate(remaining_results):
            if isinstance(result, Exception):
                logger.warning(
                    "Batch %d failed: %s", i + 1, result
                )
                continue
            all_batches.append(result)

        return self._finalise_kegg(method, all_batches, operation, get_option)

    def _finalise_kegg(
        self,
        method: str,
        batches: List[KEGGFetchedData],
        operation: str,
        get_option: Optional[str],
    ) -> Union[KEGGFetchedData, Path]:
        """Combine fetched batches into the requested output format."""
        if method == "concat":
            result = batches[0]
            for batch in batches[1:]:
                result += batch
            return result

        # stream_to_storage
        filename = f"kegg_{operation}"
        if get_option:
            filename += f"_{get_option}"

        for batch in batches:
            if batch.records:
                self._data_manager.stream_json_lines(
                    iter(batch.records), filename, key=filename
                )
            elif batch.text:
                # Append text data
                filepath = self._data_manager.storage_path / f"{filename}.txt"
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(batch.text)
                    f.write("\n///\n")  # KEGG entry separator

        self._data_manager.flush_metadata()

        if batches[0].records:
            return self._data_manager.storage_path / f"{filename}.jsonl"
        return self._data_manager.storage_path / f"{filename}.txt"
