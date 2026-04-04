"""
Test all from_type x to_type x database combinations for translate_gene_ids.

Uses a single well-known gene (TP53 / ENSG00000141510 / 7157 / P04637) so
results can be validated by eye.  Outputs a markdown table.

Usage:
    python test_translate_combinations.py              # all databases
    python test_translate_combinations.py ncbi         # single database
    python test_translate_combinations.py ncbi hgnc    # multiple databases
"""

import sys
import warnings
import argparse
from pathlib import Path

# Make sure the package root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from biodbs.translate import translate_gene_ids, GeneIDType, TranslationDatabase

# ---------------------------------------------------------------------------
# Seed IDs — one canonical value per GeneIDType that is known for TP53
# ---------------------------------------------------------------------------
SEED: dict[str, str] = {
    GeneIDType.GENE_SYMBOL:           "TP53",
    GeneIDType.ENSEMBL_GENE_ID:       "ENSG00000141510",
    GeneIDType.ENSEMBL_TRANSCRIPT_ID: "ENST00000269305",
    GeneIDType.ENSEMBL_PROTEIN_ID:    "ENSP00000269305",
    GeneIDType.ENTREZ_ID:             "7157",
    GeneIDType.HGNC_ID:              "HGNC:11998",
    GeneIDType.HGNC_SYMBOL:          "TP53",
    GeneIDType.UNIPROT_ID:           "P04637",
    GeneIDType.REFSEQ_MRNA:          "NM_000546",
    GeneIDType.REFSEQ_PROTEIN:       "NP_000537",
    # PDB_ID is structural; no single canonical TP53 PDB entry with clean mapping
    GeneIDType.PDB_ID:               None,
}

# Which (database, from_types) make sense to test — skip if seed is None
# or if the ID type is not supported by that database.
DB_FROM_SUPPORT: dict[str, list[GeneIDType]] = {
    "ncbi": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.REFSEQ_MRNA,
    ],
    "ensembl": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.ENSEMBL_TRANSCRIPT_ID,
        GeneIDType.ENSEMBL_PROTEIN_ID,
    ],
    "uniprot": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.UNIPROT_ID,
        GeneIDType.ENTREZ_ID,
    ],
    "biomart": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.HGNC_ID,
        GeneIDType.HGNC_SYMBOL,
        GeneIDType.UNIPROT_ID,
        GeneIDType.REFSEQ_MRNA,
    ],
    "hgnc": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.HGNC_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.UNIPROT_ID,
        GeneIDType.REFSEQ_MRNA,
    ],
}

# All target types to test per database
DB_TO_SUPPORT: dict[str, list[GeneIDType]] = {
    "ncbi": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.UNIPROT_ID,
        GeneIDType.REFSEQ_MRNA,
    ],
    "ensembl": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.ENSEMBL_TRANSCRIPT_ID,
        GeneIDType.ENSEMBL_PROTEIN_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.UNIPROT_ID,
        GeneIDType.REFSEQ_MRNA,
        GeneIDType.REFSEQ_PROTEIN,
    ],
    "uniprot": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.UNIPROT_ID,
        GeneIDType.REFSEQ_PROTEIN,
        GeneIDType.PDB_ID,
    ],
    "biomart": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.ENSEMBL_TRANSCRIPT_ID,
        GeneIDType.ENSEMBL_PROTEIN_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.HGNC_ID,
        GeneIDType.HGNC_SYMBOL,
        GeneIDType.UNIPROT_ID,
        GeneIDType.REFSEQ_MRNA,
        GeneIDType.REFSEQ_PROTEIN,
    ],
    "hgnc": [
        GeneIDType.GENE_SYMBOL,
        GeneIDType.HGNC_ID,
        GeneIDType.ENTREZ_ID,
        GeneIDType.ENSEMBL_GENE_ID,
        GeneIDType.UNIPROT_ID,
        GeneIDType.REFSEQ_MRNA,
    ],
}

ALL_DATABASES = list(DB_FROM_SUPPORT.keys())

# ---------------------------------------------------------------------------

def try_translate(db: str, from_type: GeneIDType, to_type: GeneIDType, seed_id: str):
    """Run translate_gene_ids and return (status, result_str)."""
    if seed_id is None:
        return "N/A", ""
    if from_type == to_type:
        return "SKIP", "(same type)"
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = translate_gene_ids(
                [seed_id],
                from_type=from_type,
                to_type=to_type,
                database=db,
                return_dict=True,
            )
        warn_flag = " [W]" if caught else ""
        value = result.get(seed_id)
        if value is not None and value != "" and str(value) != "nan":
            return f"OK{warn_flag}", str(value)
        else:
            return f"EMPTY{warn_flag}", "(no result)"
    except Exception as e:
        short = str(e)[:60].replace("\n", " ")
        return "ERR", short


def main():
    parser = argparse.ArgumentParser(
        description="Test translate_gene_ids across from_type × to_type × database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available databases: {', '.join(ALL_DATABASES)}",
    )
    parser.add_argument(
        "databases",
        nargs="*",
        metavar="DB",
        help=(
            "Databases to test (default: all). "
            f"Choose from: {', '.join(ALL_DATABASES)}."
        ),
    )
    args = parser.parse_args()

    if args.databases:
        invalid = [d for d in args.databases if d not in ALL_DATABASES]
        if invalid:
            parser.error(
                f"Unknown database(s): {', '.join(invalid)}. "
                f"Valid options: {', '.join(ALL_DATABASES)}"
            )
        databases = args.databases
    else:
        databases = ALL_DATABASES

    all_rows = []

    for db in databases:
        from_types = DB_FROM_SUPPORT[db]
        to_types   = DB_TO_SUPPORT[db]

        print(f"\n{'='*70}")
        print(f"  Database: {db.upper()}")
        print(f"{'='*70}")

        # Build header
        to_names = [t.value for t in to_types]
        header = f"{'from_type':<30} " + " | ".join(f"{n:<22}" for n in to_names)
        sep    = "-" * len(header)
        print(header)
        print(sep)

        for from_type in from_types:
            seed_id = SEED.get(from_type)
            row_cells = [f"{from_type.value:<30}"]
            row_results = {}
            for to_type in to_types:
                status, value = try_translate(db, from_type, to_type, seed_id)
                row_results[to_type] = (status, value)
                if status.startswith("OK"):
                    cell = f"{status}: {value}"
                else:
                    cell = status
                row_cells.append(f"{cell:<22}")
            print(" | ".join(row_cells))

            for to_type, (status, value) in row_results.items():
                all_rows.append({
                    "database": db,
                    "from_type": from_type.value,
                    "to_type": to_type.value,
                    "seed_id": seed_id or "",
                    "status": status,
                    "result": value,
                })

    # ------------------------------------------------------------------
    # Markdown table output
    # ------------------------------------------------------------------
    print("\n\n" + "="*80)
    print("MARKDOWN TABLE")
    print("="*80 + "\n")

    print("| database | from_type | to_type | seed_id | status | result |")
    print("|----------|-----------|---------|---------|--------|--------|")
    for r in all_rows:
        if r["status"] in ("SKIP", "N/A"):
            continue
        result_cell = r["result"].replace("|", "\\|")
        print(f"| {r['database']} | {r['from_type']} | {r['to_type']} | `{r['seed_id']}` | {r['status']} | `{result_cell}` |")


if __name__ == "__main__":
    main()
