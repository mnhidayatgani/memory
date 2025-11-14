"""Performance tests for HMC seeding and querying operations."""

import tempfile
import time
from pathlib import Path

import pytest

from hmc.core import HybridMemoryCore
from hmc.seeder import seed_project


class TestSeedingPerformance:
    """Performance tests for seeding operations."""

    @pytest.fixture
    def large_project(self):
        """Create a large sample project with 50 files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "large_project"
            project_dir.mkdir()

            # Create persona.md
            (project_dir / "persona.md").write_text(
                """# Project Persona

## Factual
- name: CodeAssistant
- role: Senior Python Developer
- tone: Professional and concise

## Semantic (Voice Examples)
- "I recommend using type hints for better code clarity"
- "Let's break this down into smaller functions"
"""
            )

            # Create requirements.txt
            (project_dir / "requirements.txt").write_text(
                """pytest>=7.0.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.5.0
chromadb>=0.4.0
"""
            )

            # Create 50 Python files with realistic content
            src_dir = project_dir / "src"
            src_dir.mkdir()

            for i in range(50):
                module_name = f"module_{i:02d}.py"
                content = f'''"""Module {i} - Business logic implementation."""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataProcessor{i}:
    """Process data for module {i}."""

    def __init__(self, config: Dict[str, str]) -> None:
        """Initialize processor with configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.results = []

    def process(self, data: List[str]) -> List[Dict]:
        """Process input data and return results.

        Args:
            data: List of input strings

        Returns:
            List of processed dictionaries
        """
        logger.info("Processing %d items in module {i}", len(data))
        results = []

        for item in data:
            processed = self._transform(item)
            if processed:
                results.append(processed)

        return results

    def _transform(self, item: str) -> Optional[Dict]:
        """Transform a single item.

        Args:
            item: Input string

        Returns:
            Transformed dictionary or None
        """
        if not item or len(item) < 3:
            return None

        return {{
            "original": item,
            "processed": item.upper(),
            "length": len(item),
            "module_id": {i}
        }}

    def validate(self, result: Dict) -> bool:
        """Validate a processed result.

        Args:
            result: Result dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_keys = ["original", "processed", "length", "module_id"]
        return all(key in result for key in required_keys)


def create_processor_{i}(config: Optional[Dict] = None) -> DataProcessor{i}:
    """Factory function for creating processor instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured DataProcessor{i} instance
    """
    if config is None:
        config = {{"mode": "default", "batch_size": "100"}}

    return DataProcessor{i}(config)


# Constants
MODULE_VERSION = "{i}.0.0"
MAX_BATCH_SIZE = 1000
DEFAULT_TIMEOUT = 30
'''
                (src_dir / module_name).write_text(content)

            yield project_dir

    @pytest.mark.slow
    def test_seed_50_file_project_performance(self, large_project):
        """Test that seeding a 50-file project completes in <30 seconds (SC-002)."""
        start_time = time.time()

        stats = seed_project(
            project_path=large_project,
            memory_dir=Path(".hmc_memory"),
            project_id="perf-test",
            verbose=False,
        )

        elapsed = time.time() - start_time

        # Verify completion
        assert stats["files_processed"] == 50
        assert stats["code_chunks"] > 0
        assert stats["persona_facts"] > 0

        # Performance requirement: <30 seconds
        assert (
            elapsed < 30.0
        ), f"Seeding took {elapsed:.2f}s, expected <30s (SC-002 requirement)"

        print(f"\n✅ Seeded 50 files in {elapsed:.2f}s")
        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Code chunks: {stats['code_chunks']}")
        print(f"   Persona facts: {stats['persona_facts']}")


class TestQueryPerformance:
    """Performance tests for query operations."""

    @pytest.fixture
    def populated_memory(self, tmp_path):
        """Create HMC with 10,000 semantic chunks."""
        memory = HybridMemoryCore(project_id="perf-test", db_directory=tmp_path)

        # Add 10,000 semantic chunks
        print("\nPopulating 10,000 semantic chunks...")
        for i in range(10000):
            content = f"""Function {i}: This is a function that processes data.
            It takes input parameters and returns processed results.
            Implementation includes error handling and logging.
            Used in module {i % 100} for batch processing tasks.
            """

            metadata = {
                "type": "code_chunk",
                "source_file": f"src/module_{i % 100}.py",
                "language": "python",
                "function_id": i,
                "module": i % 100,
            }

            memory.add_semantic(content, metadata)

            if (i + 1) % 1000 == 0:
                print(f"   Added {i + 1} chunks...")

        print("✅ Population complete")
        return memory

    @pytest.mark.slow
    def test_query_10k_chunks_performance(self, populated_memory):
        """Test that querying 10,000 chunks returns in <100ms (SC-009)."""
        memory = populated_memory

        # Warm-up query (first query may be slower)
        memory.query_semantic("process data", k=10)

        # Timed queries
        query_times = []
        num_queries = 10

        for i in range(num_queries):
            start_time = time.time()

            results = memory.query_semantic(
                query_text=f"function processing batch {i}", k=10
            )

            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            query_times.append(elapsed)

            assert len(results) > 0
            assert len(results) <= 10

        avg_query_time = sum(query_times) / len(query_times)
        max_query_time = max(query_times)
        min_query_time = min(query_times)

        # Performance requirement: <100ms
        assert (
            avg_query_time < 100.0
        ), f"Average query time {avg_query_time:.2f}ms, expected <100ms (SC-009)"

        print(f"\n✅ Query performance over {num_queries} queries:")
        print(f"   Average: {avg_query_time:.2f}ms")
        print(f"   Min: {min_query_time:.2f}ms")
        print(f"   Max: {max_query_time:.2f}ms")
        print(f"   All queries: {', '.join(f'{t:.1f}ms' for t in query_times)}")


class TestBackendSwappability:
    """Test that backends are swappable (SC-008)."""

    def test_mock_backend_injection(self, tmp_path):
        """Test that custom backends can be injected into HybridMemoryCore."""
        from unittest.mock import Mock

        from hmc.interfaces import FactualStorage, SemanticStorage

        # Create mock backends
        mock_factual = Mock(spec=FactualStorage)
        mock_semantic = Mock(spec=SemanticStorage)

        # Configure mocks
        mock_factual.setup.return_value = None
        mock_factual.set_fact.return_value = None
        mock_factual.get_fact.return_value = "test_value"

        mock_semantic.setup.return_value = None
        mock_semantic.add_semantic.return_value = "mock_doc_id"
        mock_semantic.query_semantic.return_value = [
            {"content": "test", "metadata": {}, "distance": 0.1}
        ]

        # Inject mocks into HMC
        memory = HybridMemoryCore(
            project_id="test",
            db_directory=tmp_path,
            factual_store=mock_factual,
            semantic_store=mock_semantic,
        )

        # Verify setup was called
        mock_factual.setup.assert_called_once()
        mock_semantic.setup.assert_called_once()

        # Test factual operations
        memory.set_fact("test_key", "test_value")
        mock_factual.set_fact.assert_called_once_with("test_key", "test_value")

        result = memory.get_fact("test_key")
        mock_factual.get_fact.assert_called_once_with("test_key")
        assert result == "test_value"

        # Test semantic operations
        doc_id = memory.add_semantic("test content", {"type": "test"})
        mock_semantic.add_semantic.assert_called_once_with(
            "test content", {"type": "test"}
        )
        assert doc_id == "mock_doc_id"

        results = memory.query_semantic("query", k=5)
        mock_semantic.query_semantic.assert_called_once()
        assert len(results) == 1

        print("\n✅ Backend swappability verified (SC-008)")
        print("   Custom backends successfully injected")
        print("   All operations delegated correctly")
