"""Tests for biodbs._funcs.analysis._cache module."""

import time
from pathlib import Path

import pytest
from biodbs._funcs.analysis._cache import (
    PathwayDBManager,
    StorageBackend,
    SQLiteDialect,
    MySQLDialect,
    PostgreSQLDialect,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_pathways():
    return {
        "hsa04110": ("Cell cycle", {"TP53", "BRCA1", "CDK1"}),
        "hsa04115": ("p53 signaling", {"TP53", "MDM2", "CDKN1A"}),
    }


@pytest.fixture
def sqlite_mgr(tmp_path):
    return PathwayDBManager(
        storage_path=tmp_path,
        db_name="test_pathways",
        backend="sqlite",
        cache_expiry_days=7,
    )


@pytest.fixture
def json_mgr(tmp_path):
    return PathwayDBManager(
        storage_path=tmp_path,
        db_name="test_pathways",
        backend="json",
        cache_expiry_days=7,
    )


@pytest.fixture
def csv_mgr(tmp_path):
    return PathwayDBManager(
        storage_path=tmp_path,
        db_name="test_pathways",
        backend="csv",
        cache_expiry_days=7,
    )


# =============================================================================
# TestPathwayDBManagerSQLite
# =============================================================================


class TestPathwayDBManagerSQLite:
    def test_save_and_load(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="kegg_test", database="KEGG")
        loaded = sqlite_mgr.load_pathways("kegg_test")
        assert loaded is not None
        assert len(loaded) == 2
        assert "hsa04110" in loaded
        name, genes = loaded["hsa04110"]
        assert name == "Cell cycle"
        assert genes == frozenset({"TP53", "BRCA1", "CDK1"})

    def test_load_nonexistent(self, sqlite_mgr):
        result = sqlite_mgr.load_pathways("nonexistent")
        assert result is None

    def test_expired_cache(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(
            sample_pathways, cache_key="expired",
            database="KEGG", expiry_seconds=0.001,
        )
        time.sleep(0.01)
        loaded = sqlite_mgr.load_pathways("expired", use_cache=True)
        assert loaded is None

    def test_load_ignore_cache(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(
            sample_pathways, cache_key="expired",
            database="KEGG", expiry_seconds=0.001,
        )
        time.sleep(0.01)
        loaded = sqlite_mgr.load_pathways("expired", use_cache=False)
        assert loaded is not None

    def test_query_by_gene(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="kegg_test", database="KEGG")
        results = sqlite_mgr.query_pathways(gene_id="TP53")
        assert len(results) == 2  # TP53 is in both pathways

    def test_query_by_database(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="kegg_test", database="KEGG")
        results = sqlite_mgr.query_pathways(database="KEGG")
        assert len(results) == 2

    def test_query_by_size(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="kegg_test", database="KEGG")
        results = sqlite_mgr.query_pathways(min_size=3)
        assert len(results) == 2  # Both have 3 genes
        results = sqlite_mgr.query_pathways(min_size=4)
        assert len(results) == 0

    def test_get_genes_for_pathway(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="kegg_test", database="KEGG")
        genes = sqlite_mgr.get_genes_for_pathway("hsa04110")
        assert genes == {"TP53", "BRCA1", "CDK1"}

    def test_get_genes_nonexistent_pathway(self, sqlite_mgr):
        genes = sqlite_mgr.get_genes_for_pathway("nonexistent")
        assert genes == set()

    def test_clear_cache_specific_key(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="k1", database="KEGG")
        sqlite_mgr.save_pathways(
            {"p1": ("path1", {"G1"})}, cache_key="k2", database="GO",
        )
        sqlite_mgr.clear_cache("k1")
        assert sqlite_mgr.load_pathways("k1") is None
        assert sqlite_mgr.load_pathways("k2") is not None

    def test_clear_cache_all(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="k1", database="KEGG")
        sqlite_mgr.clear_cache()
        assert sqlite_mgr.load_pathways("k1") is None

    def test_clear_expired(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(
            sample_pathways, cache_key="old",
            database="KEGG", expiry_seconds=0.001,
        )
        time.sleep(0.01)
        removed = sqlite_mgr.clear_expired()
        assert removed == 2  # Two pathways removed

    def test_overwrite_same_cache_key(self, sqlite_mgr, sample_pathways):
        sqlite_mgr.save_pathways(sample_pathways, cache_key="k1", database="KEGG")
        new_pathways = {"p_new": ("New Pathway", {"G1", "G2"})}
        sqlite_mgr.save_pathways(new_pathways, cache_key="k1", database="KEGG")
        loaded = sqlite_mgr.load_pathways("k1")
        assert len(loaded) == 1
        assert "p_new" in loaded

    def test_repr(self, sqlite_mgr):
        r = repr(sqlite_mgr)
        assert "PathwayDBManager" in r
        assert "sqlite" in r


# =============================================================================
# TestPathwayDBManagerJSON
# =============================================================================


class TestPathwayDBManagerJSON:
    def test_save_and_load(self, json_mgr, sample_pathways):
        json_mgr.save_pathways(sample_pathways, cache_key="kegg_test", database="KEGG")
        loaded = json_mgr.load_pathways("kegg_test")
        assert loaded is not None
        assert len(loaded) == 2

    def test_load_nonexistent(self, json_mgr):
        assert json_mgr.load_pathways("nonexistent") is None

    def test_expired_json(self, json_mgr, sample_pathways):
        json_mgr.save_pathways(
            sample_pathways, cache_key="expired",
            database="KEGG", expiry_seconds=0.001,
        )
        time.sleep(0.01)
        loaded = json_mgr.load_pathways("expired", use_cache=True)
        assert loaded is None

    def test_query_not_supported(self, json_mgr, sample_pathways):
        json_mgr.save_pathways(sample_pathways, cache_key="k1", database="KEGG")
        with pytest.raises(ValueError, match="not supported"):
            json_mgr.query_pathways(database="KEGG")

    def test_clear_expired_returns_zero(self, json_mgr):
        assert json_mgr.clear_expired() == 0


# =============================================================================
# TestPathwayDBManagerCSV
# =============================================================================


class TestPathwayDBManagerCSV:
    def test_save_and_load(self, csv_mgr, sample_pathways):
        csv_mgr.save_pathways(sample_pathways, cache_key="kegg_test", database="KEGG")
        loaded = csv_mgr.load_pathways("kegg_test")
        assert loaded is not None
        assert len(loaded) == 2

    def test_query_not_supported(self, csv_mgr, sample_pathways):
        csv_mgr.save_pathways(sample_pathways, cache_key="k1", database="KEGG")
        with pytest.raises(ValueError, match="not supported"):
            csv_mgr.query_pathways()

    def test_get_genes_not_supported(self, csv_mgr):
        with pytest.raises(ValueError, match="not supported"):
            csv_mgr.get_genes_for_pathway("p1")


# =============================================================================
# TestSQLDialects
# =============================================================================


class TestSQLDialects:
    def test_sqlite_placeholder(self, tmp_path):
        from biodbs.data._base import BaseDBManager
        mgr = BaseDBManager(tmp_path)
        dialect = SQLiteDialect(tmp_path / "test.db", mgr._sqlite_connection)
        assert dialect.placeholder == "?"

    def test_mysql_placeholder(self):
        dialect = MySQLDialect({"host": "localhost", "user": "u", "password": "p", "database": "db"})
        assert dialect.placeholder == "%s"
        assert dialect._quote_identifier("col") == "`col`"

    def test_postgresql_placeholder(self):
        dialect = PostgreSQLDialect({"host": "localhost", "user": "u", "password": "p", "database": "db"})
        assert dialect.placeholder == "%s"


class TestStorageBackend:
    def test_enum_values(self):
        assert StorageBackend.SQLITE.value == "sqlite"
        assert StorageBackend.JSON.value == "json"
        assert StorageBackend.CSV.value == "csv"
        assert StorageBackend.MYSQL.value == "mysql"
        assert StorageBackend.POSTGRESQL.value == "postgresql"

    def test_missing_db_config_raises(self, tmp_path):
        with pytest.raises(ValueError, match="missing required keys"):
            PathwayDBManager(
                storage_path=tmp_path,
                backend="mysql",
                db_config={"host": "localhost"},
            )
