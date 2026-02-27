#!/usr/bin/env python
"""Count public API callable items in biodbs and comparable packages.

For each package this script counts:
  - Top-level public functions / callables exported from the package
  - (optionally) methods on main user-facing classes

Usage:
    uv run python benchmarks/count_functions.py

Competitor packages are measured only when installed.
Install them with, e.g.:
    uv pip install bioservices pubchempy mygene chembl-webresource-client biopython
"""

from __future__ import annotations

import importlib
import inspect
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

class CountResult(NamedTuple):
    package: str
    version: str
    total: int
    breakdown: dict[str, int]   # label -> count
    installed: bool
    note: str = ""


# ---------------------------------------------------------------------------
# biodbs counter (uses __all__ -- the authoritative public surface)
# ---------------------------------------------------------------------------

def _is_callable_item(obj: object) -> bool:
    return inspect.isfunction(obj) or inspect.isbuiltin(obj) or inspect.isclass(obj)


def count_biodbs() -> CountResult:
    import biodbs

    version = getattr(biodbs, "__version__", "?")

    # Pull the full __all__ list and categorise each name
    all_names: list[str] = getattr(biodbs, "__all__", [])

    # Category prefixes -> label
    PREFIXES: list[tuple[str, str]] = [
        ("pubchem_",   "fetch / PubChem"),
        ("biomart_",   "fetch / BioMart"),
        ("hpa_",       "fetch / HPA"),
        ("chembl_",    "fetch / ChEMBL"),
        ("kegg_",      "fetch / KEGG"),
        ("quickgo_",   "fetch / QuickGO"),
        ("fda_",       "fetch / FDA"),
        ("enrichr_",   "fetch / EnrichR"),
        ("ensembl_",   "fetch / Ensembl"),
        ("reactome_",  "fetch / Reactome"),
        ("ncbi_",      "fetch / NCBI"),
        ("uniprot_",   "fetch / UniProt"),
        ("gene_to_",   "fetch / UniProt"),
        ("do_",        "fetch / Disease Ontology"),
        ("doid_",      "fetch / Disease Ontology"),
        ("translate_", "translate"),
        ("ora",        "analysis"),
        ("hypergeometric_", "analysis"),
        ("multiple_",  "analysis"),
        ("ORAResult",  "analysis"),
        ("API",        "exceptions"),
        ("BiodBS",     "exceptions"),
        ("IDTranslation", "exceptions"),
    ]

    # Also count graph functions by checking fetch.__init__
    try:
        from biodbs import fetch as _fetch
        extra_fetch_all: list[str] = getattr(_fetch, "__all__", [])
        # Remove items that are already in biodbs.__all__ or are utility/class names
        extra_only = [
            n for n in extra_fetch_all
            if n not in all_names and not n.startswith(("RateLimiter", "get_rate", "request_with", "retry_with", "funcs"))
        ]
    except Exception:
        extra_only = []

    combined = list(all_names) + extra_only

    breakdown: dict[str, int] = {}
    uncategorised: list[str] = []

    for name in combined:
        matched = False
        for prefix, label in PREFIXES:
            if name.startswith(prefix):
                breakdown[label] = breakdown.get(label, 0) + 1
                matched = True
                break
        if not matched:
            # Graph items
            graph_classes = {"KnowledgeGraph", "Node", "Edge", "NodeType", "EdgeType", "DataSource"}
            graph_builders = {"build_graph", "build_disease_graph", "build_go_graph",
                              "build_reactome_graph", "build_kegg_graph", "merge_graphs",
                              "build_disease_graph_with_hierarchy"}
            graph_exporters = {"to_networkx", "to_json_ld", "to_rdf", "to_neo4j_csv", "to_cypher"}
            graph_utils = {"find_shortest_path", "find_all_paths", "get_neighborhood",
                           "get_connected_component", "find_hub_nodes", "get_graph_statistics"}
            graph_all = graph_classes | graph_builders | graph_exporters | graph_utils
            submodules = {"fetch", "translate", "analysis", "graph"}

            if name in graph_all:
                breakdown["graph"] = breakdown.get("graph", 0) + 1
            elif name in submodules:
                pass  # namespace re-exports -- don't count as functions
            else:
                uncategorised.append(name)

    total = sum(breakdown.values())

    # Sub-totals
    fetch_total = sum(v for k, v in breakdown.items() if k.startswith("fetch /"))
    breakdown["SUBTOTAL: fetch"] = fetch_total
    breakdown["SUBTOTAL: translate"] = breakdown.get("translate", 0)
    breakdown["SUBTOTAL: analysis"] = breakdown.get("analysis", 0)
    breakdown["SUBTOTAL: graph"] = breakdown.get("graph", 0)
    breakdown["SUBTOTAL: exceptions"] = breakdown.get("exceptions", 0)

    note = ""
    if uncategorised:
        note = f"Uncategorised: {', '.join(uncategorised)}"

    return CountResult(
        package="biodbs",
        version=version,
        total=total,
        breakdown=breakdown,
        installed=True,
        note=note,
    )


