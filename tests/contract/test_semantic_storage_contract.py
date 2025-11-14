"""Contract tests for SemanticStorage ABC.

Verifies that ChromaSemanticStore correctly implements the SemanticStorage interface.
"""

import tempfile
from pathlib import Path

import pytest

from hmc.backends import ChromaSemanticStore
from hmc.exceptions import ValidationError
from hmc.interfaces import SemanticStorage


class TestSemanticStorageContract:
    """Test that ChromaSemanticStore satisfies SemanticStorage contract."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for ChromaDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def store(self, temp_dir):
        """Create ChromaSemanticStore instance."""
        return ChromaSemanticStore(
            collection_name="test_collection", persist_directory=temp_dir / "chroma"
        )

    def test_implements_interface(self, store):
        """Test that ChromaSemanticStore implements SemanticStorage."""
        assert isinstance(store, SemanticStorage)

    def test_setup_is_idempotent(self, store):
        """Test that setup() can be called multiple times safely."""
        store.setup()
        store.setup()  # Should not raise
        store.setup()  # Should not raise

    def test_add_semantic_returns_id(self, store):
        """Test that add_semantic() returns a unique ID."""
        store.setup()

        doc_id = store.add_semantic(content="Test content", metadata={"type": "test"})

        assert doc_id is not None
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_add_semantic_stores_content(self, store):
        """Test that add_semantic() stores content for retrieval."""
        store.setup()

        content = "This is a test document about machine learning"
        store.add_semantic(content=content, metadata={"type": "test"})

        # Query for the content
        results = store.query_semantic(query_text="machine learning", k=1)

        assert len(results) > 0
        assert results[0]["content"] == content

    def test_add_semantic_stores_metadata(self, store):
        """Test that add_semantic() preserves metadata."""
        store.setup()

        metadata = {"type": "test", "feature": "login", "status": "draft"}

        store.add_semantic(content="Test content with metadata", metadata=metadata)

        # Query and verify metadata
        results = store.query_semantic(query_text="test content", k=1)

        assert len(results) > 0
        assert results[0]["metadata"]["type"] == "test"
        assert results[0]["metadata"]["feature"] == "login"
        assert results[0]["metadata"]["status"] == "draft"

    def test_query_semantic_returns_list(self, store):
        """Test that query_semantic() returns list of results."""
        store.setup()

        results = store.query_semantic(query_text="test query", k=5)

        assert isinstance(results, list)

    def test_query_semantic_k_parameter(self, store):
        """Test that query_semantic() respects k parameter."""
        store.setup()

        # Add multiple documents
        for i in range(10):
            store.add_semantic(content=f"Document {i} about testing", metadata={"index": i})

        # Query with k=3
        results = store.query_semantic(query_text="testing", k=3)

        assert len(results) <= 3

    def test_query_semantic_filter_parameter(self, store):
        """Test that query_semantic() filters by metadata."""
        store.setup()

        # Add documents with different types
        store.add_semantic(
            content="Spec document for login", metadata={"type": "spec", "feature": "login"}
        )
        store.add_semantic(
            content="Plan document for login", metadata={"type": "plan", "feature": "login"}
        )
        store.add_semantic(
            content="Spec document for payment", metadata={"type": "spec", "feature": "payment"}
        )

        # Query with filter
        results = store.query_semantic(query_text="login", k=10, filter={"type": "spec"})

        # All results should be type="spec"
        for result in results:
            assert result["metadata"]["type"] == "spec"

    def test_query_semantic_result_format(self, store):
        """Test that query_semantic() returns correctly formatted results."""
        store.setup()

        store.add_semantic(content="Test content", metadata={"type": "test"})

        results = store.query_semantic(query_text="test", k=1)

        assert len(results) > 0
        result = results[0]

        # Check required fields
        assert "content" in result
        assert "metadata" in result
        assert "distance" in result

        assert isinstance(result["content"], str)
        assert isinstance(result["metadata"], dict)
        # distance can be None or float
        assert result["distance"] is None or isinstance(result["distance"], (int, float))

    def test_add_semantic_validates_content(self, store):
        """Test that add_semantic() validates content parameter."""
        store.setup()

        with pytest.raises(ValidationError, match="non-empty string"):
            store.add_semantic(content="", metadata={"type": "test"})

        with pytest.raises(ValidationError):
            store.add_semantic(content=None, metadata={"type": "test"})

    def test_add_semantic_validates_metadata(self, store):
        """Test that add_semantic() validates metadata parameter."""
        store.setup()

        with pytest.raises(ValidationError, match="dict"):
            store.add_semantic(content="test", metadata="not_a_dict")

        with pytest.raises(ValidationError):
            store.add_semantic(content="test", metadata=None)

    def test_add_semantic_validates_metadata_keys(self, store):
        """Test that add_semantic() requires string metadata keys."""
        store.setup()

        with pytest.raises(ValidationError, match="string"):
            store.add_semantic(content="test", metadata={123: "value"})  # Non-string key

    def test_query_semantic_validates_query_text(self, store):
        """Test that query_semantic() validates query_text parameter."""
        store.setup()

        with pytest.raises(ValidationError, match="non-empty string"):
            store.query_semantic(query_text="", k=5)

        with pytest.raises(ValidationError):
            store.query_semantic(query_text=None, k=5)

    def test_query_semantic_validates_k(self, store):
        """Test that query_semantic() validates k parameter."""
        store.setup()

        with pytest.raises(ValidationError, match="greater than 0"):
            store.query_semantic(query_text="test", k=0)

        with pytest.raises(ValidationError, match="greater than 0"):
            store.query_semantic(query_text="test", k=-1)

    def test_persistence_across_instances(self, temp_dir):
        """Test that data persists across different store instances."""
        collection_name = "persistent_collection"
        persist_dir = temp_dir / "chroma"

        # Store 1: Add document
        store1 = ChromaSemanticStore(collection_name=collection_name, persist_directory=persist_dir)
        store1.setup()
        content = "Persistent test document"
        store1.add_semantic(content=content, metadata={"type": "test"})

        # Store 2: Query document
        store2 = ChromaSemanticStore(collection_name=collection_name, persist_directory=persist_dir)
        store2.setup()
        results = store2.query_semantic(query_text="persistent test", k=1)

        assert len(results) > 0
        assert results[0]["content"] == content

    def test_similarity_ranking(self, store):
        """Test that query_semantic() ranks results by similarity."""
        store.setup()

        # Add documents with varying relevance
        store.add_semantic(
            content="Python programming language tutorial", metadata={"relevance": "high"}
        )
        store.add_semantic(
            content="Java programming language guide", metadata={"relevance": "medium"}
        )
        store.add_semantic(content="Cooking recipes for dinner", metadata={"relevance": "low"})

        # Query for Python
        results = store.query_semantic(query_text="Python programming", k=3)

        # Most relevant should be first
        assert len(results) > 0
        assert "Python" in results[0]["content"]
