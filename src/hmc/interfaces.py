"""Abstract interfaces for storage backends.

This module defines Abstract Base Classes (ABCs) that establish contracts
for factual and semantic storage implementations. This enables backend
swappability while maintaining a consistent API.
"""

from abc import ABC, abstractmethod
from typing import Any


class FactualStorage(ABC):
    """Abstract interface for factual (key-value) storage backends.

    Implementations must provide persistent key-value storage with JSON-serializable
    values. Keys are strings, values can be any JSON-compatible Python type.

    Examples:
        >>> class MyFactualStore(FactualStorage):
        ...     def setup(self) -> None:
        ...         # Initialize storage
        ...         pass
        ...     def set_fact(self, key: str, value: Any) -> None:
        ...         # Store key-value pair
        ...         pass
        ...     def get_fact(self, key: str) -> Any | None:
        ...         # Retrieve value or None
        ...         return None
    """

    @abstractmethod
    def setup(self) -> None:
        """Initialize the storage backend.

        This method should be idempotent - safe to call multiple times.
        Creates necessary database tables, files, or connections.

        Raises:
            StorageError: If setup fails
        """
        pass

    @abstractmethod
    def set_fact(self, key: str, value: Any) -> None:
        """Store a factual key-value pair.

        If the key already exists, its value should be updated (upsert behavior).
        Values must be JSON-serializable.

        Args:
            key: Non-empty string identifier
            value: JSON-serializable value (str, int, float, bool, list, dict, None)

        Raises:
            ValidationError: If key is empty or value is not JSON-serializable
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    def get_fact(self, key: str) -> Any | None:
        """Retrieve a factual value by key.

        Args:
            key: String identifier for the fact

        Returns:
            The stored value if key exists, None otherwise

        Raises:
            ValidationError: If key is empty
            StorageError: If retrieval operation fails
        """
        pass


class SemanticStorage(ABC):
    """Abstract interface for semantic (vector) storage backends.

    Implementations must provide embedding generation and similarity search
    capabilities with metadata filtering support.

    Examples:
        >>> class MySemanticStore(SemanticStorage):
        ...     def setup(self) -> None:
        ...         pass
        ...     def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        ...         return "doc-id-123"
        ...     def query_semantic(
        ...         self, query_text: str, k: int = 5, filter: dict[str, Any] | None = None
        ...     ) -> list[dict[str, Any]]:
        ...         return []
    """

    @abstractmethod
    def setup(self) -> None:
        """Initialize the semantic storage backend.

        This method should be idempotent - safe to call multiple times.
        Creates necessary collections, indexes, or connections.

        Raises:
            StorageError: If setup fails
        """
        pass

    @abstractmethod
    def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        """Add content to semantic storage with automatic embedding generation.

        Args:
            content: Non-empty text content to embed
            metadata: Dictionary with string keys containing metadata
                     (e.g., {"type": "spec", "feature": "login", "source_file": "spec.md"})

        Returns:
            Unique document ID (UUID or similar)

        Raises:
            ValidationError: If content is empty or metadata has invalid structure
            StorageError: If embedding or storage operation fails
        """
        pass

    @abstractmethod
    def query_semantic(
        self, query_text: str, k: int = 5, filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Perform semantic similarity search.

        Args:
            query_text: Text query to search for semantically similar content
            k: Number of results to return (must be > 0)
            filter: Optional metadata filter dictionary (e.g., {"type": "spec"})
                   Only documents matching ALL filter criteria are returned

        Returns:
            List of result dictionaries, each containing:
                - "content": The original text content
                - "metadata": The associated metadata dictionary
                - "distance": Similarity distance (lower is more similar)

        Raises:
            ValidationError: If query_text is empty or k <= 0
            StorageError: If search operation fails
        """
        pass
