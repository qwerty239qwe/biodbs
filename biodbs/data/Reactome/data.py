"""Reactome fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from biodbs.data.Reactome._data_model import (
    PathwaySummary,
    EntityStatistics,
    ReactionStatistics,
    SpeciesSummary,
    ResourceSummary,
    AnalysisIdentifier,
    FoundEntity,
    SpeciesInfo,
)
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class ReactomeFetchedData(BaseFetchedData):
    """Fetched data from Reactome Analysis Service.

    Contains pathway enrichment analysis results including:
        - Pathway summaries with p-values and FDR
        - Species and resource summaries
        - Expression data (if provided)
        - Token for retrieving additional data

    Attributes:
        token: Analysis token for retrieving additional data.
        pathways: List of pathway summaries.
        species_summary: Summary by species.
        resource_summary: Summary by resource type.
        identifiers_not_found: Count of unmapped identifiers.
        expression: Expression column information.
        warnings: Any warnings from the analysis.
    """

    def __init__(
        self,
        content: Union[dict, list],
        token: Optional[str] = None,
        query_identifiers: Optional[List[str]] = None,
    ):
        """Initialize ReactomeFetchedData.

        Args:
            content: Raw API response.
            token: Analysis token for follow-up queries.
            query_identifiers: Original query identifiers.
        """
        super().__init__(content)
        self.token = token
        self.query_identifiers = query_identifiers or []

        # Parse response
        if isinstance(content, dict):
            self.pathways = self._parse_pathways(content.get("pathways", []))
            self.species_summary = content.get("speciesSummary", [])
            self.resource_summary = content.get("resourceSummary", [])
            self.identifiers_not_found = content.get("identifiersNotFound", 0)
            self.expression = content.get("expression", {})
            self.warnings = content.get("warnings", [])
            self._summary = content.get("summary", {})
            # Extract token from summary if not provided
            if not self.token and self._summary:
                self.token = self._summary.get("token")
        else:
            self.pathways = []
            self.species_summary = []
            self.resource_summary = []
            self.identifiers_not_found = 0
            self.expression = {}
            self.warnings = []
            self._summary = {}

    def _parse_pathways(self, pathways_data: List[Dict]) -> List[PathwaySummary]:
        """Parse pathway data into PathwaySummary objects."""
        pathways = []
        for p in pathways_data:
            # Parse entity statistics
            entities = None
            if "entities" in p:
                e = p["entities"]
                entities = EntityStatistics(
                    curatedFound=e.get("curatedFound", 0),
                    curatedTotal=e.get("curatedTotal", 0),
                    curatedInteractorsFound=e.get("curatedInteractorsFound", 0),
                    curatedInteractorsTotal=e.get("curatedInteractorsTotal", 0),
                    found=e.get("found", 0),
                    total=e.get("total", 0),
                    ratio=e.get("ratio", 0.0),
                    pValue=e.get("pValue", 1.0),
                    fdr=e.get("fdr", 1.0),
                    exp=e.get("exp"),
                )

            # Parse reaction statistics
            reactions = None
            if "reactions" in p:
                r = p["reactions"]
                reactions = ReactionStatistics(
                    found=r.get("found", 0),
                    total=r.get("total", 0),
                    ratio=r.get("ratio", 0.0),
                )

            # Parse species
            species = None
            if "species" in p and p["species"]:
                s = p["species"]
                species = SpeciesSummary(
                    dbId=s.get("dbId", 0),
                    taxId=s.get("taxId", ""),
                    name=s.get("name", ""),
                    pathways=s.get("pathways", 0),
                    filtered=s.get("filtered", 0),
                )

            pathways.append(PathwaySummary(
                stId=p.get("stId", ""),
                dbId=p.get("dbId", 0),
                name=p.get("name", ""),
                species=species,
                llp=p.get("llp", False),
                inDisease=p.get("inDisease", False),
                entities=entities,
                reactions=reactions,
            ))

        return pathways

    def __len__(self) -> int:
        return len(self.pathways)

    def __iadd__(self, other: "ReactomeFetchedData") -> "ReactomeFetchedData":
        """Concatenate results from another ReactomeFetchedData."""
        self.pathways.extend(other.pathways)
        return self

    @property
    def results(self) -> List[PathwaySummary]:
        """Get pathway results."""
        return self.pathways

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary into dot-separated keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return pathways as list of dicts."""
        results = []
        for p in self.pathways:
            record = {
                "stId": p.stId,
                "dbId": p.dbId,
                "name": p.name,
                "llp": p.llp,
                "inDisease": p.inDisease,
                "pValue": p.p_value,
                "fdr": p.fdr,
                "found": p.found_entities,
                "total": p.total_entities,
            }
            if p.entities:
                record["ratio"] = p.entities.ratio
            if p.reactions:
                record["reactions_found"] = p.reactions.found
                record["reactions_total"] = p.reactions.total
            if p.species:
                record["species"] = p.species.name

            if columns:
                record = {k: v for k, v in record.items() if k in columns}
            results.append(record)
        return results

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
        flatten: bool = False,
    ):
        """Convert results to a DataFrame.

        Args:
            columns: Columns to include. None means all columns.
            engine: "pandas" or "polars".
            flatten: If True, flatten nested dictionaries.
        """
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if flatten:
            data = [self._flatten_dict(record) for record in data]

        if engine == "pandas":
            df = pd.DataFrame(data)
            if "fdr" in df.columns:
                df = df.sort_values("fdr")
            return df
        return pl.DataFrame(data)

    def show_columns(self) -> List[str]:
        """Return list of available column names."""
        return [
            "stId", "dbId", "name", "llp", "inDisease",
            "pValue", "fdr", "found", "total", "ratio",
            "reactions_found", "reactions_total", "species"
        ]

    def significant_pathways(
        self,
        fdr_threshold: float = 0.05,
    ) -> "ReactomeFetchedData":
        """Filter to significant pathways only.

        Args:
            fdr_threshold: FDR threshold for significance.

        Returns:
            New ReactomeFetchedData with filtered pathways.
        """
        filtered = [p for p in self.pathways if p.fdr <= fdr_threshold]

        result = ReactomeFetchedData.__new__(ReactomeFetchedData)
        result._content = self._content
        result.token = self.token
        result.query_identifiers = self.query_identifiers
        result.pathways = filtered
        result.species_summary = self.species_summary
        result.resource_summary = self.resource_summary
        result.identifiers_not_found = self.identifiers_not_found
        result.expression = self.expression
        result.warnings = self.warnings
        result._summary = self._summary
        return result

    def top_pathways(self, n: int = 10) -> "ReactomeFetchedData":
        """Get top N pathways by FDR.

        Args:
            n: Number of top pathways to return.

        Returns:
            New ReactomeFetchedData with top pathways.
        """
        sorted_pathways = sorted(self.pathways, key=lambda x: x.fdr)[:n]

        result = ReactomeFetchedData.__new__(ReactomeFetchedData)
        result._content = self._content
        result.token = self.token
        result.query_identifiers = self.query_identifiers
        result.pathways = sorted_pathways
        result.species_summary = self.species_summary
        result.resource_summary = self.resource_summary
        result.identifiers_not_found = self.identifiers_not_found
        result.expression = self.expression
        result.warnings = self.warnings
        result._summary = self._summary
        return result

    def filter(self, **kwargs) -> "ReactomeFetchedData":
        """Filter pathways by attribute values.

        Example:
            data.filter(llp=True)  # Only lowest-level pathways
            data.filter(inDisease=False)  # Exclude disease pathways
        """
        filtered = []
        for pathway in self.pathways:
            match = True
            for key, value in kwargs.items():
                pathway_value = getattr(pathway, key, None)
                if callable(value):
                    if not value(pathway_value):
                        match = False
                        break
                elif pathway_value != value:
                    match = False
                    break
            if match:
                filtered.append(pathway)

        result = ReactomeFetchedData.__new__(ReactomeFetchedData)
        result._content = self._content
        result.token = self.token
        result.query_identifiers = self.query_identifiers
        result.pathways = filtered
        result.species_summary = self.species_summary
        result.resource_summary = self.resource_summary
        result.identifiers_not_found = self.identifiers_not_found
        result.expression = self.expression
        result.warnings = self.warnings
        result._summary = self._summary
        return result

    def get_pathway_ids(self) -> List[str]:
        """Get list of pathway stable IDs."""
        return [p.stId for p in self.pathways]

    def get_pathway_names(self) -> List[str]:
        """Get list of pathway names."""
        return [p.name for p in self.pathways]

    def get_pathway(self, pathway_id: str) -> Optional[PathwaySummary]:
        """Get a specific pathway by ID."""
        for p in self.pathways:
            if p.stId == pathway_id:
                return p
        return None

    def summary(self) -> str:
        """Get a text summary of the results."""
        sig_005 = len([p for p in self.pathways if p.fdr <= 0.05])
        sig_001 = len([p for p in self.pathways if p.fdr <= 0.01])

        lines = [
            "Reactome Analysis Results",
            "=" * 40,
            f"Query identifiers: {len(self.query_identifiers)}",
            f"Not found: {self.identifiers_not_found}",
            f"Pathways tested: {len(self.pathways)}",
            f"Significant (FDR <= 0.05): {sig_005}",
            f"Significant (FDR <= 0.01): {sig_001}",
        ]

        if self.token:
            lines.append(f"Token: {self.token}")

        if self.warnings:
            lines.append(f"Warnings: {len(self.warnings)}")

        if self.pathways:
            top = sorted(self.pathways, key=lambda x: x.fdr)[:5]
            lines.append("\nTop 5 pathways:")
            for p in top:
                lines.append(
                    f"  {p.stId}: {p.name[:40]}... "
                    f"(FDR={p.fdr:.2e}, {p.found_entities}/{p.total_entities})"
                )

        return "\n".join(lines)


