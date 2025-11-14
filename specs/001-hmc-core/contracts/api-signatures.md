# API Signatures: Hybrid Memory Core (HMC)

**Complete Python API Contracts**  
**Date**: 2025-11-14

All signatures include full type hints and placeholder docstrings per Constitution Principle 5.

---

## 1. interfaces.py - Abstract Base Classes

```python
"""Abstract interfaces for HMC storage backends.

This module defines the contracts that all storage backend implementations
must satisfy, enabling backend swappability per Constitution Principle 4.
"""

from abc import ABC, abstractmethod
from typing import Any


class FactualStorage(ABC):
    """Abstract base class for factual (key-value) storage backends.

    Implementations must provide persistent key-value storage with JSON
    serialization support for Python primitive types.
    """

    @abstractmethod
    def setup(self) -> None:
        """Initialize the storage backend.

        This method MUST be idempotent - safe to call multiple times.
        Creates necessary databases, tables, directories, etc.

        Raises:
            StorageError: If initialization fails (permissions, disk space, etc.)
        """
        pass

    @abstractmethod
    def set_fact(self, key: str, value: Any) -> None:
        """Store a key-value pair in factual storage.

        Uses upsert semantics - updates existing key if present.
        Value is JSON-serialized before storage.

        Args:
            key: Non-empty string identifier. Convention: use "__prefix_name__"
                 for reserved system keys (e.g., "__persona_name__").
            value: JSON-serializable value (str, int, float, bool, list, dict, None).

        Raises:
            ValidationError: If key is empty or value is not JSON-serializable.
            StorageError: If storage operation fails.
        """
        pass

    @abstractmethod
    def get_fact(self, key: str) -> Any | None:
        """Retrieve a value by key from factual storage.

        Args:
            key: The key to look up.

        Returns:
            The deserialized value if key exists, None otherwise.
            Return type matches the type originally passed to set_fact.

        Raises:
            ValidationError: If key is empty string.
            StorageError: If storage read fails.
        """
        pass


class SemanticStorage(ABC):
    """Abstract base class for semantic (vector) storage backends.

    Implementations must provide vector embedding storage with metadata
    filtering and similarity search capabilities.
    """

    @abstractmethod
    def setup(self) -> None:
        """Initialize the storage backend.

        This method MUST be idempotent - safe to call multiple times.
        Creates necessary collections, indices, etc.

        Raises:
            StorageError: If initialization fails.
        """
        pass

    @abstractmethod
    def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        """Store content with semantic embedding and metadata.

        The backend automatically generates embeddings from content using
        its configured embedding model.

        Args:
            content: Non-empty text to embed and store.
            metadata: Metadata dict with string keys. Common keys:
                      - type: "persona_voice", "code_chunk", "spec", "plan", "task"
                      - source_file: relative path from project root
                      - feature: feature identifier
                      - status: "draft", "approved", "complete", "archived"

        Returns:
            Unique ID for the stored embedding (UUID or backend-generated).

        Raises:
            ValidationError: If content is empty or metadata invalid.
            StorageError: If storage operation fails.
        """
        pass

    @abstractmethod
    def query_semantic(
        self,
        query_text: str,
        k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Query for semantically similar content.

        Searches for content similar to query_text, optionally filtered by metadata.

        Args:
            query_text: Text to search for (embedded and compared to stored content).
            k: Maximum number of results to return. Must be > 0.
            filter: Optional metadata filter. Examples:
                    - {"type": "spec"} - only specs
                    - {"type": "plan", "feature": "login"} - login plans only
                    Backend may support operators like {"distance": {"$lt": 0.5}}.

        Returns:
            List of dicts with keys:
                - id: str - embedding ID
                - content: str - original text content
                - metadata: dict - all stored metadata
                - distance: float - similarity score (lower = more similar for L2 distance)
            Sorted by similarity (most similar first).

        Raises:
            ValidationError: If k <= 0 or filter has invalid keys.
            StorageError: If query operation fails.
        """
        pass
```

---

## 2. backends.py - Concrete Implementations

