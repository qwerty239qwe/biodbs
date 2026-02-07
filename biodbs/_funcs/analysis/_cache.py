"""Pathway data storage and caching system.

This module provides a `PathwayDBManager` that integrates with `BaseDBManager`
to store pathway-gene relationships in various database backends.

Supported storage backends:
    - SQLite: Relational storage with proper schema (recommended for local ORA)
    - MySQL: MySQL/MariaDB server storage
    - PostgreSQL: PostgreSQL server storage
    - JSON: Document-based storage (portable, human-readable)
    - CSV: Tabular export (for analysis in other tools)

Example:
    >>> from biodbs._funcs.analysis._cache import PathwayDBManager
    >>>
    >>> # Create manager with SQLite backend (default)
    >>> mgr = PathwayDBManager(storage_path="/tmp/cache", backend="sqlite")
    >>> mgr
    <PathwayDBManager storage_path='/tmp/cache' backend='sqlite'>
    >>>
    >>> # Define pathways to cache
    >>> pathways = {
    ...     "hsa04110": ("Cell cycle", {"TP53", "BRCA1", "CDK1"}),
    ...     "hsa04115": ("p53 signaling", {"TP53", "MDM2", "CDKN1A"}),
    ... }
    >>>
    >>> # Save pathways
    >>> path = mgr.save_pathways(pathways, cache_key="kegg_hsa", database="KEGG")
    >>> print(path)
    /tmp/cache/pathways.db
    >>>
    >>> # Load pathways
    >>> loaded = mgr.load_pathways("kegg_hsa")
    >>> loaded
    {'hsa04110': ('Cell cycle', frozenset({'TP53', 'BRCA1', 'CDK1'})),
     'hsa04115': ('p53 signaling', frozenset({'TP53', 'MDM2', 'CDKN1A'}))}
    >>>
    >>> # Query pathways containing a gene
    >>> tp53_pathways = mgr.query_pathways(gene_id="TP53")
    >>> print(f"TP53 is in {len(tp53_pathways)} pathways")
    TP53 is in 2 pathways

MySQL Example:
    >>> mgr = PathwayDBManager(
    ...     backend="mysql",
    ...     db_config={
    ...         "host": "localhost",
    ...         "port": 3306,
    ...         "user": "root",
    ...         "password": "password",
    ...         "database": "biodbs"
    ...     }
    ... )
    >>> mgr
    <PathwayDBManager backend='mysql' host='localhost' database='biodbs'>

PostgreSQL Example:
    >>> mgr = PathwayDBManager(
    ...     backend="postgresql",
    ...     db_config={
    ...         "host": "localhost",
    ...         "port": 5432,
    ...         "user": "postgres",
    ...         "password": "password",
    ...         "database": "biodbs"
    ...     }
    ... )
    >>> mgr
    <PathwayDBManager backend='postgresql' host='localhost' database='biodbs'>
"""

from __future__ import annotations

import json
import sqlite3
import time
import warnings
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from biodbs.data._base import BaseDBManager, _sanitize_identifier

if TYPE_CHECKING:
    from biodbs._funcs.analysis.ora import Pathway


# Default cache settings
DEFAULT_CACHE_DIR = Path.home() / ".biodbs" / "cache"
DEFAULT_CACHE_EXPIRY = 7 * 24 * 60 * 60  # 7 days in seconds


class StorageBackend(str, Enum):
    """Supported storage backends for pathway data."""

    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    JSON = "json"
    CSV = "csv"


# Type alias for database configuration
DBConfig = Dict[str, Any]


# =============================================================================
# SQL Dialect Abstraction Layer
# =============================================================================


class SQLDialect(ABC):
    """Abstract base class for SQL dialect handling.

    Provides a unified interface for different SQL databases, handling:
    - Parameter placeholders (? vs %s)
    - Connection management
    - Cursor creation with dict-like row access
    - Column name quoting for reserved words
    """

    @property
    @abstractmethod
    def placeholder(self) -> str:
        """Parameter placeholder for this dialect (? or %s)."""
        ...

    @abstractmethod
    def get_connection(self):
        """Get a database connection."""
        ...

    @abstractmethod
    def get_dict_cursor(self, conn):
        """Get a cursor that returns dict-like rows."""
        ...

    def quote_column(self, name: str) -> str:
        """Quote a column name if it's a reserved word."""
        # 'database' is reserved in MySQL
        if name.lower() == "database":
            return self._quote_identifier(name)
        return name

    def _quote_identifier(self, name: str) -> str:
        """Quote an identifier (default uses double quotes for SQL standard)."""
        return f'"{name}"'

    @contextmanager
    def connection(self) -> Generator:
        """Context manager for database connections."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class SQLiteDialect(SQLDialect):
    """SQLite dialect implementation.

    Handles SQLite-specific SQL syntax and connection management.
    Uses '?' as parameter placeholder.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: Path, sqlite_connection_func):
        """Initialize SQLite dialect.

        Args:
            db_path: Path to the SQLite database file.
            sqlite_connection_func: Function to create SQLite connections
                (typically BaseDBManager._sqlite_connection).
        """
        self.db_path = db_path
        self._sqlite_connection = sqlite_connection_func

    @property
    def placeholder(self) -> str:
        return "?"

    def get_connection(self):
        # SQLite uses a context manager from BaseDBManager
        return self._sqlite_connection(self.db_path).__enter__()

    def get_dict_cursor(self, conn):
        conn.row_factory = sqlite3.Row
        return conn.cursor()

    @contextmanager
    def connection(self) -> Generator:
        """Use the existing SQLite connection context manager."""
        with self._sqlite_connection(self.db_path, row_factory=sqlite3.Row) as conn:
            yield conn


