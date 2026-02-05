"""EnrichR API fetcher following the standardized pattern."""

from typing import Dict, Any, List
import logging
import requests

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.EnrichR._data_model import (
    EnrichRBase,
    EnrichREndpoint,
    EnrichRAddListModel,
    AddListResponse,
)
from biodbs.data.EnrichR.data import EnrichRFetchedData, EnrichRLibrariesData

logger = logging.getLogger(__name__)


class EnrichR_APIConfig(BaseAPIConfig):
    """API configuration for EnrichR."""

    def __init__(self, base_url: str = EnrichRBase.HUMAN.value):
        super().__init__()
        self._base_url = base_url

    def set_base_url(self, base_url: str):
        """Update the base URL."""
        self._base_url = base_url

    def get_url(self, endpoint: str) -> str:
        """Build URL for a specific endpoint."""
        return f"{self._base_url}/{endpoint}"


class EnrichR_Fetcher(BaseDataFetcher):
    """Fetcher for EnrichR gene set enrichment analysis API.

    EnrichR provides enrichment analysis against 200+ gene set libraries
    covering pathways, ontologies, transcription factors, and more.

    Supported organisms:
        - human (default)
        - mouse
        - fly (FlyEnrichr)
        - yeast (YeastEnrichr)
        - worm (WormEnrichr)
        - fish (FishEnrichr)

    Examples::

        fetcher = EnrichR_Fetcher()

        # Get available gene set libraries
        libraries = fetcher.get_libraries()
        print(libraries.get_library_names()[:10])

        # Perform enrichment analysis
        genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
        result = fetcher.enrich(genes, library="KEGG_2021_Human")
        print(result.significant_terms().get_term_names())

        # Enrichment with custom background
        background = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS", "AKT1", "PIK3CA", ...]
        result = fetcher.enrich_with_background(
            genes=["TP53", "BRCA1"],
            background=background,
            library="GO_Biological_Process_2023"
        )
    """

    def __init__(self, organism: str = "human"):
        """Initialize EnrichR fetcher.

        Args:
            organism: Target organism (human, mouse, fly, yeast, worm, fish).
        """
        self._organism = organism.lower()
        self._api_config = EnrichR_APIConfig(self._get_base_url())
        super().__init__(self._api_config, NameSpace(EnrichRAddListModel), {})

    def _get_base_url(self) -> str:
        """Get base URL for current organism."""
        organism_map = {
            "human": EnrichRBase.HUMAN.value,
            "mouse": EnrichRBase.HUMAN.value,
            "fly": EnrichRBase.FLY.value,
            "yeast": EnrichRBase.YEAST.value,
            "worm": EnrichRBase.WORM.value,
            "fish": EnrichRBase.FISH.value,
        }
        return organism_map.get(self._organism, EnrichRBase.HUMAN.value)

    def set_organism(self, organism: str):
        """Change the target organism.

        Args:
            organism: Target organism (human, mouse, fly, yeast, worm, fish).
        """
        self._organism = organism.lower()
        self._api_config.set_base_url(self._get_base_url())

    def _add_list(
        self,
        genes: List[str],
        description: str = "biodbs gene list",
    ) -> AddListResponse:
        """Submit a gene list to EnrichR.

        Args:
            genes: List of gene symbols.
            description: Description for the gene list.

        Returns:
            AddListResponse with userListId.

        Raises:
            ConnectionError: If the API request fails.
        """
        model = EnrichRAddListModel(
            genes=genes,
            description=description,
            organism=self._organism,
        )

        url = self._api_config.get_url(EnrichREndpoint.ADD_LIST.value)
        payload = {
            "list": (None, model.get_gene_string()),
            "description": (None, model.description),
        }

        response = requests.post(url, files=payload)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to add gene list to EnrichR. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        return AddListResponse(
            userListId=data["userListId"],
            shortId=data.get("shortId"),
        )

    def get_libraries(self) -> EnrichRLibrariesData:
        """Get available gene set libraries and their statistics.

        Returns:
            EnrichRLibrariesData containing library information.

        Example:
            >>> fetcher = EnrichR_Fetcher()
            >>> libs = fetcher.get_libraries()
            >>> kegg_libs = libs.search("KEGG")
            >>> print(kegg_libs.get_library_names())
        """
        url = self._api_config.get_url(EnrichREndpoint.DATASET_STATISTICS.value)
        response = requests.get(url)

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get library statistics. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        # The response has category names as keys, each with a list of libraries
        libraries = []
        if isinstance(data, dict) and "statistics" in data:
            # Newer API format
            for lib in data["statistics"]:
                libraries.append(lib)
        elif isinstance(data, dict):
            # Older format with categories
            for category_name, category_libs in data.items():
                if isinstance(category_libs, list):
                    libraries.extend(category_libs)
        else:
            libraries = data

        return EnrichRLibrariesData(results=libraries)

    def enrich(
        self,
        genes: List[str],
        library: str,
        description: str = "biodbs gene list",
    ) -> EnrichRFetchedData:
        """Perform enrichment analysis against a gene set library.

        Args:
            genes: List of gene symbols to analyze.
            library: Name of the gene set library (e.g., "KEGG_2021_Human").
            description: Description for the gene list.

        Returns:
            EnrichRFetchedData containing enrichment results.

        Example:
            >>> fetcher = EnrichR_Fetcher()
            >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
            >>> result = fetcher.enrich(genes, "KEGG_2021_Human")
            >>> top = result.top_terms(5)
            >>> print(top.get_term_names())
        """
        # Step 1: Add gene list
        add_response = self._add_list(genes, description)

        # Step 2: Get enrichment results
        url = self._api_config.get_url(EnrichREndpoint.ENRICH.value)
        params = {
            "userListId": add_response.userListId,
            "backgroundType": library,
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get enrichment results. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        # Extract results from the library key
        results = data.get(library, [])

        return EnrichRFetchedData(
            results=results,
            query_genes=genes,
            user_list_id=add_response.userListId,
            library_name=library,
        )

    def enrich_multiple(
        self,
        genes: List[str],
        libraries: List[str],
        description: str = "biodbs gene list",
    ) -> Dict[str, EnrichRFetchedData]:
        """Perform enrichment analysis against multiple libraries.

        Args:
            genes: List of gene symbols to analyze.
            libraries: List of library names to query.
            description: Description for the gene list.

        Returns:
            Dictionary mapping library names to EnrichRFetchedData.

        Example:
            >>> fetcher = EnrichR_Fetcher()
            >>> genes = ["TP53", "BRCA1", "EGFR"]
            >>> results = fetcher.enrich_multiple(
            ...     genes,
            ...     ["KEGG_2021_Human", "GO_Biological_Process_2023"]
            ... )
            >>> for lib, data in results.items():
            ...     print(f"{lib}: {len(data)} terms")
        """
        # Add gene list once
        add_response = self._add_list(genes, description)

        results = {}
        for library in libraries:
            url = self._api_config.get_url(EnrichREndpoint.ENRICH.value)
            params = {
                "userListId": add_response.userListId,
                "backgroundType": library,
            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                lib_results = data.get(library, [])
                results[library] = EnrichRFetchedData(
                    results=lib_results,
                    query_genes=genes,
                    user_list_id=add_response.userListId,
                    library_name=library,
                )
            else:
                logger.warning(f"Failed to get results for library {library}")
                results[library] = EnrichRFetchedData(
                    results=[],
                    query_genes=genes,
                    user_list_id=add_response.userListId,
                    library_name=library,
                )

        return results

    def enrich_with_background(
        self,
        genes: List[str],
        background: List[str],
        library: str,
        description: str = "biodbs gene list",
    ) -> EnrichRFetchedData:
        """Perform enrichment analysis with a custom background gene set.

        Uses the speedrichr API for background enrichment.

        Args:
            genes: List of query gene symbols.
            background: List of background gene symbols.
            library: Name of the gene set library.
            description: Description for the gene list.

        Returns:
            EnrichRFetchedData containing enrichment results.

        Example:
            >>> fetcher = EnrichR_Fetcher()
            >>> genes = ["TP53", "BRCA1"]
            >>> background = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS", ...]
            >>> result = fetcher.enrich_with_background(
            ...     genes, background, "GO_Biological_Process_2023"
            ... )
        """
        speed_base = EnrichRBase.SPEED.value

        # Step 1: Add gene list
        url = f"{speed_base}/{EnrichREndpoint.SPEED_ADD_LIST.value}"
        payload = {
            "list": (None, "\n".join(genes)),
            "description": (None, description),
        }
        response = requests.post(url, files=payload)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to add gene list. Status: {response.status_code}"
            )
        user_list_id = response.json()["userListId"]

        # Step 2: Add background
        url = f"{speed_base}/{EnrichREndpoint.SPEED_ADD_BACKGROUND.value}"
        payload = {"background": (None, "\n".join(background))}
        response = requests.post(url, files=payload)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to add background. Status: {response.status_code}"
            )
        background_id = response.json()["backgroundid"]

        # Step 3: Get enrichment with background
        url = f"{speed_base}/{EnrichREndpoint.SPEED_BACKGROUND_ENRICH.value}"
        payload = {
            "userListId": (None, str(user_list_id)),
            "backgroundid": (None, str(background_id)),
            "backgroundType": (None, library),
        }
        response = requests.post(url, files=payload)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get background enrichment. Status: {response.status_code}"
            )

        data = response.json()
        results = data.get(library, data.get("results", []))

        return EnrichRFetchedData(
            results=results,
            query_genes=genes,
            user_list_id=user_list_id,
            library_name=library,
        )

    def view_gene_list(self, user_list_id: int) -> List[str]:
        """Retrieve a previously submitted gene list.

        Args:
            user_list_id: The userListId from a previous addList call.

        Returns:
            List of gene symbols.
        """
        url = self._api_config.get_url(EnrichREndpoint.VIEW.value)
        params = {"userListId": user_list_id}

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to view gene list. Status: {response.status_code}"
            )

        data = response.json()
        return data.get("genes", [])

    def get_gene_map(self, gene: str, library: str) -> Dict[str, Any]:
        """Get gene set membership for a single gene.

        Args:
            gene: Gene symbol.
            library: Gene set library name.

        Returns:
            Dictionary with gene set membership information.
        """
        url = self._api_config.get_url(EnrichREndpoint.GEN_MAP.value)
        params = {"gene": gene, "backgroundType": library}

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get gene map. Status: {response.status_code}"
            )

        return response.json()

    def export_results(
        self,
        user_list_id: int,
        library: str,
        filename: str = "enrichr_results",
    ) -> str:
        """Export enrichment results as text.

        Args:
            user_list_id: The userListId from a previous addList call.
            library: Gene set library name.
            filename: Output filename (without extension).

        Returns:
            Tab-separated enrichment results as string.
        """
        url = self._api_config.get_url(EnrichREndpoint.EXPORT.value)
        params = {
            "userListId": user_list_id,
            "backgroundType": library,
            "filename": filename,
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to export results. Status: {response.status_code}"
            )

        return response.text

    # Convenience methods for common library queries
    def enrich_kegg(
        self,
        genes: List[str],
        year: str = "2021",
    ) -> EnrichRFetchedData:
        """Perform KEGG pathway enrichment.

        Args:
            genes: List of gene symbols.
            year: KEGG library year version.

        Returns:
            EnrichRFetchedData with KEGG pathway enrichment.
        """
        library = f"KEGG_{year}_Human"
        return self.enrich(genes, library)

    def enrich_go_bp(self, genes: List[str], year: str = "2023") -> EnrichRFetchedData:
        """Perform GO Biological Process enrichment.

        Args:
            genes: List of gene symbols.
            year: GO library year version.

        Returns:
            EnrichRFetchedData with GO BP enrichment.
        """
        library = f"GO_Biological_Process_{year}"
        return self.enrich(genes, library)

    def enrich_go_mf(self, genes: List[str], year: str = "2023") -> EnrichRFetchedData:
        """Perform GO Molecular Function enrichment.

        Args:
            genes: List of gene symbols.
            year: GO library year version.

        Returns:
            EnrichRFetchedData with GO MF enrichment.
        """
        library = f"GO_Molecular_Function_{year}"
        return self.enrich(genes, library)

    def enrich_go_cc(self, genes: List[str], year: str = "2023") -> EnrichRFetchedData:
        """Perform GO Cellular Component enrichment.

        Args:
            genes: List of gene symbols.
            year: GO library year version.

        Returns:
            EnrichRFetchedData with GO CC enrichment.
        """
        library = f"GO_Cellular_Component_{year}"
        return self.enrich(genes, library)

    def enrich_reactome(self, genes: List[str], year: str = "2022") -> EnrichRFetchedData:
        """Perform Reactome pathway enrichment.

        Args:
            genes: List of gene symbols.
            year: Reactome library year version.

        Returns:
            EnrichRFetchedData with Reactome enrichment.
        """
        library = f"Reactome_{year}"
        return self.enrich(genes, library)

    def enrich_wikipathways(
        self,
        genes: List[str],
        year: str = "2023",
    ) -> EnrichRFetchedData:
        """Perform WikiPathways enrichment.

        Args:
            genes: List of gene symbols.
            year: WikiPathways library year version.

        Returns:
            EnrichRFetchedData with WikiPathways enrichment.
        """
        library = f"WikiPathway_{year}_Human"
        return self.enrich(genes, library)


if __name__ == "__main__":
    fetcher = EnrichR_Fetcher()

    # Test get libraries
    print("=== Available Libraries ===")
    libs = fetcher.get_libraries()
    print(f"Found {len(libs)} libraries")
    kegg_libs = libs.search("KEGG")
    print(f"KEGG libraries: {kegg_libs.get_library_names()}")

    # Test enrichment
    print("\n=== KEGG Enrichment ===")
    genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS", "AKT1", "PIK3CA"]
    result = fetcher.enrich_kegg(genes)
    print(f"Found {len(result)} terms")
    top = result.top_terms(5)
    for term in top.get_enrichment_terms():
        print(f"  {term.term_name}: p={term.adjusted_p_value:.2e}")
