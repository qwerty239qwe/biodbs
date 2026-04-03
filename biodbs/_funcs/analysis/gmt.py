"""GMT (Gene Matrix Transposed) file I/O and database gene set fetching.

GMT is the standard interchange format for gene sets used by GSEA, gseapy,
and most pathway enrichment tools.  Format (tab-separated, one set per line)::

    pathway_id<TAB>description<TAB>gene1<TAB>gene2<TAB>...

All functions in this module work with :class:`~biodbs._funcs.analysis.ora.Pathway`
objects so results slot directly into :func:`~biodbs._funcs.analysis.ora.ora`.

Examples::

    # Load an existing GMT file
    gene_sets = load_gmt("h.all.v2023.1.Hs.symbols.gmt")
    result = ora(my_genes, gene_sets)

    # Fetch KEGG human pathways, save as GMT, and run ORA
    gene_sets = fetch_gmt("hsa", database="kegg", save_at="./kegg_hsa.gmt")
    result = ora(my_genes, gene_sets)

    # Fetch an EnrichR library
    gene_sets = fetch_gmt("KEGG_2021_Human", database="enrichr")

    # Roundtrip: ORA result gene sets → GMT
    save_gmt(gene_sets, "my_sets.gmt")
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Dict, FrozenSet, Literal, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

# Imported lazily inside functions where needed to avoid circular imports at
# module load time (ora.py imports from _cache.py which TYPE_CHECKING-imports
# Pathway from ora.py, and ora.py may later import from here).
# The type annotations below use string literals for the same reason.


# ---------------------------------------------------------------------------
# GMT I/O
# ---------------------------------------------------------------------------


def load_gmt(
    path: Union[str, Path],
    database: str = "",
    species: Optional[str] = None,
) -> "Dict[str, Any]":
    """Load a GMT file and return a dict of :class:`Pathway` objects.

    Each non-empty line becomes one ``Pathway``:

    - ``id``       ← column 1 (gene set name / pathway ID)
    - ``name``     ← column 2 (description; falls back to *id* if blank or ``"na"``)
    - ``genes``    ← columns 3 onwards
    - ``database`` ← *database* parameter (default ``""`` — set to the source name)
    - ``species``  ← *species* parameter (optional)

    Args:
        path: Path to the ``.gmt`` file.
        database: Database label to attach to every :class:`Pathway`
            (e.g. ``"KEGG"``, ``"MSigDB_H"``).
        species: Species string to attach to every :class:`Pathway`
            (e.g. ``"Homo sapiens"``).

    Returns:
        ``Dict[pathway_id, Pathway]`` ready to pass to :func:`ora`.

    Raises:
        FileNotFoundError: If *path* does not exist.

    Example::

        gene_sets = load_gmt("h.all.v2023.1.Hs.symbols.gmt", database="MSigDB_H")
        result = ora(my_genes, gene_sets)
    """
    from biodbs._funcs.analysis.ora import Pathway

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"GMT file not found: {path}")

    pathways: Dict[str, Pathway] = {}
    skipped = 0

    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                logger.debug("Skipping short line %d in %s", lineno, path.name)
                skipped += 1
                continue

            pathway_id = parts[0].strip()
            description = parts[1].strip()
            genes: FrozenSet[str] = frozenset(g.strip() for g in parts[2:] if g.strip())

            if not pathway_id or not genes:
                skipped += 1
                continue

            name = description if description and description.lower() != "na" else pathway_id

            pathways[pathway_id] = Pathway(
                id=pathway_id,
                name=name,
                genes=genes,
                database=database,
                species=species,
            )

    if skipped:
        logger.debug("Skipped %d malformed lines in %s", skipped, path.name)

    logger.info("Loaded %d gene sets from %s", len(pathways), path.name)
    return pathways


def save_gmt(
    gene_sets: Union[
        "Dict[str, Any]",          # Dict[str, Pathway]
        "Dict[str, Tuple]",        # Dict[str, (name, Set[str])]
    ],
    path: Union[str, Path],
) -> Path:
    """Save gene sets to a GMT file.

    Accepts the same dict types that :func:`ora` accepts:

    - ``Dict[str, Pathway]``
    - ``Dict[str, Tuple[str, Set[str]]]``  (legacy tuple format)

    Args:
        gene_sets: Gene sets to write.
        path: Output file path (created with parent directories if needed).

    Returns:
        Resolved :class:`~pathlib.Path` of the written file.

    Example::

        gene_sets = fetch_gmt("hsa", database="kegg")
        save_gmt(gene_sets, "kegg_hsa.gmt")
    """
    from biodbs._funcs.analysis.ora import Pathway

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as fh:
        for set_id, data in gene_sets.items():
            if isinstance(data, Pathway):
                name = data.name or set_id
                genes = sorted(data.genes)
            else:
                # Tuple[str, Set[str]]
                name = data[0] if data[0] else set_id
                genes = sorted(data[1])

            parts = [set_id, name] + genes
            fh.write("\t".join(parts) + "\n")

    logger.info("Saved %d gene sets to %s", len(gene_sets), path)
    return path.resolve()


# ---------------------------------------------------------------------------
# Database fetching
# ---------------------------------------------------------------------------

# Friendly aliases accepted by fetch_gmt's ``database`` parameter.
_DB_ALIASES: Dict[str, str] = {
    "kegg":     "kegg",
    "go":       "go",
    "gene ontology": "go",
    "reactome": "reactome",
    "enrichr":  "enrichr",
    "msigdb":   "enrichr",   # EnrichR hosts MSigDB libraries
}

_ENRICHR_GMT_URL = (
    "https://maayanlab.cloud/Enrichr/geneSetLibrary"
    "?libraryName={name}&fileType=gmt"
)


def fetch_gmt(
    name: str,
    database: Literal["kegg", "go", "gene ontology", "reactome", "enrichr", "msigdb"] = "kegg",
    save_at: Optional[str] = None,
    species: Union[str, "Species"] = "human",
    aspect: str = "biological_process",
    use_cache: bool = True,
    min_term_size: int = 5,
    max_term_size: int = 500,
) -> "Dict[str, Any]":
    """Fetch a gene set collection from a pathway database and return as
    ``Dict[str, Pathway]``.

    The returned dict is immediately usable with :func:`ora`.  Pass *save_at*
    to also write a GMT file for use with gseapy / GSEA Desktop.

    Args:
        name: Database-specific identifier:

            - **kegg** — KEGG organism code (e.g. ``"hsa"``, ``"mmu"``).
            - **reactome** — species name (e.g. ``"human"``, ``"mouse"``).
              Can be any value accepted by :class:`Species`.
            - **go** — GO aspect: ``"biological_process"`` (default),
              ``"molecular_function"``, ``"cellular_component"``, or
              ``"all"``.  Combined with the *species* parameter.
            - **enrichr** — EnrichR library name (e.g.
              ``"KEGG_2021_Human"``, ``"MSigDB_Hallmark_2020"``).
              Call :func:`~biodbs.fetch.EnrichR.funcs.enrichr_get_libraries`
              to list all available libraries.

        database: Source database.  One of ``"kegg"``, ``"reactome"``,
            ``"go"``, ``"enrichr"``.  Case-insensitive.
        save_at: Optional file path for the GMT output.  The placeholder
            ``{name}`` is replaced with the sanitised *name* argument.
            Examples: ``"./kegg_hsa.gmt"``, ``"./{name}.gmt"``.
            Pass ``None`` (default) to skip writing.
        species: Species for KEGG / GO / Reactome lookups.  Ignored for
            EnrichR (library names are already species-specific).
            Accepts anything that :func:`~biodbs._funcs._species.resolve_species`
            understands.
        aspect: GO aspect when ``database="go"``.  Overridden by *name* when
            *name* is a valid aspect string.
        use_cache: Whether to use and populate the pathway cache.
        min_term_size: Minimum genes per pathway (KEGG / GO / Reactome only).
        max_term_size: Maximum genes per pathway (KEGG / GO / Reactome only).

    Returns:
        ``Dict[pathway_id, Pathway]`` — same type accepted by :func:`ora`.

    Raises:
        ValueError: For unknown database names.
        RuntimeError: If the EnrichR download fails.

    Examples::

        # All KEGG human pathways → save GMT
        ks = fetch_gmt("hsa", database="kegg", save_at="./{name}.gmt")

        # Reactome mouse pathways
        rs = fetch_gmt("mouse", database="reactome")

        # GO Biological Process (human, cached)
        gs = fetch_gmt("biological_process", database="go")

        # EnrichR Hallmark gene sets
        hs = fetch_gmt("MSigDB_Hallmark_2020", database="enrichr",
                       save_at="./hallmark.gmt")

        # Run ORA immediately
        result = ora(my_genes, fetch_gmt("hsa", database="kegg"))
    """
    from biodbs._funcs._species import resolve_species
    from biodbs._funcs.analysis.ora import (
        GOAspect,
        Pathway,
        _get_go_terms,
        _get_kegg_pathways,
        _get_reactome_pathways,
    )

    # Normalise database alias
    db_key = _DB_ALIASES.get(database.lower())
    if db_key is None:
        raise ValueError(
            f"Unknown database: {database!r}. "
            f"Valid options: {sorted(set(_DB_ALIASES.values()))}"
        )

    gene_sets: Dict[str, Pathway] = {}

    # ------------------------------------------------------------------
    if db_key == "kegg":
        # For KEGG, `name` is the organism code (e.g. "hsa").
        # If it looks like a species string (contains a space or is a common
        # name) resolve it to a Species and use its kegg_code.
        try:
            sp = resolve_species(name)
            kegg_name = sp.kegg_code
        except Exception:
            # Assume it's already a KEGG organism code.
            kegg_name = name
            try:
                sp = resolve_species(species)
            except Exception:
                sp = None

        if sp is None:
            try:
                sp = resolve_species(species)
            except Exception:
                sp = None

        if sp is not None:
            gene_sets = _get_kegg_pathways(sp, use_cache=use_cache)
        else:
            # Fallback: build a minimal Species-like object
            from biodbs._funcs._species import Species as _Species
            gene_sets = _get_kegg_pathways(
                _Species.HUMAN, use_cache=use_cache
            )
            warnings.warn(
                f"Could not resolve species for KEGG organism {name!r}; "
                "falling back to human.",
                UserWarning,
                stacklevel=2,
            )

    # ------------------------------------------------------------------
    elif db_key == "reactome":
        sp = resolve_species(name if name else species)
        gene_sets = _get_reactome_pathways(
            sp,
            use_cache=use_cache,
            min_term_size=min_term_size,
            max_term_size=max_term_size,
        )

    # ------------------------------------------------------------------
    elif db_key == "go":
        # `name` may be an aspect string; fall back to the `aspect` param.
        go_aspect_aliases = {
            "bp": GOAspect.BIOLOGICAL_PROCESS,
            "biological_process": GOAspect.BIOLOGICAL_PROCESS,
            "mf": GOAspect.MOLECULAR_FUNCTION,
            "molecular_function": GOAspect.MOLECULAR_FUNCTION,
            "cc": GOAspect.CELLULAR_COMPONENT,
            "cellular_component": GOAspect.CELLULAR_COMPONENT,
            "all": GOAspect.ALL,
        }
        resolved_aspect = go_aspect_aliases.get(name.lower()) or go_aspect_aliases.get(
            aspect.lower(), GOAspect.BIOLOGICAL_PROCESS
        )
        sp = resolve_species(species)
        gene_sets = _get_go_terms(
            sp,
            aspect=resolved_aspect,
            use_cache=use_cache,
            min_term_size=min_term_size,
            max_term_size=max_term_size,
        )

    # ------------------------------------------------------------------
    elif db_key == "enrichr":
        gene_sets = _fetch_enrichr_gmt(name)

    # ------------------------------------------------------------------
    # Optionally save as GMT
    if save_at is not None:
        safe_name = name.replace("/", "_").replace("\\", "_").replace(" ", "_")
        out_path = Path(save_at.replace("{name}", safe_name))
        save_gmt(gene_sets, out_path)
        logger.info("Saved %d gene sets to %s", len(gene_sets), out_path)

    return gene_sets


def _fetch_enrichr_gmt(library_name: str) -> "Dict[str, Any]":
    """Download a gene set library from EnrichR as Pathway objects.

    EnrichR exposes a ``/geneSetLibrary?fileType=gmt`` endpoint that returns
    a GMT file directly, so we stream and parse it without writing to disk.

    Args:
        library_name: EnrichR library name (e.g. ``"KEGG_2021_Human"``).

    Returns:
        ``Dict[pathway_id, Pathway]``.

    Raises:
        RuntimeError: If the HTTP request fails.
    """
    from biodbs._funcs.analysis.ora import Pathway
    from biodbs.fetch._rate_limit import request_with_retry
    from biodbs.exceptions import raise_for_status

    url = _ENRICHR_GMT_URL.format(name=library_name)
    logger.info("Downloading EnrichR library %r from %s", library_name, url)

    response = request_with_retry(url)
    raise_for_status(response, "EnrichR", url=url)

    pathways: Dict[str, Pathway] = {}
    skipped = 0

    for line in response.text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            skipped += 1
            continue

        term_name = parts[0].strip()
        description = parts[1].strip()
        genes: FrozenSet[str] = frozenset(g.strip() for g in parts[2:] if g.strip())

        if not term_name or not genes:
            skipped += 1
            continue

        name = description if description and description.lower() != "na" else term_name

        pathways[term_name] = Pathway(
            id=term_name,
            name=name,
            genes=genes,
            database=f"EnrichR:{library_name}",
        )

    if skipped:
        logger.debug("Skipped %d malformed lines from EnrichR %r", skipped, library_name)

    logger.info(
        "Fetched %d gene sets from EnrichR library %r",
        len(pathways),
        library_name,
    )
    return pathways
