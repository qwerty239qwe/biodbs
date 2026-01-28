import csv
import logging
import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Iterator, Generator
from datetime import datetime, timedelta



class BaseFetchedData:
    def __init__(self, content):
        self._content = content  # returns of the requests

    def to_json(self, file_name, mode="w"):
        with open(file_name, mode=mode) as f:
            json.dump(self._content, f)
    
    def to_text(self, file_name, mode="w"):
        with open(file_name, mode=mode) as f:
            f.write(str(self._content)) 

    def to_csv(self, file_name, mode="w"):
        raise NotImplementedError("This method should be implemented in subclass.")

    def as_dict(self):
        raise NotImplementedError("This method should be implemented in subclass.")
    
    def as_dataframe(self, engine="pandas"):
        raise NotImplementedError("This method should be implemented in subclass.")


def _sanitize_identifier(name: str) -> str:
    """Validate and quote a SQL identifier (table or column name)."""
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_.]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return f'"{name}"'


class BaseDBManager:
    """Base class for managing data persistence to local storage (JSON, CSV, SQLite).

    Supports caching with expiration and streaming for large datasets.
    Use as a context manager to ensure metadata is flushed on exit::

        with BaseDBManager("/data", "mydb") as mgr:
            mgr.save_json({"a": 1}, "out", key="k1")
    """

    def __init__(
        self,
        storage_path: Union[str, Path],
        db_name: str = "data",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        self.storage_path = Path(storage_path)
        self.db_name = db_name
        self.cache_expiry_days = cache_expiry_days
        self.logger = logging.getLogger(self.__class__.__name__)

        if auto_create_dirs:
            self.storage_path.mkdir(parents=True, exist_ok=True)

        self._metadata_file = self.storage_path / f"{db_name}_metadata.json"
        self._metadata: Dict[str, Any] = self._load_metadata()
        self._metadata_dirty = False

    # -- context manager --------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush_metadata()
        return False

    def __del__(self):
        try:
            self.flush_metadata()
        except Exception:
            pass

    # -- metadata ---------------------------------------------------------

    def _load_metadata(self) -> Dict[str, Any]:
        if not self._metadata_file.exists():
            return {}
        try:
            return json.loads(self._metadata_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.logger.warning("Failed to load metadata from %s", self._metadata_file)
            return {}

    def flush_metadata(self):
        """Write metadata to disk if it has been modified since the last flush."""
        if not self._metadata_dirty:
            return
        self._metadata_file.write_text(
            json.dumps(self._metadata, indent=2), encoding="utf-8"
        )
        self._metadata_dirty = False

    def _update_metadata(self, key: str, **kwargs):
        entry = self._metadata.setdefault(key, {})
        entry.update(timestamp=datetime.now().isoformat(), **kwargs)
        self._metadata_dirty = True

    def _is_cache_valid(self, key: str) -> bool:
        if self.cache_expiry_days is None:
            return True
        entry = self._metadata.get(key)
        if not entry:
            return False
        ts = entry.get("timestamp")
        if not ts:
            return False
        try:
            return datetime.now() < datetime.fromisoformat(ts) + timedelta(
                days=self.cache_expiry_days
            )
        except (ValueError, TypeError):
            return False

    # -- sqlite helpers ---------------------------------------------------

    @contextmanager
    def _sqlite_connection(self, db_path: Path, row_factory=None):
        conn = sqlite3.connect(db_path)
        if row_factory:
            conn.row_factory = row_factory
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _build_insert_query(table: str, columns: List[str]) -> str:
        safe_table = _sanitize_identifier(table)
        safe_cols = ", ".join(_sanitize_identifier(c) for c in columns)
        placeholders = ", ".join("?" for _ in columns)
        return f"INSERT INTO {safe_table} ({safe_cols}) VALUES ({placeholders})"

    @staticmethod
    def _rows_as_tuples(rows: List[Dict], columns: List[str]):
        return [tuple(row.get(c) for c in columns) for row in rows]

    # -- JSON -------------------------------------------------------------

    def save_json(
        self,
        data: Union[Dict, List],
        filename: str,
        key: Optional[str] = None,
        **metadata_kwargs,
    ) -> Path:
        filepath = self.storage_path / f"{filename}.json"
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if key:
            self._update_metadata(
                key, filepath=str(filepath), format="json", **metadata_kwargs
            )
        self.logger.info("Saved JSON to %s", filepath)
        return filepath

    def load_json(
        self,
        filename: str,
        key: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[Union[Dict, List]]:
        if use_cache and key and not self._is_cache_valid(key):
            self.logger.info("Cache expired for key: %s", key)
            return None
        filepath = self.storage_path / f"{filename}.json"
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.logger.error("Failed to load JSON from %s: %s", filepath, e)
            return None

    # -- CSV --------------------------------------------------------------

    def save_csv(
        self,
        data: List[Dict],
        filename: str,
        key: Optional[str] = None,
        **metadata_kwargs,
    ) -> Path:
        if not data:
            raise ValueError("Cannot save empty data to CSV")
        filepath = self.storage_path / f"{filename}.csv"
        fieldnames = sorted(data[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
        if key:
            self._update_metadata(
                key, filepath=str(filepath), format="csv", **metadata_kwargs
            )
        self.logger.info("Saved CSV to %s", filepath)
        return filepath

    def load_csv(
        self,
        filename: str,
        key: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[List[Dict]]:
        if use_cache and key and not self._is_cache_valid(key):
            self.logger.info("Cache expired for key: %s", key)
            return None
        filepath = self.storage_path / f"{filename}.csv"
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except Exception as e:
            self.logger.error("Failed to load CSV from %s: %s", filepath, e)
            return None

    # -- SQLite -----------------------------------------------------------

    def save_to_sqlite(
        self,
        data: List[Dict],
        table_name: str,
        db_filename: Optional[str] = None,
        key: Optional[str] = None,
        if_exists: str = "replace",
        **metadata_kwargs,
    ) -> Path:
        if not data:
            raise ValueError("Cannot save empty data to SQLite")
        db_path = self.storage_path / f"{db_filename or self.db_name}.db"
        columns = list(data[0].keys())
        safe_table = _sanitize_identifier(table_name)

        with self._sqlite_connection(db_path) as conn:
            cur = conn.cursor()
            if if_exists == "replace":
                cur.execute(f"DROP TABLE IF EXISTS {safe_table}")
            col_defs = ", ".join(f"{_sanitize_identifier(c)} TEXT" for c in columns)
            cur.execute(f"CREATE TABLE IF NOT EXISTS {safe_table} ({col_defs})")
            query = self._build_insert_query(table_name, columns)
            cur.executemany(query, self._rows_as_tuples(data, columns))

        if key:
            self._update_metadata(
                key,
                filepath=str(db_path),
                format="sqlite",
                table=table_name,
                **metadata_kwargs,
            )
        self.logger.info("Saved %d rows to %s:%s", len(data), db_path, table_name)
        return db_path

    def load_from_sqlite(
        self,
        table_name: str,
        db_filename: Optional[str] = None,
        query: Optional[str] = None,
        key: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[List[Dict]]:
        if use_cache and key and not self._is_cache_valid(key):
            self.logger.info("Cache expired for key: %s", key)
            return None
        db_path = self.storage_path / f"{db_filename or self.db_name}.db"
        if not db_path.exists():
            return None
        safe_table = _sanitize_identifier(table_name)
        try:
            with self._sqlite_connection(db_path, row_factory=sqlite3.Row) as conn:
                sql = f"SELECT * FROM {safe_table}"
                if query:
                    sql += f" WHERE {query}"
                rows = conn.execute(sql).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.Error as e:
            self.logger.error(
                "Failed to load from %s:%s: %s", db_path, table_name, e
            )
            return None

    # -- cache management -------------------------------------------------

    def clear_cache(self, key: Optional[str] = None):
        if key:
            if self._metadata.pop(key, None) is not None:
                self._metadata_dirty = True
                self.logger.info("Cleared cache for key: %s", key)
        else:
            self._metadata = {}
            self._metadata_dirty = True
            self.logger.info("Cleared all cache metadata")
        self.flush_metadata()

    def list_cached_items(self) -> List[Dict[str, Any]]:
        return [
            {"key": k, "is_valid": self._is_cache_valid(k), **v}
            for k, v in self._metadata.items()
        ]

    def get_storage_info(self) -> Dict[str, Any]:
        total_size = 0
        file_count = 0
        for f in self.storage_path.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size
                file_count += 1
        return {
            "storage_path": str(self.storage_path),
            "db_name": self.db_name,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "cached_items": len(self._metadata),
            "cache_expiry_days": self.cache_expiry_days,
        }

    # -- streaming: JSON Lines --------------------------------------------

    def stream_json_lines(
        self,
        data_stream: Iterator[Dict],
        filename: str,
        key: Optional[str] = None,
        buffer_size: int = 100,
        **metadata_kwargs,
    ) -> Path:
        filepath = self.storage_path / f"{filename}.jsonl"
        count = 0
        buffer: list[str] = []

        with open(filepath, "w", encoding="utf-8") as f:
            for item in data_stream:
                buffer.append(json.dumps(item))
                count += 1
                if len(buffer) >= buffer_size:
                    f.write("\n".join(buffer) + "\n")
                    buffer.clear()
            if buffer:
                f.write("\n".join(buffer) + "\n")

        if key:
            self._update_metadata(
                key,
                filepath=str(filepath),
                format="jsonl",
                item_count=count,
                **metadata_kwargs,
            )
        self.logger.info("Streamed %d items to %s", count, filepath)
        return filepath

    def load_json_lines(
        self,
        filename: str,
        key: Optional[str] = None,
        use_cache: bool = True,
        limit: Optional[int] = None,
    ) -> Generator[Dict, None, None]:
        if use_cache and key and not self._is_cache_valid(key):
            self.logger.info("Cache expired for key: %s", key)
            return
        filepath = self.storage_path / f"{filename}.jsonl"
        if not filepath.exists():
            return
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                yield json.loads(stripped)
                count += 1
                if limit and count >= limit:
                    break

    # -- streaming: CSV ---------------------------------------------------

    def stream_csv(
        self,
        data_stream: Iterator[Dict],
        filename: str,
        key: Optional[str] = None,
        buffer_size: int = 100,
        fieldnames: Optional[List[str]] = None,
        **metadata_kwargs,
    ) -> Path:
        """Stream dictionaries to a CSV file.

        Field names are determined from *fieldnames* if given, otherwise from
        the first item in the stream.  Extra keys in later rows are silently
        ignored (``extrasaction='ignore'``).
        """
        filepath = self.storage_path / f"{filename}.csv"
        count = 0

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer: Optional[csv.DictWriter] = None

            for item in data_stream:
                if writer is None:
                    fieldnames = fieldnames or sorted(item.keys())
                    writer = csv.DictWriter(
                        f, fieldnames=fieldnames, extrasaction="ignore"
                    )
                    writer.writeheader()

                writer.writerow(item)
                count += 1

                if count % buffer_size == 0:
                    f.flush()

        if key:
            self._update_metadata(
                key,
                filepath=str(filepath),
                format="csv",
                item_count=count,
                fieldnames=fieldnames,
                **metadata_kwargs,
            )
        self.logger.info("Streamed %d rows to %s", count, filepath)
        return filepath

    # -- streaming: SQLite ------------------------------------------------

    def stream_to_sqlite(
        self,
        data_stream: Iterator[Dict],
        table_name: str,
        db_filename: Optional[str] = None,
        key: Optional[str] = None,
        batch_size: int = 1000,
        if_exists: str = "replace",
        create_indices: Optional[List[str]] = None,
        **metadata_kwargs,
    ) -> Path:
        db_path = self.storage_path / f"{db_filename or self.db_name}.db"
        safe_table = _sanitize_identifier(table_name)
        columns: Optional[List[str]] = None
        insert_query: Optional[str] = None
        batch: list[tuple] = []
        total_count = 0

        with self._sqlite_connection(db_path) as conn:
            cur = conn.cursor()

            for item in data_stream:
                # Lazily create the table from the first row's schema.
                if columns is None:
                    columns = list(item.keys())

                    if if_exists == "replace":
                        cur.execute(f"DROP TABLE IF EXISTS {safe_table}")
                    elif if_exists == "fail":
                        cur.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                            (table_name,),
                        )
                        if cur.fetchone():
                            raise ValueError(f"Table {table_name} already exists")

                    col_defs = ", ".join(
                        f"{_sanitize_identifier(c)} TEXT" for c in columns
                    )
                    cur.execute(
                        f"CREATE TABLE IF NOT EXISTS {safe_table} ({col_defs})"
                    )
                    insert_query = self._build_insert_query(table_name, columns)

                batch.append(tuple(item.get(c) for c in columns))

                if len(batch) >= batch_size:
                    cur.executemany(insert_query, batch)
                    total_count += len(batch)
                    batch.clear()
                    conn.commit()

            if batch:
                cur.executemany(insert_query, batch)
                total_count += len(batch)
                conn.commit()

            if create_indices and columns:
                for col in create_indices:
                    if col in columns:
                        safe_col = _sanitize_identifier(col)
                        idx = _sanitize_identifier(f"idx_{table_name}_{col}")
                        cur.execute(
                            f"CREATE INDEX IF NOT EXISTS {idx} ON {safe_table} ({safe_col})"
                        )
                conn.commit()

        if key:
            self._update_metadata(
                key,
                filepath=str(db_path),
                format="sqlite",
                table=table_name,
                item_count=total_count,
                **metadata_kwargs,
            )
        self.logger.info(
            "Streamed %d rows to %s:%s", total_count, db_path, table_name
        )
        return db_path

    # -- streaming from HTTP responses ------------------------------------

    def stream_from_requests(
        self,
        response,
        save_method: str = "jsonl",
        filename: str = "streamed_data",
        chunk_size: int = 8192,
        **save_kwargs,
    ) -> Path:
        """Stream a ``requests.Response`` (with ``stream=True``) to storage.

        For ``save_method='raw'`` the response bytes are written directly.
        For ``'jsonl'``, ``'csv'``, or ``'sqlite'`` the response is expected
        to be JSON Lines (one JSON object per line) or a JSON array which is
        fully consumed then iterated.
        """
        if save_method == "raw":
            filepath = self.storage_path / filename
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            self.logger.info("Streamed raw data to %s", filepath)
            return filepath

        def _iter_json_lines():
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    yield json.loads(line)

        def _iter_json_array():
            data = response.json()
            if isinstance(data, list):
                yield from data
            else:
                yield data

        content_type = response.headers.get("Content-Type", "")
        # JSON Lines are typically served as text/plain or application/x-ndjson
        if "application/json" in content_type:
            stream = _iter_json_array()
        else:
            stream = _iter_json_lines()

        if save_method == "jsonl":
            return self.stream_json_lines(stream, filename, **save_kwargs)
        elif save_method == "csv":
            return self.stream_csv(stream, filename, **save_kwargs)
        elif save_method == "sqlite":
            table_name = save_kwargs.pop("table_name", filename)
            return self.stream_to_sqlite(stream, table_name, **save_kwargs)
        else:
            raise ValueError(f"Unknown save_method: {save_method}")