```python
"""Concrete storage backend implementations for HMC.

This module provides SQLite3 and ChromaDB implementations of the
FactualStorage and SemanticStorage interfaces.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from .interfaces import FactualStorage, SemanticStorage
from .exceptions import StorageError, ValidationError


class SQLiteFactualStore(FactualStorage):
    """SQLite3-backed factual storage implementation.

    Stores key-value pairs in a single SQLite database file using JSON
    serialization for values. Thread-safe via SQLite's default isolation.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize SQLite factual store.

        Args:
            db_path: Path where SQLite database file will be created.
                     Parent directory must exist and be writable.
        """
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection (lazy initialization).

        Returns:
            Active SQLite connection.

        Raises:
            StorageError: If connection cannot be established.
        """
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(str(self.db_path))
                self._conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                raise StorageError(f"Failed to connect to database: {e}") from e
        return self._conn

    def setup(self) -> None:
        """Create facts table if it doesn't exist.

        Schema:
            CREATE TABLE facts (
                key TEXT PRIMARY KEY,
                json_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

        Raises:
            StorageError: If table creation fails.
        """
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    key TEXT PRIMARY KEY,
                    json_value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create facts table: {e}") from e

    def set_fact(self, key: str, value: Any) -> None:
        """Store key-value pair with JSON serialization.

        Uses INSERT OR REPLACE for upsert semantics.

        Args:
            key: Non-empty string key.
            value: JSON-serializable value.

        Raises:
            ValidationError: If key is empty or value not JSON-serializable.
            StorageError: If database write fails.
        """
        if not key or not isinstance(key, str):
            raise ValidationError("Key must be non-empty string")

        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Value must be JSON-serializable: {e}") from e

        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO facts (key, json_value, updated_at) "
                "VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, json_value)
            )
            conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to store fact: {e}") from e

    def get_fact(self, key: str) -> Any | None:
        """Retrieve and deserialize value by key.

        Args:
            key: The key to look up.

        Returns:
            Deserialized value if key exists, None otherwise.

        Raises:
            ValidationError: If key is empty.
            StorageError: If database read fails or JSON invalid.
        """
        if not key or not isinstance(key, str):
            raise ValidationError("Key must be non-empty string")

        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT json_value FROM facts WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return json.loads(row['json_value'])
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve fact: {e}") from e
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON in database: {e}") from e

    def close(self) -> None:
        """Close database connection.

        Should be called when done with the store, or use as context manager.
        """
        if self._conn:
            self._conn.close()
            self._conn = None


class ChromaSemanticStore(SemanticStorage):
    """ChromaDB-backed semantic storage implementation.

    Stores text embeddings with metadata using ChromaDB's persistent client.
    Supports similarity search with metadata filtering.

    Attributes:
        collection_name: Name of ChromaDB collection (typically project_id).
        persist_directory: Directory where ChromaDB stores data.
    """

    def __init__(self, collection_name: str, persist_directory: str | Path) -> None:
        """Initialize ChromaDB semantic store.

        Args:
            collection_name: Unique collection name (alphanumeric + hyphens/underscores).
            persist_directory: Directory for ChromaDB persistent storage.
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self._client: chromadb.PersistentClient | None = None
        self._collection: chromadb.Collection | None = None

    def _get_client(self) -> chromadb.PersistentClient:
        """Get or create ChromaDB client (lazy initialization).

        Returns:
            Active ChromaDB persistent client.

        Raises:
            StorageError: If client cannot be initialized.
        """
        if self._client is None:
            try:
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_directory)
                )
            except Exception as e:
                raise StorageError(f"Failed to initialize ChromaDB client: {e}") from e
        return self._client

    def _get_collection(self) -> chromadb.Collection:
        """Get or create ChromaDB collection (lazy initialization).

        Returns:
            Active ChromaDB collection.

        Raises:
            StorageError: If collection cannot be accessed.
        """
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_or_create_collection(
                    name=self.collection_name
                )
            except Exception as e:
                raise StorageError(f"Failed to access collection: {e}") from e
        return self._collection

    def setup(self) -> None:
        """Ensure collection exists (idempotent).

        Creates collection if it doesn't exist. Safe to call multiple times.

        Raises:
            StorageError: If setup fails.
        """
        # Accessing collection via _get_collection creates it if needed
        _ = self._get_collection()

    def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        """Add content with automatic embedding generation.

        Args:
            content: Text to embed and store.
            metadata: Metadata dict with string keys and primitive values.

        Returns:
            Generated UUID for the embedding.

        Raises:
            ValidationError: If content empty or metadata invalid.
            StorageError: If ChromaDB add fails.
        """
        if not content or not isinstance(content, str):
            raise ValidationError("Content must be non-empty string")

        if not isinstance(metadata, dict):
            raise ValidationError("Metadata must be dict")

        # Validate metadata keys are strings
        if not all(isinstance(k, str) for k in metadata.keys()):
            raise ValidationError("All metadata keys must be strings")

        collection = self._get_collection()
        embedding_id = str(uuid.uuid4())

        try:
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[embedding_id]
            )
        except Exception as e:
            raise StorageError(f"Failed to add semantic content: {e}") from e

        return embedding_id

    def query_semantic(
        self,
        query_text: str,
        k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Query for similar content with optional metadata filtering.

        Args:
            query_text: Text to search for.
            k: Number of results to return.
            filter: Optional metadata filter dict.

        Returns:
            List of result dicts with id, content, metadata, distance.

        Raises:
            ValidationError: If query_text empty or k <= 0.
            StorageError: If query fails.
        """
        if not query_text or not isinstance(query_text, str):
            raise ValidationError("Query text must be non-empty string")

        if k <= 0:
            raise ValidationError("k must be positive integer")

        collection = self._get_collection()

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=k,
                where=filter  # ChromaDB metadata filter
            )
        except Exception as e:
            raise StorageError(f"Failed to query semantic content: {e}") from e

        # Transform ChromaDB results to our standard format
        output = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                output.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results.get('distances') else None
                })

        return output
```

