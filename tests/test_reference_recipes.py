"""Execute the documented reference recipes offline with representative inputs."""

import gzip
import re
import socket
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

import biodbs.fetch
import biodbs.translate
from biodbs.data.HGNC.data import HGNCFetchedData

ROOT = Path(__file__).resolve().parents[1]
RECIPES = re.findall(
    r"```python\n(.*?)```",
    (ROOT / "docs/getting-started/mapping-databases.md").read_text(encoding="utf-8"),
    re.DOTALL,
)


def _run_recipe(index, state):
    # Only execute checked-in documentation, never externally supplied code.
    exec(RECIPES[index], state)  # noqa: S102


@pytest.fixture
def offline_reference_user(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def no_network(*args, **kwargs):
        raise AssertionError("An offline recipe attempted a network request")

    monkeypatch.setattr(socket, "socket", no_network)
    data = HGNCFetchedData(
        {
            "response": {
                "numFound": 3,
                "docs": [
                    {
                        "hgnc_id": "HGNC:11998",
                        "symbol": "TP53",
                        "entrez_id": "7157",
                        "ensembl_gene_id": "ENSG00000141510",
                        "uniprot_ids": ["P04637", "PTEST2"],
                    },
                    {
                        "hgnc_id": "HGNC:1100",
                        "symbol": "BRCA1",
                        "entrez_id": "672",
                        "ensembl_gene_id": "ENSG00000012048",
                    },
                    {"hgnc_id": "HGNC:TEST", "symbol": "NO_XREF"},
                ],
            }
        }
    )

    def hgnc_fetch(field, term):
        assert (field, term) == ("status", "Approved")
        return data

    monkeypatch.setattr(biodbs.fetch, "hgnc_fetch", hgnc_fetch)
    return {}


def test_hgnc_recipes_preserve_missing_and_multiple_ids(offline_reference_user):
    state = offline_reference_user
    _run_recipe(0, state)
    _run_recipe(1, state)
    with sqlite3.connect("human_genes.db") as db:
        assert db.execute("SELECT COUNT(*) FROM gene").fetchone() == (3,)
        assert db.execute(
            "SELECT entrez_id FROM gene WHERE symbol='NO_XREF'"
        ).fetchone() == (None,)
        assert db.execute(
            "SELECT uniprot_ids FROM gene_uniprot ORDER BY uniprot_ids"
        ).fetchall() == [
            ("P04637",),
            ("PTEST2",),
        ]
        assert (
            "USING INDEX gene_symbol"
            in db.execute(
                "EXPLAIN QUERY PLAN SELECT entrez_id FROM gene WHERE symbol=?",
                ("TP53",),
            ).fetchone()[3]
        )
    with pytest.raises(ValueError, match="already exists"):
        _run_recipe(0, state)
    with sqlite3.connect("human_genes.db") as db:
        assert db.execute("SELECT COUNT(*) FROM gene").fetchone() == (3,)


def test_kegg_recipe_preserves_one_to_many(offline_reference_user, monkeypatch):
    def chemical(ids, from_type, to_type, *, bulk):
        assert (ids, from_type, to_type, bulk) == ([], "kegg_compound", "chebi", True)
        return pd.DataFrame(
            {
                "source_id": ["cpd:C00001"] * 2,
                "target_id": ["chebi:15377", "chebi:TEST"],
            }
        )

    def gene(ids, from_type, to_type, *, species, database, bulk):
        assert (ids, from_type, to_type, species, database, bulk) == (
            [],
            "kegg_gene",
            "entrez_id",
            "human",
            "kegg",
            True,
        )
        return pd.DataFrame(
            {"source_id": ["hsa:7157"], "target_id": ["ncbi-geneid:7157"]}
        )

    monkeypatch.setattr(biodbs.translate, "translate_chemical_ids", chemical)
    monkeypatch.setattr(biodbs.translate, "translate_gene_ids", gene)
    _run_recipe(2, offline_reference_user)
    _run_recipe(3, offline_reference_user)
    with sqlite3.connect("chemicals.db") as db:
        assert db.execute(
            "SELECT target_id FROM compound_chebi WHERE source_id=?", ("cpd:C00001",)
        ).fetchall() == [("chebi:15377",), ("chebi:TEST",)]


def test_taxonomy_recipes_export_loaded_reference(offline_reference_user, monkeypatch):
    def download(dest):
        assert dest == "data/ncbi"
        return ROOT / "tests/test_taxonomy/fixtures"

    monkeypatch.setattr(biodbs.fetch, "ncbi_download_taxdump", download)
    _run_recipe(4, offline_reference_user)
    _run_recipe(5, offline_reference_user)
    with sqlite3.connect("taxonomy.db") as db:
        assert db.execute(
            "SELECT name, rank, parent FROM taxon WHERE taxid=562"
        ).fetchone() == (
            "Escherichia coli",
            "species",
            561,
        )
        assert db.execute(
            "SELECT taxid FROM taxon_name WHERE name=?", ("bacillus coli",)
        ).fetchone() == (562,)
        assert db.execute(
            "SELECT taxid FROM merged WHERE old_taxid=999999"
        ).fetchone() == (562,)
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_query_recipe_is_readonly_and_offline(offline_reference_user):
    _run_recipe(0, offline_reference_user)
    _run_recipe(6, offline_reference_user)
    assert offline_reference_user["rows"] == [("7157", "ENSG00000141510")]


@pytest.fixture
def unichem_download(monkeypatch):
    from biodbs._funcs.translate import chemical_db

    def download(url, target, service, **kwargs):
        target.write_bytes(
            gzip.compress(
                b"From src:'1'\tTo src:'22'\nCHEMBL25\t2244\nCHEMBL25\t9999\n",
            )
        )
        return target

    monkeypatch.setattr(chemical_db, "download_binary", download)


def test_unichem_build_and_query_recipes(offline_reference_user, unichem_download):
    _run_recipe(7, offline_reference_user)
    _run_recipe(8, offline_reference_user)
    assert offline_reference_user["path"] == Path("mapping.db")
    assert offline_reference_user["cids"] == [(2244,), (9999,)]
    assert offline_reference_user["chembl_ids"] == [("CHEMBL25",)]


@pytest.mark.parametrize(
    "filename, heading, result",
    [
        ("README.md", "### Build an Offline Chemical Mapping Database", "cids"),
        (
            "docs/getting-started/quickstart.md",
            "## Build an Offline Chemical Mapping Database",
            "chembl_ids",
        ),
        ("docs/translate/chemicals.md", "## Build an Offline Chemical Reference", None),
    ],
)
def test_discoverable_builder_examples(
    offline_reference_user,
    unichem_download,
    filename,
    heading,
    result,
):
    section = (ROOT / filename).read_text(encoding="utf-8").split(heading, 1)[1]
    section = section.split("\n##", 1)[0]
    snippet = re.findall(r"```python\n(.*?)```", section, re.DOTALL)[0]
    # Only execute checked-in documentation, never externally supplied code.
    exec(snippet, offline_reference_user)  # noqa: S102
    assert offline_reference_user["path"] == Path("mapping.db")
    if result == "cids":
        assert offline_reference_user[result] == [(2244,), (9999,)]
    elif result == "chembl_ids":
        assert offline_reference_user[result] == [("CHEMBL25",)]
    with sqlite3.connect("file:mapping.db?mode=ro", uri=True) as db:
        assert db.execute("SELECT COUNT(*) FROM chemical_mapping").fetchone() == (2,)
