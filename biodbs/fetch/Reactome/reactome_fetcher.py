"""Reactome API fetcher following the standardized pattern."""

from typing import Dict, Any, List, Optional, Union
import logging
import requests

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.Reactome._data_model import (
    ReactomeBase,
    ReactomeAnalysisEndpoint,
    ReactomeContentEndpoint,
    AnalysisRequestModel,
)
from biodbs.data.Reactome.data import (
    ReactomeFetchedData,
    ReactomePathwaysData,
    ReactomeSpeciesData,
)

logger = logging.getLogger(__name__)


class Reactome_APIConfig(BaseAPIConfig):
    """API configuration for Reactome."""

    def __init__(
        self,
        analysis_base: str = ReactomeBase.ANALYSIS.value,
        content_base: str = ReactomeBase.CONTENT.value,
    ):
        super().__init__()
        self._analysis_base = analysis_base
        self._content_base = content_base

    def get_analysis_url(self, endpoint: str) -> str:
        """Build URL for Analysis Service endpoint."""
        return f"{self._analysis_base}/{endpoint}"

    def get_content_url(self, endpoint: str) -> str:
        """Build URL for Content Service endpoint."""
        return f"{self._content_base}/{endpoint}"


class Reactome_Fetcher(BaseDataFetcher):
    """Fetcher for Reactome pathway analysis and content APIs.

    Reactome provides comprehensive pathway analysis including:
        - Over-representation analysis (ORA)
        - Expression analysis
        - Species comparison
        - Pathway hierarchy and content

    Examples::

        fetcher = Reactome_Fetcher()

        # Perform pathway analysis
        genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
        result = fetcher.analyze(genes)
        print(result.significant_pathways().as_dataframe())

        # Analysis with projection to human
        result = fetcher.analyze_projection(genes, species="Mus musculus")

        # Get top-level pathways
        pathways = fetcher.get_pathways_top("Homo sapiens")
        print(pathways.get_pathway_names())

        # Get species list
        species = fetcher.get_species()
        print(species.get_species_names())
    """

    def __init__(self, species: str = "Homo sapiens"):
        """Initialize Reactome fetcher.

        Args:
            species: Default species for analysis (e.g., "Homo sapiens").
        """
        self._species = species
        self._api_config = Reactome_APIConfig()
        super().__init__(self._api_config, NameSpace(AnalysisRequestModel), {})

    def set_species(self, species: str):
        """Change the default species.

        Args:
            species: Species name (e.g., "Homo sapiens", "Mus musculus").
        """
        self._species = species

    def analyze(
        self,
        identifiers: List[str],
        species: Optional[str] = None,
        interactors: bool = False,
        page_size: int = 100,
        sort_by: str = "ENTITIES_FDR",
        order: str = "ASC",
        resource: str = "TOTAL",
        p_value: float = 1.0,
        include_disease: bool = True,
        min_entities: Optional[int] = None,
        max_entities: Optional[int] = None,
    ) -> ReactomeFetchedData:
        """Perform pathway over-representation analysis.

        Submits identifiers to Reactome Analysis Service and returns
        enriched pathways with statistics.

        Args:
            identifiers: List of identifiers (gene symbols, UniProt IDs, etc.).
            species: Species name. None uses default.
            interactors: Include interactors in analysis.
            page_size: Number of results per page.
            sort_by: Sort field (ENTITIES_FDR, ENTITIES_PVALUE, etc.).
            order: Sort order (ASC, DESC).
            resource: Resource filter (TOTAL, UNIPROT, ENSEMBL, etc.).
            p_value: P-value cutoff for filtering results.
            include_disease: Include disease pathways.
            min_entities: Minimum pathway size.
            max_entities: Maximum pathway size.

        Returns:
            ReactomeFetchedData with pathway enrichment results.

        Example:
            >>> fetcher = Reactome_Fetcher()
            >>> genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
            >>> result = fetcher.analyze(genes)
            >>> print(result.significant_pathways(fdr_threshold=0.01).as_dataframe())
        """
        species = species or self._species

        # Build request
        model = AnalysisRequestModel(
            identifiers=identifiers,
            species=species,
            interactors=interactors,
            pageSize=page_size,
            sortBy=sort_by,
            order=order,
            resource=resource,
            pValue=p_value,
            includeDisease=include_disease,
            min_entities=min_entities,
            max_entities=max_entities,
        )

        url = self._api_config.get_analysis_url(
            ReactomeAnalysisEndpoint.IDENTIFIERS.value
        )

        # POST identifiers as text/plain
        headers = {"Content-Type": "text/plain"}
        params = model.get_params()

        response = requests.post(
            url,
            data=model.get_identifiers_string(),
            params=params,
            headers=headers,
        )

        if response.status_code != 200:
            raise ConnectionError(
                f"Reactome analysis failed. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        token = data.get("summary", {}).get("token")

        return ReactomeFetchedData(
            content=data,
            token=token,
            query_identifiers=identifiers,
        )

    def analyze_projection(
        self,
        identifiers: List[str],
        species: Optional[str] = None,
        interactors: bool = False,
        page_size: int = 100,
        sort_by: str = "ENTITIES_FDR",
        order: str = "ASC",
        resource: str = "TOTAL",
        p_value: float = 1.0,
        include_disease: bool = True,
    ) -> ReactomeFetchedData:
        """Analyze identifiers and project results to Homo sapiens.

        This is useful for analyzing data from other species while viewing
        results in the context of human pathways.

        Args:
            identifiers: List of identifiers.
            species: Source species name (for mapping).
            interactors: Include interactors.
            page_size: Results per page.
            sort_by: Sort field.
            order: Sort order.
            resource: Resource filter.
            p_value: P-value cutoff.
            include_disease: Include disease pathways.

        Returns:
            ReactomeFetchedData with human-projected pathway results.
        """
        species = species or self._species

        model = AnalysisRequestModel(
            identifiers=identifiers,
            species=species,
            interactors=interactors,
            pageSize=page_size,
            sortBy=sort_by,
            order=order,
            resource=resource,
            pValue=p_value,
            includeDisease=include_disease,
        )

        url = self._api_config.get_analysis_url(
            ReactomeAnalysisEndpoint.IDENTIFIERS_PROJECTION.value
        )

        headers = {"Content-Type": "text/plain"}
        params = model.get_params()

        response = requests.post(
            url,
            data=model.get_identifiers_string(),
            params=params,
            headers=headers,
        )

        if response.status_code != 200:
            raise ConnectionError(
                f"Reactome projection analysis failed. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        token = data.get("summary", {}).get("token")

        return ReactomeFetchedData(
            content=data,
            token=token,
            query_identifiers=identifiers,
        )

    def analyze_single(
        self,
        identifier: str,
        species: Optional[str] = None,
        interactors: bool = False,
    ) -> ReactomeFetchedData:
        """Analyze a single identifier across species.

        Args:
            identifier: Single identifier to analyze.
            species: Species filter.
            interactors: Include interactors.

        Returns:
            ReactomeFetchedData with pathways containing the identifier.
        """
        species = species or self._species

        endpoint = ReactomeAnalysisEndpoint.IDENTIFIER.value.format(id=identifier)
        url = self._api_config.get_analysis_url(endpoint)

        params = {
            "interactors": str(interactors).lower(),
            "species": species,
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise ConnectionError(
                f"Reactome single analysis failed. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        token = data.get("summary", {}).get("token")

        return ReactomeFetchedData(
            content=data,
            token=token,
            query_identifiers=[identifier],
        )

    def get_result_by_token(
        self,
        token: str,
        species: Optional[str] = None,
        page_size: int = 100,
        page: int = 1,
        sort_by: str = "ENTITIES_FDR",
        order: str = "ASC",
        resource: str = "TOTAL",
        p_value: float = 1.0,
    ) -> ReactomeFetchedData:
        """Retrieve analysis results by token.

        Args:
            token: Analysis token from previous analysis.
            species: Species filter.
            page_size: Results per page.
            page: Page number.
            sort_by: Sort field.
            order: Sort order.
            resource: Resource filter.
            p_value: P-value cutoff.

        Returns:
            ReactomeFetchedData with analysis results.
        """
        endpoint = ReactomeAnalysisEndpoint.TOKEN.value.format(token=token)
        url = self._api_config.get_analysis_url(endpoint)

        params = {
            "pageSize": page_size,
            "page": page,
            "sortBy": sort_by,
            "order": order,
            "resource": resource,
            "pValue": p_value,
        }
        if species:
            params["species"] = species

        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to retrieve results by token. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()

        return ReactomeFetchedData(
            content=data,
            token=token,
        )

    def get_found_entities(
        self,
        token: str,
        pathway_id: str,
    ) -> List[Dict[str, Any]]:
        """Get entities found in a specific pathway.

        Args:
            token: Analysis token.
            pathway_id: Pathway stable ID (e.g., "R-HSA-123456").

        Returns:
            List of found entity dictionaries.
        """
        endpoint = ReactomeAnalysisEndpoint.TOKEN_FOUND_ENTITIES.value.format(
            token=token, pathway=pathway_id
        )
        url = self._api_config.get_analysis_url(endpoint)

        response = requests.get(url)

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get found entities. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_not_found_identifiers(self, token: str) -> List[str]:
        """Get identifiers that were not found in Reactome.

        Args:
            token: Analysis token.

        Returns:
            List of unmapped identifier strings.
        """
        endpoint = ReactomeAnalysisEndpoint.TOKEN_NOT_FOUND.value.format(token=token)
        url = self._api_config.get_analysis_url(endpoint)

        response = requests.get(url)

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get not-found identifiers. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        # Response is list of objects with "id" field
        return [item.get("id", "") for item in data if isinstance(item, dict)]

    def download_results_json(self, token: str) -> Dict[str, Any]:
        """Download complete analysis results as JSON.

        Args:
            token: Analysis token.

        Returns:
            Complete analysis results dictionary.
        """
        endpoint = ReactomeAnalysisEndpoint.DOWNLOAD_JSON.value.format(token=token)
        url = self._api_config.get_analysis_url(endpoint)

        response = requests.get(url)

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to download results. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def map_identifiers(
        self,
        identifiers: List[str],
        interactors: bool = False,
    ) -> List[Dict[str, Any]]:
        """Map identifiers to Reactome entities without analysis.

        Args:
            identifiers: List of identifiers to map.
            interactors: Include interactor mapping.

        Returns:
            List of mapped entity dictionaries.
        """
        url = self._api_config.get_analysis_url(
            ReactomeAnalysisEndpoint.MAPPING.value
        )

        headers = {"Content-Type": "text/plain"}
        params = {"interactors": str(interactors).lower()}

        response = requests.post(
            url,
            data="\n".join(identifiers),
            params=params,
            headers=headers,
        )

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to map identifiers. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    # Content Service methods

    def get_pathways_top(self, species: Optional[str] = None) -> ReactomePathwaysData:
        """Get top-level pathways for a species.

        Args:
            species: Species name (e.g., "Homo sapiens").

        Returns:
            ReactomePathwaysData with top-level pathway information.

        Example:
            >>> fetcher = Reactome_Fetcher()
            >>> pathways = fetcher.get_pathways_top("Homo sapiens")
            >>> print(pathways.get_pathway_names())
        """
        species = species or self._species

        endpoint = ReactomeContentEndpoint.PATHWAYS_TOP.value.format(species=species)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get top pathways. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return ReactomePathwaysData(content=response.json())

    def get_events_hierarchy(
        self,
        species: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get full event hierarchy for a species.

        Args:
            species: Species name.

        Returns:
            List of event hierarchy dictionaries.
        """
        species = species or self._species

        endpoint = ReactomeContentEndpoint.EVENTS_HIERARCHY.value.format(species=species)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get events hierarchy. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_pathways_for_entity(
        self,
        entity_id: str,
    ) -> ReactomePathwaysData:
        """Get pathways containing a specific entity.

        Args:
            entity_id: Entity identifier (UniProt, gene symbol, etc.).

        Returns:
            ReactomePathwaysData with pathways containing the entity.
        """
        endpoint = ReactomeContentEndpoint.PATHWAYS_LOW_ENTITY.value.format(id=entity_id)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get pathways for entity. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return ReactomePathwaysData(content=response.json())

    def get_species(self) -> ReactomeSpeciesData:
        """Get all species in Reactome.

        Returns:
            ReactomeSpeciesData with species information.

        Example:
            >>> fetcher = Reactome_Fetcher()
            >>> species = fetcher.get_species()
            >>> print(species.get_species_names()[:10])
        """
        url = self._api_config.get_content_url(
            ReactomeContentEndpoint.SPECIES_ALL.value
        )

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get species list. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return ReactomeSpeciesData(content=response.json())

    def get_species_main(self) -> ReactomeSpeciesData:
        """Get main species with curated or computationally inferred pathways.

        Returns:
            ReactomeSpeciesData with main species information.
        """
        url = self._api_config.get_content_url(
            ReactomeContentEndpoint.SPECIES_MAIN.value
        )

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get main species list. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return ReactomeSpeciesData(content=response.json())

    def get_database_version(self) -> str:
        """Get current Reactome database version.

        Returns:
            Database version string.
        """
        url = self._api_config.get_analysis_url(
            ReactomeAnalysisEndpoint.DATABASE_VERSION.value
        )

        response = requests.get(url)

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get database version. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.text.strip()

    def query_entry(self, entry_id: str) -> Dict[str, Any]:
        """Query a Reactome entry by ID.

        Args:
            entry_id: Reactome stable ID (e.g., "R-HSA-123456").

        Returns:
            Entry details dictionary.
        """
        endpoint = ReactomeContentEndpoint.QUERY.value.format(id=entry_id)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to query entry. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()


if __name__ == "__main__":
    fetcher = Reactome_Fetcher()

    # Test database version
    print("=== Database Version ===")
    version = fetcher.get_database_version()
    print(f"Version: {version}")

    # Test species
    print("\n=== Species ===")
    species = fetcher.get_species_main()
    print(f"Main species: {species.get_species_names()[:5]}")

    # Test top pathways
    print("\n=== Top Pathways ===")
    pathways = fetcher.get_pathways_top("Homo sapiens")
    print(f"Found {len(pathways)} top-level pathways")
    print(f"Examples: {pathways.get_pathway_names()[:5]}")

    # Test analysis
    print("\n=== Pathway Analysis ===")
    genes = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS", "AKT1", "PIK3CA"]
    result = fetcher.analyze(genes)
    print(result.summary())
