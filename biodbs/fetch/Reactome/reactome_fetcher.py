"""Reactome API fetcher following the standardized pattern."""

from typing import Dict, Any, List, Optional
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

    Example:
        ```python
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
        ```
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

    # =========================================================================
    # Participants endpoints (for getting pathway gene members)
    # =========================================================================

    def get_participants(self, event_id: str) -> List[Dict[str, Any]]:
        """Get all participants in an event (pathway/reaction).

        Args:
            event_id: Reactome stable ID (e.g., "R-HSA-69278").

        Returns:
            List of participant dictionaries with physical entity info.

        Example:
            >>> fetcher = Reactome_Fetcher()
            >>> participants = fetcher.get_participants("R-HSA-69278")
            >>> for p in participants[:3]:
            ...     print(p.get("displayName"))
        """
        endpoint = ReactomeContentEndpoint.PARTICIPANTS.value.format(id=event_id)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get participants. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_participants_physical_entities(
        self, event_id: str
    ) -> List[Dict[str, Any]]:
        """Get participating physical entities in an event.

        Args:
            event_id: Reactome stable ID.

        Returns:
            List of physical entity dictionaries.
        """
        endpoint = ReactomeContentEndpoint.PARTICIPANTS_PHYSICAL_ENTITIES.value.format(
            id=event_id
        )
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get participating physical entities. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_participants_reference_entities(
        self, event_id: str
    ) -> List[Dict[str, Any]]:
        """Get reference entities (genes/proteins) for an event.

        This returns the external database references (UniProt, NCBI Gene, etc.)
        for all participants in a pathway or reaction.

        Args:
            event_id: Reactome stable ID (e.g., "R-HSA-69278").

        Returns:
            List of reference entity dictionaries containing:
                - identifier: External ID (e.g., UniProt accession)
                - databaseName: Source database (e.g., "UniProt")
                - displayName: Human-readable name
                - geneName: Gene symbol (if available)

        Example:
            >>> fetcher = Reactome_Fetcher()
            >>> refs = fetcher.get_participants_reference_entities("R-HSA-69278")
            >>> for ref in refs[:5]:
            ...     print(f"{ref.get('geneName')}: {ref.get('identifier')}")
        """
        endpoint = ReactomeContentEndpoint.PARTICIPANTS_REFERENCE_ENTITIES.value.format(
            id=event_id
        )
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get reference entities. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_pathway_genes(
        self,
        pathway_id: str,
        id_type: str = "gene_symbol",
    ) -> List[str]:
        """Get gene identifiers for a pathway.

        Convenience method that extracts gene IDs from reference entities.

        Args:
            pathway_id: Reactome pathway stable ID.
            id_type: Type of ID to return:
                - "gene_symbol": Gene symbols (default)
                - "uniprot": UniProt accessions
                - "all": Return dict with all available IDs

        Returns:
            List of gene identifiers.

        Example:
            >>> fetcher = Reactome_Fetcher()
            >>> genes = fetcher.get_pathway_genes("R-HSA-69278")
            >>> print(genes[:10])
            ['TP53', 'MDM2', 'CDKN1A', ...]
        """
        refs = self.get_participants_reference_entities(pathway_id)

        if id_type == "gene_symbol":
            genes = []
            for ref in refs:
                gene_name = ref.get("geneName")
                if gene_name:
                    # geneName can be a list or string
                    if isinstance(gene_name, list):
                        genes.extend(gene_name)
                    else:
                        genes.append(gene_name)
            return list(set(genes))

        elif id_type == "uniprot":
            return list(set(
                ref.get("identifier")
                for ref in refs
                if ref.get("databaseName") == "UniProt"
                and ref.get("identifier")
            ))

        else:
            raise ValueError(f"Unknown id_type: {id_type}")

    def get_all_pathways_with_genes(
        self,
        species: Optional[str] = None,
        id_type: str = "gene_symbol",
        include_hierarchy: bool = True,
    ) -> Dict[str, tuple]:
        """Get all pathways with their gene members for a species.

        This method builds a complete pathway-gene mapping suitable for
        local over-representation analysis.

        Args:
            species: Species name (e.g., "Homo sapiens").
            id_type: Gene ID type ("gene_symbol" or "uniprot").
            include_hierarchy: If True, include all pathways in hierarchy.
                If False, only top-level pathways.

        Returns:
            Dict mapping pathway_id -> (pathway_name, set of gene IDs).

        Example:
            >>> fetcher = Reactome_Fetcher()
            >>> pathways = fetcher.get_all_pathways_with_genes("Homo sapiens")
            >>> for pid, (name, genes) in list(pathways.items())[:3]:
            ...     print(f"{pid}: {name} ({len(genes)} genes)")

        Note:
            This method makes many API calls and may take several minutes
            for species with many pathways. Results should be cached.
        """
        species = species or self._species

        # Get all pathways
        if include_hierarchy:
            hierarchy = self.get_events_hierarchy(species)
            pathway_ids = self._extract_pathway_ids_from_hierarchy(hierarchy)
        else:
            top_pathways = self.get_pathways_top(species)
            pathway_ids = [
                (p.get("stId"), p.get("displayName", p.get("name", "")))
                for p in top_pathways.pathways
            ]

        result = {}
        for pathway_id, pathway_name in pathway_ids:
            try:
                genes = self.get_pathway_genes(pathway_id, id_type=id_type)
                if genes:
                    result[pathway_id] = (pathway_name, set(genes))
            except ConnectionError:
                logger.warning(f"Failed to get genes for pathway: {pathway_id}")
                continue

        return result

    def _extract_pathway_ids_from_hierarchy(
        self, hierarchy: List[Dict[str, Any]]
    ) -> List[tuple]:
        """Extract all pathway IDs and names from hierarchy.

        Args:
            hierarchy: Events hierarchy from get_events_hierarchy().

        Returns:
            List of (pathway_id, pathway_name) tuples.
        """
        pathways = []

        def _extract_recursive(events: List[Dict[str, Any]]):
            for event in events:
                stId = event.get("stId", "")
                name = event.get("name", "")
                if stId and stId.startswith("R-"):
                    pathways.append((stId, name))
                # Recurse into children
                children = event.get("children", [])
                if children:
                    _extract_recursive(children)

        _extract_recursive(hierarchy)
        return pathways

    # =========================================================================
    # Events endpoints
    # =========================================================================

    def get_event_ancestors(self, event_id: str) -> List[Dict[str, Any]]:
        """Get ancestor pathways for an event.

        Args:
            event_id: Reactome stable ID.

        Returns:
            List of ancestor pathway dictionaries.
        """
        endpoint = ReactomeContentEndpoint.EVENT_ANCESTORS.value.format(id=event_id)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get event ancestors. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    # =========================================================================
    # Entity endpoints
    # =========================================================================

    def get_complex_subunits(self, complex_id: str) -> List[Dict[str, Any]]:
        """Get subunits of a complex.

        Args:
            complex_id: Reactome complex stable ID.

        Returns:
            List of subunit dictionaries.
        """
        endpoint = ReactomeContentEndpoint.COMPLEX_SUBUNITS.value.format(id=complex_id)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get complex subunits. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_entity_component_of(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get complexes/sets that contain an entity.

        Args:
            entity_id: Reactome entity stable ID.

        Returns:
            List of container entity dictionaries.
        """
        endpoint = ReactomeContentEndpoint.ENTITY_COMPONENT_OF.value.format(id=entity_id)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get entity containers. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_entity_other_forms(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get other forms of a physical entity.

        Args:
            entity_id: Reactome entity stable ID.

        Returns:
            List of other form dictionaries.
        """
        endpoint = ReactomeContentEndpoint.ENTITY_OTHER_FORMS.value.format(id=entity_id)
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get entity other forms. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    # =========================================================================
    # Disease endpoints
    # =========================================================================

    def get_diseases(self) -> List[Dict[str, Any]]:
        """Get all disease objects in Reactome.

        Returns:
            List of disease dictionaries.
        """
        url = self._api_config.get_content_url(
            ReactomeContentEndpoint.DISEASES.value
        )

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get diseases. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    def get_diseases_doid(self) -> List[str]:
        """Get all Disease Ontology IDs (DOIDs) in Reactome.

        Returns:
            List of DOID strings.
        """
        url = self._api_config.get_content_url(
            ReactomeContentEndpoint.DISEASES_DOID.value
        )

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to get disease DOIDs. "
                f"Status: {response.status_code}, Message: {response.text}"
            )

        return response.json()

    # =========================================================================
    # Mapping endpoints
    # =========================================================================

    def map_to_reactions(
        self, identifier: str, resource: str = "UniProt"
    ) -> List[Dict[str, Any]]:
        """Map an identifier to Reactome reactions.

        Args:
            identifier: External identifier (e.g., UniProt accession).
            resource: Source database ("UniProt", "NCBI", "ENSEMBL", etc.).

        Returns:
            List of reaction dictionaries.
        """
        endpoint = ReactomeContentEndpoint.MAPPING_REACTIONS.value.format(
            resource=resource, identifier=identifier
        )
        url = self._api_config.get_content_url(endpoint)

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to map identifier to reactions. "
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
