"""Hybrid Memory Core (HMC) - Persistent hybrid memory system for AI agents.

This package provides a hybrid memory system combining:
- Factual storage: Key-value pairs using SQLite3
- Semantic storage: Vector embeddings using ChromaDB

Example:
    >>> from hmc import HybridMemoryCore
    >>> memory = HybridMemoryCore(project_id="my-project")
    >>> memory.set_fact("key", "value")
    >>> memory.add_semantic("Important content", {"type": "note"})
"""

__version__ = "1.0.0"

from hmc.core import HybridMemoryCore
from hmc.exceptions import HMCError, SeederError, StorageError, ValidationError

__all__ = [
    "HybridMemoryCore",
    "HMCError",
    "StorageError",
    "ValidationError",
    "SeederError",
]