# ---------------------------------------------------------------------------
# Competitor counters
# ---------------------------------------------------------------------------

def _count_public_callables(module, prefix_filter: str = "") -> list[str]:
    """Return names of public functions/classes in a module."""
    names = []
    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue
        if prefix_filter and not name.lower().startswith(prefix_filter.lower()):
            continue
        if _is_callable_item(obj):
            names.append(name)
    return names


def count_bioservices() -> CountResult:
    try:
        import bioservices
        version = getattr(bioservices, "__version__", "?")
    except ImportError:
        return CountResult("bioservices", "?", 0, {}, False, "not installed")

    # bioservices exposes service classes; count each class and its public methods
    service_classes: dict[str, int] = {}
    for name, obj in inspect.getmembers(bioservices, inspect.isclass):
        if name.startswith("_"):
            continue
        methods = [m for m, _ in inspect.getmembers(obj, predicate=inspect.isfunction)
                   if not m.startswith("_")]
        if methods:
            service_classes[name] = len(methods)

    total_methods = sum(service_classes.values())
    return CountResult(
        package="bioservices",
        version=version,
        total=total_methods,
        breakdown=service_classes,
        installed=True,
        note=f"{len(service_classes)} service classes, {total_methods} total public methods",
    )


def count_pubchempy() -> CountResult:
    try:
        import pubchempy
        version = getattr(pubchempy, "__version__", "?")
    except ImportError:
        return CountResult("pubchempy", "?", 0, {}, False, "not installed")

    breakdown: dict[str, int] = {}

    # Top-level convenience functions
    top_funcs = _count_public_callables(pubchempy)
    # Exclude class names (Compound, Substance, Atom, Bond)
    class_names = {n for n, o in inspect.getmembers(pubchempy, inspect.isclass)}
    pure_funcs = [n for n in top_funcs if n not in class_names]
    breakdown["top-level functions"] = len(pure_funcs)

    # Public methods on main classes
    for cls_name in ["Compound", "Substance"]:
        cls = getattr(pubchempy, cls_name, None)
        if cls:
            methods = [m for m, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
                       if not m.startswith("_")]
            breakdown[f"{cls_name} methods"] = len(methods)

    total = sum(breakdown.values())
    return CountResult(
        package="pubchempy",
        version=version,
        total=total,
        breakdown=breakdown,
        installed=True,
    )


def count_mygene() -> CountResult:
    try:
        import mygene
        version = getattr(mygene, "__version__", "?")
    except ImportError:
        return CountResult("mygene", "?", 0, {}, False, "not installed")

    breakdown: dict[str, int] = {}

    # MyGeneInfo class
    mg_cls = getattr(mygene, "MyGeneInfo", None)
    if mg_cls:
        methods = [m for m, _ in inspect.getmembers(mg_cls, predicate=inspect.isfunction)
                   if not m.startswith("_")]
        breakdown["MyGeneInfo methods"] = len(methods)

    # Top-level functions
    top_funcs = [n for n in _count_public_callables(mygene)
                 if not inspect.isclass(getattr(mygene, n))]
    breakdown["top-level functions"] = len(top_funcs)

    total = sum(breakdown.values())
    return CountResult(
        package="mygene",
        version=version,
        total=total,
        breakdown=breakdown,
        installed=True,
    )


