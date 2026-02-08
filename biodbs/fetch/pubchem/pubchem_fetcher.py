"""PubChem PUG REST and PUG View API fetcher following the standardized pattern.

PubChem provides two REST APIs:

1. PUG REST - Programmatic access to structured data:
   https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}/{namespace}/{identifiers}/{operation}/{output}

2. PUG View - Access to annotation/web page content:
   https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/{record_type}/{record_id}/{output}
"""

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.PubChem._data_model import (
    PUGRestModel, PUGViewModel, PUGViewHeading,
)
from biodbs.data.PubChem.data import (
    PUGRestFetchedData, PUGViewFetchedData,
    PubChemFetchedData, PubChemDataManager,
)
from typing import Dict, Any, List, Literal, Optional, Union
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)


def _build_pug_rest_url(params: Dict[str, Any]) -> str:
    """Build PubChem PUG REST API URL from validated parameters.

    PUG REST API structure:
        https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}/{namespace}/{identifiers}/{operation}/{output}
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    path = params.get("_path", "")
    return f"{base_url}/{path}"


def _build_pug_view_url(params: Dict[str, Any]) -> str:
    """Build PubChem PUG View API URL from validated parameters.

    PUG View API structure:
        https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/{record_type}/{record_id}/{output}
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"
    path = params.get("_path", "")
    return f"{base_url}/{path}"


class PUGRestNameSpaceValidator(NameSpace):
    """Namespace that validates parameters via PUGRestModel."""

    def __init__(self):
        super().__init__(PUGRestModel)

    def validate(self, **kwargs):
        """Validate and compute derived fields (path, query params)."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = PUGRestModel(**kwargs)
            self._valid_params["_path"] = model.build_path()
            self._valid_params["_query_params"] = model.build_query_params()
        return is_valid, err_msg


class PUGViewNameSpaceValidator(NameSpace):
    """Namespace that validates parameters via PUGViewModel."""

    def __init__(self):
        super().__init__(PUGViewModel)

    def validate(self, **kwargs):
        """Validate and compute derived fields (path, query params)."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = PUGViewModel(**kwargs)
            self._valid_params["_path"] = model.build_path()
            self._valid_params["_query_params"] = model.build_query_params()
        return is_valid, err_msg


# Backwards compatibility alias
PubChemNameSpaceValidator = PUGRestNameSpaceValidator


class PUGRestAPIConfig(BaseAPIConfig):
    """API config for PubChem PUG REST API."""

    def __init__(self):
        super().__init__(url_builder=_build_pug_rest_url)


class PUGViewAPIConfig(BaseAPIConfig):
    """API config for PubChem PUG View API."""

    def __init__(self):
        super().__init__(url_builder=_build_pug_view_url)


# Backwards compatibility alias
PubChem_APIConfig = PUGRestAPIConfig


