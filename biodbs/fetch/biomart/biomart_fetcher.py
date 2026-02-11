"""BioMart (Ensembl) data fetcher following the standardized pattern.

BioMart provides access to genomic data through a hierarchical structure:
- Server → Mart → Dataset

Query structure uses XML format with filters and attributes.

Note: BioMart API does not work well with async requests, so this fetcher
uses synchronous requests with threading for batch operations.

Reference:
- https://www.ensembl.org/info/data/biomart/biomart_restful.html
"""

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.exceptions import APIServerError, APIError
from biodbs.data.BioMart._data_model import (
    BioMartHost,
    BioMartMart,
    BioMartDataset,
    BioMartServerModel,
    BioMartMartModel,
    BioMartConfigModel,
    BioMartQueryModel,
    BioMartBatchQueryModel,
    DEFAULT_QUERY_ATTRIBUTES,
)
from biodbs.data.BioMart.data import (
    BioMartRegistryData,
    BioMartDatasetsData,
    BioMartConfigData,
    BioMartQueryData,
    BioMartDataManager,
)
from typing import Dict, Any, List, Optional, Union
import logging
import requests
import time
import concurrent.futures
from tqdm import tqdm

logger = logging.getLogger(__name__)


def _build_biomart_url(params: Dict[str, Any]) -> str:
    """Build BioMart URL from parameters."""
    return params.get("_url", "")


