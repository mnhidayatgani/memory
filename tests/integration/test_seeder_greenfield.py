"""Integration tests for greenfield project initialization."""

import tempfile
from pathlib import Path

import pytest

from hmc.core import HybridMemoryCore
from hmc.seeder import seed_project


class TestSeederGreenfield:
    """Integration tests for initializing HMC in new/empty projects."""

    @pytest.fixture
    def empty_project(self):
        """Create empty project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "empty_project"
            project_dir.mkdir()
            yield project_dir

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_initialize_hmc_in_empty_directory(self, empty_project):
        """Test initializing HMC in empty directory creates necessary structures."""
        memory_dir = empty_project / ".hmc_memory"

        hmc = HybridMemoryCore(project_id="greenfield-test", db_directory=memory_dir)

        # Verify memory directory created
        assert memory_dir.exists()
        assert memory_dir.is_dir()

        # Verify subdirectories created
        assert (memory_dir / "sqlite").exists()
        assert (memory_dir / "chroma").exists()

        # Verify can store and retrieve data
        hmc.set_fact("test_key", "test_value")
        assert hmc.get_fact("test_key") == "test_value"

    def test_seed_empty_project_graceful_skip(self, empty_project):
        """Test seeding empty project (no persona.md) handles gracefully."""
        stats = seed_project(
            project_path=empty_project,
            memory_dir=Path(".hmc_memory"),
            project_id="empty-project",
            verbose=False,
        )

        # Should complete without persona data
        assert stats["persona_facts"] == 0
        assert stats["persona_voices"] == 0

        # Should still create structure and track metadata
        assert stats["project_facts"] >= 2  # at least project_structure and tech_stack

        # Verify memory directory created
        memory_dir = empty_project / ".hmc_memory"
        assert memory_dir.exists()

    def test_manual_persona_storage(self, temp_dir):
        """Test manually storing persona attributes in greenfield setup."""
        hmc = HybridMemoryCore(project_id="manual-persona", db_directory=temp_dir)

        # Manually store persona attributes
        hmc.set_fact("__persona_name__", "DevAssistant")
        hmc.set_fact("__persona_role__", "A coding assistant for Python projects")
        hmc.set_fact("__persona_tone__", "Professional and helpful")
        hmc.set_fact("__persona_language_rule__", "Respond in English")

        # Verify stored
        assert hmc.get_fact("__persona_name__") == "DevAssistant"
        assert hmc.get_fact("__persona_role__") == "A coding assistant for Python projects"
        assert hmc.get_fact("__persona_tone__") == "Professional and helpful"
        assert hmc.get_fact("__persona_language_rule__") == "Respond in English"

    def test_manual_voice_example_embedding(self, temp_dir):
        """Test manually embedding voice examples in greenfield setup."""
        hmc = HybridMemoryCore(project_id="manual-voices", db_directory=temp_dir)

        # Manually embed voice examples
        voice_examples = [
            "I can help you write clean Python code.",
            "Let me review your implementation for best practices.",
            "Here's a better approach to this problem.",
        ]

        for example in voice_examples:
            doc_id = hmc.add_semantic(example, metadata={"type": "persona_voice"})
            assert doc_id is not None

        # Verify can query voice examples
        results = hmc.query_semantic("help with code", k=5, filter={"type": "persona_voice"})

        assert len(results) > 0

    def test_persistence_verification(self, temp_dir):
        """Test data persists across HMC re-initialization."""
        project_id = "persistence-test"

        # Session 1: Store data
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)

        hmc1.set_fact("persistent_fact", "persistent_value")
        hmc1.add_semantic("Persistent semantic content", metadata={"type": "test"})

        # Session 2: Verify data persists
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)

        assert hmc2.get_fact("persistent_fact") == "persistent_value"

        results = hmc2.query_semantic("persistent semantic", k=5)
        assert len(results) > 0
        assert "Persistent semantic content" in results[0]["content"]

    def test_idempotent_initialization(self, temp_dir):
        """Test that initializing HMC multiple times is safe."""
        project_id = "idempotent-test"

        # Initialize multiple times
        hmc1 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc2 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        hmc3 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)

        # Store with first instance
        hmc1.set_fact("test", "value1")

        # Should be accessible from all instances
        assert hmc2.get_fact("test") == "value1"
        assert hmc3.get_fact("test") == "value1"

        # Update with second instance
        hmc2.set_fact("test", "value2")

        # All should see update
        hmc4 = HybridMemoryCore(project_id=project_id, db_directory=temp_dir)
        assert hmc4.get_fact("test") == "value2"

    def test_greenfield_to_brownfield_transition(self, empty_project):
        """Test transitioning from greenfield to brownfield workflow."""
        memory_dir = empty_project / ".hmc_memory"

        # Stage 1: Greenfield - manual setup
        hmc = HybridMemoryCore(project_id="transition-test", db_directory=memory_dir)

        hmc.set_fact("__persona_name__", "CodeHelper")
        hmc.add_semantic(
            "I can assist with your development tasks.", metadata={"type": "persona_voice"}
        )

        # Stage 2: Add project files
        (empty_project / "main.py").write_text(
            """def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""
        )

        (empty_project / "requirements.txt").write_text("pytest>=7.0.0\n")

        # Stage 3: Seed as brownfield project
        stats = seed_project(
            project_path=empty_project,
            memory_dir=Path(".hmc_memory"),
            project_id="transition-test",
            verbose=False,
        )

        # Should have found code and dependencies
        assert stats["code_chunks"] > 0
        assert stats["files_processed"] > 0

        # Original persona data should still exist
        hmc2 = HybridMemoryCore(project_id="transition-test", db_directory=memory_dir)
        assert hmc2.get_fact("__persona_name__") == "CodeHelper"

    def test_multiple_independent_projects(self, temp_dir):
        """Test multiple greenfield projects remain independent."""
        # Project A
        hmc_a = HybridMemoryCore(project_id="project-a", db_directory=temp_dir / "project_a")
        hmc_a.set_fact("project_name", "Project A")
        hmc_a.add_semantic("Content from project A", {"project": "a"})

        # Project B
        hmc_b = HybridMemoryCore(project_id="project-b", db_directory=temp_dir / "project_b")
        hmc_b.set_fact("project_name", "Project B")
        hmc_b.add_semantic("Content from project B", {"project": "b"})

        # Verify isolation
        assert hmc_a.get_fact("project_name") == "Project A"
        assert hmc_b.get_fact("project_name") == "Project B"

        results_a = hmc_a.query_semantic("content", k=5)
        results_b = hmc_b.query_semantic("content", k=5)

        assert all("project A" in r["content"] for r in results_a)
        assert all("project B" in r["content"] for r in results_b)

    def test_minimal_greenfield_workflow(self, temp_dir):
        """Test minimal greenfield workflow for quick setup."""
        # Initialize
        hmc = HybridMemoryCore(project_id="minimal", db_directory=temp_dir)

        # Set only essential persona attributes
        hmc.set_fact("__persona_name__", "Assistant")
        hmc.set_fact("__persona_role__", "General assistant")

        # Add one voice example
        hmc.add_semantic("I'm here to help!", metadata={"type": "persona_voice"})

        # Verify functional
        assert hmc.get_fact("__persona_name__") == "Assistant"

        results = hmc.query_semantic("help", k=1)
        assert len(results) > 0

    def test_greenfield_with_initial_documents(self, temp_dir):
        """Test greenfield setup with initial workflow documents."""
        hmc = HybridMemoryCore(project_id="with-docs", db_directory=temp_dir)

        # Add initial project documents
        hmc.add_semantic(
            "Project vision: Build a task management app",
            metadata={"type": "vision", "status": "draft"},
        )

        hmc.add_semantic(
            "Specification: User authentication required",
            metadata={"type": "spec", "feature": "auth", "status": "draft"},
        )

        hmc.add_semantic(
            "Plan: Start with login screen UI",
            metadata={"type": "plan", "feature": "auth", "status": "draft"},
        )

        # Track project state
        hmc.set_fact("project_phase", "planning")
        hmc.set_fact("active_features", ["auth"])

        # Verify documents stored
        docs = hmc.query_semantic("project", k=10)
        assert len(docs) >= 3

        # Verify state tracked
        assert hmc.get_fact("project_phase") == "planning"
        assert hmc.get_fact("active_features") == ["auth"]

    def test_seed_creates_consistent_structure(self, empty_project):
        """Test that seed creates consistent directory structure."""
        seed_project(
            project_path=empty_project,
            memory_dir=Path(".hmc_memory"),
            project_id="consistent-test",
            verbose=False,
        )

        memory_dir = empty_project / ".hmc_memory"

        # Verify structure
        assert memory_dir.exists()
        assert memory_dir.is_dir()

        # Check for expected subdirectories/files
        assert (memory_dir / "sqlite").exists()
        assert (memory_dir / "sqlite" / "facts.db").exists()
        assert (memory_dir / "chroma").exists()

    def test_empty_project_metadata(self, empty_project):
        """Test that empty project still stores seeding metadata."""
        seed_project(
            project_path=empty_project,
            memory_dir=Path(".hmc_memory"),
            project_id="metadata-test",
            verbose=False,
        )

        hmc = HybridMemoryCore(
            project_id="metadata-test", db_directory=empty_project / ".hmc_memory"
        )

        # Should have metadata even for empty project
        project_root = hmc.get_fact("__project_root__")
        assert project_root is not None
        assert str(empty_project) in project_root

        seeded_at = hmc.get_fact("__seeded_at__")
        assert seeded_at is not None

        hmc_version = hmc.get_fact("__hmc_version__")
        assert hmc_version is not None

    def test_incremental_content_addition(self, temp_dir):
        """Test adding content incrementally to greenfield project."""
        hmc = HybridMemoryCore(project_id="incremental", db_directory=temp_dir)

        # Week 1: Basic setup
        hmc.set_fact("__persona_name__", "DevBot")

        # Week 2: Add voice examples
        hmc.add_semantic("Let me help you code.", metadata={"type": "persona_voice"})

        # Week 3: Add project docs
        hmc.add_semantic("Project spec v1", metadata={"type": "spec"})

        # Week 4: Add more metadata
        hmc.set_fact("team_size", 5)
        hmc.set_fact("tech_stack", {"language": "python", "framework": "fastapi"})

        # Verify all data accessible
        assert hmc.get_fact("__persona_name__") == "DevBot"
        assert hmc.get_fact("team_size") == 5

        voice_results = hmc.query_semantic("help", k=5, filter={"type": "persona_voice"})
        assert len(voice_results) > 0

        spec_results = hmc.query_semantic("spec", k=5, filter={"type": "spec"})
        assert len(spec_results) > 0
