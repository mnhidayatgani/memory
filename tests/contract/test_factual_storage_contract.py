"""Contract tests for FactualStorage ABC.

Verifies that SQLiteFactualStore correctly implements the FactualStorage interface.
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from hmc.backends import SQLiteFactualStore
from hmc.exceptions import ValidationError
from hmc.interfaces import FactualStorage


class TestFactualStorageContract:
    """Test that SQLiteFactualStore satisfies FactualStorage contract."""

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

    def test_implements_interface(self, store):
        """Test that SQLiteFactualStore implements FactualStorage."""
        assert isinstance(store, FactualStorage)

    def test_setup_is_idempotent(self, store):
        """Test that setup() can be called multiple times safely."""
        store.setup()
        store.setup()  # Should not raise
        store.setup()  # Should not raise

    def test_set_fact_stores_value(self, store):
        """Test that set_fact() persists data."""
        store.setup()
        store.set_fact("test_key", "test_value")

        # Verify stored in database
        conn = sqlite3.connect(store.db_path)
        cursor = conn.execute("SELECT json_value FROM facts WHERE key = ?", ("test_key",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert json.loads(row[0]) == "test_value"

    def test_get_fact_retrieves_value(self, store):
        """Test that get_fact() returns stored value."""
        store.setup()
        store.set_fact("test_key", "test_value")

        result = store.get_fact("test_key")
        assert result == "test_value"

    def test_get_fact_returns_none_for_missing_key(self, store):
        """Test that get_fact() returns None for non-existent keys."""
        store.setup()

        result = store.get_fact("nonexistent_key")
        assert result is None

    def test_set_fact_upsert_semantics(self, store):
        """Test that set_fact() updates existing keys."""
        store.setup()
        store.set_fact("key", "original_value")
        store.set_fact("key", "updated_value")

        result = store.get_fact("key")
        assert result == "updated_value"

    def test_set_fact_json_serialization(self, store):
        """Test that set_fact() handles various JSON types."""
        store.setup()

        test_cases = [
            ("string", "test_string"),
            ("int", 42),
            ("float", 3.14),
            ("bool", True),
            ("none", None),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value", "nested": {"a": 1}}),
        ]

        for key, value in test_cases:
            store.set_fact(key, value)
            result = store.get_fact(key)
            assert result == value, f"Failed for {key}: expected {value}, got {result}"

    def test_set_fact_validates_key(self, store):
        """Test that set_fact() rejects invalid keys."""
        store.setup()

        with pytest.raises(ValidationError, match="non-empty string"):
            store.set_fact("", "value")

        with pytest.raises(ValidationError):
            store.set_fact(None, "value")

    def test_set_fact_validates_value_json_serializable(self, store):
        """Test that set_fact() rejects non-JSON-serializable values."""
        store.setup()

        class NonSerializable:
            pass

        with pytest.raises(ValidationError, match="JSON-serializable"):
            store.set_fact("key", NonSerializable())

    def test_get_fact_validates_key(self, store):
        """Test that get_fact() validates key parameter."""
        store.setup()

        with pytest.raises(ValidationError, match="non-empty string"):
            store.get_fact("")

        with pytest.raises(ValidationError):
            store.get_fact(None)

    def test_persistence_across_instances(self, temp_db):
        """Test that data persists across different store instances."""
        store1 = SQLiteFactualStore(db_path=temp_db)
        store1.setup()
        store1.set_fact("persistent_key", "persistent_value")

        # Create new instance with same database
        store2 = SQLiteFactualStore(db_path=temp_db)
        store2.setup()
        result = store2.get_fact("persistent_key")

        assert result == "persistent_value"

    def test_updated_at_timestamp(self, store):
        """Test that updated_at timestamp is set."""
        store.setup()
        store.set_fact("key", "value")

        conn = sqlite3.connect(store.db_path)
        cursor = conn.execute("SELECT updated_at FROM facts WHERE key = ?", ("key",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] is not None  # Timestamp should be set