class BioMartNameSpaceValidator(NameSpace):
    """Namespace validator for BioMart requests."""

    def __init__(self, model_class):
        super().__init__(model_class)
        self._model_class = model_class

    def validate(self, **kwargs):
        """Validate and compute URL and query params."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = self._model_class(**kwargs)
            self._valid_params["_url"] = model.build_url()
            self._valid_params["_query_params"] = model.build_query_params()
        return is_valid, err_msg


class BioMartAPIConfig(BaseAPIConfig):
    """API config for BioMart."""

    def __init__(self):
        super().__init__(url_builder=_build_biomart_url)


class BioMart_Fetcher(BaseDataFetcher):
    """Fetcher for BioMart (Ensembl) genomic data.

    BioMart provides access to:

    - Gene information (IDs, names, descriptions, coordinates)
    - Transcript and protein data
    - Sequence data (cDNA, coding, peptide)
    - Homology information
    - Variation data
    - GO annotations

    The API has a hierarchical structure:

    - Server: Contains multiple marts (e.g., ENSEMBL_MART_ENSEMBL)
    - Mart: Contains multiple datasets (e.g., hsapiens_gene_ensembl)
    - Dataset: Contains filters and attributes for queries

    Example:
        ```python
        fetcher = BioMart_Fetcher()

        # List available marts
        marts = fetcher.list_marts()
        print(marts.marts)

        # List datasets in a mart
        datasets = fetcher.list_datasets()
        print(datasets.search(contain="human"))

        # Get gene info by Ensembl IDs
        data = fetcher.get_genes(
            ids=["ENSG00000141510", "ENSG00000012048"],
            attributes=["ensembl_gene_id", "external_gene_name", "description"]
        )
        df = data.as_dataframe()

        # Get genes by gene names
        data = fetcher.get_genes_by_name(
            names=["TP53", "BRCA1", "BRCA2"],
            attributes=["ensembl_gene_id", "chromosome_name", "start_position"]
        )
        ```

    Note:
        BioMart API has rate limits and can be slow for large queries.
        Use batching for queries with many filter values.
    """

    def __init__(
        self,
        host: Union[str, BioMartHost] = BioMartHost.main,
        **data_manager_kws: Any,
    ):
        """Initialize BioMart fetcher.

        Args:
            host: BioMart host (default: www.ensembl.org).
            **data_manager_kws: Keyword arguments for BioMartDataManager.
        """
        super().__init__(
            BioMartAPIConfig(),
            BioMartNameSpaceValidator(BioMartQueryModel),
            {}
        )
        self._host = host if isinstance(host, str) else host.value
        self._data_manager = (
            BioMartDataManager(**data_manager_kws)
            if data_manager_kws
            else None
        )
        # Cache for configurations
        self._config_cache: Dict[str, BioMartConfigData] = {}

    @property
    def host(self) -> str:
        """Get current host."""
        return self._host

    def _make_request(
        self,
        url: str,
        params: Dict[str, Any],
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> requests.Response:
        """Make HTTP request with retries.

        Args:
            url: Request URL.
            params: Query parameters.
            retries: Number of retry attempts.
            retry_delay: Delay between retries in seconds.

        Returns:
            Response object.

        Raises:
            ConnectionError: If all retries fail.
        """
        last_error = None
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params, timeout=120)
                if response.status_code == 200:
                    # Check for error in response content
                    if response.text.startswith("Query ERROR"):
                        raise ValueError(f"BioMart query error: {response.text[:200]}")
                    return response
                elif response.status_code >= 500:
                    # Server error, retry
                    last_error = f"Server error ({response.status_code}): {response.text[:200]}"
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    from biodbs.exceptions import raise_for_status
                    raise_for_status(response, "BioMart", url=url)
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                time.sleep(retry_delay * (attempt + 1))
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                time.sleep(retry_delay * (attempt + 1))

        raise APIServerError(
            service="BioMart",
            status_code=500,
            url=url,
            response_text=last_error or "",
        )

    # =========================================================================
    # Discovery methods
    # =========================================================================

    def list_marts(self) -> BioMartRegistryData:
        """List available marts on the server.

        Returns:
            BioMartRegistryData with mart information.
        """
        model = BioMartServerModel(host=self._host)
        url = model.build_url()
        params = model.build_query_params()

        response = self._make_request(url, params)
        return BioMartRegistryData(response.text)

    def list_datasets(
        self,
        mart: Union[str, BioMartMart] = BioMartMart.ensembl,
    ) -> BioMartDatasetsData:
        """List datasets available in a mart.

        Args:
            mart: Mart name (default: ENSEMBL_MART_ENSEMBL).

        Returns:
            BioMartDatasetsData with dataset information.
        """
        mart_name = mart if isinstance(mart, str) else mart.value
        model = BioMartMartModel(host=self._host, mart=mart_name)
        url = model.build_url()
        params = model.build_query_params()

        response = self._make_request(url, params)
        return BioMartDatasetsData(response.text)

    def get_config(
        self,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        use_cache: bool = True,
    ) -> BioMartConfigData:
        """Get dataset configuration (filters and attributes).

        Args:
            dataset: Dataset name.
            use_cache: Whether to use cached configuration.

        Returns:
            BioMartConfigData with filters and attributes.
        """
        dataset_name = dataset if isinstance(dataset, str) else dataset.value

        if use_cache and dataset_name in self._config_cache:
            return self._config_cache[dataset_name]

        model = BioMartConfigModel(host=self._host, dataset=dataset_name)
        url = model.build_url()
        params = model.build_query_params()

        response = self._make_request(url, params)
        config = BioMartConfigData(response.text)

        if use_cache:
            self._config_cache[dataset_name] = config

        return config

    def list_attributes(
        self,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        contain: Optional[str] = None,
        pattern: Optional[str] = None,
    ) -> Any:
        """List available attributes for a dataset.

        Args:
            dataset: Dataset name.
            contain: Filter attributes containing this string.
            pattern: Filter attributes matching this regex pattern.

        Returns:
            DataFrame with attribute information.
        """
        config = self.get_config(dataset)
        return config.get_attributes(contain=contain, pattern=pattern)

    def list_filters(
        self,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        contain: Optional[str] = None,
        pattern: Optional[str] = None,
    ) -> Any:
        """List available filters for a dataset.

        Args:
            dataset: Dataset name.
            contain: Filter filters containing this string.
            pattern: Filter filters matching this regex pattern.

        Returns:
            DataFrame with filter information.
        """
        config = self.get_config(dataset)
        return config.get_filters(contain=contain, pattern=pattern)

    # =========================================================================
    # Query methods
    # =========================================================================

    def query(
        self,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        attributes: Optional[List[str]] = None,
        filters: Optional[Dict[str, Union[str, List[str]]]] = None,
        unique_rows: bool = True,
    ) -> BioMartQueryData:
        """Execute a BioMart query.

        Args:
            dataset: Dataset name.
            attributes: List of attributes to retrieve.
            filters: Dict of filter name to value(s).
            unique_rows: Whether to return unique rows only.

        Returns:
            BioMartQueryData with query results.
        """
        if attributes is None:
            attributes = DEFAULT_QUERY_ATTRIBUTES

        dataset_name = dataset if isinstance(dataset, str) else dataset.value

        model = BioMartQueryModel(
            host=self._host,
            dataset=dataset_name,
            attributes=attributes,
            filters=filters,
            unique_rows=unique_rows,
        )

        url = model.build_url()
        params = model.build_query_params()

        response = self._make_request(url, params)
        return BioMartQueryData(response.text, columns=attributes)

    def batch_query(
        self,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        attributes: Optional[List[str]] = None,
        filter_name: str = "ensembl_gene_id",
        filter_values: List[str] = None,
        batch_size: int = 500,
        max_workers: int = 4,
        show_progress: bool = True,
    ) -> BioMartQueryData:
        """Execute a batched BioMart query for many filter values.

        BioMart has limits on query size, so large filter lists are
        split into batches and queried in parallel using threads.

        Args:
            dataset: Dataset name.
            attributes: List of attributes to retrieve.
            filter_name: Name of the filter to batch.
            filter_values: List of filter values.
            batch_size: Number of values per batch.
            max_workers: Number of parallel workers.
            show_progress: Whether to show progress bar.

        Returns:
            Combined BioMartQueryData with all results.
        """
        if filter_values is None or len(filter_values) == 0:
            return BioMartQueryData("", columns=attributes)

        if attributes is None:
            attributes = DEFAULT_QUERY_ATTRIBUTES

        dataset_name = dataset if isinstance(dataset, str) else dataset.value

        batch_model = BioMartBatchQueryModel(
            host=self._host,
            dataset=dataset_name,
            attributes=attributes,
            filter_name=filter_name,
            filter_values=filter_values,
            batch_size=batch_size,
        )

        batches = batch_model.get_batches()
        logger.info(
            "Batching %d values into %d batches of size %d",
            len(filter_values), len(batches), batch_size
        )

        if len(batches) == 1:
            return self.query(
                dataset=dataset_name,
                attributes=attributes,
                filters={filter_name: filter_values},
            )

        def _fetch_batch(batch: List[str]) -> BioMartQueryData:
            """Fetch a single batch."""
            return self.query(
                dataset=dataset_name,
                attributes=attributes,
                filters={filter_name: batch},
            )

        # Use ThreadPoolExecutor for parallel fetching
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_fetch_batch, batch): i for i, batch in enumerate(batches)}

            iterator = concurrent.futures.as_completed(futures)
            if show_progress:
                iterator = tqdm(iterator, total=len(batches), desc="Fetching batches")

            for future in iterator:
                try:
                    result = future.result()
                    if not result.has_error() and len(result) > 0:
                        results.append(result)
                except Exception as e:
                    logger.warning("Batch %d failed: %s", futures[future], e)

        # Combine results
        if not results:
            return BioMartQueryData("", columns=attributes)

        combined = results[0]
        for result in results[1:]:
            combined += result

        return combined.drop_duplicates()

    # =========================================================================
    # Convenience methods
    # =========================================================================

    def get_genes(
        self,
        ids: List[str],
        attributes: Optional[List[str]] = None,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        batch_size: int = 500,
    ) -> BioMartQueryData:
        """Get gene information by Ensembl gene IDs.

        Args:
            ids: List of Ensembl gene IDs.
            attributes: Attributes to retrieve. Defaults to common gene attributes.
            dataset: Dataset name.
            batch_size: Batch size for large queries.

        Returns:
            BioMartQueryData with gene information.
        """
        if attributes is None:
            attributes = [
                "ensembl_gene_id",
                "external_gene_name",
                "description",
                "gene_biotype",
                "chromosome_name",
                "start_position",
                "end_position",
                "strand",
            ]

        if len(ids) <= batch_size:
            return self.query(
                dataset=dataset,
                attributes=attributes,
                filters={"ensembl_gene_id": ids},
            )
        else:
            return self.batch_query(
                dataset=dataset,
                attributes=attributes,
                filter_name="ensembl_gene_id",
                filter_values=ids,
                batch_size=batch_size,
            )

    def get_genes_by_name(
        self,
        names: List[str],
        attributes: Optional[List[str]] = None,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        batch_size: int = 500,
    ) -> BioMartQueryData:
        """Get gene information by gene names (symbols).

        Args:
            names: List of gene names/symbols.
            attributes: Attributes to retrieve.
            dataset: Dataset name.
            batch_size: Batch size for large queries.

        Returns:
            BioMartQueryData with gene information.
        """
        if attributes is None:
            attributes = [
                "ensembl_gene_id",
                "external_gene_name",
                "description",
                "chromosome_name",
                "start_position",
                "end_position",
            ]

        if len(names) <= batch_size:
            return self.query(
                dataset=dataset,
                attributes=attributes,
                filters={"external_gene_name": names},
            )
        else:
            return self.batch_query(
                dataset=dataset,
                attributes=attributes,
                filter_name="external_gene_name",
                filter_values=names,
                batch_size=batch_size,
            )

    def get_genes_by_chromosome(
        self,
        chromosome: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
        attributes: Optional[List[str]] = None,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
    ) -> BioMartQueryData:
        """Get genes on a chromosome, optionally within a region.

        Args:
            chromosome: Chromosome name (e.g., "1", "X", "MT").
            start: Start position (optional).
            end: End position (optional).
            attributes: Attributes to retrieve.
            dataset: Dataset name.

        Returns:
            BioMartQueryData with genes in the region.
        """
        if attributes is None:
            attributes = [
                "ensembl_gene_id",
                "external_gene_name",
                "chromosome_name",
                "start_position",
                "end_position",
                "strand",
                "gene_biotype",
            ]

        filters = {"chromosome_name": chromosome}
        if start is not None:
            filters["start"] = str(start)
        if end is not None:
            filters["end"] = str(end)

        return self.query(
            dataset=dataset,
            attributes=attributes,
            filters=filters,
        )

    def get_transcripts(
        self,
        gene_ids: List[str],
        attributes: Optional[List[str]] = None,
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        batch_size: int = 500,
    ) -> BioMartQueryData:
        """Get transcript information for genes.

        Args:
            gene_ids: List of Ensembl gene IDs.
            attributes: Attributes to retrieve.
            dataset: Dataset name.
            batch_size: Batch size for large queries.

        Returns:
            BioMartQueryData with transcript information.
        """
        if attributes is None:
            attributes = [
                "ensembl_gene_id",
                "ensembl_transcript_id",
                "external_gene_name",
                "external_transcript_name",
                "transcript_biotype",
                "transcript_length",
            ]

        if len(gene_ids) <= batch_size:
            return self.query(
                dataset=dataset,
                attributes=attributes,
                filters={"ensembl_gene_id": gene_ids},
            )
        else:
            return self.batch_query(
                dataset=dataset,
                attributes=attributes,
                filter_name="ensembl_gene_id",
                filter_values=gene_ids,
                batch_size=batch_size,
            )

    def get_go_annotations(
        self,
        gene_ids: List[str],
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        batch_size: int = 500,
    ) -> BioMartQueryData:
        """Get Gene Ontology annotations for genes.

        Args:
            gene_ids: List of Ensembl gene IDs.
            dataset: Dataset name.
            batch_size: Batch size for large queries.

        Returns:
            BioMartQueryData with GO annotations.
        """
        attributes = [
            "ensembl_gene_id",
            "external_gene_name",
            "go_id",
            "name_1006",  # GO term name
            "namespace_1003",  # GO namespace (BP, MF, CC)
        ]

        if len(gene_ids) <= batch_size:
            return self.query(
                dataset=dataset,
                attributes=attributes,
                filters={"ensembl_gene_id": gene_ids},
            )
        else:
            return self.batch_query(
                dataset=dataset,
                attributes=attributes,
                filter_name="ensembl_gene_id",
                filter_values=gene_ids,
                batch_size=batch_size,
            )

    def get_homologs(
        self,
        gene_ids: List[str],
        target_species: str = "mmusculus",
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        batch_size: int = 500,
    ) -> BioMartQueryData:
        """Get homolog information for genes.

        Args:
            gene_ids: List of Ensembl gene IDs.
            target_species: Target species for homologs (e.g., "mmusculus").
            dataset: Dataset name.
            batch_size: Batch size for large queries.

        Returns:
            BioMartQueryData with homolog information.
        """
        attributes = [
            "ensembl_gene_id",
            "external_gene_name",
            f"{target_species}_homolog_ensembl_gene",
            f"{target_species}_homolog_associated_gene_name",
            f"{target_species}_homolog_orthology_type",
            f"{target_species}_homolog_perc_id",
        ]

        if len(gene_ids) <= batch_size:
            return self.query(
                dataset=dataset,
                attributes=attributes,
                filters={"ensembl_gene_id": gene_ids},
            )
        else:
            return self.batch_query(
                dataset=dataset,
                attributes=attributes,
                filter_name="ensembl_gene_id",
                filter_values=gene_ids,
                batch_size=batch_size,
            )

    def convert_ids(
        self,
        ids: List[str],
        from_type: str = "ensembl_gene_id",
        to_type: str = "external_gene_name",
        dataset: Union[str, BioMartDataset] = BioMartDataset.hsapiens_gene,
        batch_size: int = 500,
    ) -> BioMartQueryData:
        """Convert between different ID types.

        Common ID types:
        - ensembl_gene_id
        - ensembl_transcript_id
        - ensembl_peptide_id
        - external_gene_name
        - entrezgene_id
        - uniprot_gn_id
        - hgnc_symbol
        - hgnc_id
        - refseq_mrna
        - refseq_peptide

        Args:
            ids: List of IDs to convert.
            from_type: Source ID type (also used as filter).
            to_type: Target ID type.
            dataset: Dataset name.
            batch_size: Batch size for large queries.

        Returns:
            BioMartQueryData with ID mappings.
        """
        attributes = [from_type, to_type]

        if len(ids) <= batch_size:
            return self.query(
                dataset=dataset,
                attributes=attributes,
                filters={from_type: ids},
            )
        else:
            return self.batch_query(
                dataset=dataset,
                attributes=attributes,
                filter_name=from_type,
                filter_values=ids,
                batch_size=batch_size,
            )


if __name__ == "__main__":
    fetcher = BioMart_Fetcher()

    print("=" * 60)
    print("BioMart Fetcher Tests")
    print("=" * 60)

    # Test list_marts
    print("\n=== List Marts ===")
    try:
        marts = fetcher.list_marts()
        print(f"Found {len(marts)} marts")
        print(f"Mart names: {marts.marts[:5]}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test list_datasets
    print("\n=== List Datasets ===")
    try:
        datasets = fetcher.list_datasets()
        print(f"Found {len(datasets)} datasets")
        human_datasets = datasets.search(contain="sapiens")
        print(f"Human datasets: {len(human_datasets)}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test get_config
    print("\n=== Get Configuration ===")
    try:
        config = fetcher.get_config("hsapiens_gene_ensembl")
        print(f"Filters: {len(config.filter_names)}")
        print(f"Attributes: {len(config.attribute_names)}")
        print(f"Sample attributes: {config.attribute_names[:5]}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test query
    print("\n=== Query Genes ===")
    try:
        data = fetcher.get_genes(
            ids=["ENSG00000141510", "ENSG00000012048"],
            attributes=["ensembl_gene_id", "external_gene_name", "description"]
        )
        print(f"Found {len(data)} genes")
        df = data.as_dataframe()
        print(df)
    except Exception as e:
        print(f"Failed: {e}")

    print("\nBioMart Fetcher ready!")
