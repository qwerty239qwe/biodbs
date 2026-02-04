"""Disease Ontology fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from biodbs.data.DiseaseOntology._data_model import (
    DiseaseTerm,
    DiseaseTermDetailed,
    SearchResult,
    OntologyInfo,
    XRef,
)
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class DOFetchedData(BaseFetchedData):
    """Fetched data from Disease Ontology API.

    Contains disease term data including:
        - Disease ID (DOID), name, definition
        - Synonyms and cross-references
        - Ontology subset membership

    Attributes:
        terms: List of DiseaseTerm objects.
        total_count: Total number of terms.
    """

    def __init__(
        self,
        content: Union[dict, list],
        query_ids: Optional[List[str]] = None,
    ):
        """Initialize DOFetchedData.

        Args:
            content: Raw API response.
            query_ids: Original query identifiers.
        """
        super().__init__(content)
        self.query_ids = query_ids or []

        # Parse response
        if isinstance(content, dict):
            # Single term response from direct DO API
            if "id" in content or "doid" in content:
                term = self._parse_term(content)
                self.terms = [term] if term else []
            # Single term response from OLS API (has obo_id or label)
            elif "obo_id" in content or "label" in content:
                term = self._parse_ols_term(content)
                self.terms = [term] if term else []
            # OLS embedded response (list of terms)
            elif "_embedded" in content:
                terms_data = content.get("_embedded", {}).get("terms", [])
                self.terms = [t for t in (self._parse_ols_term(td) for td in terms_data) if t]
            else:
                self.terms = []
            self.total_count = len(self.terms)
        elif isinstance(content, list):
            self.terms = [t for t in (self._parse_term(td) for td in content) if t]
            self.total_count = len(self.terms)
        else:
            self.terms = []
            self.total_count = 0

    def _parse_term(self, data: Dict) -> Optional[DiseaseTerm]:
        """Parse direct DO API term data."""
        try:
            doid = data.get("id") or data.get("doid")
            name = data.get("name", "")

            # Handle definition - may have escaped characters
            definition = data.get("definition")
            if definition:
                definition = definition.strip('"').replace("\\:", ":")

            return DiseaseTerm(
                doid=doid,
                name=name,
                definition=definition,
                synonyms=self._parse_synonyms(data.get("synonyms")),
                xrefs=data.get("xrefs"),
                subsets=data.get("subsets"),
                is_obsolete=data.get("is_obsolete", False),
            )
        except Exception:
            return None

    def _parse_ols_term(self, data: Dict) -> Optional[DiseaseTermDetailed]:
        """Parse OLS API term data."""
        try:
            doid = data.get("obo_id") or data.get("short_form", "").replace("_", ":")
            name = data.get("label", "")

            # Get definition from description
            descriptions = data.get("description", [])
            definition = descriptions[0] if descriptions else None

            # Parse synonyms
            synonyms = data.get("synonyms", [])

            # Parse xrefs from annotation (preferred) or obo_xref
            # Use set to avoid duplicates
            xrefs_set = set()
            annotation = data.get("annotation", {})
            if annotation:
                db_xrefs = annotation.get("database_cross_reference", [])
                xrefs_set.update(db_xrefs)

            # Only use obo_xref if annotation doesn't have xrefs
            if not xrefs_set:
                obo_xrefs = data.get("obo_xref", [])
                if obo_xrefs:
                    for xref in obo_xrefs:
                        if isinstance(xref, dict):
                            db = xref.get("database", "")
                            id_ = xref.get("id", "")
                            if db and id_:
                                xrefs_set.add(f"{db}:{id_}")

            xrefs = list(xrefs_set)

            return DiseaseTermDetailed(
                doid=doid,
                name=name,
                definition=definition,
                synonyms=synonyms,
                xrefs=xrefs if xrefs else None,
                subsets=data.get("in_subset"),
                is_obsolete=data.get("is_obsolete", False),
                has_children=data.get("has_children", False),
                is_root=data.get("is_root", False),
                iri=data.get("iri"),
                short_form=data.get("short_form"),
                ontology_name=data.get("ontology_name", "doid"),
                ontology_prefix=data.get("ontology_prefix", "DOID"),
                annotation=annotation,
                in_subset=data.get("in_subset"),
            )
        except Exception:
            return None

    def _parse_synonyms(self, synonyms: Optional[List]) -> Optional[List[str]]:
        """Parse synonyms, handling DO format 'name EXACT []'."""
        if not synonyms:
            return None
        parsed = []
        for syn in synonyms:
            if isinstance(syn, str):
                # Remove DO format annotations like "EXACT []"
                if " EXACT " in syn:
                    syn = syn.split(" EXACT ")[0]
                elif " RELATED " in syn:
                    syn = syn.split(" RELATED ")[0]
                elif " NARROW " in syn:
                    syn = syn.split(" NARROW ")[0]
                elif " BROAD " in syn:
                    syn = syn.split(" BROAD ")[0]
                parsed.append(syn.strip())
        return parsed if parsed else None

    def __len__(self) -> int:
        return len(self.terms)

    def __iadd__(self, other: "DOFetchedData") -> "DOFetchedData":
        """Concatenate results from another DOFetchedData."""
        self.terms.extend(other.terms)
        self.total_count += other.total_count
        return self

    @property
    def results(self) -> List[DiseaseTerm]:
        """Get disease term results."""
        return self.terms

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return terms as list of dicts."""
        results = []
        for term in self.terms:
            record = {
                "doid": term.doid,
                "name": term.name,
                "definition": term.definition,
                "synonyms": ", ".join(term.synonyms) if term.synonyms else None,
                "xrefs": ", ".join(term.xrefs) if term.xrefs else None,
                "mesh_id": term.mesh_id,
                "umls_cui": term.umls_cui,
                "icd10_code": term.icd10_code,
                "is_obsolete": term.is_obsolete,
            }
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
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def show_columns(self) -> List[str]:
        """Return list of available column names."""
        return [
            "doid", "name", "definition", "synonyms", "xrefs",
            "mesh_id", "umls_cui", "icd10_code", "is_obsolete"
        ]

    def get_doids(self) -> List[str]:
        """Get list of DOIDs."""
        return [t.doid for t in self.terms]

    def get_names(self) -> List[str]:
        """Get list of disease names."""
        return [t.name for t in self.terms]

    def get_term(self, doid: str) -> Optional[DiseaseTerm]:
        """Get a specific term by DOID."""
        # Normalize DOID format
        if not doid.startswith("DOID:"):
            doid = f"DOID:{doid}"
        for t in self.terms:
            if t.doid == doid:
                return t
        return None

    def get_term_by_name(self, name: str) -> Optional[DiseaseTerm]:
        """Get term by name (case-insensitive partial match)."""
        name_lower = name.lower()
        for t in self.terms:
            if name_lower in t.name.lower():
                return t
        return None

    def filter_by_xref_db(self, database: str) -> "DOFetchedData":
        """Filter terms that have cross-reference to a specific database.

        Args:
            database: Database name (e.g., "MESH", "UMLS_CUI").

        Returns:
            New DOFetchedData with filtered terms.
        """
        filtered = [t for t in self.terms if t.get_xref(database)]
        result = DOFetchedData.__new__(DOFetchedData)
        result._content = self._content
        result.query_ids = self.query_ids
        result.terms = filtered
        result.total_count = len(filtered)
        return result

    def to_xref_mapping(self, database: str) -> Dict[str, str]:
        """Create mapping from DOID to external database ID.

        Args:
            database: Target database (e.g., "MESH", "UMLS_CUI").

        Returns:
            Dictionary mapping DOID to external ID.
        """
        return {
            t.doid: t.get_xref(database)
            for t in self.terms
            if t.get_xref(database)
        }

    def summary(self) -> str:
        """Get a text summary of the results."""
        lines = [
            "Disease Ontology Results",
            "=" * 40,
            f"Query IDs: {len(self.query_ids)}",
            f"Terms found: {len(self.terms)}",
        ]

        if self.terms:
            lines.append("\nTop 5 terms:")
            for t in self.terms[:5]:
                def_short = (t.definition[:40] + "...") if t.definition and len(t.definition) > 40 else (t.definition or "N/A")
                lines.append(f"  {t.doid}: {t.name} - {def_short}")

        return "\n".join(lines)