---

## 3. core.py - HybridMemoryCore Main API

```python
"""Main HybridMemoryCore API facade.

This module provides the unified interface that coordinates factual and
semantic storage backends.
"""

from pathlib import Path
from typing import Any

from .interfaces import FactualStorage, SemanticStorage
from .backends import SQLiteFactualStore, ChromaSemanticStore
from .exceptions import ValidationError, StorageError


class HybridMemoryCore:
    """Unified API for hybrid memory management.

    Coordinates factual (key-value) and semantic (vector) storage through
    a single interface. Implements Constitution Principle 4 (Strict Abstraction)
    by depending only on storage interfaces, not concrete implementations.

    Attributes:
        project_id: Unique identifier for this memory instance.
        db_directory: Root directory for all storage files.

    Example:
        >>> hmc = HybridMemoryCore(project_id="my_agent", db_directory=".hmc_memory")
        >>> hmc.set_fact("__persona_name__", "Jarvis")
        >>> hmc.add_semantic("Hello, Sir.", metadata={"type": "persona_voice"})
        >>> results = hmc.query_semantic("greeting", k=5, filter={"type": "persona_voice"})
    """

    def __init__(
        self,
        project_id: str,
        db_directory: str | Path = ".hmc_memory",
        factual_store: FactualStorage | None = None,
        semantic_store: SemanticStorage | None = None
    ) -> None:
        """Initialize HybridMemoryCore with storage backends.

        By default, uses SQLiteFactualStore and ChromaSemanticStore. Custom
        implementations can be provided via dependency injection for testing
        or alternative backends.

        Args:
            project_id: Unique project identifier (alphanumeric + hyphens/underscores).
            db_directory: Directory for all storage files. Created if doesn't exist.
            factual_store: Optional custom FactualStorage implementation.
            semantic_store: Optional custom SemanticStorage implementation.

        Raises:
            ValidationError: If project_id invalid or db_directory not writable.
            StorageError: If backend initialization fails.
        """
        # Validate project_id
        if not project_id or not isinstance(project_id, str):
            raise ValidationError("project_id must be non-empty string")

        if not project_id.replace('-', '').replace('_', '').isalnum():
            raise ValidationError(
                "project_id must be alphanumeric with hyphens/underscores only"
            )

        self.project_id = project_id
        self.db_directory = Path(db_directory)

        # Create directory if doesn't exist
        try:
            self.db_directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValidationError(f"Cannot create db_directory: {e}") from e

        # Initialize storage backends (dependency injection or defaults)
        if factual_store is None:
            factual_store = SQLiteFactualStore(
                db_path=self.db_directory / "facts.db"
            )

        if semantic_store is None:
            semantic_store = ChromaSemanticStore(
                collection_name=project_id,
                persist_directory=self.db_directory / "chroma"
            )

        self._factual_store = factual_store
        self._semantic_store = semantic_store

        # Setup storage backends (idempotent)
        self._factual_store.setup()
        self._semantic_store.setup()

    def set_fact(self, key: str, value: Any) -> None:
        """Store a key-value pair in factual storage.

        Delegates to the configured FactualStorage backend.

        Args:
            key: Non-empty string key.
            value: JSON-serializable value.

        Raises:
            ValidationError: If key or value invalid.
            StorageError: If storage fails.
        """
        self._factual_store.set_fact(key, value)

    def get_fact(self, key: str) -> Any | None:
        """Retrieve a value by key from factual storage.

        Delegates to the configured FactualStorage backend.

        Args:
            key: The key to look up.

        Returns:
            The value if key exists, None otherwise.

        Raises:
            ValidationError: If key invalid.
            StorageError: If retrieval fails.
        """
        return self._factual_store.get_fact(key)

    def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        """Store content with semantic embedding.

        Delegates to the configured SemanticStorage backend.

        Args:
            content: Text to embed and store.
            metadata: Metadata dict with string keys.

        Returns:
            Unique ID for the stored embedding.

        Raises:
            ValidationError: If content or metadata invalid.
            StorageError: If storage fails.
        """
        return self._semantic_store.add_semantic(content, metadata)

    def query_semantic(
        self,
        query_text: str,
        k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Query for semantically similar content.

        Delegates to the configured SemanticStorage backend.

        Args:
            query_text: Text to search for.
            k: Maximum number of results.
            filter: Optional metadata filter.

        Returns:
            List of result dicts with id, content, metadata, distance.

        Raises:
            ValidationError: If query parameters invalid.
            StorageError: If query fails.
        """
        return self._semantic_store.query_semantic(query_text, k, filter)
```