class MySQLDialect(SQLDialect):
    """MySQL dialect implementation.

    Handles MySQL-specific SQL syntax and connection management.
    Uses '%s' as parameter placeholder and backticks for identifier quoting.

    Attributes:
        db_config: Database connection configuration dict.

    Note:
        Requires mysql-connector-python package.
        Install with: pip install mysql-connector-python
    """

    def __init__(self, db_config: DBConfig):
        """Initialize MySQL dialect.

        Args:
            db_config: Database configuration with keys:
                - host: Server hostname (default: "localhost")
                - port: Server port (default: 3306)
                - user: Database username (required)
                - password: Database password (required)
                - database: Database name (required)
                - charset: Character set (default: "utf8mb4")
        """
        self.db_config = db_config

    @property
    def placeholder(self) -> str:
        return "%s"

    def _quote_identifier(self, name: str) -> str:
        """MySQL uses backticks for quoting."""
        return f"`{name}`"

    def get_connection(self):
        try:
            import mysql.connector
        except ImportError:
            raise ImportError(
                "MySQL backend requires mysql-connector-python. "
                "Install with: pip install mysql-connector-python"
            )

        return mysql.connector.connect(
            host=self.db_config.get("host", "localhost"),
            port=self.db_config.get("port", 3306),
            user=self.db_config["user"],
            password=self.db_config["password"],
            database=self.db_config["database"],
            charset=self.db_config.get("charset", "utf8mb4"),
        )

    def get_dict_cursor(self, conn):
        return conn.cursor(dictionary=True)


class PostgreSQLDialect(SQLDialect):
    """PostgreSQL dialect implementation.

    Handles PostgreSQL-specific SQL syntax and connection management.
    Uses '%s' as parameter placeholder and double quotes for identifier quoting.

    Attributes:
        db_config: Database connection configuration dict.

    Note:
        Requires psycopg2 package.
        Install with: pip install psycopg2-binary
    """

    def __init__(self, db_config: DBConfig):
        """Initialize PostgreSQL dialect.

        Args:
            db_config: Database configuration with keys:
                - host: Server hostname (default: "localhost")
                - port: Server port (default: 5432)
                - user: Database username (required)
                - password: Database password (required)
                - database: Database name (required)
        """
        self.db_config = db_config

    @property
    def placeholder(self) -> str:
        return "%s"

    def get_connection(self):
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "PostgreSQL backend requires psycopg2. "
                "Install with: pip install psycopg2-binary"
            )

        return psycopg2.connect(
            host=self.db_config.get("host", "localhost"),
            port=self.db_config.get("port", 5432),
            user=self.db_config["user"],
            password=self.db_config["password"],
            database=self.db_config["database"],
        )

    def get_dict_cursor(self, conn):
        import psycopg2.extras
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


