"""Caching system for pathway/gene set data.

This module provides SQLite-based caching for pathway data to improve
performance when running multiple ORA analyses.

The cache stores:
    - Pathway/gene set definitions
    - Gene-pathway mappings
    - Metadata (last updated, version, etc.)

Cache files are stored in:
    - User-specified directory
    - Or default: ~/.biodbs/cache/

Cache expiration:
    - Default: 7 days
    - Configurable per cache key
"""

from __future__ import annotations
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Any
import warnings


# Default cache settings
DEFAULT_CACHE_DIR = Path.home() / ".biodbs" / "cache"
DEFAULT_CACHE_EXPIRY = 7 * 24 * 60 * 60  # 7 days in seconds


def _get_cache_path(cache_dir: Optional[str] = None) -> Path:
    """Get the cache directory path."""
    if cache_dir:
        path = Path(cache_dir)
    else:
        path = DEFAULT_CACHE_DIR

    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_db_path(cache_dir: Optional[str] = None) -> Path:
    """Get the SQLite database path."""
    return _get_cache_path(cache_dir) / "pathways.db"


def _init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pathway_cache (
            cache_key TEXT PRIMARY KEY,
            data BLOB,
            created_at REAL,
            expires_at REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()


def get_cached_pathways(
    cache_key: str,
    cache_dir: Optional[str] = None,
    max_age: Optional[float] = None,
) -> Optional[Dict[str, Tuple[str, frozenset]]]:
    """Get cached pathway data.

    Args:
        cache_key: Unique key for the cached data (e.g., "kegg_hsa").
        cache_dir: Directory for cache files.
        max_age: Maximum age in seconds (None = use default expiry).

    Returns:
        Cached pathway data or None if not found/expired.
    """
    db_path = _get_db_path(cache_dir)

    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT data, expires_at FROM pathway_cache WHERE cache_key = ?",
            (cache_key,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        data_blob, expires_at = row

        # Check expiration
        if time.time() > expires_at:
            return None

        # Check max_age if specified
        if max_age is not None:
            cursor.execute(
                "SELECT created_at FROM pathway_cache WHERE cache_key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            if row and time.time() - row[0] > max_age:
                return None

        # Deserialize data
        data_dict = json.loads(data_blob)

        # Convert gene lists back to frozensets
        result = {}
        for pathway_id, (name, genes) in data_dict.items():
            result[pathway_id] = (name, frozenset(genes))

        return result

    except (sqlite3.Error, json.JSONDecodeError) as e:
        warnings.warn(f"Cache read error: {e}")
        return None


def cache_pathways(
    cache_key: str,
    data: Dict[str, Tuple[str, frozenset]],
    cache_dir: Optional[str] = None,
    expiry: Optional[float] = None,
) -> bool:
    """Cache pathway data.

    Args:
        cache_key: Unique key for the cached data.
        data: Pathway data to cache (pathway_id -> (name, gene_set)).
        cache_dir: Directory for cache files.
        expiry: Expiration time in seconds (None = use default).

    Returns:
        True if caching succeeded.
    """
    db_path = _get_db_path(cache_dir)

    try:
        conn = sqlite3.connect(str(db_path))
        _init_db(conn)

        # Serialize data (convert frozensets to lists for JSON)
        data_dict = {}
        for pathway_id, (name, genes) in data.items():
            data_dict[pathway_id] = (name, list(genes))

        data_blob = json.dumps(data_dict)

        now = time.time()
        expires_at = now + (expiry if expiry else DEFAULT_CACHE_EXPIRY)

        conn.execute(
            """
            INSERT OR REPLACE INTO pathway_cache (cache_key, data, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (cache_key, data_blob, now, expires_at)
        )
        conn.commit()
        conn.close()

        return True

    except sqlite3.Error as e:
        warnings.warn(f"Cache write error: {e}")
        return False


def clear_cache(
    cache_key: Optional[str] = None,
    cache_dir: Optional[str] = None,
) -> bool:
    """Clear cached data.

    Args:
        cache_key: Specific cache key to clear (None = clear all).
        cache_dir: Directory for cache files.

    Returns:
        True if clearing succeeded.
    """
    db_path = _get_db_path(cache_dir)

    if not db_path.exists():
        return True

    try:
        conn = sqlite3.connect(str(db_path))

        if cache_key:
            conn.execute(
                "DELETE FROM pathway_cache WHERE cache_key = ?",
                (cache_key,)
            )
        else:
            conn.execute("DELETE FROM pathway_cache")

        conn.commit()
        conn.close()
        return True

    except sqlite3.Error as e:
        warnings.warn(f"Cache clear error: {e}")
        return False


def get_cache_info(
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Get information about cached data.

    Args:
        cache_dir: Directory for cache files.

    Returns:
        Dict with cache information.
    """
    db_path = _get_db_path(cache_dir)

    info = {
        "cache_dir": str(_get_cache_path(cache_dir)),
        "db_exists": db_path.exists(),
        "entries": [],
    }

    if not db_path.exists():
        return info

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cache_key, created_at, expires_at,
                   length(data) as size_bytes
            FROM pathway_cache
        """)

        for row in cursor.fetchall():
            cache_key, created_at, expires_at, size_bytes = row
            info["entries"].append({
                "cache_key": cache_key,
                "created_at": created_at,
                "expires_at": expires_at,
                "size_bytes": size_bytes,
                "expired": time.time() > expires_at,
            })

        conn.close()

    except sqlite3.Error as e:
        info["error"] = str(e)

    return info


def set_cache_expiry(
    cache_key: str,
    expiry_seconds: float,
    cache_dir: Optional[str] = None,
) -> bool:
    """Update the expiry time for a cached entry.

    Args:
        cache_key: Cache key to update.
        expiry_seconds: New expiry time in seconds from now.
        cache_dir: Directory for cache files.

    Returns:
        True if update succeeded.
    """
    db_path = _get_db_path(cache_dir)

    if not db_path.exists():
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        expires_at = time.time() + expiry_seconds

        conn.execute(
            "UPDATE pathway_cache SET expires_at = ? WHERE cache_key = ?",
            (expires_at, cache_key)
        )
        conn.commit()
        conn.close()
        return True

    except sqlite3.Error as e:
        warnings.warn(f"Cache update error: {e}")
        return False
