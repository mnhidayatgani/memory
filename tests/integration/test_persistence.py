"""Integration tests for data persistence across sessions."""

import tempfile
from pathlib import Path

import pytest

from hmc.core import HybridMemoryCore


class TestPersistence:
    """Test that data persists across HybridMemoryCore sessions."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_factual_data_persists_across_sessions(self, temp_dir):
        """Test that factual data survives process restart."""
        project_id = "test-persistence"
        
        # Session 1: Store data
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc1.set_fact("persistent_key", "persistent_value")
        hmc1.set_fact("number", 42)
        hmc1.set_fact("complex", {"nested": {"data": [1, 2, 3]}})
        
        # Session 2: Retrieve data
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        assert hmc2.get_fact("persistent_key") == "persistent_value"
        assert hmc2.get_fact("number") == 42
        assert hmc2.get_fact("complex") == {"nested": {"data": [1, 2, 3]}}

    def test_semantic_data_persists_across_sessions(self, temp_dir):
        """Test that semantic data survives process restart."""
        project_id = "test-semantic-persist"
        
        # Session 1: Store semantic content
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        doc_id = hmc1.add_semantic(
            "Persistent semantic document",
            metadata={"type": "test", "persistent": True}
        )
        assert doc_id is not None
        
        # Session 2: Query semantic content
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        results = hmc2.query_semantic("persistent semantic", k=5)
        
        assert len(results) > 0
        assert "Persistent semantic document" in results[0]["content"]
        assert results[0]["metadata"]["type"] == "test"
        assert results[0]["metadata"]["persistent"] is True

    def test_mixed_data_persists(self, temp_dir):
        """Test that both factual and semantic data persist together."""
        project_id = "test-mixed-persist"
        
        # Session 1: Store both types
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc1.set_fact("__persona_name__", "PersistentBot")
        hmc1.set_fact("__persona_tone__", "Persistent and reliable")
        hmc1.add_semantic(
            "I always remember our conversations.",
            metadata={"type": "persona_voice"}
        )
        hmc1.add_semantic(
            "Your data is safe with me.",
            metadata={"type": "persona_voice"}
        )
        
        # Session 2: Verify both types
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        
        # Check facts
        assert hmc2.get_fact("__persona_name__") == "PersistentBot"
        assert hmc2.get_fact("__persona_tone__") == "Persistent and reliable"
        
        # Check semantic
        results = hmc2.query_semantic(
            "remember conversations",
            k=5,
            filter={"type": "persona_voice"}
        )
        assert len(results) > 0

    def test_sqlite_file_persistence(self, temp_dir):
        """Test that SQLite database file is created and persists."""
        project_id = "test-sqlite-file"
        db_path = temp_dir / "sqlite" / "facts.db"
        
        # Create and store data
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc1.set_fact("test", "value")
        
        # Verify file exists
        assert db_path.exists()
        assert db_path.is_file()
        assert db_path.stat().st_size > 0
        
        # Verify data accessible after file check
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        assert hmc2.get_fact("test") == "value"

    def test_chromadb_directory_persistence(self, temp_dir):
        """Test that ChromaDB directory is created and persists."""
        project_id = "test-chroma-dir"
        chroma_dir = temp_dir / "chroma"
        
        # Create and store data
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc1.add_semantic("Test document", {"type": "test"})
        
        # Verify directory exists
        assert chroma_dir.exists()
        assert chroma_dir.is_dir()
        
        # ChromaDB should have created some files
        files = list(chroma_dir.rglob("*"))
        assert len(files) > 0
        
        # Verify data accessible after directory check
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        results = hmc2.query_semantic("test", k=1)
        assert len(results) > 0

    def test_multiple_projects_isolated(self, temp_dir):
        """Test that different projects have isolated storage."""
        # Project A
        hmc_a = HybridMemoryCore(project_id="project-a", db_directory=temp_dir / "a")
        hmc_a.set_fact("project", "A")
        hmc_a.add_semantic("Document from project A", {"project": "A"})
        
        # Project B
        hmc_b = HybridMemoryCore(project_id="project-b", db_directory=temp_dir / "b")
        hmc_b.set_fact("project", "B")
        hmc_b.add_semantic("Document from project B", {"project": "B"})
        
        # Verify isolation
        assert hmc_a.get_fact("project") == "A"
        assert hmc_b.get_fact("project") == "B"
        
        results_a = hmc_a.query_semantic("document", k=5)
        results_b = hmc_b.query_semantic("document", k=5)
        
        # Each should only see their own data
        assert all("project A" in r["content"] for r in results_a)
        assert all("project B" in r["content"] for r in results_b)

    def test_large_dataset_persistence(self, temp_dir):
        """Test persistence with larger dataset."""
        project_id = "test-large-persist"
        
        # Session 1: Store many facts and documents
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        
        # Store 100 facts
        for i in range(100):
            hmc1.set_fact(f"key_{i}", f"value_{i}")
        
        # Store 50 semantic documents
        for i in range(50):
            hmc1.add_semantic(
                f"Document number {i} about topic {i % 5}",
                metadata={"index": i, "topic": i % 5}
            )
        
        # Session 2: Verify all data
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        
        # Check all facts
        for i in range(100):
            assert hmc2.get_fact(f"key_{i}") == f"value_{i}"
        
        # Check semantic documents
        for topic in range(5):
            results = hmc2.query_semantic(
                f"topic {topic}",
                k=20,
                filter={"topic": topic}
            )
            assert len(results) >= 10  # Should find documents for this topic

    def test_update_persists(self, temp_dir):
        """Test that updates to existing data persist."""
        project_id = "test-update-persist"
        
        # Session 1: Create data
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc1.set_fact("status", "draft")
        
        # Session 2: Update data
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc2.set_fact("status", "approved")
        
        # Session 3: Verify update persisted
        hmc3 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        assert hmc3.get_fact("status") == "approved"

    def test_empty_query_persistence(self, temp_dir):
        """Test that empty results don't break persistence."""
        project_id = "test-empty-persist"
        
        # Session 1: Create HMC with no data
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        
        # Session 2: Query for non-existent data
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        assert hmc2.get_fact("nonexistent") is None
        results = hmc2.query_semantic("nonexistent content", k=5)
        assert len(results) == 0
        
        # Session 3: Should still work
        hmc3 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc3.set_fact("new_key", "new_value")
        
        # Session 4: Verify new data
        hmc4 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        assert hmc4.get_fact("new_key") == "new_value"

    def test_idempotent_initialization(self, temp_dir):
        """Test that multiple HMC initializations are safe."""
        project_id = "test-idempotent"
        
        # Store data
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc1.set_fact("key", "value")
        
        # Create multiple instances
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc3 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc4 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        
        # All should access same data
        assert hmc2.get_fact("key") == "value"
        assert hmc3.get_fact("key") == "value"
        assert hmc4.get_fact("key") == "value"