class PathwayDBManager(BaseDBManager):
    """Manager for storing and retrieving pathway-gene relationships.

    Extends `BaseDBManager` to provide specialized methods for pathway data
    with support for multiple storage backends.

    Attributes:
        backend: Storage backend to use (sqlite, mysql, postgresql, json, csv).
        db_config: Database configuration for MySQL/PostgreSQL backends.

    Example:
        >>> # SQLite (default)
        >>> mgr = PathwayDBManager("~/.biodbs/cache", backend="sqlite")
        >>>
        >>> # MySQL
        >>> mgr = PathwayDBManager(
        ...     backend="mysql",
        ...     db_config={"host": "localhost", "user": "root", "password": "pw", "database": "biodbs"}
        ... )
        >>>
        >>> # PostgreSQL
        >>> mgr = PathwayDBManager(
        ...     backend="postgresql",
        ...     db_config={"host": "localhost", "user": "postgres", "password": "pw", "database": "biodbs"}
        ... )
        >>>
        >>> with mgr:
        ...     mgr.save_pathways(pathways, "kegg_hsa", database="KEGG")
        ...     loaded = mgr.load_pathways("kegg_hsa")
    """

    # Table names for pathway storage
    PATHWAYS_TABLE = "pathways"
    GENES_TABLE = "pathway_genes"

    def __init__(
        self,
        storage_path: Optional[Union[str, Path]] = None,
        db_name: str = "pathways",
        backend: Union[str, StorageBackend] = StorageBackend.SQLITE,
        db_config: Optional[DBConfig] = None,
        cache_expiry_days: int = 7,
        auto_create_dirs: bool = True,
    ):
        """Initialize the PathwayDBManager.

        Args:
            storage_path: Directory for storage files. Defaults to ~/.biodbs/cache.
                Used for SQLite, JSON, and CSV backends.
            db_name: Base name for database files (SQLite) or database name.
            backend: Storage backend ("sqlite", "mysql", "postgresql", "json", or "csv").
            db_config: Database configuration for MySQL/PostgreSQL. Required keys:
                - host: Database server hostname
                - user: Database username
                - password: Database password
                - database: Database name
                Optional keys:
                - port: Server port (default: 3306 for MySQL, 5432 for PostgreSQL)
                - charset: Character set (MySQL only, default: utf8mb4)
            cache_expiry_days: Number of days before cache expires.
            auto_create_dirs: Create directories if they don't exist (file backends only).
        """
        if storage_path is None:
            storage_path = DEFAULT_CACHE_DIR

        super().__init__(
            storage_path=storage_path,
            db_name=db_name,
            cache_expiry_days=cache_expiry_days,
            auto_create_dirs=auto_create_dirs,
        )

        if isinstance(backend, str):
            backend = StorageBackend(backend.lower())
        self.backend = backend
        self.db_config = db_config or {}

        # Validate db_config for server backends
        if backend in (StorageBackend.MYSQL, StorageBackend.POSTGRESQL):
            required_keys = {"host", "user", "password", "database"}
            missing = required_keys - set(self.db_config.keys())
            if missing:
                raise ValueError(
                    f"db_config missing required keys for {backend.value}: {missing}"
                )

        # Initialize dialect for SQL backends
        self._dialect: Optional[SQLDialect] = None

    def __repr__(self) -> str:
        """Return a string representation of the PathwayDBManager.

        Returns:
            str: A human-readable representation showing backend and connection info.

        Example:
            >>> mgr = PathwayDBManager(storage_path="/tmp/cache", backend="sqlite")
            >>> repr(mgr)
            "<PathwayDBManager storage_path='/tmp/cache' backend='sqlite'>"
        """
        if self.backend in (StorageBackend.MYSQL, StorageBackend.POSTGRESQL):
            host = self.db_config.get("host", "localhost")
            db = self.db_config.get("database", "unknown")
            return f"<PathwayDBManager backend='{self.backend.value}' host='{host}' database='{db}'>"
        else:
            return f"<PathwayDBManager storage_path='{self.storage_path}' backend='{self.backend.value}'>"

    def _get_dialect(self) -> SQLDialect:
        """Get the SQL dialect for the current backend.

        Returns:
            SQLDialect instance for the configured backend.

        Raises:
            ValueError: If backend doesn't support SQL operations.
        """
        if self._dialect is not None:
            return self._dialect

        if self.backend == StorageBackend.SQLITE:
            db_path = self.storage_path / f"{self.db_name}.db"
            self._dialect = SQLiteDialect(db_path, self._sqlite_connection)
        elif self.backend == StorageBackend.MYSQL:
            self._dialect = MySQLDialect(self.db_config)
        elif self.backend == StorageBackend.POSTGRESQL:
            self._dialect = PostgreSQLDialect(self.db_config)
        else:
            raise ValueError(f"SQL dialect not available for {self.backend.value}")

        return self._dialect

    def _is_sql_backend(self) -> bool:
        """Check if current backend is a SQL database."""
        return self.backend in (
            StorageBackend.SQLITE,
            StorageBackend.MYSQL,
            StorageBackend.POSTGRESQL,
        )

    def _init_sql_schema(self, conn, dialect: SQLDialect) -> None:
        """Initialize the SQL schema for pathway storage.

        Uses dialect-specific DDL for each database backend.
        """
        cur = conn.cursor()
        db_col = dialect.quote_column("database")
        pathways_table = _sanitize_identifier(self.PATHWAYS_TABLE)
        genes_table = _sanitize_identifier(self.GENES_TABLE)

        if self.backend == StorageBackend.SQLITE:
            # SQLite schema
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {pathways_table} (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    database TEXT NOT NULL,
                    species TEXT,
                    url TEXT,
                    gene_count INTEGER DEFAULT 0,
                    cache_key TEXT,
                    created_at REAL,
                    expires_at REAL
                )
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {genes_table} (
                    pathway_id TEXT NOT NULL,
                    gene_id TEXT NOT NULL,
                    gene_type TEXT DEFAULT 'symbol',
                    PRIMARY KEY (pathway_id, gene_id),
                    FOREIGN KEY (pathway_id) REFERENCES {pathways_table}(id)
                )
            """)
            # SQLite indices (separate statements)
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathway_genes_pathway ON {genes_table}(pathway_id)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathway_genes_gene ON {genes_table}(gene_id)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathways_cache_key ON {pathways_table}(cache_key)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathways_database ON {pathways_table}(database)")

        elif self.backend == StorageBackend.MYSQL:
            # MySQL schema with inline indices
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {pathways_table} (
                    id VARCHAR(255) PRIMARY KEY,
                    name TEXT NOT NULL,
                    {db_col} VARCHAR(100) NOT NULL,
                    species VARCHAR(100),
                    url TEXT,
                    gene_count INT DEFAULT 0,
                    cache_key VARCHAR(255),
                    created_at DOUBLE,
                    expires_at DOUBLE,
                    INDEX idx_cache_key (cache_key),
                    INDEX idx_database ({db_col})
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {genes_table} (
                    pathway_id VARCHAR(255) NOT NULL,
                    gene_id VARCHAR(255) NOT NULL,
                    gene_type VARCHAR(50) DEFAULT 'symbol',
                    PRIMARY KEY (pathway_id, gene_id),
                    INDEX idx_pathway (pathway_id),
                    INDEX idx_gene (gene_id),
                    FOREIGN KEY (pathway_id) REFERENCES {pathways_table}(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

        elif self.backend == StorageBackend.POSTGRESQL:
            # PostgreSQL schema
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {pathways_table} (
                    id VARCHAR(255) PRIMARY KEY,
                    name TEXT NOT NULL,
                    database VARCHAR(100) NOT NULL,
                    species VARCHAR(100),
                    url TEXT,
                    gene_count INTEGER DEFAULT 0,
                    cache_key VARCHAR(255),
                    created_at DOUBLE PRECISION,
                    expires_at DOUBLE PRECISION
                )
            """)
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathways_cache_key ON {pathways_table}(cache_key)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathways_database ON {pathways_table}(database)")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {genes_table} (
                    pathway_id VARCHAR(255) NOT NULL,
                    gene_id VARCHAR(255) NOT NULL,
                    gene_type VARCHAR(50) DEFAULT 'symbol',
                    PRIMARY KEY (pathway_id, gene_id),
                    FOREIGN KEY (pathway_id) REFERENCES {pathways_table}(id) ON DELETE CASCADE
                )
            """)
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathway_genes_pathway ON {genes_table}(pathway_id)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_pathway_genes_gene ON {genes_table}(gene_id)")

        conn.commit()

    def save_pathways(
        self,
        pathways: Union[Dict[str, Tuple[str, Set[str]]], Dict[str, "Pathway"]],
        cache_key: str,
        database: str = "custom",
        species: Optional[str] = None,
        gene_type: str = "symbol",
        expiry_seconds: Optional[float] = None,
    ) -> Path:
        """Save pathway data to the configured backend.

        Args:
            pathways: Dict mapping pathway_id to either:
                - Tuple of (name, gene_set): e.g., ("Cell Cycle", {"TP53", "BRCA1"})
                - Pathway object with name and genes attributes
            cache_key: Unique key for this pathway set (e.g., "kegg_hsa", "reactome_human").
            database: Source database name (e.g., "KEGG", "Reactome", "GO").
            species: Species name (e.g., "Homo sapiens", "Mus musculus").
            gene_type: Type of gene IDs stored (e.g., "symbol", "entrez", "uniprot").
            expiry_seconds: Cache expiry in seconds. None uses default (7 days).

        Returns:
            Path: Path to the storage file or database URI.
                - SQLite: PosixPath('/home/user/.biodbs/cache/pathways.db')
                - MySQL: PosixPath('mysql://localhost/biodbs')
                - PostgreSQL: PosixPath('postgresql://localhost/biodbs')
                - JSON: PosixPath('/home/user/.biodbs/cache/kegg_hsa.json')
                - CSV: PosixPath('/home/user/.biodbs/cache/kegg_hsa.csv')

        Example:
            >>> mgr = PathwayDBManager(storage_path="/tmp/cache", backend="sqlite")
            >>> pathways = {
            ...     "hsa04110": ("Cell cycle", {"TP53", "BRCA1", "CDK1"}),
            ...     "hsa04115": ("p53 signaling", {"TP53", "MDM2", "CDKN1A"}),
            ... }
            >>> path = mgr.save_pathways(pathways, cache_key="kegg_hsa", database="KEGG")
            >>> print(path)
            /tmp/cache/pathways.db
        """
        if self._is_sql_backend():
            return self._save_pathways_sql(
                pathways, cache_key, database, species, gene_type, expiry_seconds
            )
        elif self.backend == StorageBackend.JSON:
            return self._save_pathways_json(
                pathways, cache_key, database, species, gene_type, expiry_seconds
            )
        elif self.backend == StorageBackend.CSV:
            return self._save_pathways_csv(
                pathways, cache_key, database, species, gene_type
            )
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _save_pathways_sql(
        self,
        pathways: Union[Dict[str, Tuple[str, Set[str]]], Dict[str, "Pathway"]],
        cache_key: str,
        database: str,
        species: Optional[str],
        gene_type: str,
        expiry_seconds: Optional[float],
    ) -> Path:
        """Save pathways to any SQL backend using the dialect abstraction."""
        dialect = self._get_dialect()
        now = time.time()
        expires_at = now + (expiry_seconds or DEFAULT_CACHE_EXPIRY)
        ph = dialect.placeholder
        db_col = dialect.quote_column("database")
        pathways_table = _sanitize_identifier(self.PATHWAYS_TABLE)
        genes_table = _sanitize_identifier(self.GENES_TABLE)

        # Prepare rows
        pathway_rows = []
        gene_rows = []

        for pathway_id, data in pathways.items():
            if hasattr(data, "name") and hasattr(data, "genes"):
                name = data.name
                genes = data.genes
                url = getattr(data, "url", None)
                pathway_species = getattr(data, "species", species)
                pathway_database = getattr(data, "database", database)
            else:
                name, genes = data
                url = None
                pathway_species = species
                pathway_database = database

            pathway_rows.append((
                pathway_id, name, pathway_database, pathway_species,
                url, len(genes), cache_key, now, expires_at,
            ))

            for gene_id in genes:
                gene_rows.append((pathway_id, str(gene_id), gene_type))

        with dialect.connection() as conn:
            self._init_sql_schema(conn, dialect)
            cur = conn.cursor()

            # Clear existing data for this cache_key
            cur.execute(
                f"DELETE FROM {genes_table} "
                f"WHERE pathway_id IN (SELECT id FROM {pathways_table} WHERE cache_key = {ph})",
                (cache_key,)
            )
            cur.execute(
                f"DELETE FROM {pathways_table} WHERE cache_key = {ph}",
                (cache_key,)
            )

            # Batch insert pathways
            cur.executemany(
                f"INSERT INTO {pathways_table} "
                f"(id, name, {db_col}, species, url, gene_count, cache_key, created_at, expires_at) "
                f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})",
                pathway_rows,
            )

            # Batch insert genes
            cur.executemany(
                f"INSERT INTO {genes_table} (pathway_id, gene_id, gene_type) "
                f"VALUES ({ph}, {ph}, {ph})",
                gene_rows,
            )

        # Log and return path
        if self.backend == StorageBackend.SQLITE:
            db_path = self.storage_path / f"{self.db_name}.db"
            self._update_metadata(
                cache_key,
                filepath=str(db_path),
                format="sqlite",
                database=database,
                species=species,
                pathway_count=len(pathway_rows),
                gene_count=len(gene_rows),
            )
            self.logger.info(
                "Saved %d pathways (%d genes) to %s [cache_key=%s]",
                len(pathway_rows), len(gene_rows), db_path, cache_key,
            )
            return db_path
        else:
            self.logger.info(
                "Saved %d pathways (%d genes) to %s [cache_key=%s]",
                len(pathway_rows), len(gene_rows), self.backend.value, cache_key,
            )
            host = self.db_config.get("host", "localhost")
            db_name = self.db_config["database"]
            return Path(f"{self.backend.value}://{host}/{db_name}")

    def _save_pathways_json(
        self,
        pathways: Union[Dict[str, Tuple[str, Set[str]]], Dict[str, "Pathway"]],
        cache_key: str,
        database: str,
        species: Optional[str],
        gene_type: str,
        expiry_seconds: Optional[float],
    ) -> Path:
        """Save pathways to JSON format."""
        # Convert to serializable format
        data = {
            "cache_key": cache_key,
            "database": database,
            "species": species,
            "gene_type": gene_type,
            "created_at": time.time(),
            "expires_at": time.time() + (expiry_seconds or DEFAULT_CACHE_EXPIRY),
            "pathways": {},
        }

        for pathway_id, pathway_data in pathways.items():
            if hasattr(pathway_data, "name") and hasattr(pathway_data, "genes"):
                data["pathways"][pathway_id] = {
                    "name": pathway_data.name,
                    "genes": list(pathway_data.genes),
                    "url": getattr(pathway_data, "url", None),
                    "database": getattr(pathway_data, "database", database),
                    "species": getattr(pathway_data, "species", species),
                }
            else:
                name, genes = pathway_data
                data["pathways"][pathway_id] = {
                    "name": name,
                    "genes": list(genes),
                }

        return self.save_json(data, cache_key, key=cache_key, database=database)

    def _save_pathways_csv(
        self,
        pathways: Union[Dict[str, Tuple[str, Set[str]]], Dict[str, "Pathway"]],
        cache_key: str,
        database: str,
        species: Optional[str],
        gene_type: str,
    ) -> Path:
        """Save pathways to CSV format (pathway-gene pairs)."""
        rows = []
        for pathway_id, pathway_data in pathways.items():
            if hasattr(pathway_data, "name") and hasattr(pathway_data, "genes"):
                name = pathway_data.name
                genes = pathway_data.genes
            else:
                name, genes = pathway_data

            for gene_id in genes:
                rows.append({
                    "pathway_id": pathway_id,
                    "pathway_name": name,
                    "gene_id": str(gene_id),
                    "gene_type": gene_type,
                    "database": database,
                    "species": species or "",
                })

        return self.save_csv(rows, cache_key, key=cache_key, database=database)

    def load_pathways(
        self,
        cache_key: str,
        use_cache: bool = True,
        as_pathway_objects: bool = False,
    ) -> Optional[Dict[str, Tuple[str, FrozenSet[str]]]]:
        """Load pathway data from storage.

        Args:
            cache_key: Unique key for the pathway set (e.g., "kegg_hsa").
            use_cache: If True, check cache expiry and return None if expired.
                If False, load data regardless of expiry.
            as_pathway_objects: If True, return Pathway objects instead of tuples.

        Returns:
            Dict[str, Tuple[str, FrozenSet[str]]] or None:
                - If found: Dict mapping pathway_id to (name, frozenset of genes)
                - If not found or expired: None

            When as_pathway_objects=True:
                Dict[str, Pathway]: Dict mapping pathway_id to Pathway objects

        Example:
            >>> mgr = PathwayDBManager(storage_path="/tmp/cache", backend="sqlite")
            >>> pathways = mgr.load_pathways("kegg_hsa")
            >>> pathways
            {'hsa04110': ('Cell cycle', frozenset({'TP53', 'BRCA1', 'CDK1'})),
             'hsa04115': ('p53 signaling', frozenset({'TP53', 'MDM2', 'CDKN1A'}))}

            >>> # Access individual pathway
            >>> name, genes = pathways["hsa04110"]
            >>> print(f"{name}: {len(genes)} genes")
            Cell cycle: 3 genes

            >>> # Load as Pathway objects
            >>> pathways = mgr.load_pathways("kegg_hsa", as_pathway_objects=True)
            >>> pathways["hsa04110"]
            Pathway(id='hsa04110', name='Cell cycle', genes=3, database='KEGG')
        """
        if self._is_sql_backend():
            return self._load_pathways_sql(cache_key, use_cache, as_pathway_objects)
        elif self.backend == StorageBackend.JSON:
            return self._load_pathways_json(cache_key, use_cache, as_pathway_objects)
        elif self.backend == StorageBackend.CSV:
            return self._load_pathways_csv(cache_key, use_cache, as_pathway_objects)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _load_pathways_sql(
        self,
        cache_key: str,
        use_cache: bool,
        as_pathway_objects: bool,
    ) -> Optional[Dict[str, Tuple[str, FrozenSet[str]]]]:
        """Load pathways from any SQL backend using the dialect abstraction."""
        # For SQLite, check if file exists
        if self.backend == StorageBackend.SQLITE:
            db_path = self.storage_path / f"{self.db_name}.db"
            if not db_path.exists():
                return None
            # Note: We don't check _is_cache_valid here because the database
            # stores expires_at directly, which we check below. This avoids
            # issues when a new manager instance is created without metadata.

        dialect = self._get_dialect()
        ph = dialect.placeholder
        db_col = dialect.quote_column("database")
        pathways_table = _sanitize_identifier(self.PATHWAYS_TABLE)
        genes_table = _sanitize_identifier(self.GENES_TABLE)

        try:
            with dialect.connection() as conn:
                cur = dialect.get_dict_cursor(conn)

                # Check cache expiry
                cur.execute(
                    f"SELECT expires_at FROM {pathways_table} WHERE cache_key = {ph} LIMIT 1",
                    (cache_key,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                if use_cache and time.time() > row["expires_at"]:
                    return None

                # Load pathways
                cur.execute(
                    f"SELECT id, name, {db_col} as database, species, url FROM {pathways_table} "
                    f"WHERE cache_key = {ph}",
                    (cache_key,)
                )
                pathway_rows = cur.fetchall()

                # Load genes for all pathways in this cache_key
                cur.execute(
                    f"SELECT pg.pathway_id, pg.gene_id FROM {genes_table} pg "
                    f"JOIN {pathways_table} p ON pg.pathway_id = p.id "
                    f"WHERE p.cache_key = {ph}",
                    (cache_key,)
                )
                gene_rows = cur.fetchall()

            # Build pathway -> genes mapping
            pathway_genes: Dict[str, Set[str]] = {}
            for row in gene_rows:
                pathway_id = row["pathway_id"]
                if pathway_id not in pathway_genes:
                    pathway_genes[pathway_id] = set()
                pathway_genes[pathway_id].add(row["gene_id"])

            # Build result
            result = {}
            for row in pathway_rows:
                pathway_id = row["id"]
                genes = frozenset(pathway_genes.get(pathway_id, set()))

                if as_pathway_objects:
                    from biodbs._funcs.analysis.ora import Pathway

                    result[pathway_id] = Pathway(
                        id=pathway_id,
                        name=row["name"],
                        genes=genes,
                        database=row["database"],
                        species=row["species"],
                        url=row["url"],
                    )
                else:
                    result[pathway_id] = (row["name"], genes)

            return result

        except Exception as e:
            self.logger.error("Failed to load pathways: %s", e)
            return None

    def _load_pathways_json(
        self,
        cache_key: str,
        use_cache: bool,
        as_pathway_objects: bool,
    ) -> Optional[Dict[str, Tuple[str, FrozenSet[str]]]]:
        """Load pathways from JSON."""
        data = self.load_json(cache_key, key=cache_key, use_cache=use_cache)
        if data is None:
            return None

        # Check expiry in JSON data
        if use_cache and time.time() > data.get("expires_at", 0):
            return None

        result = {}
        for pathway_id, pathway_data in data.get("pathways", {}).items():
            genes = frozenset(pathway_data["genes"])

            if as_pathway_objects:
                from biodbs._funcs.analysis.ora import Pathway

                result[pathway_id] = Pathway(
                    id=pathway_id,
                    name=pathway_data["name"],
                    genes=genes,
                    database=pathway_data.get("database", data.get("database", "custom")),
                    species=pathway_data.get("species", data.get("species")),
                    url=pathway_data.get("url"),
                )
            else:
                result[pathway_id] = (pathway_data["name"], genes)

        return result

    def _load_pathways_csv(
        self,
        cache_key: str,
        use_cache: bool,
        as_pathway_objects: bool,
    ) -> Optional[Dict[str, Tuple[str, FrozenSet[str]]]]:
        """Load pathways from CSV."""
        rows = self.load_csv(cache_key, key=cache_key, use_cache=use_cache)
        if rows is None:
            return None

        # Group by pathway_id
        pathway_data: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            pathway_id = row["pathway_id"]
            if pathway_id not in pathway_data:
                pathway_data[pathway_id] = {
                    "name": row["pathway_name"],
                    "genes": set(),
                    "database": row.get("database", "custom"),
                    "species": row.get("species"),
                }
            pathway_data[pathway_id]["genes"].add(row["gene_id"])

        result = {}
        for pathway_id, data in pathway_data.items():
            genes = frozenset(data["genes"])

            if as_pathway_objects:
                from biodbs._funcs.analysis.ora import Pathway

                result[pathway_id] = Pathway(
                    id=pathway_id,
                    name=data["name"],
                    genes=genes,
                    database=data["database"],
                    species=data["species"],
                )
            else:
                result[pathway_id] = (data["name"], genes)

        return result

    def query_pathways(
        self,
        gene_id: Optional[str] = None,
        database: Optional[str] = None,
        species: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query pathways from storage with optional filters.

        Only supported for SQL backends (SQLite, MySQL, PostgreSQL).

        Args:
            gene_id: Filter by gene ID. Returns only pathways containing this gene.
            database: Filter by source database (e.g., "KEGG", "Reactome", "GO").
            species: Filter by species (e.g., "Homo sapiens").
            min_size: Minimum number of genes in pathway.
            max_size: Maximum number of genes in pathway.

        Returns:
            List[Dict[str, Any]]: List of pathway dictionaries, each containing:
                - id: Pathway identifier (e.g., "hsa04110")
                - name: Pathway name (e.g., "Cell cycle")
                - database: Source database
                - species: Species name
                - url: Pathway URL (if available)
                - gene_count: Number of genes in pathway
                - cache_key: Cache key used when saving

            Results are sorted by gene_count in descending order.
            Returns empty list if no pathways match or database doesn't exist.

        Raises:
            ValueError: If backend is JSON or CSV (not supported).

        Example:
            >>> mgr = PathwayDBManager(storage_path="/tmp/cache", backend="sqlite")
            >>> # Find all KEGG pathways
            >>> pathways = mgr.query_pathways(database="KEGG")
            >>> pathways
            [{'id': 'hsa04110', 'name': 'Cell cycle', 'database': 'KEGG',
              'species': 'Homo sapiens', 'url': None, 'gene_count': 124,
              'cache_key': 'kegg_hsa'},
             {'id': 'hsa04115', 'name': 'p53 signaling', 'database': 'KEGG',
              'species': 'Homo sapiens', 'url': None, 'gene_count': 72,
              'cache_key': 'kegg_hsa'}]

            >>> # Find pathways containing TP53
            >>> tp53_pathways = mgr.query_pathways(gene_id="TP53")
            >>> print(f"TP53 is in {len(tp53_pathways)} pathways")
            TP53 is in 15 pathways

            >>> # Find medium-sized pathways
            >>> medium = mgr.query_pathways(min_size=50, max_size=200)
        """
        if not self._is_sql_backend():
            raise ValueError(f"query_pathways not supported with {self.backend.value} backend")

        # For SQLite, check if file exists
        if self.backend == StorageBackend.SQLITE:
            db_path = self.storage_path / f"{self.db_name}.db"
            if not db_path.exists():
                return []

        dialect = self._get_dialect()
        ph = dialect.placeholder
        db_col = dialect.quote_column("database")
        pathways_table = _sanitize_identifier(self.PATHWAYS_TABLE)
        genes_table = _sanitize_identifier(self.GENES_TABLE)

        conditions = []
        params: List[Any] = []

        if gene_id:
            conditions.append(f"p.id IN (SELECT pathway_id FROM {genes_table} WHERE gene_id = {ph})")
            params.append(gene_id)
        if database:
            conditions.append(f"p.{db_col} = {ph}")
            params.append(database)
        if species:
            conditions.append(f"p.species = {ph}")
            params.append(species)
        if min_size is not None:
            conditions.append(f"p.gene_count >= {ph}")
            params.append(min_size)
        if max_size is not None:
            conditions.append(f"p.gene_count <= {ph}")
            params.append(max_size)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        try:
            with dialect.connection() as conn:
                cur = dialect.get_dict_cursor(conn)
                cur.execute(
                    f"SELECT p.id, p.name, p.{db_col} as database, p.species, p.url, p.gene_count, p.cache_key "
                    f"FROM {pathways_table} p WHERE {where_clause} ORDER BY p.gene_count DESC",
                    params,
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            self.logger.error("Query failed: %s", e)
            return []

    def get_genes_for_pathway(self, pathway_id: str) -> Set[str]:
        """Get all genes for a specific pathway.

        Only supported for SQL backends (SQLite, MySQL, PostgreSQL).

        Args:
            pathway_id: Pathway identifier (e.g., "hsa04110", "R-HSA-69620").

        Returns:
            Set[str]: Set of gene IDs in the pathway.
                Returns empty set if pathway not found or database doesn't exist.

        Raises:
            ValueError: If backend is JSON or CSV (not supported).

        Example:
            >>> mgr = PathwayDBManager(storage_path="/tmp/cache", backend="sqlite")
            >>> genes = mgr.get_genes_for_pathway("hsa04110")
            >>> genes
            {'TP53', 'BRCA1', 'CDK1', 'CDK2', 'CCND1', ...}
            >>> print(f"Cell cycle has {len(genes)} genes")
            Cell cycle has 124 genes
        """
        if not self._is_sql_backend():
            raise ValueError(f"get_genes_for_pathway not supported with {self.backend.value} backend")

        # For SQLite, check if file exists
        if self.backend == StorageBackend.SQLITE:
            db_path = self.storage_path / f"{self.db_name}.db"
            if not db_path.exists():
                return set()

        dialect = self._get_dialect()
        ph = dialect.placeholder
        genes_table = _sanitize_identifier(self.GENES_TABLE)

        try:
            with dialect.connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    f"SELECT gene_id FROM {genes_table} WHERE pathway_id = {ph}",
                    (pathway_id,)
                )
                return {row[0] for row in cur.fetchall()}
        except Exception as e:
            self.logger.error("Failed to get genes for %s: %s", pathway_id, e)
            return set()

    def clear_expired(self) -> int:
        """Remove expired cache entries from the database.

        Only supported for SQL backends (SQLite, MySQL, PostgreSQL).
        JSON and CSV backends return 0 (no operation performed).

        Returns:
            int: Number of pathways removed.
                Returns 0 if no expired entries or database doesn't exist.

        Example:
            >>> mgr = PathwayDBManager(storage_path="/tmp/cache", backend="sqlite")
            >>> # Remove all expired pathways
            >>> removed = mgr.clear_expired()
            >>> print(f"Removed {removed} expired pathways")
            Removed 5 expired pathways
        """
        if not self._is_sql_backend():
            # JSON and CSV don't support this operation
            return 0

        # For SQLite, check if file exists
        if self.backend == StorageBackend.SQLITE:
            db_path = self.storage_path / f"{self.db_name}.db"
            if not db_path.exists():
                return 0

        dialect = self._get_dialect()
        ph = dialect.placeholder
        pathways_table = _sanitize_identifier(self.PATHWAYS_TABLE)
        genes_table = _sanitize_identifier(self.GENES_TABLE)

        try:
            with dialect.connection() as conn:
                cur = conn.cursor()
                now = time.time()

                # Get expired pathway IDs
                cur.execute(f"SELECT id FROM {pathways_table} WHERE expires_at < {ph}", (now,))
                expired_ids = [row[0] for row in cur.fetchall()]

                if not expired_ids:
                    return 0

                # Delete genes first (foreign key)
                placeholders = ",".join(ph for _ in expired_ids)
                cur.execute(
                    f"DELETE FROM {genes_table} WHERE pathway_id IN ({placeholders})",
                    expired_ids,
                )

                # Delete pathways
                cur.execute(f"DELETE FROM {pathways_table} WHERE expires_at < {ph}", (now,))

                self.logger.info("Cleared %d expired pathways from %s", len(expired_ids), self.backend.value)
                return len(expired_ids)

        except Exception as e:
            self.logger.error("Failed to clear expired cache: %s", e)
            return 0


