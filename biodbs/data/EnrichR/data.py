"""EnrichR fetched data container."""

from typing import Dict, List, Any, Optional
from biodbs.data._base import BaseFetchedData
from biodbs.data.EnrichR._data_model import (
    EnrichmentTerm,
    EnrichmentResult,
    LibraryStatistics,
)


class EnrichRFetchedData(BaseFetchedData):
    """Container for EnrichR API responses.

    Provides methods for accessing and converting enrichment analysis results.
    """

    def __init__(
        self,
        results: List[Dict[str, Any]],
        query_genes: Optional[List[str]] = None,
        user_list_id: Optional[int] = None,
        library_name: Optional[str] = None,
    ):
        """Initialize EnrichR fetched data.

        Args:
            results: List of result dictionaries.
            query_genes: Original query gene list.
            user_list_id: EnrichR user list ID.
            library_name: Gene set library used.
        """
        super().__init__(results)
        self.query_genes = query_genes or []
        self.user_list_id = user_list_id
        self.library_name = library_name

    @property
    def results(self) -> List[Dict[str, Any]]:
        """Get the results list."""
        return self._content

    def __len__(self) -> int:
        """Return number of results."""
        return len(self._content)

    def get_enrichment_terms(self) -> List[EnrichmentTerm]:
        """Parse results as EnrichmentTerm objects.

        Returns:
            List of EnrichmentTerm objects.
        """
        terms = []
        for i, result in enumerate(self.results):
            if isinstance(result, dict):
                # Already parsed dict format
                # Handle overlapping_genes which may be list or string
                genes = result.get("overlapping_genes", result.get("Genes", []))
                if isinstance(genes, str):
                    genes = genes.split(";") if genes else []
                elif not isinstance(genes, list):
                    genes = []

                terms.append(EnrichmentTerm(
                    rank=result.get("rank", i + 1),
                    term_name=result.get("term_name", result.get("Term", "")),
                    p_value=result.get("p_value", result.get("P-value", 1.0)),
                    z_score=result.get("z_score", result.get("Z-score", 0.0)),
                    combined_score=result.get("combined_score", result.get("Combined Score", 0.0)),
                    overlapping_genes=genes,
                    adjusted_p_value=result.get("adjusted_p_value", result.get("Adjusted P-value", 1.0)),
                    odds_ratio=result.get("odds_ratio", result.get("Odds Ratio")),
                ))
            elif isinstance(result, list):
                # Raw API row format
                terms.append(EnrichmentTerm.from_api_row(result, rank=i + 1))
        return terms

    def get_enrichment_result(self) -> EnrichmentResult:
        """Get results as an EnrichmentResult object.

        Returns:
            EnrichmentResult with all terms.
        """
        return EnrichmentResult(
            library_name=self.library_name or "unknown",
            terms=self.get_enrichment_terms(),
        )

    def significant_terms(
        self,
        p_threshold: float = 0.05,
        use_adjusted: bool = True,
    ) -> "EnrichRFetchedData":
        """Filter to significant terms only.

        Args:
            p_threshold: P-value threshold.
            use_adjusted: Use adjusted p-value if True.

        Returns:
            New EnrichRFetchedData with filtered results.
        """
        terms = self.get_enrichment_terms()
        if use_adjusted:
            filtered = [t for t in terms if t.adjusted_p_value < p_threshold]
        else:
            filtered = [t for t in terms if t.p_value < p_threshold]

        return EnrichRFetchedData(
            results=[t.model_dump() for t in filtered],
            query_genes=self.query_genes,
            user_list_id=self.user_list_id,
            library_name=self.library_name,
        )

    def top_terms(self, n: int = 10) -> "EnrichRFetchedData":
        """Get top N terms by combined score.

        Args:
            n: Number of top terms to return.

        Returns:
            New EnrichRFetchedData with top terms.
        """
        terms = self.get_enrichment_terms()
        top = sorted(terms, key=lambda x: x.combined_score, reverse=True)[:n]

        return EnrichRFetchedData(
            results=[t.model_dump() for t in top],
            query_genes=self.query_genes,
            user_list_id=self.user_list_id,
            library_name=self.library_name,
        )

    def get_term_names(self) -> List[str]:
        """Get list of term names.

        Returns:
            List of term/pathway names.
        """
        return [t.term_name for t in self.get_enrichment_terms()]

    def get_genes_for_term(self, term_name: str) -> List[str]:
        """Get overlapping genes for a specific term.

        Args:
            term_name: Name of the term/pathway.

        Returns:
            List of genes overlapping with the term.
        """
        for term in self.get_enrichment_terms():
            if term.term_name == term_name:
                return term.overlapping_genes
        return []


class EnrichRLibrariesData(BaseFetchedData):
    """Container for EnrichR library statistics."""

    def __init__(self, results: List[Dict[str, Any]]):
        """Initialize EnrichR libraries data.

        Args:
            results: List of library statistic dictionaries.
        """
        super().__init__(results)

    @property
    def results(self) -> List[Dict[str, Any]]:
        """Get the results list."""
        return self._content

    def __len__(self) -> int:
        """Return number of libraries."""
        return len(self._content)

    def get_libraries(self) -> List[LibraryStatistics]:
        """Parse results as LibraryStatistics objects.

        Returns:
            List of LibraryStatistics objects.
        """
        libraries = []
        for result in self.results:
            if isinstance(result, dict):
                libraries.append(LibraryStatistics(**result))
        return libraries

    def get_library_names(self) -> List[str]:
        """Get list of available library names.

        Returns:
            List of library names.
        """
        return [lib.libraryName for lib in self.get_libraries()]

    def filter_by_category(self, category_id: int) -> "EnrichRLibrariesData":
        """Filter libraries by category.

        Args:
            category_id: Category ID (1-8).

        Returns:
            New EnrichRLibrariesData with filtered libraries.
        """
        filtered = [r for r in self.results if r.get("categoryId") == category_id]
        return EnrichRLibrariesData(results=filtered)

    def search(self, query: str) -> "EnrichRLibrariesData":
        """Search libraries by name.

        Args:
            query: Search string (case-insensitive).

        Returns:
            New EnrichRLibrariesData with matching libraries.
        """
        query_lower = query.lower()
        filtered = [
            r for r in self.results
            if query_lower in r.get("libraryName", "").lower()
        ]
        return EnrichRLibrariesData(results=filtered)
