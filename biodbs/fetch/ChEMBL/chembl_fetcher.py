"""ChEMBL REST API fetcher following the standardized pattern."""

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.ChEMBL._data_model import ChEMBLModel
from biodbs.data.ChEMBL.data import ChEMBLFetchedData, ChEMBLDataManager
from biodbs.exceptions import raise_for_status
from typing import Dict, Any, List, Literal, Optional, Union
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)


def _build_chembl_url(params: Dict[str, Any]) -> str:
    """Build ChEMBL REST API URL from validated parameters.

    ChEMBL API structure:
        https://www.ebi.ac.uk/chembl/api/data/{resource}.{format}
        https://www.ebi.ac.uk/chembl/api/data/{resource}/{chembl_id}.{format}
        https://www.ebi.ac.uk/chembl/api/data/{resource}/search.{format}?q={query}
    """
    base_url = "https://www.ebi.ac.uk/chembl/api/data"
    path = params.get("_path", params.get("resource", ""))
    fmt = params.get("format", "json")
    # Extract enum value if needed
    if hasattr(fmt, "value"):
        fmt = fmt.value
    return f"{base_url}/{path}.{fmt}"


class ChEMBLNameSpace(NameSpace):
    """Namespace that validates parameters via ChEMBLModel."""

    def __init__(self):
        super().__init__(ChEMBLModel)

    def validate(self, **kwargs):
        """Validate and compute derived fields (path, query params)."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = ChEMBLModel(**kwargs)
            self._valid_params["_path"] = model.build_path()
            self._valid_params["_query_params"] = model.build_query_params()
        return is_valid, err_msg


class ChEMBL_APIConfig(BaseAPIConfig):
    """API config for ChEMBL REST API using a custom URL builder."""

    def __init__(self):
        super().__init__(url_builder=_build_chembl_url)


class ChEMBL_Fetcher(BaseDataFetcher):
    """Fetcher for ChEMBL REST API.

    ChEMBL provides bioactivity data for drug-like molecules including:

    - Molecules and their properties
    - Bioactivity measurements
    - Targets (proteins, cell lines, organisms)
    - Assays and documents
    - Drug information and indications

    Example:
        ```python
        fetcher = ChEMBL_Fetcher()

        # Get a specific molecule by ChEMBL ID
        aspirin = fetcher.get(resource="molecule", chembl_id="CHEMBL25")
        print(aspirin.results[0]["pref_name"])

        # Search for molecules
        results = fetcher.get(
            resource="molecule",
            search_query="aspirin",
            limit=10
        )

        # Filter activities by target
        activities = fetcher.get(
            resource="activity",
            filters={"target_chembl_id": "CHEMBL240"},
            limit=100
        )

        # Similarity search
        similar = fetcher.get(
            resource="similarity",
            smiles="CC(=O)Oc1ccccc1C(=O)O",  # Aspirin SMILES
            similarity_threshold=70,
            limit=50
        )
        ```
    """

    DEFAULT_LIMIT = 20

    def __init__(self, **data_manager_kws):
        super().__init__(ChEMBL_APIConfig(), ChEMBLNameSpace(), {})
        self._data_manager = (
            ChEMBLDataManager(**data_manager_kws)
            if data_manager_kws
            else None
        )

    def get(
        self,
        resource: str,
        chembl_id: Optional[str] = None,
        search_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        smiles: Optional[str] = None,
        similarity_threshold: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        format: str = "json",
    ) -> ChEMBLFetchedData:
        """Fetch data from ChEMBL REST API.

        Args:
            resource: ChEMBL resource (molecule, activity, target, etc.).
            chembl_id: Optional ChEMBL ID for single-entry lookup.
            search_query: Optional full-text search query.
            filters: Optional field filters (e.g., {"max_phase": 4}).
            smiles: SMILES string for similarity/substructure search.
            similarity_threshold: Threshold for similarity search (40-100).
            limit: Max records to return (1-1000).
            offset: Pagination offset.
            format: Output format (json or xml).

        Returns:
            ChEMBLFetchedData with parsed results.
        """
        is_valid, err_msg = self._namespace.validate(
            resource=resource,
            chembl_id=chembl_id,
            search_query=search_query,
            filters=filters,
            smiles=smiles,
            similarity_threshold=similarity_threshold,
            limit=limit,
            offset=offset,
            format=format,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url
        query_params = self._namespace.valid_params.get("_query_params", {})

        response = requests.get(url, params=query_params)
        if response.status_code == 404:
            # Entry not found - return empty result
            return ChEMBLFetchedData({}, resource=resource)
        if response.status_code != 200:
            raise_for_status(response, "ChEMBL", url=url)

        return ChEMBLFetchedData(response.json(), resource=resource)

    def _fetch_page(
        self,
        url: str,
        query_params: Dict[str, Any],
        resource: str,
    ) -> ChEMBLFetchedData:
        """Thread-safe fetch for a single page."""
        response = requests.get(url, params=query_params)
        if response.status_code != 200:
            raise_for_status(response, "ChEMBL", url=url)
        return ChEMBLFetchedData(response.json(), resource=resource)

    def get_all(
        self,
        resource: str,
        method: Literal["concat", "stream_to_storage"] = "concat",
        limit_per_page: int = 1000,
        max_records: Optional[int] = None,
        rate_limit_per_second: int = 5,
        search_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Union[ChEMBLFetchedData, Path]:
        """Fetch multiple pages of results concurrently.

        Args:
            resource: ChEMBL resource (molecule, activity, target, etc.).
            method: "concat" returns a single ChEMBLFetchedData.
                "stream_to_storage" streams each batch to storage and
                returns the output file Path.
            limit_per_page: Records per request (default 1000, max 1000).
            max_records: Total records to fetch. None means fetch all.
            rate_limit_per_second: Max concurrent requests per second.
            search_query: Optional full-text search query.
            filters: Optional field filters.
            **kwargs: Additional parameters.

        Returns:
            Combined ChEMBLFetchedData or Path to output file.
        """
        if method == "stream_to_storage" and self._data_manager is None:
            raise ValueError(
                "stream_to_storage requires storage_path in ChEMBL_Fetcher constructor"
            )

        if limit_per_page > 1000:
            limit_per_page = 1000

        # Validate and build base URL
        is_valid, err_msg = self._namespace.validate(
            resource=resource,
            search_query=search_query,
            filters=filters,
            limit=limit_per_page,
            offset=0,
            **kwargs,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._api_config.update_params(**self._namespace.valid_params)
        base_url = self._api_config.api_url
        base_query_params = self._namespace.valid_params.get("_query_params", {})

        # First request to discover total
        first_params = {**base_query_params, "limit": limit_per_page, "offset": 0}
        first_page = self._fetch_page(base_url, first_params, resource)

        if not first_page.results:
            return ChEMBLFetchedData({}, resource=resource)

        # Get total from metadata
        total_available = first_page.get_total_count() or len(first_page.results)
        target = (
            min(max_records, total_available)
            if max_records is not None
            else total_available
        )
        first_count = len(first_page.results)

        # Compute remaining pages
        if first_count >= target:
            return self._finalise_chembl(method, [first_page], resource)

        # Calculate offsets for remaining pages
        offsets = list(range(first_count, target, limit_per_page))

        logger.info(
            "Fetching %d more pages concurrently (rate=%d/s)",
            len(offsets),
            rate_limit_per_second,
        )

        def _fetch(offset):
            params = {**base_query_params, "limit": limit_per_page, "offset": offset}
            return self._fetch_page(base_url, params, resource)

        remaining_results: list = self.schedule_process(
            get_func=_fetch,
            args_list=[(o,) for o in offsets],
            rate_limit_per_second=rate_limit_per_second,
            return_exceptions=True,
        )

        # Collect results
        all_pages: List[ChEMBLFetchedData] = [first_page]
        for i, result in enumerate(remaining_results):
            if isinstance(result, Exception):
                logger.warning("Page at offset %d failed: %s", offsets[i], result)
                continue
            if result.results:
                all_pages.append(result)

        return self._finalise_chembl(method, all_pages, resource, target)

    def _finalise_chembl(
        self,
        method: str,
        pages: List[ChEMBLFetchedData],
        resource: str,
        max_records: Optional[int] = None,
    ) -> Union[ChEMBLFetchedData, Path]:
        """Combine fetched pages into the requested output format."""
        filename = f"chembl_{resource}"

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

    # Convenience methods for common operations
    def get_molecule(self, chembl_id: str) -> ChEMBLFetchedData:
        """Get a single molecule by ChEMBL ID."""
        return self.get(resource="molecule", chembl_id=chembl_id)

    def get_target(self, chembl_id: str) -> ChEMBLFetchedData:
        """Get a single target by ChEMBL ID."""
        return self.get(resource="target", chembl_id=chembl_id)

    def search_molecules(
        self,
        query: str,
        limit: int = 20,
    ) -> ChEMBLFetchedData:
        """Search molecules by name or description."""
        return self.get(resource="molecule", search_query=query, limit=limit)

    def get_activities_for_target(
        self,
        target_chembl_id: str,
        limit: int = 1000,
    ) -> ChEMBLFetchedData:
        """Get bioactivity data for a specific target."""
        return self.get(
            resource="activity",
            filters={"target_chembl_id": target_chembl_id},
            limit=limit,
        )

    def get_activities_for_molecule(
        self,
        molecule_chembl_id: str,
        limit: int = 1000,
    ) -> ChEMBLFetchedData:
        """Get bioactivity data for a specific molecule."""
        return self.get(
            resource="activity",
            filters={"molecule_chembl_id": molecule_chembl_id},
            limit=limit,
        )

    def similarity_search(
        self,
        smiles: str,
        threshold: int = 70,
        limit: int = 100,
    ) -> ChEMBLFetchedData:
        """Find molecules similar to a given SMILES structure."""
        return self.get(
            resource="similarity",
            smiles=smiles,
            similarity_threshold=threshold,
            limit=limit,
        )

    def substructure_search(
        self,
        smiles: str,
        limit: int = 100,
    ) -> ChEMBLFetchedData:
        """Find molecules containing a given substructure."""
        return self.get(
            resource="substructure",
            smiles=smiles,
            limit=limit,
        )

    def get_approved_drugs(self, limit: int = 1000) -> ChEMBLFetchedData:
        """Get approved drugs (max_phase = 4)."""
        return self.get(
            resource="drug",
            filters={"max_phase": 4},
            limit=limit,
        )

    def get_drug_indications(
        self,
        molecule_chembl_id: str,
        limit: int = 100,
    ) -> ChEMBLFetchedData:
        """Get indications for a specific drug/molecule."""
        return self.get(
            resource="drug_indication",
            filters={"molecule_chembl_id": molecule_chembl_id},
            limit=limit,
        )

    def get_mechanisms(
        self,
        molecule_chembl_id: str,
        limit: int = 100,
    ) -> ChEMBLFetchedData:
        """Get mechanisms of action for a specific molecule."""
        return self.get(
            resource="mechanism",
            filters={"molecule_chembl_id": molecule_chembl_id},
            limit=limit,
        )


if __name__ == "__main__":
    fetcher = ChEMBL_Fetcher()

    # Test get molecule
    print("=== Get Aspirin (CHEMBL25) ===")
    aspirin = fetcher.get_molecule("CHEMBL25")
    print(f"Found: {aspirin.results[0].get('pref_name', 'N/A')}")
    print(f"Max phase: {aspirin.results[0].get('max_phase', 'N/A')}")

    # Test search
    print("\n=== Search for 'ibuprofen' ===")
    results = fetcher.search_molecules("ibuprofen", limit=5)
    print(f"Found {len(results)} molecules")
    for r in results.results[:3]:
        print(f"  - {r.get('molecule_chembl_id')}: {r.get('pref_name', 'N/A')}")

    # Test activities
    print("\n=== Activities for CHEMBL25 ===")
    activities = fetcher.get_activities_for_molecule("CHEMBL25", limit=5)
    print(f"Found {len(activities)} activities")
    print(f"Columns: {activities.show_columns()[:10]}...")

    # Test approved drugs
    print("\n=== Approved Drugs ===")
    drugs = fetcher.get_approved_drugs(limit=5)
    print(f"Found {len(drugs)} drugs")
    for d in drugs.results:
        print(f"  - {d.get('molecule_chembl_id')}: {d.get('pref_name', 'N/A')}")
