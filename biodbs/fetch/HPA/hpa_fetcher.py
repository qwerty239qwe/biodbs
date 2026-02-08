"""Human Protein Atlas (HPA) data fetcher following the standardized pattern.

HPA provides protein expression data through several APIs:

1. Individual entry access:
   https://www.proteinatlas.org/{ensembl_id}.{format}

2. Search query downloads:
   https://www.proteinatlas.org/search/{query}?format={format}

3. Customized data retrieval API:
   https://www.proteinatlas.org/api/search_download.php?search={query}&format={format}&columns={columns}

Reference:
- https://www.proteinatlas.org/about/help/dataaccess
- https://www.proteinatlas.org/about/download
"""

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.HPA._data_model import (
    HPAEntryModel,
    HPASearchModel,
    HPASearchDownloadModel,
    HPABulkDownloadModel,
    HPA_COLUMNS,
    DEFAULT_GENE_COLUMNS,
    DEFAULT_EXPRESSION_COLUMNS,
    DEFAULT_SUBCELLULAR_COLUMNS,
    DEFAULT_PATHOLOGY_COLUMNS,
)
from biodbs.data.HPA.data import HPAFetchedData, HPADataManager
from typing import Dict, Any, List, Literal, Optional, Union
from pathlib import Path
import logging
import requests
import gzip

logger = logging.getLogger(__name__)


def _build_entry_url(params: Dict[str, Any]) -> str:
    """Build HPA individual entry URL."""
    return params.get("_url", "")


def _build_search_url(params: Dict[str, Any]) -> str:
    """Build HPA search URL."""
    return params.get("_url", "")


def _build_search_download_url(params: Dict[str, Any]) -> str:
    """Build HPA search/download API URL."""
    return params.get("_url", "")


class HPAEntryNameSpaceValidator(NameSpace):
    """Namespace validator for HPA individual entry access."""

    def __init__(self):
        super().__init__(HPAEntryModel)

    def validate(self, **kwargs):
        """Validate and compute URL."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = HPAEntryModel(**kwargs)
            self._valid_params["_url"] = model.build_url()
        return is_valid, err_msg


class HPASearchNameSpaceValidator(NameSpace):
    """Namespace validator for HPA search query access."""

    def __init__(self):
        super().__init__(HPASearchModel)

    def validate(self, **kwargs):
        """Validate and compute URL and query params."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = HPASearchModel(**kwargs)
            self._valid_params["_url"] = model.build_url()
            self._valid_params["_query_params"] = model.build_query_params()
        return is_valid, err_msg