class DOSearchFetchedData(BaseFetchedData):
    """Fetched data from Disease Ontology search."""

    def __init__(
        self,
        content: Dict,
        query: Optional[str] = None,
    ):
        """Initialize DOSearchFetchedData.

        Args:
            content: Raw search response.
            query: Original search query.
        """
        super().__init__(content)
        self.query = query

        # Parse OLS search response
        response = content.get("response", {})
        self.results = self._parse_results(response.get("docs", []))
        self.total_count = response.get("numFound", len(self.results))
        self.start = response.get("start", 0)

    def _parse_results(self, docs: List[Dict]) -> List[SearchResult]:
        """Parse search result documents."""
        results = []
        for doc in docs:
            try:
                results.append(SearchResult(
                    iri=doc.get("iri", ""),
                    obo_id=doc.get("obo_id", ""),
                    label=doc.get("label", ""),
                    description=doc.get("description"),
                    synonyms=doc.get("exact_synonyms") or doc.get("related_synonyms"),
                    ontology_name=doc.get("ontology_name", "doid"),
                    short_form=doc.get("short_form"),
                ))
            except Exception:
                pass
        return results

    def __len__(self) -> int:
        return len(self.results)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return results as list of dicts."""
        results = []
        for r in self.results:
            record = {
                "doid": r.doid,
                "name": r.name,
                "definition": r.definition,
                "synonyms": ", ".join(r.synonyms) if r.synonyms else None,
            }
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
        """Convert to DataFrame."""
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def get_doids(self) -> List[str]:
        """Get list of DOIDs from search results."""
        return [r.doid for r in self.results]

    def get_names(self) -> List[str]:
        """Get list of disease names from search results."""
        return [r.name for r in self.results]


class DODataManager(BaseDBManager):
    """Data manager for Disease Ontology data."""

    def __init__(
        self,
        storage_path,
        db_name: str = "disease_ontology",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_disease_data(
        self,
        data: DOFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save DOFetchedData to storage."""
        if fmt == "csv" and data.terms:
            records = data.as_dict(columns) if columns else data.as_dict()
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.as_dict(), filename, key=key)
        elif fmt == "jsonl" and data.terms:
            return self.stream_json_lines(iter(data.as_dict()), filename, key=key)
        else:
            raise ValueError(f"Cannot save format {fmt} for empty data")
