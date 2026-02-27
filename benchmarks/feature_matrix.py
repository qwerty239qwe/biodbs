#!/usr/bin/env python
"""Feature comparison matrix: biodbs vs similar bioinformatics Python packages.

Prints structured comparison tables covering:
- Databases/services supported
- API feature coverage
- Output format support
- Developer experience features

Usage:
    uv run python benchmarks/feature_matrix.py
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

PACKAGES = [
    "biodbs",
    "bioservices",
    "pubchempy",
    "chembl-webresource-client",
    "mygene",
    "biopython (Entrez)",
]

# (database/service, supported_by) -- list of package names (short) that support it
DATABASE_COVERAGE = [
    ("PubChem",            ["biodbs", "pubchempy"]),
    ("ChEMBL",             ["biodbs", "bioservices", "chembl-wrc"]),
    ("KEGG",               ["biodbs", "bioservices"]),
    ("Ensembl REST",       ["biodbs", "bioservices"]),
    ("BioMart",            ["biodbs", "bioservices"]),
    ("UniProt",            ["biodbs", "bioservices"]),
    ("Human Protein Atlas", ["biodbs"]),
    ("FDA openFDA",        ["biodbs"]),
    ("QuickGO",            ["biodbs", "bioservices"]),
    ("Reactome",           ["biodbs", "bioservices"]),
    ("Disease Ontology",   ["biodbs"]),
    ("NCBI Entrez",        ["biodbs", "biopython", "bioservices"]),
    ("EnrichR (service)",  ["biodbs"]),  # analysis service, not a traditional database
    ("MyGene.info",        ["mygene"]),
    ("ArrayExpress",       ["bioservices"]),
    ("ChEBI",              ["bioservices"]),
    ("PDB",                ["bioservices"]),
    ("WikiPathways",       ["bioservices"]),
    ("TOTAL",              None),  # sentinel -- filled programmatically
]

# Feature matrix rows: (feature_label, {package_short: value_str})
FEATURES = [
    (
        "Databases / services",
        {
            "biodbs":      "12",
            "bioservices": "~40 (many legacy)",
            "pubchempy":   "1 (PubChem)",
            "chembl-wrc":  "1 (ChEMBL)",
            "mygene":      "1* (aggregates many)",
            "biopython":   "1* (NCBI Entrez, ~30 sub-DBs)",
        },
    ),
    (
        "Rate limiting",
        {
            "biodbs":      "per-host singleton, exp. backoff",
            "bioservices": "basic (sleep between calls)",
            "pubchempy":   "none built-in",
            "chembl-wrc":  "none built-in",
            "mygene":      "none built-in",
            "biopython":   "minimal (max_tries only)",
        },
    ),
    (
        "Async / batch fetch",
        {
            "biodbs":      "batch via thread pool; individual calls sync",
            "bioservices": "no",
            "pubchempy":   "partial (chunked sync)",
            "chembl-wrc":  "yes (streaming/lazy eval)",
            "mygene":      "yes (bulk POST)",
            "biopython":   "partial (epost batching)",
        },
    ),
    (
        "Cross-DB ID translation",
        {
            "biodbs":      "yes (gene, protein, chemical)",
            "bioservices": "via UniChem / individual services",
            "pubchempy":   "within PubChem only",
            "chembl-wrc":  "within ChEMBL only",
            "mygene":      "yes (gene IDs only)",
            "biopython":   "via elink (NCBI IDs only)",
        },
    ),
    (
        "pandas DataFrame output",
        {
            "biodbs":      "yes (.as_dataframe())",
            "bioservices": "yes (most services)",
            "pubchempy":   "no (Compound objects)",
            "chembl-wrc":  "no (list of dicts)",
            "mygene":      "yes",
            "biopython":   "no (BioPython records)",
        },
    ),
    (
        "polars DataFrame output",
        {
            "biodbs":      "yes (.as_dataframe(engine='polars'))",
            "bioservices": "no",
            "pubchempy":   "no",
            "chembl-wrc":  "no",
            "mygene":      "no",
            "biopython":   "no",
        },
    ),
    (
        "Knowledge graph (KG)",
        {
            "biodbs":      "yes (KnowledgeGraph, Node, Edge)",
            "bioservices": "no",
            "pubchempy":   "no",
            "chembl-wrc":  "no",
            "mygene":      "no",
            "biopython":   "no",
        },
    ),
    (
        "Graph export formats",
        {
            "biodbs":      "NetworkX, JSON-LD, RDF/Turtle, Neo4j CSV, Cypher",
            "bioservices": "none",
            "pubchempy":   "none",
            "chembl-wrc":  "none",
            "mygene":      "none",
            "biopython":   "none",
        },
    ),
    (
        "Enrichment / ORA analysis",
        {
            "biodbs":      "yes (KEGG, GO, EnrichR + hypergeom. test)",
            "bioservices": "no",
            "pubchempy":   "no",
            "chembl-wrc":  "no",
            "mygene":      "no",
            "biopython":   "no",
        },
    ),
    (
        "Local caching",
        {
            "biodbs":      "yes (SQLite / JSON / CSV + expiry)",
            "bioservices": "no",
            "pubchempy":   "no",
            "chembl-wrc":  "no",
            "mygene":      "yes (SQLite, per-query)",
            "biopython":   "no",
        },
    ),
    (
        "Custom exception hierarchy",
        {
            "biodbs":      "yes (8 types: APIServerError, RateLimit, NotFound...)",
            "bioservices": "minimal (generic errors)",
            "pubchempy":   "minimal (PubChemHTTPError)",
            "chembl-wrc":  "no (raw requests exceptions)",
            "mygene":      "no (raw requests exceptions)",
            "biopython":   "minimal (urllib errors)",
        },
    ),
    (
        "Drug-drug interactions",
        {
            "biodbs":      "yes (kegg_ddi)",
            "bioservices": "via KEGG wrapper",
            "pubchempy":   "no",
            "chembl-wrc":  "via metabolism endpoint",
            "mygene":      "no",
            "biopython":   "no",
        },
    ),
    (
        "Variant effect prediction",
        {
            "biodbs":      "yes (ensembl_vep_*)",
            "bioservices": "via Ensembl wrapper",
            "pubchempy":   "no",
            "chembl-wrc":  "no",
            "mygene":      "no",
            "biopython":   "no",
        },
    ),
    (
        "Requires Python",
        {
            "biodbs":      ">= 3.10",
            "bioservices": ">= 3.7",
            "pubchempy":   ">= 3.10",
            "chembl-wrc":  ">= 3.x",
            "mygene":      "2 or 3",
            "biopython":   ">= 3.10",
        },
    ),
]

# Short keys used in the dicts above -> display names
SHORT_TO_DISPLAY = {
    "biodbs":      "biodbs",
    "bioservices": "bioservices",
    "pubchempy":   "pubchempy",
    "chembl-wrc":  "chembl-wrc",
    "mygene":      "mygene",
    "biopython":   "biopython",
}

COL_ORDER = ["biodbs", "bioservices", "pubchempy", "chembl-wrc", "mygene", "biopython"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hr(widths: list[int], char: str = "-") -> str:
    return "+" + "+".join(char * (w + 2) for w in widths) + "+"


def _row(cells: list[str], widths: list[int]) -> str:
    parts = []
    for cell, w in zip(cells, widths):
        parts.append(f" {cell:<{w}} ")
    return "|" + "|".join(parts) + "|"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    all_rows = [headers] + rows
    widths = [max(len(str(cell)) for cell in col) for col in zip(*all_rows)]
    print(_hr(widths, "="))
    print(_row(headers, widths))
    print(_hr(widths, "="))
    for r in rows:
        print(_row(r, widths))
    print(_hr(widths))
    print()


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def print_database_coverage() -> None:
    print("\n" + "=" * 70)
    print("  DATABASE / SERVICE COVERAGE")
    print("=" * 70)

    short_keys = COL_ORDER
    headers = ["Database / Service"] + [SHORT_TO_DISPLAY[k] for k in short_keys]

    rows = []
    totals = {k: 0 for k in short_keys}

    for db, supported in DATABASE_COVERAGE:
        if db == "TOTAL":
            continue
        if isinstance(supported, str):
            supported = [supported]
        row = [db]
        for k in short_keys:
            if k in supported:
                row.append("yes")
                totals[k] += 1
            else:
                row.append("")
        rows.append(row)

    # Total row
    total_row = ["TOTAL (distinct DBs)"] + [str(totals[k]) for k in short_keys]
    rows.append(total_row)

    print_table(headers, rows)

    print(
        "  * mygene aggregates NCBI Gene, Ensembl, UniProt etc. through one endpoint\n"
        "  * biopython Entrez covers ~30 NCBI sub-databases (PubMed, GenBank, GEO...)\n"
        "  * bioservices supports ~40 services; several are legacy/unmaintained\n"
    )


def print_feature_matrix() -> None:
    print("\n" + "=" * 70)
    print("  FEATURE COMPARISON MATRIX")
    print("=" * 70)

    short_keys = COL_ORDER
    headers = ["Feature"] + [SHORT_TO_DISPLAY[k] for k in short_keys]

    rows = []
    for label, vals in FEATURES:
        row = [label]
        for k in short_keys:
            row.append(vals.get(k, "--"))
        rows.append(row)

    print_table(headers, rows)


def print_summary() -> None:
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    summary = [
        [
            "biodbs",
            "12 databases",
            "Highest breadth; only package with KG, ORA, and polars support",
        ],
        [
            "bioservices",
            "~40 services",
            "Widest service count but many are legacy; no graph/analysis layer",
        ],
        [
            "pubchempy",
            "1 (PubChem)",
            "Best PubChem specialist; clean API; no rate limiting",
        ],
        [
            "chembl-wrc",
            "1 (ChEMBL)",
            "Official ChEMBL client; lazy streaming; Django QuerySet style",
        ],
        [
            "mygene",
            "1* (aggregated)",
            "Fastest gene ID lookup; SQLite cache; pandas output",
        ],
        [
            "biopython",
            "1* (NCBI, ~30 sub-DBs)",
            "Mature ecosystem; best for NCBI Entrez; no unified fetch layer",
        ],
    ]
    print_table(["Package", "DB Coverage", "Standout Characteristic"], summary)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("\nbioDBs Benchmark -- Feature Comparison")
    print("Generated by benchmarks/feature_matrix.py")
    print_database_coverage()
    print_feature_matrix()
    print_summary()


if __name__ == "__main__":
    main()
