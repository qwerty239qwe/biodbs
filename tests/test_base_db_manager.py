"""Tests for biodbs.data._base module — BaseFetchedData and BaseDBManager."""

import json
import sqlite3
from datetime import datetime, timedelta

import pytest

from biodbs.data._base import BaseFetchedData, BaseDBManager, _sanitize_identifier


# =============================================================================
# BaseFetchedData
# =============================================================================


class TestBaseFetchedData:
    def test_repr_with_list(self):
        data = BaseFetchedData([1, 2, 3])
        assert "3 results" in repr(data)

    def test_repr_with_dict(self):
        data = BaseFetchedData({"a": 1, "b": 2})
        assert "2 results" in repr(data)

    def test_repr_with_non_iterable(self):
        data = BaseFetchedData(42)
        assert "BaseFetchedData" in repr(data)

    def test_str_same_as_repr(self):
        data = BaseFetchedData([1])
        assert str(data) == repr(data)

    def test_to_json(self, tmp_path):
        data = BaseFetchedData({"key": "value"})
        filepath = tmp_path / "out.json"
        data.to_json(str(filepath))
        assert json.loads(filepath.read_text()) == {"key": "value"}

    def test_to_text(self, tmp_path):
        data = BaseFetchedData("hello world")
        filepath = tmp_path / "out.txt"
        data.to_text(str(filepath))
        assert filepath.read_text() == "hello world"

    def test_to_csv_not_implemented(self):
        data = BaseFetchedData([])
        with pytest.raises(NotImplementedError):
            data.to_csv("file.csv")

    def test_as_dict_not_implemented(self):
        data = BaseFetchedData([])
        with pytest.raises(NotImplementedError):
            data.as_dict()

    def test_as_dataframe_not_implemented(self):
        data = BaseFetchedData([])
        with pytest.raises(NotImplementedError):
            data.as_dataframe()


# =============================================================================
# _sanitize_identifier
# =============================================================================


