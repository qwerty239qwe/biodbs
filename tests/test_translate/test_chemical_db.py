"""Offline tests of the path-based UniChem reference builder."""

import gzip
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

import biodbs
import biodbs.translate
from biodbs._funcs.translate import chemical_db
from biodbs.translate import build_chemical_mapping_db

HEADER = "From src:'1'\tTo src:'22'\n"
ROWS = "CHEMBL25\t2244\nCHEMBL25\t9999\nCHEMBL521\t2519\nCHEMBL25\t2244\n"


@pytest.fixture
def archive_download(monkeypatch):
    payload = gzip.compress((HEADER + ROWS).encode("ascii"))
    calls = []

    def download(url, target, service, **kwargs):
        calls.append((url, target, service, kwargs))
        Path(target).write_bytes(payload)
        return Path(target)

    monkeypatch.setattr(chemical_db, "download_binary", download)
    return calls, payload


def test_public_exports():
    assert biodbs.build_chemical_mapping_db is build_chemical_mapping_db
    assert "build_chemical_mapping_db" in biodbs.__all__
    assert "build_chemical_mapping_db" in biodbs.translate.__all__


def test_build_and_query_both_directions(tmp_path, archive_download):
    calls, payload = archive_download
    path = tmp_path / "nested" / "mapping.db"
    assert build_chemical_mapping_db(path, source="unichem") == path
    assert len(calls) == 1
    assert calls[0][0] == chemical_db._UNICHEM_URL
    assert calls[0][2:] == ("UniChem", {"reject_html": True})
    assert not calls[0][1].exists()
    assert not list(path.parent.glob(".biodbs-unichem-*"))
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT pubchem_cid FROM chemical_mapping WHERE chembl_id=? ORDER BY pubchem_cid",
            ("CHEMBL25",),
        ).fetchall() == [(2244,), (9999,)]
        assert db.execute(
            "SELECT chembl_id FROM chemical_mapping WHERE pubchem_cid=?",
            (2519,),
        ).fetchall() == [("CHEMBL521",)]
        assert db.execute("SELECT COUNT(*) FROM chemical_mapping").fetchone() == (3,)
        assert db.execute(
            "SELECT typeof(pubchem_cid) FROM chemical_mapping LIMIT 1"
        ).fetchone() == ("integer",)
        metadata = db.execute("SELECT * FROM chemical_mapping_metadata").fetchone()
        assert metadata[:2] == ("unichem", chemical_db._UNICHEM_URL)
        assert datetime.fromisoformat(metadata[2]).utcoffset().total_seconds() == 0
        assert metadata[3:] == (hashlib.sha256(payload).hexdigest(), 3)
        assert (
            "USING PRIMARY KEY"
            in db.execute(
                "EXPLAIN QUERY PLAN SELECT pubchem_cid FROM chemical_mapping WHERE chembl_id=?",
                ("CHEMBL25",),
            ).fetchone()[3]
        )
        assert (
            "chemical_mapping_cid"
            in db.execute(
                "EXPLAIN QUERY PLAN SELECT chembl_id FROM chemical_mapping WHERE pubchem_cid=?",
                (2519,),
            ).fetchone()[3]
        )
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_preserves_existing_other_tables(tmp_path, archive_download):
    path = tmp_path / "mapping.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE gene (symbol TEXT)")
        db.execute("INSERT INTO gene VALUES ('TP53')")
    build_chemical_mapping_db(str(path))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT * FROM gene").fetchall() == [("TP53",)]


@pytest.mark.parametrize(
    "object_name", ["chemical_mapping", "chemical_mapping_metadata"]
)
@pytest.mark.parametrize("object_type", ["TABLE", "VIEW"])
def test_existing_builder_objects_fail_before_download(
    tmp_path,
    archive_download,
    object_name,
    object_type,
):
    path = tmp_path / "mapping.db"
    with sqlite3.connect(path) as db:
        if object_type == "TABLE":
            db.execute(f"CREATE TABLE {object_name} (value TEXT)")
            db.execute(f"INSERT INTO {object_name} VALUES ('original')")
        else:
            db.execute(f"CREATE VIEW {object_name} AS SELECT 'original' AS value")
    with pytest.raises(ValueError, match="already exists"):
        build_chemical_mapping_db(path)
    assert not archive_download[0]
    with sqlite3.connect(path) as db:
        assert db.execute(f"SELECT * FROM {object_name}").fetchall() == [("original",)]


@pytest.mark.parametrize("source", ["pubchem", "chembl", "unknown", "", None])
def test_unsupported_source_has_no_side_effects(tmp_path, archive_download, source):
    path = tmp_path / "new" / "mapping.db"
    with pytest.raises(ValueError, match="Only source='unichem'"):
        build_chemical_mapping_db(path, source=source)
    assert not path.parent.exists()
    assert not archive_download[0]