class PubChem_Fetcher(BaseDataFetcher):
    """Fetcher for PubChem PUG REST and PUG View APIs.

    PubChem provides two REST APIs:

    **PUG REST** - Structured data access:

    - Compound records (structures, properties, synonyms)
    - Substance records (deposited data)
    - Bioassay data
    - Gene and protein information
    - Structure searches (similarity, substructure)

    **PUG View** - Annotation/web page content:

    - Detailed compound annotations
    - Safety and hazards information
    - Pharmacology and biochemistry
    - Literature and patents
    - Drug and medication information

    Example:
        ```python
        fetcher = PubChem_Fetcher()

        # Get compound by CID
        aspirin = fetcher.get_compound(2244)
        print(aspirin.results[0])

        # Get compound properties
        props = fetcher.get_properties(
            [2244, 3672],
            properties=["MolecularFormula", "MolecularWeight"]
        )
        df = props.as_dataframe()

        # Search by name
        results = fetcher.search_by_name("aspirin")

        # Similarity search
        similar = fetcher.similarity_search(
            smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
            threshold=90
        )

        # Get safety data
        safety = fetcher.get_safety_data(2244)

        # Get pharmacology info
        pharma = fetcher.get_pharmacology(2244)
        ```
    """

    def __init__(self, **data_manager_kws):
        super().__init__(PUGRestAPIConfig(), PUGRestNameSpaceValidator(), {})
        # Secondary configs for PUG View API
        self._view_api_config = PUGViewAPIConfig()
        self._view_namespace = PUGViewNameSpaceValidator()
        self._data_manager = (
            PubChemDataManager(**data_manager_kws)
            if data_manager_kws
            else None
        )

    def get(
        self,
        domain: str,
        namespace: str,
        identifiers: Optional[Union[str, int, List[Union[str, int]]]] = None,
        operation: Optional[str] = None,
        properties: Optional[List[str]] = None,
        output: str = "JSON",
        search_type: Optional[str] = None,
        threshold: Optional[int] = None,
        max_records: Optional[int] = None,
    ) -> PUGRestFetchedData:
        """Fetch data from PubChem PUG REST API.

        Args:
            domain: PubChem domain (compound, substance, assay, etc.).
            namespace: Identifier namespace (cid, name, smiles, etc.).
            identifiers: ID(s) to look up.
            operation: Operation to perform (property, synonyms, etc.).
            properties: List of properties for property operation.
            output: Output format (JSON, XML, CSV, SDF, PNG).
            search_type: For structure searches (smiles, smarts, inchi).
            threshold: Similarity threshold (0-100) for similarity searches.
            max_records: Maximum records to return.

        Returns:
            PUGRestFetchedData with parsed results.
        """
        # Normalize identifiers to list format for validation
        if identifiers is not None and not isinstance(identifiers, list):
            identifiers = [identifiers]

        is_valid, err_msg = self._namespace.validate(
            domain=domain,
            namespace=namespace,
            identifiers=identifiers,
            operation=operation,
            properties=properties,
            output=output,
            search_type=search_type,
            threshold=threshold,
            max_records=max_records,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url
        query_params = self._namespace.valid_params.get("_query_params", {})

        # Determine if binary response expected
        is_binary = output.upper() in ["PNG", "SDF"]

        response = requests.get(url, params=query_params)
        if response.status_code == 404:
            return PUGRestFetchedData({}, domain=domain, operation=operation)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to fetch data from PubChem PUG REST API. "
                f"Status code: {response.status_code}, Message: {response.text}"
            )

        if is_binary:
            content = response.content
        else:
            content = response.json()

        return PUGRestFetchedData(content, domain=domain, operation=operation)

    def _fetch_batch(
        self,
        url: str,
        query_params: Dict[str, Any],
        domain: str,
        operation: Optional[str] = None,
    ) -> PUGRestFetchedData:
        """Thread-safe fetch for a batch."""
        response = requests.get(url, params=query_params)
        if response.status_code != 200:
            raise ConnectionError(
                f"PubChem PUG REST API error {response.status_code}: {response.text}"
            )
        return PUGRestFetchedData(response.json(), domain=domain, operation=operation)

    def get_all(
        self,
        domain: str,
        namespace: str,
        identifiers: List[Union[str, int]],
        method: Literal["concat", "stream_to_storage"] = "concat",
        batch_size: int = 100,
        rate_limit_per_second: int = 5,
        operation: Optional[str] = None,
        properties: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Union[PUGRestFetchedData, Path]:
        """Fetch data for many identifiers by batching.

        PubChem allows multiple CIDs/SIDs in a single request (comma-separated),
        but there are limits. This method batches requests.

        Args:
            domain: PubChem domain.
            namespace: Identifier namespace.
            identifiers: List of IDs to fetch.
            method: "concat" or "stream_to_storage".
            batch_size: IDs per request (default 100).
            rate_limit_per_second: Max requests per second.
            operation: Operation to perform.
            properties: Properties for property operation.
            **kwargs: Additional parameters.

        Returns:
            Combined PUGRestFetchedData or Path to output file.
        """
        if method == "stream_to_storage" and self._data_manager is None:
            raise ValueError(
                "stream_to_storage requires storage_path in PubChem_Fetcher constructor"
            )

        if not identifiers:
            return PUGRestFetchedData({}, domain=domain, operation=operation)

        # Split into batches
        batches = [
            identifiers[i:i + batch_size]
            for i in range(0, len(identifiers), batch_size)
        ]

        logger.info(
            "Fetching %d identifiers in %d batches (rate=%d/s)",
            len(identifiers),
            len(batches),
            rate_limit_per_second,
        )

        # Fetch first batch
        first_batch = self.get(
            domain=domain,
            namespace=namespace,
            identifiers=batches[0],
            operation=operation,
            properties=properties,
            **kwargs,
        )

        if len(batches) == 1:
            return self._finalise_pubchem(method, [first_batch], domain, operation)

        # Fetch remaining batches
        def _fetch(batch_ids):
            return self.get(
                domain=domain,
                namespace=namespace,
                identifiers=batch_ids,
                operation=operation,
                properties=properties,
                **kwargs,
            )

        remaining_results: list = self.schedule_process(
            get_func=_fetch,
            args_list=[(batch,) for batch in batches[1:]],
            rate_limit_per_second=rate_limit_per_second,
            return_exceptions=True,
        )

        # Collect results
        all_batches: List[PubChemFetchedData] = [first_batch]
        for i, result in enumerate(remaining_results):
            if isinstance(result, Exception):
                logger.warning("Batch %d failed: %s", i + 1, result)
                continue
            if result.results:
                all_batches.append(result)

        return self._finalise_pubchem(method, all_batches, domain, operation)

    def _finalise_pubchem(
        self,
        method: str,
        batches: List[PUGRestFetchedData],
        domain: str,
        operation: Optional[str],
    ) -> Union[PUGRestFetchedData, Path]:
        """Combine fetched batches into the requested output format."""
        filename = f"pubchem_{domain}"
        if operation:
            filename += f"_{operation}"

        if method == "concat":
            result = batches[0]
            for batch in batches[1:]:
                result += batch
            return result

        # stream_to_storage
        for batch in batches:
            if batch.results:
                self._data_manager.stream_json_lines(
                    iter(batch.results), filename, key=filename
                )

        self._data_manager.flush_metadata()
        return self._data_manager.storage_path / f"{filename}.jsonl"

    # =========================================================================
    # PUG REST Convenience methods
    # =========================================================================

    def get_compound(self, cid: int) -> PUGRestFetchedData:
        """Get a compound record by CID."""
        return self.get(domain="compound", namespace="cid", identifiers=cid)

    def get_compounds(self, cids: List[int]) -> PUGRestFetchedData:
        """Get multiple compound records by CID."""
        return self.get(domain="compound", namespace="cid", identifiers=cids)

    def get_substance(self, sid: int) -> PUGRestFetchedData:
        """Get a substance record by SID."""
        return self.get(domain="substance", namespace="sid", identifiers=sid)

    def get_assay(self, aid: int) -> PUGRestFetchedData:
        """Get an assay record by AID."""
        return self.get(domain="assay", namespace="aid", identifiers=aid)

    def search_by_name(self, name: str) -> PUGRestFetchedData:
        """Search compounds by name."""
        return self.get(domain="compound", namespace="name", identifiers=name)

    def search_by_smiles(self, smiles: str) -> PUGRestFetchedData:
        """Search compounds by SMILES."""
        return self.get(domain="compound", namespace="smiles", identifiers=smiles)

    def search_by_inchikey(self, inchikey: str) -> PUGRestFetchedData:
        """Search compounds by InChIKey."""
        return self.get(domain="compound", namespace="inchikey", identifiers=inchikey)

    def search_by_formula(self, formula: str) -> PUGRestFetchedData:
        """Search compounds by molecular formula."""
        return self.get(domain="compound", namespace="formula", identifiers=formula)

    def get_properties(
        self,
        cids: Union[int, List[int]],
        properties: Optional[List[str]] = None,
    ) -> PUGRestFetchedData:
        """Get compound properties.

        Args:
            cids: Compound ID(s).
            properties: Properties to retrieve. Defaults to common properties.
        """
        if properties is None:
            properties = [
                "MolecularFormula", "MolecularWeight", "CanonicalSMILES",
                "IUPACName", "XLogP", "TPSA", "HBondDonorCount",
                "HBondAcceptorCount", "RotatableBondCount",
            ]
        return self.get(
            domain="compound",
            namespace="cid",
            identifiers=cids,
            operation="property",
            properties=properties,
        )

    def get_synonyms(self, cid: int) -> PUGRestFetchedData:
        """Get synonyms for a compound."""
        return self.get(
            domain="compound",
            namespace="cid",
            identifiers=cid,
            operation="synonyms",
        )

    def get_cids_by_name(self, name: str) -> PUGRestFetchedData:
        """Get CIDs matching a name."""
        return self.get(
            domain="compound",
            namespace="name",
            identifiers=name,
            operation="cids",
        )

    def get_sids_for_compound(self, cid: int) -> PUGRestFetchedData:
        """Get SIDs associated with a compound."""
        return self.get(
            domain="compound",
            namespace="cid",
            identifiers=cid,
            operation="sids",
        )

    def get_aids_for_compound(self, cid: int) -> PUGRestFetchedData:
        """Get assay AIDs associated with a compound."""
        return self.get(
            domain="compound",
            namespace="cid",
            identifiers=cid,
            operation="aids",
        )

    def similarity_search(
        self,
        smiles: str,
        threshold: int = 90,
        max_records: int = 100,
    ) -> PUGRestFetchedData:
        """Find similar compounds by SMILES.

        Args:
            smiles: Query SMILES string.
            threshold: Similarity threshold (0-100).
            max_records: Maximum records to return.
        """
        return self.get(
            domain="compound",
            namespace="fastsimilarity_2d",
            identifiers=smiles,
            search_type="smiles",
            threshold=threshold,
            max_records=max_records,
            operation="cids",
        )

    def substructure_search(
        self,
        smiles: str,
        max_records: int = 100,
    ) -> PUGRestFetchedData:
        """Find compounds containing a substructure.

        Args:
            smiles: Query SMILES string.
            max_records: Maximum records to return.
        """
        return self.get(
            domain="compound",
            namespace="fastsubstructure",
            identifiers=smiles,
            search_type="smiles",
            max_records=max_records,
            operation="cids",
        )

    def get_compound_image(
        self,
        cid: int,
        image_size: str = "large",
    ) -> PUGRestFetchedData:
        """Get compound structure image (PNG).

        Args:
            cid: Compound ID.
            image_size: Image size (small, large, or pixel size like "300x300").
        """
        return self.get(
            domain="compound",
            namespace="cid",
            identifiers=cid,
            output="PNG",
        )

    def get_compound_sdf(self, cid: int) -> PUGRestFetchedData:
        """Get compound structure in SDF format."""
        return self.get(
            domain="compound",
            namespace="cid",
            identifiers=cid,
            output="SDF",
        )

    def get_description(self, cid: int) -> PUGRestFetchedData:
        """Get compound description."""
        return self.get(
            domain="compound",
            namespace="cid",
            identifiers=cid,
            operation="description",
        )

    # =========================================================================
    # PUG View API methods
    # =========================================================================

    def get_view(
        self,
        record_id: Union[int, str],
        record_type: str = "compound",
        heading: Optional[str] = None,
        output: str = "JSON",
    ) -> PUGViewFetchedData:
        """Fetch annotation data from PubChem PUG View API.

        PUG View provides detailed annotation/web page content including
        safety data, pharmacology, literature, patents, etc.

        Args:
            record_id: Record ID (CID for compounds, SID for substances, etc.).
            record_type: Type of record (compound, substance, assay, gene, protein, etc.).
            heading: Optional heading to filter to a specific section.
            output: Output format (JSON or XML).

        Returns:
            PUGViewFetchedData with hierarchical annotation data.
        """
        is_valid, err_msg = self._view_namespace.validate(
            record_type=record_type,
            record_id=record_id,
            heading=heading,
            output=output,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._view_api_config.update_params(**self._view_namespace.valid_params)
        url = self._view_api_config.api_url
        query_params = self._view_namespace.valid_params.get("_query_params", {})

        response = requests.get(url, params=query_params)
        if response.status_code == 404:
            return PUGViewFetchedData({}, record_type=record_type)
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to fetch data from PubChem PUG View API. "
                f"Status code: {response.status_code}, Message: {response.text}"
            )

        return PUGViewFetchedData(response.json(), record_type=record_type)

    def get_compound_annotations(self, cid: int) -> PUGViewFetchedData:
        """Get full annotation data for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData with all annotation sections.
        """
        return self.get_view(record_id=cid, record_type="compound")

    def get_substance_annotations(self, sid: int) -> PUGViewFetchedData:
        """Get full annotation data for a substance.

        Args:
            sid: Substance ID.

        Returns:
            PUGViewFetchedData with all annotation sections.
        """
        return self.get_view(record_id=sid, record_type="substance")

    def get_safety_data(self, cid: int) -> PUGViewFetchedData:
        """Get safety and hazards information for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Safety and Hazards section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.safety_and_hazards.value,
        )

    def get_toxicity_data(self, cid: int) -> PUGViewFetchedData:
        """Get toxicity information for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Toxicity section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.toxicity.value,
        )

    def get_pharmacology(self, cid: int) -> PUGViewFetchedData:
        """Get pharmacology and biochemistry information for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Pharmacology and Biochemistry section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.pharmacology_and_biochemistry.value,
        )

    def get_drug_info(self, cid: int) -> PUGViewFetchedData:
        """Get drug and medication information for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Drug and Medication Information section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.drug_and_medication_information.value,
        )

    def get_literature(self, cid: int) -> PUGViewFetchedData:
        """Get literature references for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Literature section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.literature.value,
        )

    def get_patents(self, cid: int) -> PUGViewFetchedData:
        """Get patent information for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Patents section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.patents.value,
        )

    def get_names_and_identifiers(self, cid: int) -> PUGViewFetchedData:
        """Get names and identifiers for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Names and Identifiers section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.names_and_identifiers.value,
        )

    def get_physical_properties(self, cid: int) -> PUGViewFetchedData:
        """Get chemical and physical properties for a compound.

        Args:
            cid: Compound ID.

        Returns:
            PUGViewFetchedData filtered to Chemical and Physical Properties section.
        """
        return self.get_view(
            record_id=cid,
            record_type="compound",
            heading=PUGViewHeading.chemical_and_physical_properties.value,
        )


if __name__ == "__main__":
    fetcher = PubChem_Fetcher()

    # === PUG REST Tests ===
    print("=" * 60)
    print("PUG REST API Tests")
    print("=" * 60)

    # Test get compound
    print("\n=== Get Aspirin (CID 2244) ===")
    aspirin = fetcher.get_compound(2244)
    print(f"Found {len(aspirin)} record(s)")

    # Test properties
    print("\n=== Get Properties ===")
    props = fetcher.get_properties([2244, 3672])
    print(f"Found {len(props)} records")
    df = props.as_dataframe()
    print(df)

    # Test search by name
    print("\n=== Search by Name ===")
    results = fetcher.search_by_name("aspirin")
    cids = results.get_cids()
    print(f"Found CIDs: {cids[:5]}")

    # Test synonyms
    print("\n=== Get Synonyms ===")
    synonyms = fetcher.get_synonyms(2244)
    print(f"Found {len(synonyms)} synonym record(s)")
    if synonyms.results:
        syns = synonyms.results[0].get("Synonym", [])
        print(f"Sample synonyms: {syns[:5]}")

    # === PUG View Tests ===
    print("\n" + "=" * 60)
    print("PUG View API Tests")
    print("=" * 60)

    # Test get compound annotations
    print("\n=== Get Compound Annotations ===")
    annotations = fetcher.get_compound_annotations(2244)
    print(f"Record type: {annotations.record_type}")
    print(f"Record ID: {annotations.record_id}")
    print(f"Section headings: {annotations.get_all_headings()[:5]}")

    # Test get safety data
    print("\n=== Get Safety Data ===")
    safety = fetcher.get_safety_data(2244)
    if safety.sections:
        print(f"Found safety section with {len(safety.sections)} subsections")
    else:
        print("No safety data found (may be filtered to specific heading)")

    # Test get pharmacology
    print("\n=== Get Pharmacology ===")
    pharma = fetcher.get_pharmacology(2244)
    if pharma.record:
        print("Found pharmacology data")
    else:
        print("No pharmacology data found")

    print("\nPubChem fetcher works with both PUG REST and PUG View APIs!")
