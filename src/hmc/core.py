"""Core Hybrid Memory API.

This module provides the main HybridMemoryCore class that coordinates
factual and semantic storage through a unified interface.
"""

import re
from pathlib import Path
from typing import Any

from hmc.backends import ChromaSemanticStore, SQLiteFactualStore
from hmc.exceptions import ValidationError
from hmc.interfaces import FactualStorage, SemanticStorage


class HybridMemoryCore:
    """Main API for hybrid memory operations.

    Coordinates factual (key-value) and semantic (vector) storage through
    a unified interface. Supports dependency injection for custom backends.

    Args:
        project_id: Unique identifier (alphanumeric, hyphens, underscores)
        db_directory: Path to memory storage directory (default: "./.hmc_memory")
        factual_store: Optional custom factual storage backend
        semantic_store: Optional custom semantic storage backend

    Example:
        >>> memory = HybridMemoryCore(project_id="my-project")
        >>> memory.set_fact("key", "value")
        >>> memory.add_semantic("Important note", {"type": "note"})
        >>> results = memory.query_semantic("note", k=5)
    """

    def __init__(
        self,
        project_id: str,
        db_directory: str | Path = "./.hmc_memory",
        factual_store: FactualStorage | None = None,
        semantic_store: SemanticStorage | None = None,
    ) -> None:
        """Initialize Hybrid Memory Core.

        Args:
            project_id: Unique project identifier
            db_directory: Path to storage directory
            factual_store: Optional custom factual storage implementation
            semantic_store: Optional custom semantic storage implementation

        Raises:
            ValidationError: If project_id format is invalid
            StorageError: If backend initialization fails
        """
        # Validate project_id
        if not project_id or not isinstance(project_id, str):
            raise ValidationError("project_id must be a non-empty string", field="project_id")

        # Project ID must be alphanumeric with hyphens/underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", project_id):
            raise ValidationError(
                "project_id must contain only alphanumeric characters, hyphens, and underscores",
                field="project_id",
            )

        self.project_id = project_id
        self.db_directory = Path(db_directory)

        # Create storage directory if needed
        self.db_directory.mkdir(parents=True, exist_ok=True)

        # Initialize or inject storage backends
        if factual_store is None:
            sqlite_path = self.db_directory / "sqlite" / "facts.db"
            self.factual_store: FactualStorage = SQLiteFactualStore(db_path=sqlite_path)
        else:
            self.factual_store = factual_store

        if semantic_store is None:
            chroma_path = self.db_directory / "chroma"
            self.semantic_store: SemanticStorage = ChromaSemanticStore(
                collection_name=project_id, persist_directory=chroma_path
            )
        else:
            self.semantic_store = semantic_store

        # Setup both backends (idempotent)
        self.factual_store.setup()
        self.semantic_store.setup()

    def set_fact(self, key: str, value: Any) -> None:
        """Store a factual key-value pair.

        Args:
            key: Non-empty string identifier
            value: JSON-serializable value

        Raises:
            ValidationError: If key is empty or value not JSON-serializable
            StorageError: If storage operation fails
        """
        self.factual_store.set_fact(key, value)

    def get_fact(self, key: str) -> Any | None:
        """Retrieve a factual value by key.

        Args:
            key: String identifier

        Returns:
            Stored value if key exists, None otherwise

        Raises:
            ValidationError: If key is empty
            StorageError: If retrieval operation fails
        """
        return self.factual_store.get_fact(key)

    def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        """Add content to semantic storage with automatic embedding.

        Args:
            content: Non-empty text content to embed
            metadata: Dictionary with metadata (e.g., {"type": "spec", "feature": "login"})

        Returns:
            Unique document ID (UUID)

        Raises:
            ValidationError: If content is empty or metadata invalid
            StorageError: If embedding or storage fails
        """
        return self.semantic_store.add_semantic(content, metadata)

    def query_semantic(
        self, query_text: str, k: int = 5, filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Perform semantic similarity search.

        Args:
            query_text: Query string for semantic search
            k: Number of results to return (default: 5, must be > 0)
            filter: Optional metadata filter (e.g., {"type": "spec", "status": "approved"})

        Returns:
            List of result dictionaries, each containing:
                - "content": Original text content
                - "metadata": Associated metadata dictionary
                - "distance": Similarity distance (lower = more similar)

        Raises:
            ValidationError: If query_text is empty or k <= 0
            StorageError: If search operation fails
        """
        return self.semantic_store.query_semantic(query_text, k, filter)