@pytest.mark.parametrize("path", [":memory:", "file:reference.db?mode=memory"])
def test_rejects_non_file_paths(archive_download, path):
    with pytest.raises(ValueError, match="filesystem path"):
        build_chemical_mapping_db(path)
    assert not archive_download[0]


def test_rejects_directory(tmp_path, archive_download):
    with pytest.raises(IsADirectoryError):
        build_chemical_mapping_db(tmp_path)
    assert not archive_download[0]


@pytest.mark.parametrize(
    "text",
    [
        "",
        HEADER,
        "chembl_id\tpubchem_cid\n" + ROWS,
        "From src:'22'\tTo src:'1'\n2244\tCHEMBL25\n",
        "From src:'1'\tTo src:'2'\n" + ROWS,
        HEADER + "CHEMBL25\tpubchem:2244\n",
        HEADER + "CHEMBL25\t-1\n",
        HEADER + "CHEMBL25\t0\n",
        HEADER + "CHEMBL25\t9999999999999999999\n",
        HEADER + "CHEMBL25\t0002244\n",
        HEADER + "CHEMBL25\t2244.0\n",
        HEADER + "CHEMBL25\t2244\textra\n",
        HEADER + "BAD25\t2244\n",
        HEADER + "CHEMBL0\t2244\n",
        HEADER + "CHEMBL25\n",
    ],
)
def test_malformed_exports_roll_back(tmp_path, monkeypatch, text):
    def download(url, target, service, **kwargs):
        target.write_bytes(gzip.compress(text.encode("ascii")))
        return target

    monkeypatch.setattr(chemical_db, "download_binary", download)
    path = tmp_path / "mapping.db"
    with pytest.raises(ValueError):
        build_chemical_mapping_db(path)
    with sqlite3.connect(path) as db:
        assert (
            db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            == []
        )
    assert not list(tmp_path.glob(".biodbs-unichem-*"))


def test_late_invalid_row_rolls_back_previous_batch(
    tmp_path, monkeypatch, archive_download
):
    def download(url, target, service, **kwargs):
        text = HEADER + "CHEMBL25\t2244\n" * 10_001 + "BAD\t1\n"
        target.write_bytes(gzip.compress(text.encode("ascii")))
        return target

    monkeypatch.setattr(chemical_db, "download_binary", download)
    path = tmp_path / "mapping.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE gene (symbol TEXT)")
        db.execute("INSERT INTO gene VALUES ('TP53')")
    with pytest.raises(ValueError, match="line 10003"):
        build_chemical_mapping_db(path)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall() == [("gene",)]
        assert db.execute("SELECT * FROM gene").fetchall() == [("TP53",)]
    # An aborted import does not prevent a subsequent successful retry.
    monkeypatch.setattr(
        chemical_db,
        "download_binary",
        lambda url, target, service, **kw: (
            target.write_bytes(archive_download[1]),
            target,
        )[1],
    )
    build_chemical_mapping_db(path)


@pytest.mark.parametrize(
    "payload",
    [b"<html>Not a gzip</html>", gzip.compress((HEADER + ROWS).encode())[:-4]],
)
def test_bad_or_truncated_gzip_rolls_back(tmp_path, monkeypatch, payload):
    def download(url, target, service, **kwargs):
        target.write_bytes(payload)
        return target

    monkeypatch.setattr(chemical_db, "download_binary", download)
    path = tmp_path / "mapping.db"
    with pytest.raises((OSError, EOFError)):
        build_chemical_mapping_db(path)
    with sqlite3.connect(path) as db:
        assert (
            db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            == []
        )
    assert not list(tmp_path.glob(".biodbs-unichem-*"))


def test_failed_download_does_not_create_database(tmp_path, monkeypatch):
    def download(url, target, service, **kwargs):
        target.write_bytes(b"partial")
        raise OSError("transfer interrupted")

    monkeypatch.setattr(chemical_db, "download_binary", download)
    path = tmp_path / "mapping.db"
    with pytest.raises(OSError, match="interrupted"):
        build_chemical_mapping_db(path)
    assert not path.exists()
    assert not list(tmp_path.glob(".biodbs-unichem-*"))


def test_target_created_during_download_is_preserved(
    tmp_path, monkeypatch, archive_download
):
    path = tmp_path / "mapping.db"

    def download(url, target, service, **kwargs):
        target.write_bytes(archive_download[1])
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE chemical_mapping (value TEXT)")
            db.execute("INSERT INTO chemical_mapping VALUES ('another builder')")
        return target

    monkeypatch.setattr(chemical_db, "download_binary", download)
    with pytest.raises(ValueError, match="already exists"):
        build_chemical_mapping_db(path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT * FROM chemical_mapping").fetchall() == [
            ("another builder",)
        ]
    assert not list(tmp_path.glob(".biodbs-unichem-*"))