def count_chembl_client() -> CountResult:
    try:
        from chembl_webresource_client.new_client import new_client
        import chembl_webresource_client
        version = getattr(chembl_webresource_client, "__version__", "?")
    except ImportError:
        return CountResult("chembl-webresource-client", "?", 0, {}, False, "not installed")

    breakdown: dict[str, int] = {}

    resource_count = 0
    method_count = 0
    for name in dir(new_client):
        if name.startswith("_"):
            continue
        resource = getattr(new_client, name, None)
        if resource is None:
            continue
        # Each resource is a Manager; count its public methods
        methods = [m for m in dir(resource) if not m.startswith("_")
                   and callable(getattr(resource, m, None))]
        if methods:
            resource_count += 1
            method_count += len(methods)
            breakdown[f"resource: {name}"] = len(methods)

    total = resource_count  # resource endpoints is the meaningful count
    return CountResult(
        package="chembl-webresource-client",
        version=version,
        total=total,
        breakdown={"resource endpoints": resource_count, "total methods across resources": method_count},
        installed=True,
        note=f"{resource_count} queryable resource types",
    )


def count_biopython_entrez() -> CountResult:
    try:
        from Bio import Entrez
        import Bio
        version = getattr(Bio, "__version__", "?")
    except ImportError:
        return CountResult("biopython (Entrez)", "?", 0, {}, False, "not installed")

    funcs = _count_public_callables(Entrez)
    breakdown = {"Bio.Entrez functions": len(funcs)}
    return CountResult(
        package="biopython (Bio.Entrez)",
        version=version,
        total=len(funcs),
        breakdown=breakdown,
        installed=True,
        note="Entrez module only; biopython has many more modules (SeqIO, Align, etc.)",
    )


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _hr(widths: list[int], char: str = "-") -> str:
    return "+" + "+".join(char * (w + 2) for w in widths) + "+"


def _row(cells: list[str], widths: list[int]) -> str:
    return "|" + "|".join(f" {c:<{w}} " for c, w in zip(cells, widths)) + "|"


def print_biodbs_breakdown(result: CountResult) -> None:
    print("\n" + "=" * 60)
    print(f"  biodbs v{result.version}  --  Public API Breakdown")
    print("=" * 60)

    # Only show named categories (not SUBTOTAL lines)
    rows = [
        (label, str(count))
        for label, count in sorted(result.breakdown.items())
        if not label.startswith("SUBTOTAL")
    ]
    subtotals = [
        (label, str(count))
        for label, count in result.breakdown.items()
        if label.startswith("SUBTOTAL")
    ]
    rows += [("-" * 30, "-" * 6)]
    rows += subtotals
    rows += [("GRAND TOTAL", str(result.total))]

    widths = [max(len(r[0]) for r in rows), max(len(r[1]) for r in rows)]
    print(_hr(widths))
    print(_row(["Category", "Count"], widths))
    print(_hr(widths, "="))
    for label, count in rows:
        print(_row([label, count], widths))
    print(_hr(widths))
    if result.note:
        print(f"  Note: {result.note}")
    print()


def print_comparison_table(results: list[CountResult]) -> None:
    print("\n" + "=" * 70)
    print("  PACKAGE COMPARISON -- PUBLIC API SIZE")
    print("=" * 70)

    headers = ["Package", "Version", "Installed", "API Items", "Notes"]
    rows = []
    for r in results:
        rows.append([
            r.package,
            r.version if r.installed else "--",
            "yes" if r.installed else "no",
            str(r.total) if r.installed else "--",
            r.note or "--",
        ])

    all_rows = [headers] + rows
    widths = [max(len(str(cell)) for cell in col) for col in zip(*all_rows)]

    print(_hr(widths, "="))
    print(_row(headers, widths))
    print(_hr(widths, "="))
    for r in rows:
        print(_row(r, widths))
    print(_hr(widths))

    print(
        "\n  Notes on counting methodology:\n"
        "  * biodbs: items in __all__ (functions, classes, enums, exceptions)\n"
        "  * bioservices: public methods across all service classes\n"
        "  * pubchempy: top-level functions + Compound/Substance public methods\n"
        "  * mygene: MyGeneInfo public methods + top-level functions\n"
        "  * chembl-wrc: count of queryable resource endpoints (not methods)\n"
        "  * biopython: Bio.Entrez module public functions only\n"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("\nbioDBs Benchmark -- Public API Function Count")
    print("Generated by benchmarks/count_functions.py\n")

    biodbs_result = count_biodbs()
    print_biodbs_breakdown(biodbs_result)

    all_results = [
        biodbs_result,
        count_bioservices(),
        count_pubchempy(),
        count_mygene(),
        count_chembl_client(),
        count_biopython_entrez(),
    ]

    print_comparison_table(all_results)


if __name__ == "__main__":
    main()
