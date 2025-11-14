"""Unit tests for HybridMemoryCore."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from hmc.core import HybridMemoryCore
from hmc.exceptions import ValidationError
from hmc.interfaces import FactualStorage, SemanticStorage


class TestHybridMemoryCore:
    """Unit tests for HybridMemoryCore class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_factual_store(self):
        """Create mock FactualStorage."""
        mock = Mock(spec=FactualStorage)
        mock.setup = Mock()
        mock.set_fact = Mock()
        mock.get_fact = Mock(return_value=None)
        return mock

    @pytest.fixture
    def mock_semantic_store(self):
        """Create mock SemanticStorage."""
        mock = Mock(spec=SemanticStorage)
        mock.setup = Mock()
        mock.add_semantic = Mock(return_value="test-id-123")
        mock.query_semantic = Mock(return_value=[])
        return mock

    def test_init_validates_project_id(self, temp_dir):
        """Test that __init__ validates project_id format."""
        with pytest.raises(ValidationError, match="non-empty string"):
            HybridMemoryCore(project_id="", db_directory=temp_dir)

        with pytest.raises(ValidationError):
            HybridMemoryCore(project_id=None, db_directory=temp_dir)

    def test_init_validates_project_id_characters(self, temp_dir):
        """Test that project_id must be alphanumeric with hyphens/underscores."""
        with pytest.raises(ValidationError, match="alphanumeric"):
            HybridMemoryCore(project_id="invalid@project", db_directory=temp_dir)

        with pytest.raises(ValidationError, match="alphanumeric"):
            HybridMemoryCore(project_id="invalid project", db_directory=temp_dir)

    def test_init_accepts_valid_project_ids(self, temp_dir):
        """Test that valid project_id formats are accepted."""
        valid_ids = [
            "my-project",
            "my_project",
            "MyProject123",
            "project-with_both",
            "abc123",
        ]

        for project_id in valid_ids:
            core = HybridMemoryCore(project_id=project_id, db_directory=temp_dir / project_id)
            assert core.project_id == project_id

    def test_init_creates_directory(self, temp_dir):
        """Test that __init__ creates db_directory if it doesn't exist."""
        db_dir = temp_dir / "new_directory"
        assert not db_dir.exists()

        HybridMemoryCore(project_id="test", db_directory=db_dir)
        assert db_dir.exists()

    def test_init_stores_project_id(self, temp_dir):
        """Test that __init__ stores project_id."""
        core = HybridMemoryCore(project_id="test-project", db_directory=temp_dir)
        assert core.project_id == "test-project"

    def test_init_stores_db_directory(self, temp_dir):
        """Test that __init__ stores db_directory as Path."""
        core = HybridMemoryCore(project_id="test", db_directory=temp_dir)
        assert core.db_directory == temp_dir
        assert isinstance(core.db_directory, Path)

    def test_init_accepts_string_path(self, temp_dir):
        """Test that __init__ accepts string db_directory."""
        str_path = str(temp_dir)
        core = HybridMemoryCore(project_id="test", db_directory=str_path)
        assert core.db_directory == Path(str_path)

    def test_init_uses_default_backends(self, temp_dir):
        """Test that __init__ creates default backends if not provided."""
        core = HybridMemoryCore(project_id="test", db_directory=temp_dir)

        assert core._factual_store is not None
        assert core._semantic_store is not None

    def test_init_accepts_custom_backends(self, temp_dir, mock_factual_store, mock_semantic_store):
        """Test that __init__ accepts custom backend instances."""
        core = HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        assert core._factual_store is mock_factual_store
        assert core._semantic_store is mock_semantic_store

    def test_init_calls_setup_on_backends(self, temp_dir, mock_factual_store, mock_semantic_store):
        """Test that __init__ calls setup() on both backends."""
        HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        mock_factual_store.setup.assert_called_once()
        mock_semantic_store.setup.assert_called_once()

    def test_set_fact_delegates_to_backend(self, temp_dir, mock_factual_store, mock_semantic_store):
        """Test that set_fact() delegates to factual storage."""
        core = HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        core.set_fact("test_key", "test_value")
        mock_factual_store.set_fact.assert_called_once_with("test_key", "test_value")

    def test_get_fact_delegates_to_backend(self, temp_dir, mock_factual_store, mock_semantic_store):
        """Test that get_fact() delegates to factual storage."""
        mock_factual_store.get_fact.return_value = "retrieved_value"

        core = HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        result = core.get_fact("test_key")

        mock_factual_store.get_fact.assert_called_once_with("test_key")
        assert result == "retrieved_value"

    def test_add_semantic_delegates_to_backend(
        self, temp_dir, mock_factual_store, mock_semantic_store
    ):
        """Test that add_semantic() delegates to semantic storage."""
        core = HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        metadata = {"type": "test"}
        doc_id = core.add_semantic("test content", metadata)

        mock_semantic_store.add_semantic.assert_called_once_with("test content", metadata)
        assert doc_id == "test-id-123"

    def test_query_semantic_delegates_to_backend(
        self, temp_dir, mock_factual_store, mock_semantic_store
    ):
        """Test that query_semantic() delegates to semantic storage."""
        expected_results = [{"id": "1", "content": "result", "metadata": {}}]
        mock_semantic_store.query_semantic.return_value = expected_results

        core = HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        results = core.query_semantic("test query", k=5, filter={"type": "test"})

        mock_semantic_store.query_semantic.assert_called_once_with(
            "test query", k=5, filter={"type": "test"}
        )
        assert results == expected_results

    def test_query_semantic_default_parameters(
        self, temp_dir, mock_factual_store, mock_semantic_store
    ):
        """Test that query_semantic() uses default k and filter."""
        core = HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        core.query_semantic("test query")

        mock_semantic_store.query_semantic.assert_called_once_with("test query", k=5, filter=None)

    def test_integration_with_real_backends(self, temp_dir):
        """Test HybridMemoryCore with real backends (integration test)."""
        core = HybridMemoryCore(project_id="test-real", db_directory=temp_dir)

        # Test factual storage
        core.set_fact("test_key", "test_value")
        assert core.get_fact("test_key") == "test_value"

        # Test semantic storage
        doc_id = core.add_semantic("Test document", {"type": "test"})
        assert doc_id is not None

        results = core.query_semantic("test document", k=1)
        assert len(results) > 0
        assert "Test document" in results[0]["content"]

    def test_backend_errors_propagate(self, temp_dir, mock_factual_store, mock_semantic_store):
        """Test that backend errors are propagated to caller."""
        mock_factual_store.set_fact.side_effect = ValidationError("Test error")

        core = HybridMemoryCore(
            project_id="test",
            db_directory=temp_dir,
            factual_store=mock_factual_store,
            semantic_store=mock_semantic_store,
        )

        with pytest.raises(ValidationError, match="Test error"):
            core.set_fact("key", "value")

    def test_multiple_operations(self, temp_dir):
        """Test multiple operations on same HybridMemoryCore instance."""
        core = HybridMemoryCore(project_id="test-multi", db_directory=temp_dir)

        # Store multiple facts
        core.set_fact("key1", "value1")
        core.set_fact("key2", 42)
        core.set_fact("key3", {"nested": "data"})

        # Store multiple semantic documents
        core.add_semantic("Document 1", {"type": "doc", "index": 1})
        core.add_semantic("Document 2", {"type": "doc", "index": 2})

        # Retrieve facts
        assert core.get_fact("key1") == "value1"
        assert core.get_fact("key2") == 42
        assert core.get_fact("key3") == {"nested": "data"}

        # Query semantics
        results = core.query_semantic("document", k=2, filter={"type": "doc"})
        assert len(results) == 2