---

## 4. exceptions.py - Custom Exception Hierarchy

```python
"""Custom exceptions for HMC package.

Provides clear, specific error types for different failure modes.
"""


class HMCError(Exception):
    """Base exception for all HMC errors."""
    pass


class StorageError(HMCError):
    """Raised when storage backend operations fail.

    Examples: Database connection errors, ChromaDB initialization failures,
    disk I/O errors, permission denied.
    """
    pass


class ValidationError(HMCError):
    """Raised when input validation fails.

    Examples: Empty key, non-JSON-serializable value, invalid project_id,
    negative k value, malformed filter dict.
    """
    pass


class SeederError(HMCError):
    """Raised when seeding process encounters errors.

    Examples: Project directory not found, persona.md parse errors,
    file read failures during scanning.
    """
    pass
```

---

## 5. CLI Entry Point Signature (cli.py)

```python
"""CLI interface for HMC using Typer.

Provides the 'hmc seed' command for populating memory from existing projects.
"""

import typer
from pathlib import Path

app = typer.Typer(help="Hybrid Memory Core CLI")


@app.command()
def seed(
    path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Path to project directory to seed from"
    ),
    memory_dir: Path = typer.Option(
        ".hmc_memory",
        "--memory-dir",
        "-m",
        help="Directory for HMC storage files (relative to project path)"
    ),
    project_id: str | None = typer.Option(
        None,
        "--project-id",
        "-p",
        help="Unique project ID (defaults to directory name)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
) -> None:
    """Seed HMC memory from existing project files and persona.md.

    Scans the project directory for:
    - persona.md: Extracts factual attributes and voice examples
    - requirements.txt / pyproject.toml: Extracts technology stack
    - Source files (*.py, *.js, *.md): Chunks and embeds semantically
    - Directory structure: Stores project organization

    Example:
        $ hmc seed /path/to/project
        $ hmc seed . --memory-dir custom_memory --project-id my_agent
    """
    # Implementation details in seeder.py
    pass


if __name__ == "__main__":
    app()
```

---

## Summary

All API signatures defined with:

- ✅ Full Python 3.10+ type hints (using `|` union syntax)
- ✅ Google-style docstrings on all public methods
- ✅ Clear parameter and return type documentation
- ✅ Exception documentation (Raises sections)
- ✅ Abstract interfaces separated from concrete implementations
- ✅ Dependency injection support in HybridMemoryCore
- ✅ Custom exception hierarchy for clear error handling