class TestSanitizeIdentifier:
    def test_valid_name(self):
        assert _sanitize_identifier("my_table") == '"my_table"'

    def test_valid_dotted(self):
        assert _sanitize_identifier("schema.table") == '"schema.table"'

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _sanitize_identifier("DROP TABLE; --")

    def test_starts_with_number_raises(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _sanitize_identifier("123table")


# =============================================================================
# BaseDBManager — context manager & metadata
# =============================================================================


class TestDBManagerInit:
    def test_creates_directory(self, tmp_path):
        path = tmp_path / "subdir" / "data"
        mgr = BaseDBManager(path)
        assert path.exists()

    def test_no_auto_create(self, tmp_path):
        path = tmp_path / "no_create"
        with pytest.raises(Exception):
            # Saving should fail because dir doesn't exist
            mgr = BaseDBManager(path, auto_create_dirs=False)
            mgr.save_json({"a": 1}, "test")

    def test_context_manager(self, tmp_path):
        with BaseDBManager(tmp_path, db_name="ctx") as mgr:
            mgr._update_metadata("k1", note="test")
        # Metadata should be flushed
        meta_file = tmp_path / "ctx_metadata.json"
        assert meta_file.exists()
        meta = json.loads(meta_file.read_text())
        assert "k1" in meta


class TestMetadata:
    def test_update_and_flush(self, tmp_path):
        mgr = BaseDBManager(tmp_path, db_name="md")
        mgr._update_metadata("key1", filepath="/tmp/x.json")
        assert mgr._metadata_dirty is True
        mgr.flush_metadata()
        assert mgr._metadata_dirty is False

        meta = json.loads((tmp_path / "md_metadata.json").read_text())
        assert meta["key1"]["filepath"] == "/tmp/x.json"
        assert "timestamp" in meta["key1"]

    def test_load_existing_metadata(self, tmp_path):
        # Write metadata manually
        meta_file = tmp_path / "data_metadata.json"
        meta_file.write_text(json.dumps({"old_key": {"timestamp": "2025-01-01T00:00:00"}}))
        mgr = BaseDBManager(tmp_path)
        assert "old_key" in mgr._metadata

    def test_corrupted_metadata_returns_empty(self, tmp_path):
        meta_file = tmp_path / "data_metadata.json"
        meta_file.write_text("not valid json{{{")
        mgr = BaseDBManager(tmp_path)
        assert mgr._metadata == {}


# =============================================================================
# Cache validation
# =============================================================================


class TestCacheValidation:
    def test_no_expiry_always_valid(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=None)
        mgr._update_metadata("k", note="x")
        assert mgr._is_cache_valid("k") is True

    def test_fresh_cache_valid(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=7)
        mgr._update_metadata("k", note="x")
        assert mgr._is_cache_valid("k") is True

    def test_expired_cache_invalid(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr._metadata["old"] = {
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat()
        }
        assert mgr._is_cache_valid("old") is False

    def test_missing_key_invalid(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        assert mgr._is_cache_valid("nonexistent") is False

    def test_no_timestamp_invalid(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr._metadata["no_ts"] = {"filepath": "/x"}
        assert mgr._is_cache_valid("no_ts") is False

    def test_bad_timestamp_invalid(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr._metadata["bad_ts"] = {"timestamp": "not-a-date"}
        assert mgr._is_cache_valid("bad_ts") is False


# =============================================================================
# JSON save/load
# =============================================================================


class TestJSON:
    def test_save_load_cycle(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr.save_json({"a": 1, "b": [2, 3]}, "test", key="k1")
        result = mgr.load_json("test", key="k1")
        assert result == {"a": 1, "b": [2, 3]}

    def test_save_list(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr.save_json([1, 2, 3], "nums")
        assert mgr.load_json("nums") == [1, 2, 3]

    def test_load_nonexistent_returns_none(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        assert mgr.load_json("missing") is None

    def test_load_expired_cache_returns_none(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr.save_json({"x": 1}, "data", key="k")
        # Manually expire the cache
        mgr._metadata["k"]["timestamp"] = (
            datetime.now() - timedelta(days=2)
        ).isoformat()
        result = mgr.load_json("data", key="k", use_cache=True)
        assert result is None

    def test_load_expired_cache_bypass(self, tmp_path):
        """use_cache=False loads even if cache is expired."""
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr.save_json({"x": 1}, "data", key="k")
        mgr._metadata["k"]["timestamp"] = (
            datetime.now() - timedelta(days=2)
        ).isoformat()
        result = mgr.load_json("data", key="k", use_cache=False)
        assert result == {"x": 1}

    def test_load_corrupted_json_returns_none(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        (tmp_path / "bad.json").write_text("{invalid json")
        assert mgr.load_json("bad") is None

    def test_save_with_extra_metadata(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr.save_json({"a": 1}, "file", key="k", source="api", version=2)
        assert mgr._metadata["k"]["source"] == "api"
        assert mgr._metadata["k"]["version"] == 2


# =============================================================================
# CSV save/load
# =============================================================================


class TestCSV:
    def test_save_load_cycle(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
        mgr.save_csv(data, "people", key="pk")
        result = mgr.load_csv("people", key="pk")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_save_empty_raises(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        with pytest.raises(ValueError, match="empty"):
            mgr.save_csv([], "empty")

    def test_load_nonexistent_returns_none(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        assert mgr.load_csv("missing") is None

    def test_load_expired_cache_returns_none(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr.save_csv([{"x": "1"}], "data", key="k")
        mgr._metadata["k"]["timestamp"] = (
            datetime.now() - timedelta(days=2)
        ).isoformat()
        assert mgr.load_csv("data", key="k") is None


# =============================================================================
# SQLite save/load
# =============================================================================


class TestSQLite:
    def test_save_load_cycle(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        data = [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]
        mgr.save_to_sqlite(data, "items", key="sk")
        result = mgr.load_from_sqlite("items", key="sk")
        assert len(result) == 2
        assert result[0]["name"] == "A"

    def test_save_empty_raises(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        with pytest.raises(ValueError, match="empty"):
            mgr.save_to_sqlite([], "empty_table")

    def test_load_nonexistent_returns_none(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        assert mgr.load_from_sqlite("missing_table") is None

    def test_if_exists_replace(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr.save_to_sqlite([{"v": "old"}], "t")
        mgr.save_to_sqlite([{"v": "new"}], "t", if_exists="replace")
        result = mgr.load_from_sqlite("t")
        assert len(result) == 1
        assert result[0]["v"] == "new"

    def test_if_exists_append(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr.save_to_sqlite([{"v": "1"}], "t", if_exists="replace")
        mgr.save_to_sqlite([{"v": "2"}], "t", if_exists="append")
        result = mgr.load_from_sqlite("t")
        assert len(result) == 2

    def test_load_with_query(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        data = [{"id": "1", "status": "active"}, {"id": "2", "status": "inactive"}]
        mgr.save_to_sqlite(data, "items")
        result = mgr.load_from_sqlite("items", query="\"status\" = 'active'")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_load_expired_cache_returns_none(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr.save_to_sqlite([{"v": "x"}], "t", key="k")
        mgr._metadata["k"]["timestamp"] = (
            datetime.now() - timedelta(days=2)
        ).isoformat()
        assert mgr.load_from_sqlite("t", key="k") is None


# =============================================================================
# Cache management
# =============================================================================


class TestCacheManagement:
    def test_clear_single_key(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr._update_metadata("k1", note="a")
        mgr._update_metadata("k2", note="b")
        mgr.clear_cache("k1")
        assert "k1" not in mgr._metadata
        assert "k2" in mgr._metadata

    def test_clear_all(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr._update_metadata("k1", note="a")
        mgr._update_metadata("k2", note="b")
        mgr.clear_cache()
        assert mgr._metadata == {}

    def test_list_cached_items(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=7)
        mgr._update_metadata("k1", note="a")
        items = mgr.list_cached_items()
        assert len(items) == 1
        assert items[0]["key"] == "k1"
        assert items[0]["is_valid"] is True

    def test_get_storage_info(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr.save_json({"a": 1}, "info_test")
        info = mgr.get_storage_info()
        assert info["file_count"] >= 1
        assert info["total_size_bytes"] > 0
        assert "total_size_mb" in info


# =============================================================================
# Streaming: JSON Lines
# =============================================================================


class TestStreamJSONLines:
    def test_stream_and_load(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        items = [{"id": i, "val": f"v{i}"} for i in range(5)]
        mgr.stream_json_lines(iter(items), "stream", key="sk")
        result = list(mgr.load_json_lines("stream", key="sk"))
        assert len(result) == 5
        assert result[0]["id"] == 0

    def test_load_with_limit(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        items = [{"id": i} for i in range(10)]
        mgr.stream_json_lines(iter(items), "many")
        result = list(mgr.load_json_lines("many", limit=3))
        assert len(result) == 3

    def test_load_nonexistent_yields_nothing(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        result = list(mgr.load_json_lines("missing"))
        assert result == []

    def test_load_expired_cache_yields_nothing(self, tmp_path):
        mgr = BaseDBManager(tmp_path, cache_expiry_days=1)
        mgr.stream_json_lines(iter([{"a": 1}]), "data", key="k")
        mgr._metadata["k"]["timestamp"] = (
            datetime.now() - timedelta(days=2)
        ).isoformat()
        result = list(mgr.load_json_lines("data", key="k"))
        assert result == []

    def test_buffer_flush(self, tmp_path):
        """Items are correctly written even with buffer_size=2."""
        mgr = BaseDBManager(tmp_path)
        items = [{"id": i} for i in range(5)]
        mgr.stream_json_lines(iter(items), "buf", buffer_size=2)
        result = list(mgr.load_json_lines("buf"))
        assert len(result) == 5


# =============================================================================
# Streaming: CSV
# =============================================================================


class TestStreamCSV:
    def test_stream_and_load(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        items = [{"name": "A", "val": "1"}, {"name": "B", "val": "2"}]
        mgr.stream_csv(iter(items), "stream_csv")
        result = mgr.load_csv("stream_csv")
        assert len(result) == 2

    def test_custom_fieldnames(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        items = [{"a": "1", "b": "2", "c": "3"}]
        mgr.stream_csv(iter(items), "custom", fieldnames=["a", "b"])
        result = mgr.load_csv("custom")
        assert list(result[0].keys()) == ["a", "b"]

    def test_empty_stream(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        mgr.stream_csv(iter([]), "empty_stream")
        # File exists but is empty
        result = mgr.load_csv("empty_stream")
        assert result == []


# =============================================================================
# Streaming: SQLite
# =============================================================================


class TestStreamSQLite:
    def test_stream_and_load(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        items = [{"id": str(i), "val": f"v{i}"} for i in range(5)]
        mgr.stream_to_sqlite(iter(items), "streamed")
        result = mgr.load_from_sqlite("streamed")
        assert len(result) == 5

    def test_batch_size(self, tmp_path):
        """Data committed in batches still produces correct results."""
        mgr = BaseDBManager(tmp_path)
        items = [{"id": str(i)} for i in range(7)]
        mgr.stream_to_sqlite(iter(items), "batched", batch_size=3)
        result = mgr.load_from_sqlite("batched")
        assert len(result) == 7

    def test_create_indices(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        items = [{"id": "1", "name": "A"}]
        mgr.stream_to_sqlite(
            iter(items), "indexed", create_indices=["id"]
        )
        # Verify index was created
        db_path = tmp_path / "data.db"
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indices = [row[0] for row in cursor.fetchall()]
            assert any("idx_indexed_id" in idx for idx in indices)
        finally:
            conn.close()

    def test_if_exists_fail(self, tmp_path):
        mgr = BaseDBManager(tmp_path)
        items = [{"id": "1"}]
        mgr.stream_to_sqlite(iter(items), "fail_test", if_exists="replace")
        with pytest.raises(ValueError, match="already exists"):
            mgr.stream_to_sqlite(iter(items), "fail_test", if_exists="fail")


# =============================================================================
# Helper methods
# =============================================================================


class TestHelpers:
    def test_build_insert_query(self):
        q = BaseDBManager._build_insert_query("my_table", ["col1", "col2"])
        assert '"my_table"' in q
        assert '"col1"' in q
        assert "?" in q

    def test_rows_as_tuples(self):
        rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = BaseDBManager._rows_as_tuples(rows, ["a", "b"])
        assert result == [(1, 2), (3, 4)]

    def test_rows_as_tuples_missing_key(self):
        rows = [{"a": 1}]
        result = BaseDBManager._rows_as_tuples(rows, ["a", "b"])
        assert result == [(1, None)]