# =============================================================================
# Backwards-compatible functions for existing code
# =============================================================================

# Global manager instance (lazy initialization)
_default_manager: Optional[PathwayDBManager] = None


def _get_default_manager() -> PathwayDBManager:
    """Get or create the default PathwayDBManager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = PathwayDBManager()
    return _default_manager


def get_cached_pathways(
    cache_key: str,
    cache_dir: Optional[str] = None,
    max_age: Optional[float] = None,
) -> Optional[Dict[str, Tuple[str, FrozenSet[str]]]]:
    """Get cached pathway data (backwards-compatible function).

    Args:
        cache_key: Unique key for the cached data (e.g., "kegg_hsa").
        cache_dir: Directory for cache files.
        max_age: Maximum age in seconds (not used with new system).

    Returns:
        Cached pathway data or None if not found/expired.
    """
    if cache_dir:
        mgr = PathwayDBManager(storage_path=cache_dir)
    else:
        mgr = _get_default_manager()

    return mgr.load_pathways(cache_key, use_cache=True)


def cache_pathways(
    cache_key: str,
    data: Dict[str, Tuple[str, FrozenSet[str]]],
    cache_dir: Optional[str] = None,
    expiry: Optional[float] = None,
) -> bool:
    """Cache pathway data (backwards-compatible function).

    Args:
        cache_key: Unique key for the cached data.
        data: Pathway data to cache (pathway_id -> (name, gene_set)).
        cache_dir: Directory for cache files.
        expiry: Expiration time in seconds.

    Returns:
        True if caching succeeded.
    """
    try:
        if cache_dir:
            mgr = PathwayDBManager(storage_path=cache_dir)
        else:
            mgr = _get_default_manager()

        # Extract database name from cache_key (e.g., "kegg_hsa" -> "KEGG")
        database = cache_key.split("_")[0].upper() if "_" in cache_key else "custom"

        mgr.save_pathways(
            pathways=data,
            cache_key=cache_key,
            database=database,
            expiry_seconds=expiry,
        )
        return True

    except Exception as e:
        warnings.warn(f"Cache write error: {e}")
        return False


def clear_cache(
    cache_key: Optional[str] = None,
    cache_dir: Optional[str] = None,
) -> bool:
    """Clear cached data (backwards-compatible function).

    Args:
        cache_key: Specific cache key to clear (None = clear all).
        cache_dir: Directory for cache files.

    Returns:
        True if clearing succeeded.
    """
    try:
        if cache_dir:
            mgr = PathwayDBManager(storage_path=cache_dir)
        else:
            mgr = _get_default_manager()

        mgr.clear_cache(cache_key)
        return True

    except Exception as e:
        warnings.warn(f"Cache clear error: {e}")
        return False


def get_cache_info(
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Get information about cached data (backwards-compatible function).

    Args:
        cache_dir: Directory for cache files.

    Returns:
        Dict with cache information including:
            - db_exists: Whether the database file exists
            - entries: List of cache entries with metadata
            - storage_path, db_name, total_size_bytes, etc.
    """
    if cache_dir:
        mgr = PathwayDBManager(storage_path=cache_dir)
    else:
        mgr = _get_default_manager()

    info = mgr.get_storage_info()

    # Add backwards-compatible keys
    db_path = mgr.storage_path / f"{mgr.db_name}.db"
    info["db_exists"] = db_path.exists()

    # Build entries list from cached pathways in the database
    entries = []
    if info["db_exists"]:
        try:
            dialect = mgr._get_dialect()
            pathways_table = _sanitize_identifier(mgr.PATHWAYS_TABLE)
            with dialect.connection() as conn:
                cur = dialect.get_dict_cursor(conn)
                cur.execute(
                    f"SELECT DISTINCT cache_key, created_at, expires_at "
                    f"FROM {pathways_table}"
                )
                for row in cur.fetchall():
                    entries.append({
                        "cache_key": row["cache_key"],
                        "created_at": row["created_at"],
                        "expires_at": row["expires_at"],
                    })
        except Exception:
            pass  # Return empty entries on error

    info["entries"] = entries

    return info


def set_cache_expiry(
    cache_key: str,
    expiry_seconds: float,
    cache_dir: Optional[str] = None,
) -> bool:
    """Update the expiry time for a cached entry (backwards-compatible function).

    Note: This function is a no-op with the new storage system.
    Use PathwayDBManager.save_pathways() with expiry_seconds instead.

    Returns:
        True (always succeeds as a no-op).
    """
    warnings.warn(
        "set_cache_expiry is deprecated. Use PathwayDBManager.save_pathways() "
        "with expiry_seconds parameter instead.",
        DeprecationWarning,
    )
    return True
