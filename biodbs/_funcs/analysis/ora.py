"""Over-Representation Analysis (ORA) for gene set enrichment.

This module provides functions for performing over-representation analysis
using the hypergeometric test to identify enriched gene sets or pathways.

Supported pathway databases:
    - KEGG: Pathways from KEGG database
    - GO (QuickGO): Gene Ontology terms
    - EnrichR: External enrichment analysis service

Example:
    >>> from biodbs._funcs.analysis import ora_kegg, ora_go
    >>>
    >>> # KEGG pathway enrichment
    >>> genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]
    >>> result = ora_kegg(genes, organism="hsa", id_type="symbol")
    >>> print(result.as_dataframe().head())
    >>>
    >>> # GO enrichment
    >>> result = ora_go(genes, taxon_id=9606, aspect="biological_process")
    >>> print(result.significant_terms())
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import (
    Dict,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
    Callable,
    Any,
    TYPE_CHECKING,
)
from enum import Enum
import math
from functools import lru_cache
import warnings

if TYPE_CHECKING:
    import pandas as pd


class PathwayDatabase(str, Enum):
    """Supported pathway databases."""

    KEGG = "kegg"
    GO = "go"
    ENRICHR = "enrichr"
    # Future: REACTOME = "reactome"
    # Future: WIKIPATHWAYS = "wikipathways"


class GOAspect(str, Enum):
    """Gene Ontology aspects."""

    BIOLOGICAL_PROCESS = "biological_process"
    MOLECULAR_FUNCTION = "molecular_function"
    CELLULAR_COMPONENT = "cellular_component"
    ALL = "all"


class CorrectionMethod(str, Enum):
    """Multiple testing correction methods."""

    BONFERRONI = "bonferroni"
    BH = "benjamini_hochberg"  # Benjamini-Hochberg FDR
    BY = "benjamini_yekutieli"  # Benjamini-Yekutieli FDR
    HOLM = "holm"
    NONE = "none"


@dataclass
class ORATermResult:
    """Result for a single term/pathway in ORA."""

    term_id: str
    term_name: str
    p_value: float
    adjusted_p_value: float
    overlap_count: int  # k: genes in both query and term
    term_size: int  # K: total genes in term
    query_size: int  # n: query gene count
    background_size: int  # N: background/universe size
    fold_enrichment: float
    overlap_genes: List[str]
    database: str

    @property
    def odds_ratio(self) -> float:
        """Calculate odds ratio for enrichment."""
        # (k / (n - k)) / ((K - k) / (N - K - n + k))
        k = self.overlap_count
        K = self.term_size
        n = self.query_size
        N = self.background_size

        # Avoid division by zero
        if (n - k) == 0 or (K - k) == 0 or (N - K - n + k) == 0:
            return float('inf') if k > 0 else 0.0

        return (k / (n - k)) / ((K - k) / (N - K - n + k))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "term_id": self.term_id,
            "term_name": self.term_name,
            "p_value": self.p_value,
            "adjusted_p_value": self.adjusted_p_value,
            "overlap_count": self.overlap_count,
            "term_size": self.term_size,
            "query_size": self.query_size,
            "background_size": self.background_size,
            "fold_enrichment": self.fold_enrichment,
            "odds_ratio": self.odds_ratio,
            "overlap_genes": ",".join(self.overlap_genes),
            "database": self.database,
        }


@dataclass
class ORAResult:
    """Result container for over-representation analysis."""

    results: List[ORATermResult]
    query_genes: List[str]
    mapped_genes: List[str]  # Genes successfully mapped to pathway DB
    unmapped_genes: List[str]  # Genes that couldn't be mapped
    background_size: int
    database: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def significant_terms(
        self,
        p_threshold: float = 0.05,
        use_adjusted: bool = True,
    ) -> "ORAResult":
        """Filter to only significant terms.

        Args:
            p_threshold: P-value threshold for significance.
            use_adjusted: Use adjusted p-values (default) or raw p-values.

        Returns:
            New ORAResult with only significant terms.
        """
        if use_adjusted:
            filtered = [r for r in self.results if r.adjusted_p_value <= p_threshold]
        else:
            filtered = [r for r in self.results if r.p_value <= p_threshold]

        return ORAResult(
            results=filtered,
            query_genes=self.query_genes,
            mapped_genes=self.mapped_genes,
            unmapped_genes=self.unmapped_genes,
            background_size=self.background_size,
            database=self.database,
            parameters={**self.parameters, "p_threshold": p_threshold},
        )

    def top_terms(self, n: int = 10) -> "ORAResult":
        """Get top N terms by adjusted p-value.

        Args:
            n: Number of top terms to return.

        Returns:
            New ORAResult with top N terms.
        """
        sorted_results = sorted(self.results, key=lambda x: x.adjusted_p_value)
        return ORAResult(
            results=sorted_results[:n],
            query_genes=self.query_genes,
            mapped_genes=self.mapped_genes,
            unmapped_genes=self.unmapped_genes,
            background_size=self.background_size,
            database=self.database,
            parameters=self.parameters,
        )

    def as_dataframe(self, engine: Literal["pandas", "polars"] = "pandas") -> "pd.DataFrame":
        """Convert results to a DataFrame.

        Args:
            engine: DataFrame engine to use ("pandas" or "polars").

        Returns:
            DataFrame with ORA results.
        """
        data = [r.to_dict() for r in self.results]

        if engine == "pandas":
            import pandas as pd
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values("adjusted_p_value")
            return df
        elif engine == "polars":
            import polars as pl
            df = pl.DataFrame(data)
            if len(df) > 0:
                df = df.sort("adjusted_p_value")
            return df
        else:
            raise ValueError(f"Unsupported engine: {engine}")

    def summary(self) -> str:
        """Get a text summary of the results."""
        sig_005 = len([r for r in self.results if r.adjusted_p_value <= 0.05])
        sig_001 = len([r for r in self.results if r.adjusted_p_value <= 0.01])

        lines = [
            f"ORA Results Summary ({self.database})",
            "=" * 40,
            f"Query genes: {len(self.query_genes)}",
            f"Mapped genes: {len(self.mapped_genes)}",
            f"Unmapped genes: {len(self.unmapped_genes)}",
            f"Background size: {self.background_size}",
            f"Terms tested: {len(self.results)}",
            f"Significant (adj.p <= 0.05): {sig_005}",
            f"Significant (adj.p <= 0.01): {sig_001}",
        ]

        if self.results:
            top = sorted(self.results, key=lambda x: x.adjusted_p_value)[:5]
            lines.append("\nTop 5 terms:")
            for r in top:
                lines.append(
                    f"  {r.term_id}: {r.term_name[:40]}... "
                    f"(p={r.adjusted_p_value:.2e}, {r.overlap_count}/{r.term_size})"
                )

        return "\n".join(lines)


# =============================================================================
# Core Statistical Functions
# =============================================================================

def hypergeometric_test(
    k: int,  # overlap: genes in both query and term
    K: int,  # term size: total genes in term
    n: int,  # query size: number of query genes
    N: int,  # background size: total genes in universe
) -> float:
    """Perform hypergeometric test for over-representation.

    Calculates P(X >= k) where X follows a hypergeometric distribution.
    This is a one-sided test for enrichment (over-representation).

    Args:
        k: Number of genes in both query and term (successes in sample).
        K: Total genes in the term (successes in population).
        n: Number of query genes (sample size).
        N: Total genes in background/universe (population size).

    Returns:
        P-value for the hypergeometric test.

    Example:
        >>> # 5 genes overlap between 100 query genes and a term with 50 genes
        >>> # out of 20000 total genes
        >>> p = hypergeometric_test(k=5, K=50, n=100, N=20000)
    """
    if k < 0 or K < 0 or n < 0 or N < 0:
        raise ValueError("All parameters must be non-negative")
    if k > min(n, K):
        raise ValueError("k cannot exceed min(n, K)")
    if K > N or n > N:
        raise ValueError("K and n cannot exceed N")

    # Try to use scipy if available (more accurate for edge cases)
    try:
        from scipy import stats
        # P(X >= k) = 1 - P(X < k) = 1 - P(X <= k-1)
        # scipy.stats.hypergeom.sf(k-1, N, K, n) gives P(X > k-1) = P(X >= k)
        return stats.hypergeom.sf(k - 1, N, K, n)
    except ImportError:
        pass

    # Fallback to pure Python implementation
    # P(X >= k) = sum_{i=k}^{min(n,K)} P(X = i)
    # P(X = i) = C(K, i) * C(N-K, n-i) / C(N, n)

    def _log_comb(n: int, k: int) -> float:
        """Compute log of binomial coefficient using log-gamma."""
        if k < 0 or k > n:
            return float('-inf')
        if k == 0 or k == n:
            return 0.0
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)

    # Calculate P(X >= k) = sum of P(X = i) for i = k to min(n, K)
    max_i = min(n, K)

    # Use log probabilities for numerical stability
    log_denom = _log_comb(N, n)

    p_value = 0.0
    for i in range(k, max_i + 1):
        # P(X = i) = C(K, i) * C(N-K, n-i) / C(N, n)
        log_p = _log_comb(K, i) + _log_comb(N - K, n - i) - log_denom
        if log_p > -700:  # Avoid underflow
            p_value += math.exp(log_p)

    return min(1.0, p_value)


def multiple_test_correction(
    p_values: List[float],
    method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
) -> List[float]:
    """Apply multiple testing correction to p-values.

    Args:
        p_values: List of raw p-values.
        method: Correction method to use.

    Returns:
        List of adjusted p-values.

    Supported methods:
        - "bonferroni": Bonferroni correction (conservative)
        - "benjamini_hochberg" or "bh": Benjamini-Hochberg FDR
        - "benjamini_yekutieli" or "by": Benjamini-Yekutieli FDR
        - "holm": Holm-Bonferroni method
        - "none": No correction
    """
    if isinstance(method, str):
        method = method.lower()
        method_map = {
            "bonferroni": CorrectionMethod.BONFERRONI,
            "bh": CorrectionMethod.BH,
            "benjamini_hochberg": CorrectionMethod.BH,
            "by": CorrectionMethod.BY,
            "benjamini_yekutieli": CorrectionMethod.BY,
            "holm": CorrectionMethod.HOLM,
            "none": CorrectionMethod.NONE,
        }
        method = method_map.get(method, CorrectionMethod.BH)

    n = len(p_values)
    if n == 0:
        return []

    if method == CorrectionMethod.NONE:
        return list(p_values)

    if method == CorrectionMethod.BONFERRONI:
        return [min(1.0, p * n) for p in p_values]

    if method == CorrectionMethod.HOLM:
        # Holm-Bonferroni step-down procedure
        indexed = sorted(enumerate(p_values), key=lambda x: x[1])
        adjusted = [0.0] * n
        cummax = 0.0
        for rank, (orig_idx, p) in enumerate(indexed):
            adj_p = p * (n - rank)
            cummax = max(cummax, adj_p)
            adjusted[orig_idx] = min(1.0, cummax)
        return adjusted

    if method == CorrectionMethod.BH:
        # Benjamini-Hochberg FDR
        indexed = sorted(enumerate(p_values), key=lambda x: x[1])
        adjusted = [0.0] * n
        cummin = 1.0
        for rank in range(n - 1, -1, -1):
            orig_idx, p = indexed[rank]
            adj_p = p * n / (rank + 1)
            cummin = min(cummin, adj_p)
            adjusted[orig_idx] = min(1.0, cummin)
        return adjusted

    if method == CorrectionMethod.BY:
        # Benjamini-Yekutieli FDR
        # Includes correction factor for arbitrary dependence
        c_n = sum(1.0 / i for i in range(1, n + 1))
        indexed = sorted(enumerate(p_values), key=lambda x: x[1])
        adjusted = [0.0] * n
        cummin = 1.0
        for rank in range(n - 1, -1, -1):
            orig_idx, p = indexed[rank]
            adj_p = p * n * c_n / (rank + 1)
            cummin = min(cummin, adj_p)
            adjusted[orig_idx] = min(1.0, cummin)
        return adjusted

    raise ValueError(f"Unknown correction method: {method}")


# =============================================================================
# Gene Set Providers
# =============================================================================

def _get_kegg_pathways(
    organism: str = "hsa",
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> Dict[str, Tuple[str, Set[str]]]:
    """Get KEGG pathway gene sets.

    Args:
        organism: KEGG organism code (e.g., "hsa" for human).
        use_cache: Whether to use cached data.
        cache_dir: Directory for cache files.

    Returns:
        Dict mapping pathway_id -> (pathway_name, set of gene IDs)
    """
    from biodbs._funcs.analysis._cache import get_cached_pathways, cache_pathways

    cache_key = f"kegg_{organism}"

    if use_cache:
        cached = get_cached_pathways(cache_key, cache_dir)
        if cached is not None:
            return cached

    from biodbs.fetch.KEGG.funcs import kegg_list, kegg_link

    # Get pathway list
    pathway_data = kegg_list("pathway", organism=organism)
    df_pathways = pathway_data.as_dataframe()

    pathways = {}
    pathway_names = {}

    # Parse pathway names
    for _, row in df_pathways.iterrows():
        pathway_id = row.get("entry_id", "")
        name = row.get("description", "")
        if pathway_id and name:
            # Remove organism prefix if present
            clean_id = pathway_id.replace(f"path:{organism}", f"{organism}")
            pathway_names[clean_id] = name.split(" - ")[0] if " - " in name else name

    # Get gene-pathway links
    link_data = kegg_link("pathway", organism)
    df_links = link_data.as_dataframe()

    # Build pathway -> genes mapping
    for _, row in df_links.iterrows():
        gene_id = row.get("source_id", "")
        pathway_id = row.get("target_id", "")

        if gene_id and pathway_id:
            # Clean IDs
            clean_pathway = pathway_id.replace("path:", "")
            clean_gene = gene_id.replace(f"{organism}:", "")

            if clean_pathway not in pathways:
                name = pathway_names.get(clean_pathway, clean_pathway)
                pathways[clean_pathway] = (name, set())

            pathways[clean_pathway][1].add(clean_gene)

    # Convert to immutable structure for caching
    result = {k: (v[0], frozenset(v[1])) for k, v in pathways.items()}

    if use_cache:
        cache_pathways(cache_key, result, cache_dir)

    # Convert back to mutable sets
    return {k: (v[0], set(v[1])) for k, v in result.items()}


def _get_go_terms(
    taxon_id: int = 9606,
    aspect: Union[str, GOAspect] = GOAspect.BIOLOGICAL_PROCESS,
    evidence_codes: Optional[List[str]] = None,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
    min_term_size: int = 5,
    max_term_size: int = 500,
) -> Dict[str, Tuple[str, Set[str]]]:
    """Get GO term gene sets from QuickGO.

    Args:
        taxon_id: NCBI taxonomy ID (e.g., 9606 for human).
        aspect: GO aspect to use.
        evidence_codes: Evidence codes to include (None = all except IEA).
        use_cache: Whether to use cached data.
        cache_dir: Directory for cache files.
        min_term_size: Minimum genes per term.
        max_term_size: Maximum genes per term.

    Returns:
        Dict mapping GO_id -> (term_name, set of gene IDs)
    """
    from biodbs._funcs.analysis._cache import get_cached_pathways, cache_pathways

    if isinstance(aspect, GOAspect):
        aspect = aspect.value

    cache_key = f"go_{taxon_id}_{aspect}"

    if use_cache:
        cached = get_cached_pathways(cache_key, cache_dir)
        if cached is not None:
            # Filter by size
            return {
                k: (v[0], set(v[1]))
                for k, v in cached.items()
                if min_term_size <= len(v[1]) <= max_term_size
            }

    from biodbs.fetch.QuickGO.funcs import quickgo_search_annotations_all

    # Build query parameters
    kwargs = {"taxonId": taxon_id}

    if aspect != "all":
        kwargs["aspect"] = aspect

    if evidence_codes:
        kwargs["goEvidence"] = evidence_codes
    else:
        # Exclude IEA (electronic annotations) by default for higher quality
        kwargs["goEvidence"] = ["IDA", "IPI", "IMP", "IGI", "IEP", "TAS", "IC"]

    # Fetch annotations (this may take a while)
    try:
        data = quickgo_search_annotations_all(max_records=100000, **kwargs)
    except Exception as e:
        warnings.warn(f"Failed to fetch GO annotations: {e}")
        return {}

    # Get GO term names
    go_terms: Dict[str, Tuple[str, Set[str]]] = {}
    term_names: Dict[str, str] = {}

    for annot in data.results:
        go_id = annot.get("goId", "")
        go_name = annot.get("goName", go_id)
        gene_id = annot.get("geneProductId", "")

        if go_id and gene_id:
            # Extract UniProt ID from gene product ID
            # Format is usually "UniProtKB:P12345"
            if ":" in gene_id:
                gene_id = gene_id.split(":")[-1]

            if go_id not in go_terms:
                go_terms[go_id] = (go_name, set())
                term_names[go_id] = go_name

            go_terms[go_id][1].add(gene_id)

    # Filter by size
    filtered = {
        k: v for k, v in go_terms.items()
        if min_term_size <= len(v[1]) <= max_term_size
    }

    # Cache the results
    if use_cache and filtered:
        cache_data = {k: (v[0], frozenset(v[1])) for k, v in filtered.items()}
        cache_pathways(cache_key, cache_data, cache_dir)

    return filtered


def _map_gene_ids(
    genes: List[str],
    from_type: str,
    to_type: str,
    organism: str = "human",
) -> Tuple[List[str], Dict[str, str], List[str]]:
    """Map gene IDs between different identifier types.

    Args:
        genes: List of gene identifiers.
        from_type: Source ID type.
        to_type: Target ID type.
        organism: Organism name.

    Returns:
        Tuple of (mapped_genes, mapping_dict, unmapped_genes)
    """
    if from_type == to_type:
        return genes, {g: g for g in genes}, []

    from biodbs._funcs.translate import translate_gene_ids

    try:
        result = translate_gene_ids(
            genes,
            from_type=from_type,
            to_type=to_type,
            species=organism,
            return_dict=True,
        )

        mapped = []
        mapping = {}
        unmapped = []

        for gene in genes:
            target = result.get(gene)
            if target and target != "":
                mapped.append(target)
                mapping[gene] = target
            else:
                unmapped.append(gene)

        return mapped, mapping, unmapped

    except Exception as e:
        warnings.warn(f"Gene ID mapping failed: {e}")
        return genes, {g: g for g in genes}, []


# =============================================================================
# Main ORA Functions
# =============================================================================

def ora(
    genes: List[str],
    gene_sets: Dict[str, Tuple[str, Set[str]]],
    background: Optional[Set[str]] = None,
    min_overlap: int = 3,
    correction_method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
    database_name: str = "custom",
) -> ORAResult:
    """Perform over-representation analysis with custom gene sets.

    This is the core ORA function that can be used with any gene set collection.

    Args:
        genes: List of query genes (e.g., differentially expressed genes).
        gene_sets: Dict mapping set_id -> (set_name, set of genes).
        background: Background gene set (universe). If None, uses union of all
            genes in gene_sets.
        min_overlap: Minimum overlap required to test a gene set.
        correction_method: Multiple testing correction method.
        database_name: Name of the database for result annotation.

    Returns:
        ORAResult with enrichment results.

    Example:
        >>> gene_sets = {
        ...     "pathway1": ("Pathway 1", {"GENE1", "GENE2", "GENE3"}),
        ...     "pathway2": ("Pathway 2", {"GENE2", "GENE3", "GENE4"}),
        ... }
        >>> result = ora(["GENE1", "GENE2", "GENE5"], gene_sets)
    """
    query_set = set(genes)

    # Determine background
    if background is None:
        # Use union of all genes in gene sets
        background = set()
        for _, gene_set in gene_sets.values():
            background.update(gene_set)

    # Ensure query genes are in background
    background = background | query_set

    N = len(background)
    n = len(query_set & background)

    if n == 0:
        return ORAResult(
            results=[],
            query_genes=genes,
            mapped_genes=[],
            unmapped_genes=genes,
            background_size=N,
            database=database_name,
        )

    # Calculate enrichment for each gene set
    results = []
    p_values = []

    for set_id, (set_name, gene_set) in gene_sets.items():
        # Filter to genes in background
        K = len(gene_set & background)
        if K == 0:
            continue

        # Calculate overlap
        overlap = query_set & gene_set & background
        k = len(overlap)

        if k < min_overlap:
            continue

        # Hypergeometric test
        p_value = hypergeometric_test(k, K, n, N)

        # Calculate fold enrichment
        expected = (K / N) * n
        fold_enrichment = k / expected if expected > 0 else float('inf')

        result = ORATermResult(
            term_id=set_id,
            term_name=set_name,
            p_value=p_value,
            adjusted_p_value=p_value,  # Will be corrected later
            overlap_count=k,
            term_size=K,
            query_size=n,
            background_size=N,
            fold_enrichment=fold_enrichment,
            overlap_genes=list(overlap),
            database=database_name,
        )
        results.append(result)
        p_values.append(p_value)

    # Apply multiple testing correction
    if results:
        adjusted = multiple_test_correction(p_values, correction_method)
        for i, result in enumerate(results):
            result.adjusted_p_value = adjusted[i]

    # Sort by adjusted p-value
    results.sort(key=lambda x: x.adjusted_p_value)

    return ORAResult(
        results=results,
        query_genes=genes,
        mapped_genes=list(query_set & background),
        unmapped_genes=list(query_set - background),
        background_size=N,
        database=database_name,
        parameters={
            "min_overlap": min_overlap,
            "correction_method": str(correction_method),
        },
    )


def ora_kegg(
    genes: List[str],
    organism: str = "hsa",
    id_type: str = "entrez",
    background: Optional[Set[str]] = None,
    min_overlap: int = 3,
    correction_method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> ORAResult:
    """Perform KEGG pathway over-representation analysis.

    Args:
        genes: List of query genes.
        organism: KEGG organism code (e.g., "hsa" for human, "mmu" for mouse).
        id_type: Input gene ID type:
            - "entrez": NCBI Entrez Gene ID (default)
            - "symbol": Gene symbol (will be converted)
            - "ensembl": Ensembl gene ID (will be converted)
            - "kegg": KEGG gene ID (no conversion needed)
        background: Background gene set. If None, uses all genes in KEGG.
        min_overlap: Minimum overlap required to test a pathway.
        correction_method: Multiple testing correction method.
        use_cache: Whether to use cached pathway data.
        cache_dir: Directory for cache files.

    Returns:
        ORAResult with KEGG pathway enrichment results.

    Example:
        >>> genes = ["7157", "672", "675", "7158"]  # Entrez IDs
        >>> result = ora_kegg(genes, organism="hsa")
        >>> print(result.summary())

        >>> # Using gene symbols
        >>> genes = ["TP53", "BRCA1", "BRCA2", "TP73"]
        >>> result = ora_kegg(genes, id_type="symbol")
    """
    # Map gene IDs if needed
    mapped_genes = genes
    mapping = {}
    unmapped = []

    organism_map = {
        "hsa": "human",
        "mmu": "mouse",
        "rno": "rat",
    }
    species = organism_map.get(organism, organism)

    if id_type == "symbol":
        mapped_genes, mapping, unmapped = _map_gene_ids(
            genes,
            from_type="external_gene_name",
            to_type="entrezgene_id",
            organism=species,
        )
    elif id_type == "ensembl":
        mapped_genes, mapping, unmapped = _map_gene_ids(
            genes,
            from_type="ensembl_gene_id",
            to_type="entrezgene_id",
            organism=species,
        )
    elif id_type == "kegg":
        # Strip organism prefix if present
        mapped_genes = [g.replace(f"{organism}:", "") for g in genes]
        mapping = {g: g.replace(f"{organism}:", "") for g in genes}

    # Get KEGG pathways
    pathways = _get_kegg_pathways(
        organism=organism,
        use_cache=use_cache,
        cache_dir=cache_dir,
    )

    if not pathways:
        warnings.warn(f"No KEGG pathways found for organism: {organism}")
        return ORAResult(
            results=[],
            query_genes=genes,
            mapped_genes=mapped_genes,
            unmapped_genes=unmapped,
            background_size=0,
            database="KEGG",
        )

    # Run ORA
    result = ora(
        genes=mapped_genes,
        gene_sets=pathways,
        background=background,
        min_overlap=min_overlap,
        correction_method=correction_method,
        database_name="KEGG",
    )

    # Update with original gene info
    result.query_genes = genes
    result.unmapped_genes = unmapped
    result.parameters["organism"] = organism
    result.parameters["id_type"] = id_type

    return result


def ora_go(
    genes: List[str],
    taxon_id: int = 9606,
    id_type: str = "uniprot",
    aspect: Union[str, GOAspect] = GOAspect.BIOLOGICAL_PROCESS,
    evidence_codes: Optional[List[str]] = None,
    background: Optional[Set[str]] = None,
    min_overlap: int = 3,
    min_term_size: int = 5,
    max_term_size: int = 500,
    correction_method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> ORAResult:
    """Perform Gene Ontology over-representation analysis using QuickGO.

    Args:
        genes: List of query genes.
        taxon_id: NCBI taxonomy ID (9606 for human, 10090 for mouse).
        id_type: Input gene ID type:
            - "uniprot": UniProt accession (default)
            - "symbol": Gene symbol (will be converted)
            - "ensembl": Ensembl gene ID (will be converted)
        aspect: GO aspect to analyze:
            - "biological_process": Biological processes
            - "molecular_function": Molecular functions
            - "cellular_component": Cellular components
            - "all": All aspects
        evidence_codes: Evidence codes to include. Default excludes IEA.
        background: Background gene set. If None, uses all genes in GO.
        min_overlap: Minimum overlap required.
        min_term_size: Minimum genes per GO term.
        max_term_size: Maximum genes per GO term.
        correction_method: Multiple testing correction method.
        use_cache: Whether to use cached GO data.
        cache_dir: Directory for cache files.

    Returns:
        ORAResult with GO term enrichment results.

    Example:
        >>> genes = ["P04637", "P38398", "O15350"]  # UniProt IDs
        >>> result = ora_go(genes, taxon_id=9606)
        >>> print(result.significant_terms().as_dataframe())
    """
    # Map gene IDs if needed
    mapped_genes = genes
    mapping = {}
    unmapped = []

    taxon_to_species = {
        9606: "human",
        10090: "mouse",
        10116: "rat",
    }
    species = taxon_to_species.get(taxon_id, "human")

    if id_type == "symbol":
        # Map to UniProt
        mapped_genes, mapping, unmapped = _map_gene_ids(
            genes,
            from_type="external_gene_name",
            to_type="uniprot_gn_id",
            organism=species,
        )
    elif id_type == "ensembl":
        mapped_genes, mapping, unmapped = _map_gene_ids(
            genes,
            from_type="ensembl_gene_id",
            to_type="uniprot_gn_id",
            organism=species,
        )

    # Get GO terms
    go_terms = _get_go_terms(
        taxon_id=taxon_id,
        aspect=aspect,
        evidence_codes=evidence_codes,
        use_cache=use_cache,
        cache_dir=cache_dir,
        min_term_size=min_term_size,
        max_term_size=max_term_size,
    )

    # Determine aspect string
    aspect_str = aspect if isinstance(aspect, str) else aspect.value if hasattr(aspect, 'value') else str(aspect)

    if not go_terms:
        warnings.warn(f"No GO terms found for taxon: {taxon_id}")
        return ORAResult(
            results=[],
            query_genes=genes,
            mapped_genes=mapped_genes,
            unmapped_genes=unmapped,
            background_size=0,
            database="GO",
            parameters={
                "taxon_id": taxon_id,
                "id_type": id_type,
                "aspect": aspect_str,
            },
        )

    # Create database name with aspect
    db_name = f"GO:{aspect_str}"

    # Run ORA
    result = ora(
        genes=mapped_genes,
        gene_sets=go_terms,
        background=background,
        min_overlap=min_overlap,
        correction_method=correction_method,
        database_name=db_name,
    )

    # Update with original gene info
    result.query_genes = genes
    result.unmapped_genes = unmapped
    result.parameters["taxon_id"] = taxon_id
    result.parameters["id_type"] = id_type
    result.parameters["aspect"] = aspect_str

    return result


def ora_enrichr(
    genes: List[str],
    gene_set_library: str = "KEGG_2021_Human",
    organism: str = "human",
) -> ORAResult:
    """Perform over-representation analysis using EnrichR web service.

    This function uses the EnrichR API to perform enrichment analysis,
    which handles ID mapping and statistical testing on their servers.

    Args:
        genes: List of gene symbols.
        gene_set_library: EnrichR library to use. Common options:
            - "KEGG_2021_Human"
            - "GO_Biological_Process_2023"
            - "GO_Molecular_Function_2023"
            - "GO_Cellular_Component_2023"
            - "Reactome_2022"
            - "WikiPathway_2023_Human"
            - "MSigDB_Hallmark_2020"
        organism: Organism ("human", "mouse", "fly", "yeast", "worm", "fish").

    Returns:
        ORAResult with EnrichR enrichment results.

    Note:
        This requires internet access to the EnrichR servers.
        Rate limits may apply for heavy usage.

    Example:
        >>> genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]
        >>> result = ora_enrichr(genes, "KEGG_2021_Human")
        >>> print(result.top_terms(10).as_dataframe())
    """
    from biodbs.fetch.EnrichR import EnrichR_Fetcher

    # Use the EnrichR fetcher
    fetcher = EnrichR_Fetcher(organism=organism)
    enrichr_data = fetcher.enrich(genes, gene_set_library)

    # Convert EnrichR results to ORATermResult objects
    results = []
    for term in enrichr_data.get_enrichment_terms():
        # Parse overlap genes - handle both string and list formats
        overlap_genes = term.overlapping_genes
        if isinstance(overlap_genes, str):
            overlap_genes = overlap_genes.split(";") if overlap_genes else []

        overlap_count = len(overlap_genes)

        result = ORATermResult(
            term_id=term.term_name,
            term_name=term.term_name,
            p_value=term.p_value,
            adjusted_p_value=term.adjusted_p_value,
            overlap_count=overlap_count,
            term_size=overlap_count,  # EnrichR doesn't provide term size directly
            query_size=len(genes),
            background_size=0,  # Not provided by EnrichR
            fold_enrichment=term.combined_score,
            overlap_genes=overlap_genes,
            database=f"EnrichR:{gene_set_library}",
        )
        results.append(result)

    # Sort by adjusted p-value
    results.sort(key=lambda x: x.adjusted_p_value)

    return ORAResult(
        results=results,
        query_genes=genes,
        mapped_genes=genes,
        unmapped_genes=[],
        background_size=0,
        database=f"EnrichR:{gene_set_library}",
        parameters={
            "gene_set_library": gene_set_library,
            "organism": organism,
            "method": "enrichr_fetcher",
        },
    )
