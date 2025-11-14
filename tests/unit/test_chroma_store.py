"""Unit tests for ChromaSemanticStore."""

import tempfile
from pathlib import Path

import pytest

from hmc.backends import ChromaSemanticStore
from hmc.exceptions import ValidationError


class TestChromaSemanticStore:
    """Unit tests for ChromaSemanticStore implementation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def store(self, temp_dir):
        """Create ChromaSemanticStore instance."""
        return ChromaSemanticStore(
            collection_name="test_collection",
            persist_directory=temp_dir / "chroma"
        )

    def test_init_stores_collection_name(self, temp_dir):
        """Test that __init__ stores collection name."""
        store = ChromaSemanticStore(
            collection_name="my_collection",
            persist_directory=temp_dir
        )
        assert store.collection_name == "my_collection"

    def test_init_stores_persist_directory(self, temp_dir):
        """Test that __init__ stores persist directory."""
        store = ChromaSemanticStore(
            collection_name="test",
            persist_directory=temp_dir / "chroma"
        )
        assert store.persist_directory == temp_dir / "chroma"

    def test_init_client_is_none(self, temp_dir):
        """Test that client is lazy-initialized."""
        store = ChromaSemanticStore(
            collection_name="test",
            persist_directory=temp_dir
        )
        assert store._client is None

    def test_get_client_creates_persistent_client(self, store):
        """Test that _get_client creates PersistentClient."""
        client = store._get_client()
        assert client is not None

    def test_get_client_is_cached(self, store):
        """Test that _get_client returns same client."""
        client1 = store._get_client()
        client2 = store._get_client()
        assert client1 is client2

    def test_setup_creates_collection(self, store):
        """Test that setup() creates collection."""
        store.setup()
        
        client = store._get_client()
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        
        assert "test_collection" in collection_names

    def test_setup_is_idempotent(self, store):
        """Test that setup() can be called multiple times."""
        store.setup()
        store.setup()
        store.setup()
        # Should not raise

    def test_add_semantic_generates_id(self, store):
        """Test that add_semantic() generates unique ID."""
        store.setup()
        
        doc_id = store.add_semantic(
            content="Test document",
            metadata={"type": "test"}
        )
        
        assert doc_id is not None
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_add_semantic_stores_content(self, store):
        """Test that add_semantic() stores content."""
        store.setup()
        
        content = "This is test content about Python programming"
        doc_id = store.add_semantic(content=content, metadata={"type": "test"})
        
        # Query to verify
        results = store.query_semantic(query_text="Python programming", k=1)
        assert len(results) > 0
        assert results[0]["content"] == content

    def test_add_semantic_stores_metadata(self, store):
        """Test that add_semantic() preserves metadata."""
        store.setup()
        
        metadata = {"type": "doc", "category": "tutorial", "status": "published"}
        doc_id = store.add_semantic(
            content="Tutorial document",
            metadata=metadata
        )
        
        results = store.query_semantic(query_text="tutorial", k=1)
        assert len(results) > 0
        assert results[0]["metadata"]["type"] == "doc"
        assert results[0]["metadata"]["category"] == "tutorial"
        assert results[0]["metadata"]["status"] == "published"

    def test_add_semantic_validates_empty_content(self, store):
        """Test that add_semantic() rejects empty content."""
        store.setup()
        
        with pytest.raises(ValidationError, match="non-empty string"):
            store.add_semantic(content="", metadata={"type": "test"})

    def test_add_semantic_validates_none_content(self, store):
        """Test that add_semantic() rejects None content."""
        store.setup()
        
        with pytest.raises(ValidationError):
            store.add_semantic(content=None, metadata={"type": "test"})

    def test_add_semantic_validates_non_string_content(self, store):
        """Test that add_semantic() rejects non-string content."""
        store.setup()
        
        with pytest.raises(ValidationError):
            store.add_semantic(content=123, metadata={"type": "test"})

    def test_add_semantic_validates_metadata_is_dict(self, store):
        """Test that add_semantic() requires dict metadata."""
        store.setup()
        
        with pytest.raises(ValidationError, match="dict"):
            store.add_semantic(content="test", metadata="not_a_dict")

    def test_add_semantic_validates_metadata_keys_are_strings(self, store):
        """Test that add_semantic() requires string keys in metadata."""
        store.setup()
        
        with pytest.raises(ValidationError, match="string"):
            store.add_semantic(content="test", metadata={123: "value"})

    def test_query_semantic_returns_list(self, store):
        """Test that query_semantic() returns list."""
        store.setup()
        
        results = store.query_semantic(query_text="test", k=5)
        assert isinstance(results, list)

    def test_query_semantic_respects_k_parameter(self, store):
        """Test that query_semantic() limits results by k."""
        store.setup()
        
        # Add 10 documents
        for i in range(10):
            store.add_semantic(
                content=f"Document {i} about testing",
                metadata={"index": i}
            )
        
        results = store.query_semantic(query_text="testing", k=3)
        assert len(results) <= 3

    def test_query_semantic_filters_by_metadata(self, store):
        """Test that query_semantic() filters by metadata."""
        store.setup()
        
        # Add documents with different types
        store.add_semantic("Spec doc", metadata={"type": "spec"})
        store.add_semantic("Plan doc", metadata={"type": "plan"})
        store.add_semantic("Task doc", metadata={"type": "task"})
        
        results = store.query_semantic(
            query_text="doc",
            k=10,
            filter={"type": "spec"}
        )
        
        # All should be type="spec"
        for result in results:
            assert result["metadata"]["type"] == "spec"

    def test_query_semantic_result_format(self, store):
        """Test that query_semantic() returns correct format."""
        store.setup()
        
        store.add_semantic("Test content", metadata={"type": "test"})
        results = store.query_semantic(query_text="test", k=1)
        
        assert len(results) > 0
        result = results[0]
        
        assert "content" in result
        assert "metadata" in result
        assert "distance" in result
        
        assert isinstance(result["content"], str)
        assert isinstance(result["metadata"], dict)

    def test_query_semantic_validates_empty_query(self, store):
        """Test that query_semantic() rejects empty query."""
        store.setup()
        
        with pytest.raises(ValidationError, match="non-empty string"):
            store.query_semantic(query_text="", k=5)

    def test_query_semantic_validates_none_query(self, store):
        """Test that query_semantic() rejects None query."""
        store.setup()
        
        with pytest.raises(ValidationError):
            store.query_semantic(query_text=None, k=5)

    def test_query_semantic_validates_k_positive(self, store):
        """Test that query_semantic() requires k > 0."""
        store.setup()
        
        with pytest.raises(ValidationError, match="greater than 0"):
            store.query_semantic(query_text="test", k=0)
        
        with pytest.raises(ValidationError, match="greater than 0"):
            store.query_semantic(query_text="test", k=-1)

    def test_multiple_documents(self, store):
        """Test storing and querying multiple documents."""
        store.setup()
        
        documents = [
            ("Python is a programming language", {"lang": "python"}),
            ("JavaScript is used for web development", {"lang": "javascript"}),
            ("Go is a compiled language", {"lang": "go"}),
        ]
        
        for content, metadata in documents:
            store.add_semantic(content, metadata)
        
        # Query for Python
        results = store.query_semantic("Python programming", k=1)
        assert len(results) > 0
        assert "Python" in results[0]["content"]

    def test_semantic_similarity_ranking(self, store):
        """Test that results are ranked by similarity."""
        store.setup()
        
        # Add highly relevant and less relevant docs
        store.add_semantic(
            "Complete guide to Python programming fundamentals",
            metadata={"relevance": "high"}
        )
        store.add_semantic(
            "JavaScript and Python comparison",
            metadata={"relevance": "medium"}
        )
        store.add_semantic(
            "How to cook pasta",
            metadata={"relevance": "low"}
        )
        
        results = store.query_semantic("Python programming guide", k=3)
        
        # Most relevant should be first
        assert len(results) > 0
        assert "Python programming fundamentals" in results[0]["content"]

    def test_persistence_across_instances(self, temp_dir):
        """Test that data persists across store instances."""
        persist_dir = temp_dir / "chroma"
        collection_name = "persistent_test"
        
        # Store 1: Add document
        store1 = ChromaSemanticStore(
            collection_name=collection_name,
            persist_directory=persist_dir
        )
        store1.setup()
        content = "Persistent test document"
        store1.add_semantic(content, metadata={"type": "test"})
        
        # Store 2: Query document
        store2 = ChromaSemanticStore(
            collection_name=collection_name,
            persist_directory=persist_dir
        )
        store2.setup()
        results = store2.query_semantic("persistent test", k=1)
        
        assert len(results) > 0
        assert results[0]["content"] == content

    def test_empty_query_results(self, store):
        """Test that empty results are handled gracefully."""
        store.setup()
        
        # Query with no documents
        results = store.query_semantic("nonexistent content", k=5)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_complex_metadata(self, store):
        """Test handling of complex metadata structures."""
        store.setup()
        
        metadata = {
            "type": "code_chunk",
            "source_file": "src/main.py",
            "language": "python",
            "chunk_index": 0,
            "line_range": "1-50",
            "functions": "main,helper"  # ChromaDB requires string values, not lists
        }
        
        doc_id = store.add_semantic("def main():\n    pass", metadata=metadata)
        assert doc_id is not None
        
        results = store.query_semantic("main function", k=1)
        assert len(results) > 0
        assert results[0]["metadata"]["type"] == "code_chunk"
        assert results[0]["metadata"]["source_file"] == "src/main.py"
        assert results[0]["metadata"]["functions"] == "main,helper"
