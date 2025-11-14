"""Concrete storage backend implementations.

This module provides SQLite and ChromaDB implementations of the storage interfaces.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import chromadb

from hmc.exceptions import StorageError, ValidationError
from hmc.interfaces import FactualStorage, SemanticStorage


class SQLiteFactualStore(FactualStorage):
    """SQLite implementation of factual key-value storage.

    Stores key-value pairs in a SQLite database with JSON serialization.
    Values must be JSON-serializable (str, int, float, bool, list, dict, None).

    Args:
        db_path: Path to SQLite database file (created if doesn't exist)

    Example:
        >>> store = SQLiteFactualStore(db_path="./memory/facts.db")
        >>> store.setup()
        >>> store.set_fact("key", "value")
        >>> store.get_fact("key")
        'value'
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize SQLite factual storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection.

        Returns:
            Active SQLite connection

        Raises:
            StorageError: If connection fails
        """
        if self._connection is None:
            try:
                # Create parent directory if needed
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self._connection = sqlite3.connect(str(self.db_path))
                # Enable foreign keys and other pragmas
                self._connection.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error as e:
                raise StorageError(f"Failed to connect to database: {e}", e) from e
        return self._connection

    def setup(self) -> None:
        """Initialize database schema.

        Creates facts table if it doesn't exist. Idempotent operation.

        Raises:
            StorageError: If table creation fails
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    key TEXT PRIMARY KEY,
                    json_value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create facts table: {e}", e)

    def set_fact(self, key: str, value: Any) -> None:
        """Store a key-value pair with upsert semantics.

        Args:
            key: Non-empty string identifier
            value: JSON-serializable value

        Raises:
            ValidationError: If key is empty or value not JSON-serializable
            StorageError: If database operation fails
        """
        if not key or not isinstance(key, str):
            raise ValidationError("Key must be a non-empty string", field="key")

        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Value is not JSON-serializable: {e}", field="value") from e

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO facts (key, json_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (key, json_value),
            )
            conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to store fact '{key}': {e}", e)

    def get_fact(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: String identifier

        Returns:
            Stored value if key exists, None otherwise

        Raises:
            ValidationError: If key is empty
            StorageError: If database operation fails
        """
        if not key or not isinstance(key, str):
            raise ValidationError("Key must be a non-empty string", field="key")

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT json_value FROM facts WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row is None:
                return None
            return json.loads(row[0])
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve fact '{key}': {e}", e)
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to deserialize value for key '{key}': {e}", e)


class ChromaSemanticStore(SemanticStorage):
    """ChromaDB implementation of semantic vector storage.

    Stores text content with automatic embedding generation and supports
    similarity search with metadata filtering.

    Args:
        collection_name: Name of ChromaDB collection
        persist_directory: Path to ChromaDB persistence directory

    Example:
        >>> store = ChromaSemanticStore(
        ...     collection_name="my-project",
        ...     persist_directory="./memory/chroma"
        ... )
        >>> store.setup()
        >>> doc_id = store.add_semantic("Example content", {"type": "note"})
        >>> results = store.query_semantic("example", k=5)
    """

    def __init__(self, collection_name: str, persist_directory: str | Path) -> None:
        """Initialize ChromaDB semantic storage.

        Args:
            collection_name: Name for the ChromaDB collection
            persist_directory: Path to persistence directory
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self._client: chromadb.Client | None = None
        self._collection: chromadb.Collection | None = None

    def _get_client(self) -> chromadb.Client:
        """Get or create ChromaDB client.

        Returns:
            Active ChromaDB persistent client

        Raises:
            StorageError: If client creation fails
        """
        if self._client is None:
            try:
                # Create persistence directory if needed
                self.persist_directory.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(path=str(self.persist_directory))
            except Exception as e:
                raise StorageError(f"Failed to create ChromaDB client: {e}", e)
        return self._client

    def _get_collection(self) -> chromadb.Collection:
        """Get or create ChromaDB collection.

        Returns:
            ChromaDB collection instance

        Raises:
            StorageError: If collection access fails
        """
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_or_create_collection(name=self.collection_name)
            except Exception as e:
                raise StorageError(
                    f"Failed to get/create collection '{self.collection_name}': {e}", e
                )
        return self._collection

    def setup(self) -> None:
        """Initialize ChromaDB collection.

        Creates collection if it doesn't exist. Idempotent operation.

        Raises:
            StorageError: If setup fails
        """
        # Collection is created lazily via _get_collection
        self._get_collection()

    def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        """Add content with automatic embedding generation.

        Args:
            content: Non-empty text content to embed
            metadata: Dictionary with string keys (e.g., {"type": "spec", "source_file": "x.py"})

        Returns:
            Unique document ID (UUID)

        Raises:
            ValidationError: If content is empty or metadata invalid
            StorageError: If embedding or storage fails
        """
        if not content or not isinstance(content, str):
            raise ValidationError("Content must be a non-empty string", field="content")

        if not isinstance(metadata, dict):
            raise ValidationError("Metadata must be a dictionary", field="metadata")

        # Validate metadata keys are strings
        if not all(isinstance(k, str) for k in metadata):
            raise ValidationError("All metadata keys must be strings", field="metadata")

        collection = self._get_collection()
        doc_id = str(uuid.uuid4())

        try:
            collection.add(documents=[content], metadatas=[metadata], ids=[doc_id])
        except Exception as e:
            raise StorageError(f"Failed to add semantic content: {e}", e)

        return doc_id

    def query_semantic(
        self, query_text: str, k: int = 5, filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Perform semantic similarity search.

        Args:
            query_text: Query string for semantic search
            k: Number of results to return (must be > 0)
            filter: Optional metadata filter (e.g., {"type": "spec"})

        Returns:
            List of result dictionaries with "content", "metadata", and "distance" keys

        Raises:
            ValidationError: If query_text is empty or k <= 0
            StorageError: If search operation fails
        """
        if not query_text or not isinstance(query_text, str):
            raise ValidationError("Query text must be a non-empty string", field="query_text")

        if k <= 0:
            raise ValidationError("k must be greater than 0", field="k")

        collection = self._get_collection()

        try:
            results = collection.query(
                query_texts=[query_text], n_results=k, where=filter if filter else None
            )
        except Exception as e:
            raise StorageError(f"Failed to query semantic content: {e}", e)

        # Transform ChromaDB results to standard format
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i, content in enumerate(results["documents"][0]):
                formatted_results.append(
                    {
                        "content": content,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                )

        return formatted_results
