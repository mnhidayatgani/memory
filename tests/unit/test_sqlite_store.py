"""Unit tests for SQLiteFactualStore."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from hmc.backends import SQLiteFactualStore
from hmc.exceptions import StorageError, ValidationError


class TestSQLiteFactualStore:
    """Unit tests for SQLiteFactualStore implementation."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_facts.db"
            yield db_path

    @pytest.fixture
    def store(self, temp_db):
        """Create SQLiteFactualStore instance."""
        return SQLiteFactualStore(db_path=temp_db)

    def test_init_stores_db_path(self, temp_db):
        """Test that __init__ stores database path."""
        store = SQLiteFactualStore(db_path=temp_db)
        assert store.db_path == temp_db

    def test_init_connection_is_none(self, temp_db):
        """Test that connection is lazy-initialized."""
        store = SQLiteFactualStore(db_path=temp_db)
        assert store._connection is None

    def test_get_connection_creates_connection(self, store):
        """Test that _get_connection creates database connection."""
        conn = store._get_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

    def test_get_connection_is_cached(self, store):
        """Test that _get_connection returns same connection."""
        conn1 = store._get_connection()
        conn2 = store._get_connection()
        assert conn1 is conn2

    def test_setup_creates_table(self, store):
        """Test that setup() creates facts table."""
        store.setup()
        
        conn = store._get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='facts'"
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "facts"

    def test_setup_table_has_correct_schema(self, store):
        """Test that facts table has correct columns."""
        store.setup()
        
        conn = store._get_connection()
        cursor = conn.execute("PRAGMA table_info(facts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert "key" in columns
        assert "json_value" in columns
        assert "updated_at" in columns
        assert columns["key"] == "TEXT"
        assert columns["json_value"] == "TEXT"

    def test_setup_is_idempotent(self, store):
        """Test that setup() can be called multiple times."""
        store.setup()
        store.setup()
        store.setup()
        # Should not raise

    def test_set_fact_inserts_data(self, store):
        """Test that set_fact() inserts data into database."""
        store.setup()
        store.set_fact("test_key", "test_value")
        
        conn = store._get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM facts WHERE key = ?", ("test_key",))
        count = cursor.fetchone()[0]
        
        assert count == 1

    def test_set_fact_json_serializes_value(self, store):
        """Test that set_fact() serializes value as JSON."""
        store.setup()
        test_value = {"nested": {"data": [1, 2, 3]}}
        store.set_fact("complex_key", test_value)
        
        conn = store._get_connection()
        cursor = conn.execute("SELECT json_value FROM facts WHERE key = ?", ("complex_key",))
        row = cursor.fetchone()
        
        stored_value = json.loads(row[0])
        assert stored_value == test_value

    def test_set_fact_updates_existing_key(self, store):
        """Test that set_fact() updates value for existing key."""
        store.setup()
        store.set_fact("key", "original")
        store.set_fact("key", "updated")
        
        conn = store._get_connection()
        cursor = conn.execute("SELECT json_value FROM facts WHERE key = ?", ("key",))
        row = cursor.fetchone()
        
        assert json.loads(row[0]) == "updated"

    def test_set_fact_updates_timestamp(self, store):
        """Test that set_fact() updates updated_at timestamp."""
        store.setup()
        store.set_fact("key", "value")
        
        conn = store._get_connection()
        cursor = conn.execute("SELECT updated_at FROM facts WHERE key = ?", ("key",))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] is not None

    def test_set_fact_validates_empty_key(self, store):
        """Test that set_fact() rejects empty key."""
        store.setup()
        
        with pytest.raises(ValidationError, match="non-empty string"):
            store.set_fact("", "value")

    def test_set_fact_validates_none_key(self, store):
        """Test that set_fact() rejects None key."""
        store.setup()
        
        with pytest.raises(ValidationError):
            store.set_fact(None, "value")

    def test_set_fact_validates_non_string_key(self, store):
        """Test that set_fact() rejects non-string key."""
        store.setup()
        
        with pytest.raises(ValidationError):
            store.set_fact(123, "value")

    def test_set_fact_validates_json_serializable(self, store):
        """Test that set_fact() rejects non-JSON-serializable values."""
        store.setup()
        
        class NotSerializable:
            pass
        
        with pytest.raises(ValidationError, match="JSON-serializable"):
            store.set_fact("key", NotSerializable())

    def test_set_fact_handles_various_types(self, store):
        """Test that set_fact() handles all JSON types."""
        store.setup()
        
        test_cases = [
            ("string", "test"),
            ("int", 42),
            ("float", 3.14),
            ("bool_true", True),
            ("bool_false", False),
            ("none", None),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value"}),
            ("nested", {"list": [1, {"nested": True}], "value": None}),
        ]
        
        for key, value in test_cases:
            store.set_fact(key, value)
            
            conn = store._get_connection()
            cursor = conn.execute("SELECT json_value FROM facts WHERE key = ?", (key,))
            row = cursor.fetchone()
            stored = json.loads(row[0])
            
            assert stored == value, f"Failed for {key}"

    def test_get_fact_retrieves_value(self, store):
        """Test that get_fact() returns stored value."""
        store.setup()
        store.set_fact("key", "value")
        
        result = store.get_fact("key")
        assert result == "value"

    def test_get_fact_deserializes_json(self, store):
        """Test that get_fact() deserializes JSON value."""
        store.setup()
        complex_value = {"nested": {"data": [1, 2, 3]}}
        store.set_fact("key", complex_value)
        
        result = store.get_fact("key")
        assert result == complex_value

    def test_get_fact_returns_none_for_missing(self, store):
        """Test that get_fact() returns None for non-existent key."""
        store.setup()
        
        result = store.get_fact("nonexistent")
        assert result is None

    def test_get_fact_validates_empty_key(self, store):
        """Test that get_fact() rejects empty key."""
        store.setup()
        
        with pytest.raises(ValidationError, match="non-empty string"):
            store.get_fact("")

    def test_get_fact_validates_none_key(self, store):
        """Test that get_fact() rejects None key."""
        store.setup()
        
        with pytest.raises(ValidationError):
            store.get_fact(None)

    def test_get_fact_validates_non_string_key(self, store):
        """Test that get_fact() rejects non-string key."""
        store.setup()
        
        with pytest.raises(ValidationError):
            store.get_fact(123)

    # Note: SQLiteFactualStore uses lazy connection and doesn't expose close() method
    # Connection cleanup is handled automatically by Python's garbage collector
    
    def test_persistence_across_instances(self, store, temp_db):
        """Test that data persists across different store instances."""
        store.setup()
        store.set_fact("persistent", "data")
        
        # Create new store instance
        new_store = SQLiteFactualStore(db_path=temp_db)
        new_store.setup()
        result = new_store.get_fact("persistent")
        
        assert result == "data"

    def test_multiple_facts(self, store):
        """Test storing and retrieving multiple facts."""
        store.setup()
        
        facts = {
            "__persona_name__": "Jarvis",
            "__persona_tone__": "Polite, witty",
            "__tech_stack__": {"python": "3.10", "deps": ["chromadb"]},
            "current_feature": "login",
            "task_counter": 42,
        }
        
        for key, value in facts.items():
            store.set_fact(key, value)
        
        for key, expected_value in facts.items():
            result = store.get_fact(key)
            assert result == expected_value, f"Failed for {key}"