class HPASearchDownloadNameSpaceValidator(NameSpace):
    """Namespace validator for HPA search/download API."""

    def __init__(self):
        super().__init__(HPASearchDownloadModel)

    def validate(self, **kwargs):
        """Validate and compute URL and query params."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = HPASearchDownloadModel(**kwargs)
            self._valid_params["_url"] = model.build_url()
            self._valid_params["_query_params"] = model.build_query_params()
        return is_valid, err_msg


class HPAEntryAPIConfig(BaseAPIConfig):
    """API config for HPA individual entry access."""

    def __init__(self):
        super().__init__(url_builder=_build_entry_url)


class HPASearchAPIConfig(BaseAPIConfig):
    """API config for HPA search access."""

    def __init__(self):
        super().__init__(url_builder=_build_search_url)


class HPASearchDownloadAPIConfig(BaseAPIConfig):
    """API config for HPA search/download API."""

    def __init__(self):
        super().__init__(url_builder=_build_search_download_url)


class HPA_Fetcher(BaseDataFetcher):
    """Fetcher for Human Protein Atlas data.

    The Human Protein Atlas provides proteomics data including:

    - Tissue expression (protein and RNA)
    - Subcellular location
    - Cell type expression
    - Blood cell expression
    - Brain region expression
    - Cancer/pathology data

    Example:
        ```python
        fetcher = HPA_Fetcher()

        # Get gene data by Ensembl ID
        tp53 = fetcher.get_gene("ENSG00000141510")
        print(tp53.results[0])

        # Search for genes
        results = fetcher.search("TP53")
        print(results.get_gene_names())

        # Get specific columns for genes
        data = fetcher.search_download(
            search="TP53",
            columns=["g", "gs", "eg", "gd", "rnats_s"]
        )
        df = data.as_dataframe()

        # Get expression data with default columns
        expr = fetcher.get_expression("BRCA1")

        # Get subcellular location data
        loc = fetcher.get_subcellular_location("ENSG00000141510")
        ```
    """

    def __init__(self, **data_manager_kws):
        super().__init__(
            HPAEntryAPIConfig(),
            HPAEntryNameSpaceValidator(),
            {"User-Agent": "biodbs/1.0"}
        )
        # Additional API configs for different endpoints
        self._search_api_config = HPASearchAPIConfig()
        self._search_namespace = HPASearchNameSpaceValidator()
        self._search_download_api_config = HPASearchDownloadAPIConfig()
        self._search_download_namespace = HPASearchDownloadNameSpaceValidator()
        self._data_manager = (
            HPADataManager(**data_manager_kws)
            if data_manager_kws
            else None
        )

    def get_gene(
        self,
        ensembl_id: str,
        format: str = "json",
    ) -> HPAFetchedData:
        """Get gene data by Ensembl ID.

        Args:
            ensembl_id: Ensembl gene ID (e.g., "ENSG00000141510").
            format: Output format (json, tsv, xml).

        Returns:
            HPAFetchedData with gene information.
        """
        is_valid, err_msg = self._namespace.validate(
            ensembl_id=ensembl_id,
            format=format,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url

        response = requests.get(url, headers=self._headers)
        if response.status_code == 404:
            return HPAFetchedData([], format=format, query_type="entry")
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to fetch data from HPA. "
                f"Status code: {response.status_code}, Message: {response.text}"
            )

        if format.lower() == "json":
            content = response.json()
        else:
            content = response.text

        return HPAFetchedData(content, format=format, query_type="entry")

    def get_genes(
        self,
        ensembl_ids: List[str],
        format: str = "json",
        rate_limit_per_second: int = 5,
    ) -> HPAFetchedData:
        """Get data for multiple genes by Ensembl IDs.

        Args:
            ensembl_ids: List of Ensembl gene IDs.
            format: Output format.
            rate_limit_per_second: Rate limit for API calls.

        Returns:
            Combined HPAFetchedData.
        """
        if not ensembl_ids:
            return HPAFetchedData([], format=format, query_type="entry")

        # Fetch first gene
        first_result = self.get_gene(ensembl_ids[0], format=format)

        if len(ensembl_ids) == 1:
            return first_result

        # Fetch remaining genes
        def _fetch(ens_id):
            return self.get_gene(ens_id, format=format)

        remaining_results = self.schedule_process(
            get_func=_fetch,
            args_list=[(ens_id,) for ens_id in ensembl_ids[1:]],
            rate_limit_per_second=rate_limit_per_second,
            return_exceptions=True,
        )

        # Combine results
        for i, result in enumerate(remaining_results):
            if isinstance(result, Exception):
                logger.warning("Failed to fetch %s: %s", ensembl_ids[i + 1], result)
                continue
            first_result += result

        return first_result

    def search(
        self,
        query: str,
        format: str = "json",
        compress: str = "no",
    ) -> HPAFetchedData:
        """Search for genes in HPA.

        Args:
            query: Search query (gene name, etc.).
            format: Output format (json, tsv, xml).
            compress: Whether to compress response (yes/no).

        Returns:
            HPAFetchedData with search results.
        """
        is_valid, err_msg = self._search_namespace.validate(
            query=query,
            format=format,
            compress=compress,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._search_api_config.update_params(**self._search_namespace.valid_params)
        url = self._search_api_config.api_url
        query_params = self._search_namespace.valid_params.get("_query_params", {})

        response = requests.get(url, params=query_params, headers=self._headers)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to fetch data from HPA search. "
                f"Status code: {response.status_code}, Message: {response.text}"
            )

        # Handle compressed response
        if compress == "yes" and response.content:
            try:
                content = gzip.decompress(response.content)
                if format.lower() == "json":
                    import json
                    content = json.loads(content.decode("utf-8"))
                else:
                    content = content.decode("utf-8")
            except Exception:
                content = response.content
        else:
            if format.lower() == "json":
                content = response.json()
            else:
                content = response.text

        return HPAFetchedData(content, format=format, query_type="search")

    def search_download(
        self,
        search: str,
        columns: Optional[List[str]] = None,
        format: str = "json",
        compress: str = "no",
    ) -> HPAFetchedData:
        """Fetch customized data using the search_download API.

        This is the most flexible way to retrieve HPA data, allowing
        selection of specific columns.

        Args:
            search: Gene search query.
            columns: List of column specifiers (see HPA_COLUMNS).
                    If None, uses DEFAULT_GENE_COLUMNS.
            format: Output format (json or tsv).
            compress: Whether to compress response (yes/no).

        Returns:
            HPAFetchedData with requested columns.
        """
        if columns is None:
            columns = DEFAULT_GENE_COLUMNS

        is_valid, err_msg = self._search_download_namespace.validate(
            search=search,
            format=format,
            columns=columns,
            compress=compress,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._search_download_api_config.update_params(
            **self._search_download_namespace.valid_params
        )
        url = self._search_download_api_config.api_url
        query_params = self._search_download_namespace.valid_params.get("_query_params", {})

        response = requests.get(url, params=query_params, headers=self._headers)
        if response.status_code == 400:
            # HPA returns 400 for excessive results or bad requests
            raise ValueError(
                f"HPA request failed (400 Bad Request). "
                f"This may indicate too many results or invalid query. "
                f"Message: {response.text}"
            )
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to fetch data from HPA search_download API. "
                f"Status code: {response.status_code}, Message: {response.text}"
            )

        # Handle compressed response
        if compress == "yes" and response.content:
            try:
                content = gzip.decompress(response.content)
                if format.lower() == "json":
                    import json
                    content = json.loads(content.decode("utf-8"))
                else:
                    content = content.decode("utf-8")
            except Exception:
                content = response.content
        else:
            if format.lower() == "json":
                content = response.json()
            else:
                content = response.text

        return HPAFetchedData(content, format=format, query_type="search_download")

    def get_all(
        self,
        search: str,
        columns: Optional[List[str]] = None,
        method: Literal["concat", "stream_to_storage"] = "concat",
        format: str = "json",
        **kwargs: Any,
    ) -> Union[HPAFetchedData, Path]:
        """Fetch data with batching support.

        Note: HPA's search_download API doesn't natively support pagination,
        so this method is mainly useful for storing results.

        Args:
            search: Gene search query.
            columns: List of column specifiers.
            method: "concat" or "stream_to_storage".
            format: Output format.
            **kwargs: Additional parameters.

        Returns:
            HPAFetchedData or Path to stored file.
        """
        if method == "stream_to_storage" and self._data_manager is None:
            raise ValueError(
                "stream_to_storage requires storage_path in HPA_Fetcher constructor"
            )

        data = self.search_download(search=search, columns=columns, format=format)

        if method == "concat":
            return data

        # Stream to storage
        filename = f"hpa_{search.replace(' ', '_')}"
        self._data_manager.stream_json_lines(
            iter(data.results), filename, key=filename
        )
        self._data_manager.flush_metadata()
        return self._data_manager.storage_path / f"{filename}.jsonl"

    # =========================================================================
    # Convenience methods
    # =========================================================================

    def get_expression(
        self,
        search: str,
        columns: Optional[List[str]] = None,
    ) -> HPAFetchedData:
        """Get expression data for gene(s).

        Args:
            search: Gene search query.
            columns: Expression columns to retrieve.
                    If None, uses DEFAULT_EXPRESSION_COLUMNS.

        Returns:
            HPAFetchedData with expression data.
        """
        if columns is None:
            columns = DEFAULT_EXPRESSION_COLUMNS
        return self.search_download(search=search, columns=columns)

    def get_subcellular_location(
        self,
        search: str,
        columns: Optional[List[str]] = None,
    ) -> HPAFetchedData:
        """Get subcellular location data for gene(s).

        Args:
            search: Gene search query.
            columns: Subcellular location columns to retrieve.
                    If None, uses DEFAULT_SUBCELLULAR_COLUMNS.

        Returns:
            HPAFetchedData with subcellular location data.
        """
        if columns is None:
            columns = DEFAULT_SUBCELLULAR_COLUMNS
        return self.search_download(search=search, columns=columns)

    def get_pathology(
        self,
        search: str,
        columns: Optional[List[str]] = None,
    ) -> HPAFetchedData:
        """Get pathology/cancer prognostics data for gene(s).

        Args:
            search: Gene search query.
            columns: Pathology columns to retrieve.
                    If None, uses DEFAULT_PATHOLOGY_COLUMNS.

        Returns:
            HPAFetchedData with pathology data.
        """
        if columns is None:
            columns = DEFAULT_PATHOLOGY_COLUMNS
        return self.search_download(search=search, columns=columns)

    def get_protein_class(
        self,
        search: str,
    ) -> HPAFetchedData:
        """Get protein class information for gene(s).

        Args:
            search: Gene search query.

        Returns:
            HPAFetchedData with protein class information.
        """
        columns = ["g", "eg", "pc", "mclass", "sec"]
        return self.search_download(search=search, columns=columns)

    def get_tissue_expression(
        self,
        search: str,
        tissues: Optional[List[str]] = None,
    ) -> HPAFetchedData:
        """Get tissue-specific RNA expression data.

        Args:
            search: Gene search query.
            tissues: List of tissue column names to include.
                    If None, gets general tissue expression info.

        Returns:
            HPAFetchedData with tissue expression data.
        """
        columns = ["g", "eg", "rnats_s", "rnats_d"]
        if tissues:
            columns.extend(tissues)
        return self.search_download(search=search, columns=columns)

    def get_blood_expression(
        self,
        search: str,
    ) -> HPAFetchedData:
        """Get blood cell expression data for gene(s).

        Args:
            search: Gene search query.

        Returns:
            HPAFetchedData with blood cell expression data.
        """
        columns = ["g", "eg", "rnabts_s", "rnabts_d", "rna_blood"]
        return self.search_download(search=search, columns=columns)

    def get_brain_expression(
        self,
        search: str,
    ) -> HPAFetchedData:
        """Get brain region expression data for gene(s).

        Args:
            search: Gene search query.

        Returns:
            HPAFetchedData with brain region expression data.
        """
        columns = ["g", "eg", "rnabrs_s", "rnabrs_d", "rna_brain"]
        return self.search_download(search=search, columns=columns)

    def download_bulk_data(
        self,
        file_type: str = "json",
        version: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Path:
        """Download bulk HPA data file.

        Args:
            file_type: File type to download (tsv, json, xml).
            version: HPA version number (e.g., "24"). None for latest.
            output_path: Path to save file. If None, saves to data manager path.

        Returns:
            Path to downloaded file.
        """
        model = HPABulkDownloadModel(file_type=file_type, version=version)
        url = model.build_url()

        if output_path:
            filepath = Path(output_path)
        elif self._data_manager:
            ext_map = {"tsv": "tsv.zip", "json": "json.gz", "xml": "xml.gz"}
            filename = f"proteinatlas.{ext_map[file_type]}"
            filepath = self._data_manager.storage_path / filename
        else:
            raise ValueError("output_path required when data_manager not configured")

        logger.info("Downloading HPA bulk data from %s", url)
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to download HPA bulk data. "
                f"Status code: {response.status_code}"
            )

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info("Downloaded HPA bulk data to %s", filepath)
        return filepath

    @staticmethod
    def list_columns() -> Dict[str, str]:
        """List available column specifiers for search_download API.

        Returns:
            Dictionary mapping column codes to descriptions.
        """
        return HPA_COLUMNS.copy()


if __name__ == "__main__":
    fetcher = HPA_Fetcher()

    print("=" * 60)
    print("HPA Fetcher Tests")
    print("=" * 60)

    # Test search_download
    print("\n=== Search Download API ===")
    try:
        data = fetcher.search_download(
            search="TP53",
            columns=["g", "gs", "eg", "gd"]
        )
        print(f"Found {len(data)} records")
        if data.results:
            print(f"Sample: {data.results[0]}")
    except Exception as e:
        print(f"Search download test failed: {e}")

    # Test expression data
    print("\n=== Expression Data ===")
    try:
        expr = fetcher.get_expression("BRCA1")
        print(f"Found {len(expr)} expression records")
    except Exception as e:
        print(f"Expression test failed: {e}")

    # Test subcellular location
    print("\n=== Subcellular Location ===")
    try:
        loc = fetcher.get_subcellular_location("TP53")
        print(f"Found {len(loc)} location records")
    except Exception as e:
        print(f"Subcellular location test failed: {e}")

    # List available columns
    print("\n=== Available Columns ===")
    columns = fetcher.list_columns()
    print(f"Total columns: {len(columns)}")
    print("Sample columns:")
    for i, (code, desc) in enumerate(list(columns.items())[:5]):
        print(f"  {code}: {desc}")

    print("\nHPA Fetcher ready!")
