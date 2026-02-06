"""Over-Representation Analysis (ORA) for gene set enrichment.

This module provides functions for performing over-representation analysis
using the hypergeometric test to identify enriched gene sets or pathways.

Supported pathway databases:
    - KEGG: Pathways from KEGG database
    - GO (QuickGO): Gene Ontology terms
    - EnrichR: External enrichment analysis service
    - Reactome: Curated biological pathways

Example:
    >>> from biodbs._funcs.analysis import ora_kegg, ora_go
    >>>
    >>> # KEGG pathway enrichment
    >>> genes = ["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"]
    >>> result = ora_kegg(genes, organism="hsa", from_id_type="symbol")
    >>> print(result.as_dataframe().head())
    >>>
    >>> # GO enrichment
    >>> result = ora_go(genes, taxon_id=9606, aspect="biological_process")
    >>> print(result.significant_terms())
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
)

# Import fetchers and utilities at module level
from biodbs._funcs.analysis._cache import cache_pathways, get_cached_pathways
from biodbs._funcs.translate import translate_gene_ids
from biodbs.fetch.EnrichR import EnrichR_Fetcher
from biodbs.fetch.KEGG.funcs import kegg_link, kegg_list
from biodbs.fetch.QuickGO.funcs import quickgo_search_annotations_all
from biodbs.fetch.Reactome import Reactome_Fetcher

if TYPE_CHECKING:
    import pandas as pd


# =============================================================================
# Enums and Constants
# =============================================================================


class Species(Enum):
    """Species with their NCBI taxon IDs and common names.

    Each member has: (taxon_id, common_name, kegg_code, scientific_name)
    """

    HUMAN = (9606, "human", "hsa", "Homo sapiens")
    MOUSE = (10090, "mouse", "mmu", "Mus musculus")
    RAT = (10116, "rat", "rno", "Rattus norvegicus")
    ZEBRAFISH = (7955, "zebrafish", "dre", "Danio rerio")
    FLY = (7227, "fly", "dme", "Drosophila melanogaster")
    WORM = (6239, "worm", "cel", "Caenorhabditis elegans")
    YEAST = (559292, "yeast", "sce", "Saccharomyces cerevisiae")

    def __init__(self, taxon_id: int, common_name: str, kegg_code: str, scientific_name: str):
        self.taxon_id = taxon_id
        self.common_name = common_name
        self.kegg_code = kegg_code
        self.scientific_name = scientific_name

    @classmethod
    def from_taxon_id(cls, taxon_id: int) -> "Species":
        """Get Species from NCBI taxon ID."""
        for species in cls:
            if species.taxon_id == taxon_id:
                return species
        raise ValueError(
            f"Unknown taxon ID: {taxon_id}. "
            f"Supported: {', '.join(f'{s.name}={s.taxon_id}' for s in cls)}"
        )

    @classmethod
    def from_kegg_code(cls, kegg_code: str) -> "Species":
        """Get Species from KEGG organism code."""
        for species in cls:
            if species.kegg_code == kegg_code:
                return species
        raise ValueError(
            f"Unknown KEGG code: {kegg_code}. "
            f"Supported: {', '.join(f'{s.kegg_code}' for s in cls)}"
        )

    @classmethod
    def from_name(cls, name: str) -> "Species":
        """Get Species from common name, scientific name, or KEGG code."""
        name_lower = name.lower().strip()
        for species in cls:
            if name_lower in (
                species.common_name.lower(),
                species.scientific_name.lower(),
                species.kegg_code.lower(),
                species.name.lower(),
            ):
                return species
        raise ValueError(
            f"Unknown species: {name}. "
            f"Supported: {', '.join(s.common_name for s in cls)}"
        )


class PathwayDatabase(str, Enum):
    """Supported pathway databases."""

    KEGG = "kegg"
    GO = "go"
    ENRICHR = "enrichr"
    REACTOME = "reactome"


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


class TranslationDatabase(str, Enum):
    """Databases for ID translation."""

    BIOMART = "biomart"
    UNIPROT = "uniprot"
    NCBI = "ncbi"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Pathway:
    """A biological pathway or gene set.

    Attributes:
        id: Unique pathway identifier (e.g., "hsa04110", "R-HSA-69278", "GO:0006915")
        name: Human-readable pathway name
        genes: Set of gene identifiers in this pathway
        database: Source database (KEGG, Reactome, GO, etc.)
        species: Species this pathway belongs to (optional)
        url: URL to pathway page (optional)
    """

    id: str
    name: str
    genes: FrozenSet[str]
    database: str
    species: Optional[str] = None
    url: Optional[str] = None

    def __len__(self) -> int:
        return len(self.genes)

    def __contains__(self, gene: str) -> bool:
        return gene in self.genes

    def overlap(self, gene_list: Set[str]) -> Set[str]:
        """Get genes that overlap with a query gene list."""
        return self.genes & gene_list

    def to_tuple(self) -> Tuple[str, Set[str]]:
        """Convert to legacy tuple format (name, genes)."""
        return (self.name, set(self.genes))

    @classmethod
    def from_tuple(
        cls, pathway_id: str, data: Tuple[str, Set[str]], database: str
    ) -> "Pathway":
        """Create Pathway from legacy tuple format."""
        name, genes = data
        return cls(
            id=pathway_id,
            name=name,
            genes=frozenset(genes),
            database=database,
        )


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
        k = self.overlap_count
        K = self.term_size
        n = self.query_size
        N = self.background_size

        # Avoid division by zero
        if (n - k) == 0 or (K - k) == 0 or (N - K - n + k) == 0:
            return float("inf") if k > 0 else 0.0

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
        """Filter to only significant terms."""
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
        """Get top N terms by adjusted p-value."""
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

    def as_dataframe(
        self, engine: Literal["pandas", "polars"] = "pandas"
    ) -> "pd.DataFrame":
        """Convert results to a DataFrame."""
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

        return stats.hypergeom.sf(k - 1, N, K, n)
    except ImportError:
        pass

    # Fallback to pure Python implementation
    def _log_comb(n: int, k: int) -> float:
        if k < 0 or k > n:
            return float("-inf")
        if k == 0 or k == n:
            return 0.0
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)

    max_i = min(n, K)
    log_denom = _log_comb(N, n)

    p_value = 0.0
    for i in range(k, max_i + 1):
        log_p = _log_comb(K, i) + _log_comb(N - K, n - i) - log_denom
        if log_p > -700:
            p_value += math.exp(log_p)

    return min(1.0, p_value)


def multiple_test_correction(
    p_values: List[float],
    method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
) -> List[float]:
    """Apply multiple testing correction to p-values."""
    if isinstance(method, str):
        method = method.lower()
        method_map = {
            "bonferroni": CorrectionMethod.BONFERRONI,
            "bh": CorrectionMethod.BH,
            "benjamini_hochberg": CorrectionMethod.BH,
            "fdr_bh": CorrectionMethod.BH,
            "by": CorrectionMethod.BY,
            "benjamini_yekutieli": CorrectionMethod.BY,
            "fdr_by": CorrectionMethod.BY,
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
        indexed = sorted(enumerate(p_values), key=lambda x: x[1])
        adjusted = [0.0] * n
        cummax = 0.0
        for rank, (orig_idx, p) in enumerate(indexed):
            adj_p = p * (n - rank)
            cummax = max(cummax, adj_p)
            adjusted[orig_idx] = min(1.0, cummax)
        return adjusted

    if method == CorrectionMethod.BH:
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
# ID Type Definitions and Translation
# =============================================================================

# Supported ID types with their aliases
ID_TYPE_ALIASES = {
    # Gene symbols
    "symbol": "symbol",
    "gene_symbol": "symbol",
    "gene_name": "symbol",
    "hgnc_symbol": "symbol",
    # Entrez/NCBI Gene ID
    "entrez": "entrez",
    "entrezgene": "entrez",
    "entrezgene_id": "entrez",
    "ncbi_gene": "entrez",
    "ncbi_geneid": "entrez",
    "gene_id": "entrez",
    # Ensembl
    "ensembl": "ensembl",
    "ensembl_gene_id": "ensembl",
    "ensembl_gene": "ensembl",
    # UniProt
    "uniprot": "uniprot",
    "uniprot_id": "uniprot",
    "uniprot_ac": "uniprot",
    "swissprot": "uniprot",
    # RefSeq
    "refseq": "refseq",
    "refseq_mrna": "refseq",
}


def _normalize_id_type(id_type: str) -> str:
    """Normalize ID type to canonical form."""
    return ID_TYPE_ALIASES.get(id_type.lower(), id_type.lower())


def _translate_ids_for_ora(
    genes: List[str],
    from_type: str,
    to_type: str,
    species: Species,
    database: TranslationDatabase = TranslationDatabase.BIOMART,
) -> Tuple[List[str], Dict[str, str], List[str]]:
    """Translate gene IDs for ORA analysis.

    Args:
        genes: List of gene identifiers.
        from_type: Source ID type (normalized).
        to_type: Target ID type (normalized).
        species: Species enum for translation.
        database: Database to use for ID translation.

    Returns:
        Tuple of (translated_genes, mapping_dict, unmapped_genes)
    """
    if from_type == to_type:
        return genes, {g: g for g in genes}, []

    # Map normalized types to BioMart attribute names
    biomart_attrs = {
        "symbol": "external_gene_name",
        "entrez": "entrezgene_id",
        "ensembl": "ensembl_gene_id",
        "uniprot": "uniprotswissprot",
        "refseq": "refseq_mrna",
    }

    from_attr = biomart_attrs.get(from_type)
    to_attr = biomart_attrs.get(to_type)

    if not from_attr or not to_attr:
        warnings.warn(
            f"Unknown ID type for translation: {from_type} -> {to_type}. "
            "Returning original IDs."
        )
        return genes, {g: g for g in genes}, []

    try:
        result = translate_gene_ids(
            genes,
            from_type=from_attr,
            to_type=to_attr,
            species=species.common_name,
            database=database.value,
            return_dict=True,
        )

        mapped = []
        mapping = {}
        unmapped = []

        for gene in genes:
            target = result.get(gene)
            if target and target != "" and str(target) != "nan":
                if isinstance(target, list):
                    target = target[0] if target else None
                if target:
                    mapped.append(str(target))
                    mapping[gene] = str(target)
                else:
                    unmapped.append(gene)
            else:
                unmapped.append(gene)

        return mapped, mapping, unmapped

    except Exception as e:
        warnings.warn(f"ID translation failed ({from_type} -> {to_type}): {e}")
        return genes, {g: g for g in genes}, []


# =============================================================================
# Pathway Data Providers
# =============================================================================


def _get_kegg_pathways(
    species: Species,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> Dict[str, Pathway]:
    """Get KEGG pathway gene sets.

    Args:
        species: Species enum.
        use_cache: Whether to use cached data.
        cache_dir: Directory for cache files.

    Returns:
        Dict mapping pathway_id -> Pathway object
    """
    organism = species.kegg_code
    cache_key = f"kegg_{organism}"

    if use_cache:
        cached = get_cached_pathways(cache_key, cache_dir)
        if cached is not None:
            # Convert cached tuples to Pathway objects
            return {
                k: Pathway.from_tuple(k, (v[0], set(v[1])), "KEGG")
                for k, v in cached.items()
            }

    # Get pathway list
    pathway_data = kegg_list("pathway", organism=organism)
    df_pathways = pathway_data.as_dataframe()

    pathway_names = {}
    for _, row in df_pathways.iterrows():
        pathway_id = row.get("entry_id", "")
        name = row.get("description", "")
        if pathway_id and name:
            clean_id = pathway_id.replace(f"path:{organism}", f"{organism}")
            pathway_names[clean_id] = name.split(" - ")[0] if " - " in name else name

    # Get gene-pathway links
    link_data = kegg_link("pathway", organism)
    df_links = link_data.as_dataframe()

    pathway_genes: Dict[str, Set[str]] = {}
    for _, row in df_links.iterrows():
        gene_id = row.get("source_id", "")
        pathway_id = row.get("target_id", "")

        if gene_id and pathway_id:
            clean_pathway = pathway_id.replace("path:", "")
            clean_gene = gene_id.replace(f"{organism}:", "")

            if clean_pathway not in pathway_genes:
                pathway_genes[clean_pathway] = set()
            pathway_genes[clean_pathway].add(clean_gene)

    # Build Pathway objects
    pathways = {}
    for pathway_id, genes in pathway_genes.items():
        name = pathway_names.get(pathway_id, pathway_id)
        pathways[pathway_id] = Pathway(
            id=pathway_id,
            name=name,
            genes=frozenset(genes),
            database="KEGG",
            species=species.scientific_name,
            url=f"https://www.kegg.jp/pathway/{pathway_id}",
        )

    # Cache as tuples for compatibility
    if use_cache:
        cache_data = {k: (v.name, v.genes) for k, v in pathways.items()}
        cache_pathways(cache_key, cache_data, cache_dir)

    return pathways


def _get_go_terms(
    species: Species,
    aspect: Union[str, GOAspect] = GOAspect.BIOLOGICAL_PROCESS,
    evidence_codes: Optional[List[str]] = None,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
    min_term_size: int = 5,
    max_term_size: int = 500,
) -> Dict[str, Pathway]:
    """Get GO term gene sets from QuickGO.

    Args:
        species: Species enum.
        aspect: GO aspect to use.
        evidence_codes: Evidence codes to include (None = all except IEA).
        use_cache: Whether to use cached data.
        cache_dir: Directory for cache files.
        min_term_size: Minimum genes per term.
        max_term_size: Maximum genes per term.

    Returns:
        Dict mapping GO_id -> Pathway object
    """
    if isinstance(aspect, GOAspect):
        aspect = aspect.value

    taxon_id = species.taxon_id
    cache_key = f"go_{taxon_id}_{aspect}"

    if use_cache:
        cached = get_cached_pathways(cache_key, cache_dir)
        if cached is not None:
            return {
                k: Pathway.from_tuple(k, (v[0], set(v[1])), f"GO:{aspect}")
                for k, v in cached.items()
                if min_term_size <= len(v[1]) <= max_term_size
            }

    # Build query parameters
    kwargs = {"taxonId": taxon_id}

    if aspect != "all":
        kwargs["aspect"] = aspect

    if evidence_codes:
        kwargs["goEvidence"] = evidence_codes
    else:
        kwargs["goEvidence"] = ["IDA", "IPI", "IMP", "IGI", "IEP", "TAS", "IC"]

    try:
        data = quickgo_search_annotations_all(max_records=100000, **kwargs)
    except Exception as e:
        warnings.warn(f"Failed to fetch GO annotations: {e}")
        return {}

    go_terms: Dict[str, Tuple[str, Set[str]]] = {}

    for annot in data.results:
        go_id = annot.get("goId", "")
        go_name = annot.get("goName", go_id)
        gene_id = annot.get("geneProductId", "")

        if go_id and gene_id:
            if ":" in gene_id:
                gene_id = gene_id.split(":")[-1]

            if go_id not in go_terms:
                go_terms[go_id] = (go_name, set())
            go_terms[go_id][1].add(gene_id)

    # Filter by size and convert to Pathway objects
    pathways = {}
    for go_id, (name, genes) in go_terms.items():
        if min_term_size <= len(genes) <= max_term_size:
            pathways[go_id] = Pathway(
                id=go_id,
                name=name,
                genes=frozenset(genes),
                database=f"GO:{aspect}",
                species=species.scientific_name,
                url=f"https://www.ebi.ac.uk/QuickGO/term/{go_id}",
            )

    if use_cache and pathways:
        cache_data = {k: (v.name, v.genes) for k, v in pathways.items()}
        cache_pathways(cache_key, cache_data, cache_dir)

    return pathways


def _get_reactome_pathways(
    species: Species,
    id_type: str = "gene_symbol",
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
    min_term_size: int = 5,
    max_term_size: int = 500,
) -> Dict[str, Pathway]:
    """Get Reactome pathway gene sets.

    Args:
        species: Species enum.
        id_type: Gene ID type ("gene_symbol" or "uniprot").
        use_cache: Whether to use cached data.
        cache_dir: Directory for cache files.
        min_term_size: Minimum genes per pathway.
        max_term_size: Maximum genes per pathway.

    Returns:
        Dict mapping pathway_id -> Pathway object
    """
    species_name = species.scientific_name
    species_key = species_name.lower().replace(" ", "_")
    cache_key = f"reactome_{species_key}_{id_type}"

    if use_cache:
        cached = get_cached_pathways(cache_key, cache_dir)
        if cached is not None:
            return {
                k: Pathway.from_tuple(k, (v[0], set(v[1])), "Reactome")
                for k, v in cached.items()
                if min_term_size <= len(v[1]) <= max_term_size
            }

    fetcher = Reactome_Fetcher(species=species_name)

    try:
        hierarchy = fetcher.get_events_hierarchy(species_name)
    except Exception as e:
        warnings.warn(f"Failed to fetch Reactome hierarchy: {e}")
        return {}

    pathway_ids = fetcher._extract_pathway_ids_from_hierarchy(hierarchy)
    pathways = {}

    for pathway_id, pathway_name in pathway_ids:
        try:
            genes = fetcher.get_pathway_genes(pathway_id, id_type=id_type)
            if genes and min_term_size <= len(genes) <= max_term_size:
                pathways[pathway_id] = Pathway(
                    id=pathway_id,
                    name=pathway_name,
                    genes=frozenset(genes),
                    database="Reactome",
                    species=species_name,
                    url=f"https://reactome.org/content/detail/{pathway_id}",
                )
        except Exception:
            continue

    if use_cache and pathways:
        cache_data = {k: (v.name, v.genes) for k, v in pathways.items()}
        cache_pathways(cache_key, cache_data, cache_dir)

    return pathways


# =============================================================================
# Main ORA Functions
# =============================================================================


def ora(
    genes: List[str],
    gene_sets: Union[Dict[str, Tuple[str, Set[str]]], Dict[str, Pathway]],
    background: Optional[Set[str]] = None,
    min_overlap: int = 3,
    correction_method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
    database_name: str = "custom",
) -> ORAResult:
    """Perform over-representation analysis with custom gene sets.

    Args:
        genes: List of query genes.
        gene_sets: Dict mapping set_id -> (set_name, set of genes) or Pathway objects.
        background: Background gene set (universe). If None, uses union of all genes.
        min_overlap: Minimum overlap required to test a gene set.
        correction_method: Multiple testing correction method.
        database_name: Name of the database for result annotation.

    Returns:
        ORAResult with enrichment results.
    """
    query_set = set(genes)

    # Normalize gene_sets to Dict[str, Tuple[str, Set[str]]]
    normalized_gene_sets: Dict[str, Tuple[str, Set[str]]] = {}
    for set_id, data in gene_sets.items():
        if isinstance(data, Pathway):
            normalized_gene_sets[set_id] = (data.name, set(data.genes))
        else:
            normalized_gene_sets[set_id] = data

    # Determine background
    if background is None:
        background = set()
        for _, gene_set in normalized_gene_sets.values():
            background.update(gene_set)

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

    results = []
    p_values = []

    for set_id, (set_name, gene_set) in normalized_gene_sets.items():
        K = len(gene_set & background)
        if K == 0:
            continue

        overlap = query_set & gene_set & background
        k = len(overlap)

        if k < min_overlap:
            continue

        p_value = hypergeometric_test(k, K, n, N)
        expected = (K / N) * n
        fold_enrichment = k / expected if expected > 0 else float("inf")

        result = ORATermResult(
            term_id=set_id,
            term_name=set_name,
            p_value=p_value,
            adjusted_p_value=p_value,
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

    if results:
        adjusted = multiple_test_correction(p_values, correction_method)
        for i, result in enumerate(results):
            result.adjusted_p_value = adjusted[i]

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
    from_id_type: str = "entrez",
    background: Optional[Set[str]] = None,
    min_overlap: int = 3,
    correction_method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
    translation_database: Union[str, TranslationDatabase] = TranslationDatabase.BIOMART,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> ORAResult:
    """Perform KEGG pathway over-representation analysis.

    Args:
        genes: List of query genes.
        organism: KEGG organism code (e.g., "hsa" for human, "mmu" for mouse).
        from_id_type: Input gene ID type. Automatically translates to Entrez IDs.
            Supported: "entrez", "symbol", "ensembl", "uniprot", "kegg"
        background: Background gene set. If None, uses all genes in KEGG.
        min_overlap: Minimum overlap required to test a pathway.
        correction_method: Multiple testing correction method.
        translation_database: Database for ID translation ("biomart", "uniprot", "ncbi").
        use_cache: Whether to use cached pathway data.
        cache_dir: Directory for cache files.

    Returns:
        ORAResult with KEGG pathway enrichment results.

    Example:
        >>> genes = ["TP53", "BRCA1", "BRCA2"]
        >>> result = ora_kegg(genes, organism="hsa", from_id_type="symbol")
    """
    # Get species from KEGG code
    species = Species.from_kegg_code(organism)

    # Normalize ID type
    from_type = _normalize_id_type(from_id_type)

    # Normalize translation database
    if isinstance(translation_database, str):
        translation_database = TranslationDatabase(translation_database.lower())

    # Translate IDs if needed
    mapped_genes = genes
    unmapped = []

    if from_type == "kegg":
        mapped_genes = [g.replace(f"{organism}:", "") for g in genes]
    elif from_type != "entrez":
        mapped_genes, _, unmapped = _translate_ids_for_ora(
            genes,
            from_type=from_type,
            to_type="entrez",
            species=species,
            database=translation_database,
        )

    # Get KEGG pathways
    pathways = _get_kegg_pathways(
        species=species,
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

    result = ora(
        genes=mapped_genes,
        gene_sets=pathways,
        background=background,
        min_overlap=min_overlap,
        correction_method=correction_method,
        database_name="KEGG",
    )

    result.query_genes = genes
    result.unmapped_genes = unmapped
    result.parameters["organism"] = organism
    result.parameters["from_id_type"] = from_id_type
    result.parameters["translation_database"] = translation_database.value

    return result


def ora_go(
    genes: List[str],
    taxon_id: int = 9606,
    from_id_type: str = "uniprot",
    aspect: Union[str, GOAspect] = GOAspect.BIOLOGICAL_PROCESS,
    evidence_codes: Optional[List[str]] = None,
    background: Optional[Set[str]] = None,
    min_overlap: int = 3,
    min_term_size: int = 5,
    max_term_size: int = 500,
    correction_method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
    translation_database: Union[str, TranslationDatabase] = TranslationDatabase.BIOMART,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> ORAResult:
    """Perform Gene Ontology over-representation analysis using QuickGO.

    Args:
        genes: List of query genes.
        taxon_id: NCBI taxonomy ID (9606 for human, 10090 for mouse).
        from_id_type: Input gene ID type. Automatically translates to UniProt IDs.
            Supported: "uniprot", "symbol", "ensembl", "entrez"
        aspect: GO aspect to analyze.
        evidence_codes: Evidence codes to include. Default excludes IEA.
        background: Background gene set. If None, uses all genes in GO.
        min_overlap: Minimum overlap required.
        min_term_size: Minimum genes per GO term.
        max_term_size: Maximum genes per GO term.
        correction_method: Multiple testing correction method.
        translation_database: Database for ID translation.
        use_cache: Whether to use cached GO data.
        cache_dir: Directory for cache files.

    Returns:
        ORAResult with GO term enrichment results.

    Raises:
        ValueError: If taxon_id is not supported.

    Example:
        >>> genes = ["TP53", "BRCA1", "BRCA2"]
        >>> result = ora_go(genes, taxon_id=9606, from_id_type="symbol")
    """
    # Get species from taxon ID
    species = Species.from_taxon_id(taxon_id)

    # Normalize ID type
    from_type = _normalize_id_type(from_id_type)

    # Normalize translation database
    if isinstance(translation_database, str):
        translation_database = TranslationDatabase(translation_database.lower())

    # Translate IDs if needed
    mapped_genes = genes
    unmapped = []

    if from_type != "uniprot":
        mapped_genes, _, unmapped = _translate_ids_for_ora(
            genes,
            from_type=from_type,
            to_type="uniprot",
            species=species,
            database=translation_database,
        )

    # Get GO terms
    go_terms = _get_go_terms(
        species=species,
        aspect=aspect,
        evidence_codes=evidence_codes,
        use_cache=use_cache,
        cache_dir=cache_dir,
        min_term_size=min_term_size,
        max_term_size=max_term_size,
    )

    aspect_str = aspect if isinstance(aspect, str) else aspect.value

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
                "from_id_type": from_id_type,
                "aspect": aspect_str,
            },
        )

    db_name = f"GO:{aspect_str}"

    result = ora(
        genes=mapped_genes,
        gene_sets=go_terms,
        background=background,
        min_overlap=min_overlap,
        correction_method=correction_method,
        database_name=db_name,
    )

    result.query_genes = genes
    result.unmapped_genes = unmapped
    result.parameters["taxon_id"] = taxon_id
    result.parameters["from_id_type"] = from_id_type
    result.parameters["aspect"] = aspect_str
    result.parameters["translation_database"] = translation_database.value

    return result


def ora_enrichr(
    genes: List[str],
    gene_set_library: str = "KEGG_2021_Human",
    organism: str = "human",
    from_id_type: str = "symbol",
    translation_database: Union[str, TranslationDatabase] = TranslationDatabase.BIOMART,
) -> ORAResult:
    """Perform over-representation analysis using EnrichR web service.

    Args:
        genes: List of gene identifiers.
        gene_set_library: EnrichR library to use.
        organism: Organism ("human", "mouse", "fly", "yeast", "worm", "fish").
        from_id_type: Input gene ID type. Automatically translates to gene symbols.
            Supported: "symbol", "ensembl", "entrez", "uniprot"
        translation_database: Database for ID translation.

    Returns:
        ORAResult with EnrichR enrichment results.

    Example:
        >>> genes = ["ENSG00000141510", "ENSG00000012048"]
        >>> result = ora_enrichr(genes, "KEGG_2021_Human", from_id_type="ensembl")
    """
    # Get species from organism name
    species = Species.from_name(organism)

    # Normalize ID type
    from_type = _normalize_id_type(from_id_type)

    # Normalize translation database
    if isinstance(translation_database, str):
        translation_database = TranslationDatabase(translation_database.lower())

    # Translate IDs if needed
    mapped_genes = genes
    unmapped = []

    if from_type != "symbol":
        mapped_genes, _, unmapped = _translate_ids_for_ora(
            genes,
            from_type=from_type,
            to_type="symbol",
            species=species,
            database=translation_database,
        )

    fetcher = EnrichR_Fetcher(organism=organism)
    enrichr_data = fetcher.enrich(mapped_genes, gene_set_library)

    results = []
    for term in enrichr_data.get_enrichment_terms():
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
            term_size=overlap_count,
            query_size=len(genes),
            background_size=0,
            fold_enrichment=term.combined_score,
            overlap_genes=overlap_genes,
            database=f"EnrichR:{gene_set_library}",
        )
        results.append(result)

    results.sort(key=lambda x: x.adjusted_p_value)

    return ORAResult(
        results=results,
        query_genes=genes,
        mapped_genes=mapped_genes,
        unmapped_genes=unmapped,
        background_size=0,
        database=f"EnrichR:{gene_set_library}",
        parameters={
            "gene_set_library": gene_set_library,
            "organism": organism,
            "from_id_type": from_id_type,
            "translation_database": translation_database.value,
            "method": "enrichr_api",
        },
    )


def ora_reactome(
    genes: List[str],
    species: str = "Homo sapiens",
    from_id_type: str = "symbol",
    interactors: bool = False,
    include_disease: bool = True,
    min_entities: Optional[int] = None,
    max_entities: Optional[int] = None,
    fetch_overlap_genes: bool = False,
    translation_database: Union[str, TranslationDatabase] = TranslationDatabase.BIOMART,
) -> ORAResult:
    """Perform over-representation analysis using Reactome pathway database.

    Args:
        genes: List of gene identifiers.
        species: Species name (e.g., "Homo sapiens", "Mus musculus").
        from_id_type: Input gene ID type. Automatically translates to gene symbols.
            Supported: "symbol", "ensembl", "entrez", "uniprot"
        interactors: Include interactors in the analysis.
        include_disease: Include disease pathways.
        min_entities: Minimum pathway size.
        max_entities: Maximum pathway size.
        fetch_overlap_genes: If True, fetch specific overlap genes (slower).
        translation_database: Database for ID translation.

    Returns:
        ORAResult with Reactome pathway enrichment results.

    Example:
        >>> genes = ["7157", "672", "675"]
        >>> result = ora_reactome(genes, from_id_type="entrez")
    """
    # Get species from name
    species_enum = Species.from_name(species)

    # Normalize ID type
    from_type = _normalize_id_type(from_id_type)

    # Normalize translation database
    if isinstance(translation_database, str):
        translation_database = TranslationDatabase(translation_database.lower())

    # Translate IDs if needed
    mapped_genes = genes
    unmapped_translate = []

    if from_type not in ("symbol", "uniprot"):
        mapped_genes, _, unmapped_translate = _translate_ids_for_ora(
            genes,
            from_type=from_type,
            to_type="symbol",
            species=species_enum,
            database=translation_database,
        )

    fetcher = Reactome_Fetcher(species=species)
    reactome_data = fetcher.analyze(
        identifiers=mapped_genes,
        species=species,
        interactors=interactors,
        include_disease=include_disease,
        min_entities=min_entities,
        max_entities=max_entities,
        page_size=500,
    )

    results = []
    for pathway in reactome_data.pathways:
        overlap_genes = []
        if fetch_overlap_genes and reactome_data.token and pathway.found_entities > 0:
            try:
                found = fetcher.get_found_entities(reactome_data.token, pathway.stId)
                overlap_genes = [e.get("id", "") for e in found if isinstance(e, dict)]
            except Exception:
                pass

        result = ORATermResult(
            term_id=pathway.stId,
            term_name=pathway.name,
            p_value=pathway.p_value,
            adjusted_p_value=pathway.fdr,
            overlap_count=pathway.found_entities,
            term_size=pathway.total_entities,
            query_size=len(genes),
            background_size=0,
            fold_enrichment=pathway.entities.ratio if pathway.entities else 0.0,
            overlap_genes=overlap_genes,
            database="Reactome",
        )
        results.append(result)

    results.sort(key=lambda x: x.adjusted_p_value)

    unmapped_reactome = []
    if reactome_data.token:
        try:
            unmapped_reactome = fetcher.get_not_found_identifiers(reactome_data.token)
        except Exception:
            pass

    all_unmapped = list(set(unmapped_translate + unmapped_reactome))
    mapped_count = len(mapped_genes) - reactome_data.identifiers_not_found

    return ORAResult(
        results=results,
        query_genes=genes,
        mapped_genes=mapped_genes[:mapped_count] if mapped_count > 0 else [],
        unmapped_genes=all_unmapped,
        background_size=0,
        database="Reactome",
        parameters={
            "species": species,
            "from_id_type": from_id_type,
            "translation_database": translation_database.value,
            "interactors": interactors,
            "include_disease": include_disease,
            "method": "reactome_api",
            "token": reactome_data.token,
        },
    )


def ora_reactome_local(
    genes: List[str],
    species: str = "Homo sapiens",
    from_id_type: str = "symbol",
    background: Optional[Set[str]] = None,
    min_overlap: int = 3,
    min_term_size: int = 5,
    max_term_size: int = 500,
    correction_method: Union[str, CorrectionMethod] = CorrectionMethod.BH,
    translation_database: Union[str, TranslationDatabase] = TranslationDatabase.BIOMART,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> ORAResult:
    """Perform local over-representation analysis using Reactome pathway data.

    Args:
        genes: List of gene identifiers.
        species: Species name (e.g., "Homo sapiens", "Mus musculus").
        from_id_type: Input gene ID type. Automatically translates to gene symbols.
            Supported: "symbol", "ensembl", "entrez", "uniprot"
        background: Background gene set. If None, uses all genes in pathways.
        min_overlap: Minimum overlap required to test a pathway.
        min_term_size: Minimum genes per pathway.
        max_term_size: Maximum genes per pathway.
        correction_method: Multiple testing correction method.
        translation_database: Database for ID translation.
        use_cache: Cache pathway data (recommended).
        cache_dir: Directory for cache files.

    Returns:
        ORAResult with Reactome pathway enrichment results.

    Example:
        >>> genes = ["TP53", "BRCA1", "BRCA2"]
        >>> result = ora_reactome_local(genes, species="Homo sapiens")
    """
    # Get species from name
    species_enum = Species.from_name(species)

    # Normalize ID type
    from_type = _normalize_id_type(from_id_type)

    # Normalize translation database
    if isinstance(translation_database, str):
        translation_database = TranslationDatabase(translation_database.lower())

    # Translate IDs if needed
    mapped_genes = genes
    unmapped = []

    if from_type != "symbol":
        mapped_genes, _, unmapped = _translate_ids_for_ora(
            genes,
            from_type=from_type,
            to_type="symbol",
            species=species_enum,
            database=translation_database,
        )

    pathways = _get_reactome_pathways(
        species=species_enum,
        id_type="gene_symbol",
        use_cache=use_cache,
        cache_dir=cache_dir,
        min_term_size=min_term_size,
        max_term_size=max_term_size,
    )

    if not pathways:
        warnings.warn(f"No Reactome pathways found for species: {species}")
        return ORAResult(
            results=[],
            query_genes=genes,
            mapped_genes=[],
            unmapped_genes=genes,
            background_size=0,
            database="Reactome",
            parameters={
                "species": species,
                "from_id_type": from_id_type,
                "method": "local",
            },
        )

    result = ora(
        genes=mapped_genes,
        gene_sets=pathways,
        background=background,
        min_overlap=min_overlap,
        correction_method=correction_method,
        database_name="Reactome",
    )

    result.query_genes = genes
    result.unmapped_genes = unmapped
    result.parameters["species"] = species
    result.parameters["from_id_type"] = from_id_type
    result.parameters["translation_database"] = translation_database.value
    result.parameters["method"] = "local"
    result.parameters["min_term_size"] = min_term_size
    result.parameters["max_term_size"] = max_term_size

    return result