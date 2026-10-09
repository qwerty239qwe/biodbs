"""Build a persistent UniChem ChEMBL/PubChem CID crosswalk."""

from __future__ import annotations

import gzip
import hashlib
import re
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path

from biodbs.fetch._download import download_binary

_UNICHEM_URL = (
    "https://ftp.ebi.ac.uk/pub/databases/chembl/UniChem/data/"
    "wholeSourceMapping/src_id1/src1src22.txt.gz"
)
_HEADER = "From src:'1'\tTo src:'22'"


def _check_tables(db: sqlite3.Connection) -> None:
    existing = db.execute(
        "SELECT name FROM sqlite_master WHERE name IN (?, ?)",
        ("chemical_mapping", "chemical_mapping_metadata"),
    ).fetchone()
    if existing:
        raise ValueError(
            f"Table or object {existing[0]!r} already exists; build into a fresh database"
        )


def _mapping_rows(archive: Path):
    with gzip.open(archive, "rt", encoding="ascii") as handle:
        if handle.readline().rstrip("\r\n") != _HEADER:
            raise ValueError(
                "Expected a UniChem ChEMBL (1) to PubChem CID (22) mapping header"
            )
        for line_number, line in enumerate(handle, start=2):
            fields = line.rstrip("\r\n").split("\t")
            if (
                len(fields) != 2
                or not re.fullmatch(r"CHEMBL[1-9][0-9]*", fields[0])
                or not re.fullmatch(r"[1-9][0-9]{0,18}", fields[1])
                or int(fields[1]) > 2**63 - 1
            ):
                raise ValueError(
                    f"Invalid ChEMBL/PubChem CID mapping at line {line_number}"
                )
            yield fields[0], int(fields[1])


def build_chemical_mapping_db(path: str | Path, *, source: str = "unichem") -> Path:
    """Download and import the full published ChEMBL/PubChem CID crosswalk.

    Args:
        path: SQLite file to create, or an existing SQLite file without the
            builder's tables. Parent directories are created when needed.
        source: Only ``"unichem"`` is supported. Its source 1 to source 22
            export supplies ChEMBL molecule IDs and PubChem compound IDs (CIDs).

    Returns:
        Path to the SQLite file. ``chemical_mapping(chembl_id, pubchem_cid)``
        stores distinct pairs, indexed for both lookup directions. The
        ``chemical_mapping_metadata`` table records the source URL, retrieval
        timestamp, downloaded archive SHA-256, and distinct mapping count.

    Raises:
        ValueError: Unsupported source/path, existing builder tables, or an
            empty or malformed export. Download, gzip, and SQLite errors
            propagate. All mapping tables are rolled back on import failure;
            a newly created empty SQLite file may remain and can be retried.

    Notes:
        Existing unrelated tables are preserved. Existing mapping tables are
        never replaced: refresh into a new database file. Imports use bounded
        batches and one transaction; temporary download files are removed on
        success or failure. The recorded SHA-256 identifies the downloaded
        snapshot, not an independently verified upstream checksum. Coverage
        and structure matching follow UniChem, not the online translators.

    Example:
        >>> from biodbs.translate import build_chemical_mapping_db
        >>> path = build_chemical_mapping_db("mapping.db", source="unichem")
    """
    if source != "unichem":
        raise ValueError("Only source='unichem' is supported")
    if str(path) == ":memory:" or str(path).startswith("file:"):
        raise ValueError("path must be a filesystem path, not a SQLite URI or :memory:")
    path = Path(path)
    if path.is_dir():
        raise IsADirectoryError(path)
    if path.exists():
        with closing(sqlite3.connect(path)) as db:
            _check_tables(db)
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".biodbs-unichem-", dir=path.parent
    ) as temp_dir:
        archive = download_binary(
            _UNICHEM_URL,
            Path(temp_dir) / "src1src22.txt.gz",
            "UniChem",
            reject_html=True,
        )
        retrieved_at = datetime.now(timezone.utc).isoformat()
        digest = hashlib.sha256()
        with archive.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)

        with closing(sqlite3.connect(path)) as db, db:
            # Explicit BEGIN makes schema creation and every batch roll back together.
            db.execute("BEGIN IMMEDIATE")
            _check_tables(db)
            db.execute(
                "CREATE TABLE chemical_mapping ("
                "chembl_id TEXT NOT NULL, pubchem_cid INTEGER NOT NULL, "
                "PRIMARY KEY (chembl_id, pubchem_cid)) WITHOUT ROWID"
            )
            rows = _mapping_rows(archive)
            with closing(rows):
                while batch := list(islice(rows, 10_000)):
                    db.executemany(
                        "INSERT OR IGNORE INTO chemical_mapping VALUES (?, ?)", batch
                    )
            row_count = db.execute("SELECT COUNT(*) FROM chemical_mapping").fetchone()[
                0
            ]
            if not row_count:
                raise ValueError("UniChem mapping export is empty")
            db.execute(
                "CREATE INDEX chemical_mapping_cid ON chemical_mapping(pubchem_cid)"
            )
            db.execute(
                "CREATE TABLE chemical_mapping_metadata (source TEXT PRIMARY KEY, "
                "source_url TEXT NOT NULL, retrieved_at TEXT NOT NULL, "
                "archive_sha256 TEXT NOT NULL, row_count INTEGER NOT NULL)"
            )
            db.execute(
                "INSERT INTO chemical_mapping_metadata VALUES (?, ?, ?, ?, ?)",
                (source, _UNICHEM_URL, retrieved_at, digest.hexdigest(), row_count),
            )
    return path
