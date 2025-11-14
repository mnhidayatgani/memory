"""Integration tests for brownfield seeding workflow."""

import tempfile
from pathlib import Path

import pytest

from hmc.core import HybridMemoryCore
from hmc.seeder import seed_project


class TestSeederBrownfield:
    """Integration tests for seeding existing projects."""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "sample_project"
            project_dir.mkdir()
            
            # Create persona.md
            persona_md = project_dir / "persona.md"
            persona_md.write_text("""# Persona: Test Assistant

## Factual
- name: TestBot
- role: A testing assistant for automation
- tone: Professional, concise, helpful
- user_title: User
- core_directive: Assist with testing workflows
- language_rule: Respond in English

## Semantic (Voice Examples)
- "I've completed the test suite analysis."
- "The integration tests are passing successfully."
- "Let me help you debug that issue."
""")
            
            # Create requirements.txt
            requirements_txt = project_dir / "requirements.txt"
            requirements_txt.write_text("""pytest>=7.4.0
black>=23.0.0
# This is a comment
mypy>=1.5.0
""")
            
            # Create pyproject.toml
            pyproject_toml = project_dir / "pyproject.toml"
            pyproject_toml.write_text("""[project]
name = "sample"
dependencies = ["requests>=2.28.0", "pydantic>=2.0.0"]
""")
            
            # Create source files
            src_dir = project_dir / "src"
            src_dir.mkdir()
            
            (src_dir / "main.py").write_text("""def main():
    \"\"\"Main entry point.\"\"\"
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""")
            
            (src_dir / "utils.py").write_text("""def helper_function(x, y):
    \"\"\"Add two numbers.\"\"\"
    return x + y

def another_helper():
    \"\"\"Do something useful.\"\"\"
    pass
""")
            
            # Create README
            readme = project_dir / "README.md"
            readme.write_text("""# Sample Project

This is a test project for seeding.

## Features
- Feature A
- Feature B
""")
            
            yield project_dir

    def test_seed_complete_project(self, sample_project):
        """Test seeding a complete project with all components."""
        memory_dir = sample_project / ".hmc_memory"
        
        stats = seed_project(
            project_path=sample_project,
            memory_dir=memory_dir,
            project_id="test-project",
            verbose=False
        )
        
        # Verify statistics
        assert stats["persona_facts"] == 6  # All factual attributes
        assert stats["persona_voices"] == 3  # Three voice examples
        assert stats["project_facts"] >= 2  # tech_stack and project_structure
        assert stats["code_chunks"] > 0  # Should have embedded some code
        assert stats["files_processed"] >= 3  # main.py, utils.py, README.md
        
        # Verify memory directory created
        assert memory_dir.exists()
        assert (memory_dir / "sqlite" / "facts.db").exists()
        assert (memory_dir / "chroma").exists()

    def test_persona_facts_stored(self, sample_project):
        """Test that persona factual attributes are correctly stored."""
        seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-persona",
            verbose=False
        )
        
        # Initialize HMC and verify persona facts
        hmc = HybridMemoryCore(
            project_id="test-persona",
            db_directory=sample_project / ".hmc_memory"
        )
        
        assert hmc.get_fact("__persona_name__") == "TestBot"
        assert hmc.get_fact("__persona_role__") == "A testing assistant for automation"
        assert hmc.get_fact("__persona_tone__") == "Professional, concise, helpful"
        assert hmc.get_fact("__persona_user_title__") == "User"
        assert hmc.get_fact("__persona_core_directive__") == "Assist with testing workflows"
        assert hmc.get_fact("__persona_language_rule__") == "Respond in English"

    def test_persona_voices_embedded(self, sample_project):
        """Test that persona voice examples are semantically embedded."""
        seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-voices",
            verbose=False
        )
        
        hmc = HybridMemoryCore(
            project_id="test-voices",
            db_directory=sample_project / ".hmc_memory"
        )
        
        # Query for voice examples
        results = hmc.query_semantic(
            "test suite analysis",
            k=5,
            filter={"type": "persona_voice"}
        )
        
        assert len(results) > 0
        # Should find the voice example about test suite
        contents = [r["content"] for r in results]
        assert any("test suite" in c.lower() for c in contents)

    def test_tech_stack_extracted(self, sample_project):
        """Test that technology stack is extracted from dependency files."""
        seed_project(
            project_path=sample_project,
            memory_dir=sample_project / ".hmc_memory",
            project_id="test-tech",
            verbose=False
        )
        
        hmc = HybridMemoryCore(
            project_id="test-tech",
            db_directory=sample_project / ".hmc_memory"
        )
        
        tech_stack = hmc.get_fact("__tech_stack__")
        assert tech_stack is not None
        assert isinstance(tech_stack, list)
        
        # Should have dependencies from requirements.txt and pyproject.toml
        assert any("pytest" in d for d in tech_stack)
        assert any("black" in d for d in tech_stack)
        assert any("mypy" in d for d in tech_stack)
        assert any("requests" in d for d in tech_stack)
        assert any("pydantic" in d for d in tech_stack)

    def test_project_structure_stored(self, sample_project):
        """Test that project structure is scanned and stored."""
        seed_project(
            project_path=sample_project,
            memory_dir=sample_project / ".hmc_memory",
            project_id="test-structure",
            verbose=False
        )
        
        hmc = HybridMemoryCore(
            project_id="test-structure",
            db_directory=sample_project / ".hmc_memory"
        )
        
        structure = hmc.get_fact("__project_structure__")
        assert structure is not None
        assert isinstance(structure, dict)
        
        # Verify structure components
        assert "total_files" in structure
        assert "total_dirs" in structure
        assert "file_types" in structure
        
        # Should have found files
        assert structure["total_files"] > 0
        assert structure["total_dirs"] >= 0
        
        # Should have found Python files
        file_types = structure["file_types"]
        assert ".py" in file_types

    def test_code_chunks_embedded(self, sample_project):
        """Test that source files are chunked and embedded."""
        seed_project(
            project_path=sample_project,
            memory_dir=sample_project / ".hmc_memory",
            project_id="test-code",
            verbose=False
        )
        
        hmc = HybridMemoryCore(
            project_id="test-code",
            db_directory=sample_project / ".hmc_memory"
        )
        
        # Search for main function
        results = hmc.query_semantic(
            "main entry point",
            k=5,
            filter={"type": "code_chunk"}
        )
        
        assert len(results) > 0
        
        # Verify metadata
        result = results[0]
        assert "source_file" in result["metadata"]
        assert "chunk_index" in result["metadata"]
        assert "language" in result["metadata"]
        assert result["metadata"]["language"] == "python"

    def test_semantic_search_for_code(self, sample_project):
        """Test semantic search finds relevant code chunks."""
        seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-search",
            verbose=False
        )
        
        hmc = HybridMemoryCore(
            project_id="test-search",
            db_directory=sample_project / ".hmc_memory"
        )
        
        # Search for helper function
        results = hmc.query_semantic(
            "helper function add numbers",
            k=3,
            filter={"type": "code_chunk"}
        )
        
        assert len(results) > 0
        # Should find utils.py content
        assert any("helper_function" in r["content"] for r in results)

    def test_multiple_seeding_runs(self, sample_project):
        """Test that multiple seeding runs work (upsert behavior)."""
        # First seeding
        stats1 = seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-multi",
            verbose=False
        )
        
        # Second seeding (should update)
        stats2 = seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-multi",
            verbose=False
        )
        
        # Stats should be similar
        assert stats2["persona_facts"] == stats1["persona_facts"]
        assert stats2["files_processed"] == stats1["files_processed"]
        
        # Data should still be accessible
        hmc = HybridMemoryCore(
            project_id="test-multi",
            db_directory=sample_project / ".hmc_memory"
        )
        assert hmc.get_fact("__persona_name__") == "TestBot"

    def test_seeding_without_persona(self, sample_project):
        """Test seeding works gracefully without persona.md."""
        # Remove persona.md
        (sample_project / "persona.md").unlink()
        
        stats = seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-no-persona",
            verbose=False
        )
        
        # Should still process project
        assert stats["persona_facts"] == 0
        assert stats["persona_voices"] == 0
        assert stats["project_facts"] >= 2  # Still has tech_stack and structure
        assert stats["code_chunks"] > 0

    def test_metadata_facts_stored(self, sample_project):
        """Test that seeding metadata is stored."""
        seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-metadata",
            verbose=False
        )
        
        hmc = HybridMemoryCore(
            project_id="test-metadata",
            db_directory=sample_project / ".hmc_memory"
        )
        
        # Check metadata facts
        project_root = hmc.get_fact("__project_root__")
        assert project_root is not None
        assert str(sample_project) in project_root
        
        seeded_at = hmc.get_fact("__seeded_at__")
        assert seeded_at is not None
        
        hmc_version = hmc.get_fact("__hmc_version__")
        assert hmc_version is not None

    def test_verbose_mode(self, sample_project, capsys):
        """Test that verbose mode produces output."""
        seed_project(
            project_path=sample_project,
            memory_dir=Path(".hmc_memory"),
            project_id="test-verbose",
            verbose=True
        )
        
        captured = capsys.readouterr()
        # Should have printed progress
        assert "Seeding project" in captured.out
        assert "test-verbose" in captured.out