class ReactomePathwaysData(BaseFetchedData):
    """Fetched data for Reactome pathways (from Content Service)."""

    def __init__(self, content: Union[dict, list]):
        """Initialize ReactomePathwaysData.

        Args:
            content: Raw API response (list of pathway objects).
        """
        super().__init__(content)
        if isinstance(content, list):
            self.pathways = content
        elif isinstance(content, dict):
            self.pathways = [content]
        else:
            self.pathways = []

    def __len__(self) -> int:
        return len(self.pathways)

    @property
    def results(self) -> List[Dict[str, Any]]:
        """Get pathway results."""
        return self.pathways

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return pathways as list of dicts."""
        if columns:
            return [{k: v for k, v in p.items() if k in columns} for p in self.pathways]
        return self.pathways

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
        flatten: bool = False,
    ):
        """Convert to DataFrame."""
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if flatten:
            flattened = []
            for record in data:
                flat = {}
                for k, v in record.items():
                    if isinstance(v, dict):
                        for sub_k, sub_v in v.items():
                            flat[f"{k}.{sub_k}"] = sub_v
                    else:
                        flat[k] = v
                flattened.append(flat)
            data = flattened

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def get_pathway_ids(self) -> List[str]:
        """Get list of pathway stable IDs."""
        return [p.get("stId", "") for p in self.pathways]

    def get_pathway_names(self) -> List[str]:
        """Get list of pathway names."""
        return [p.get("displayName", p.get("name", "")) for p in self.pathways]


class ReactomeSpeciesData(BaseFetchedData):
    """Fetched data for Reactome species list."""

    def __init__(self, content: list):
        """Initialize ReactomeSpeciesData."""
        super().__init__(content)
        self.species = content if isinstance(content, list) else []

    def __len__(self) -> int:
        return len(self.species)

    @property
    def results(self) -> List[Dict[str, Any]]:
        """Get species results."""
        return self.species

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return species as list of dicts."""
        if columns:
            return [{k: v for k, v in s.items() if k in columns} for s in self.species]
        return self.species

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
        flatten: bool = False,
    ):
        """Convert to DataFrame."""
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def get_species_names(self) -> List[str]:
        """Get list of species names."""
        return [s.get("displayName", "") for s in self.species]

    def get_species_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get species info by name (case-insensitive partial match)."""
        name_lower = name.lower()
        for s in self.species:
            display_name = s.get("displayName", "").lower()
            short_name = s.get("shortName", "").lower()
            if name_lower in display_name or name_lower in short_name:
                return s
        return None

    def get_taxon_id(self, species_name: str) -> Optional[str]:
        """Get taxonomy ID for a species."""
        species = self.get_species_by_name(species_name)
        if species:
            return species.get("taxId", "")
        return None


class ReactomeDataManager(BaseDBManager):
    """Data manager for Reactome data."""

    def __init__(
        self,
        storage_path,
        db_name: str = "reactome",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_analysis_data(
        self,
        data: ReactomeFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save ReactomeFetchedData to storage.

        Args:
            data: The Reactome data to save.
            filename: Base filename (without extension).
            fmt: Output format.
            key: Optional cache key.
            columns: Optional columns to include (for CSV).
        """
        if fmt == "csv" and data.pathways:
            records = data.as_dict(columns) if columns else data.as_dict()
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.as_dict(), filename, key=key)
        elif fmt == "jsonl" and data.pathways:
            return self.stream_json_lines(iter(data.as_dict()), filename, key=key)
        else:
            raise ValueError(f"Cannot save format {fmt} for empty data")
