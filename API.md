# API Reference

Complete API documentation for Hybrid Memory Core (HMC).

## Table of Contents

- [Core API](#core-api)
- [Storage Backends](#storage-backends)
- [Seeder Utilities](#seeder-utilities)
- [CLI Commands](#cli-commands)
- [Exceptions](#exceptions)
- [Type Definitions](#type-definitions)

---

## Core API

### `HybridMemoryCore`

Main interface for hybrid memory operations. Coordinates factual and semantic storage.

#### Constructor

```python
HybridMemoryCore(
    project_id: str,
    db_directory: str | Path = "./.hmc_memory",
    factual_store: FactualStorage | None = None,
    semantic_store: SemanticStorage | None = None
)
```

**Parameters:**

- `project_id` (str): Unique project identifier. Must contain only alphanumeric characters, hyphens, and underscores.
- `db_directory` (str | Path, optional): Path to memory storage directory. Defaults to `./.hmc_memory`.
- `factual_store` (FactualStorage | None, optional): Custom factual storage backend. If None, uses `SQLiteFactualStore`.
- `semantic_store` (SemanticStorage | None, optional): Custom semantic storage backend. If None, uses `ChromaSemanticStore`.

**Raises:**

- `ValidationError`: If `project_id` format is invalid.
- `StorageError`: If backend initialization fails.

**Example:**

```python
from hmc import HybridMemoryCore

# Default backends
memory = HybridMemoryCore(project_id="my-project")

# Custom directory
memory = HybridMemoryCore(
    project_id="my-project",
    db_directory="/custom/path/.hmc_memory"
)

# Custom backends (for testing)
from hmc.interfaces import FactualStorage, SemanticStorage
from unittest.mock import Mock

mock_factual = Mock(spec=FactualStorage)
mock_semantic = Mock(spec=SemanticStorage)

memory = HybridMemoryCore(
    project_id="test",
    factual_store=mock_factual,
    semantic_store=mock_semantic
)
```

---

#### `set_fact(key: str, value: Any) -> None`

Store a factual key-value pair.

**Parameters:**

- `key` (str): Non-empty string identifier for the fact.
- `value` (Any): JSON-serializable value (str, int, float, bool, None, list, dict).

**Raises:**

- `ValidationError`: If key is empty or value is not JSON-serializable.
- `StorageError`: If storage operation fails.

**Example:**

```python
# Simple values
memory.set_fact("persona_name", "CodeAssistant")
memory.set_fact("task_counter", 42)
memory.set_fact("is_active", True)

# Complex values
memory.set_fact("tech_stack", {
    "language": "python",
    "version": "3.10",
    "dependencies": ["chromadb", "typer"]
})

# Lists
memory.set_fact("active_features", ["login", "signup", "profile"])
```

---

#### `get_fact(key: str) -> Any | None`

Retrieve a factual value by key.

**Parameters:**

- `key` (str): Non-empty string identifier.

**Returns:**

- The stored value, or `None` if key doesn't exist.

**Raises:**

- `ValidationError`: If key is empty.
- `StorageError`: If storage operation fails.

**Example:**

```python
value = memory.get_fact("persona_name")
if value is None:
    print("Key not found")
else:
    print(f"Persona: {value}")

# Type-specific retrieval
counter: int = memory.get_fact("task_counter") or 0
features: list = memory.get_fact("active_features") or []
```

---

#### `add_semantic(content: str, metadata: dict[str, Any]) -> str`

Embed content semantically for vector search.

**Parameters:**

- `content` (str): Non-empty text content to embed.
- `metadata` (dict[str, Any]): Dictionary with metadata. All keys must be strings.

**Returns:**

- Unique document ID (str).

**Raises:**

- `ValidationError`: If content is empty or metadata is invalid.
- `StorageError`: If embedding operation fails.

**Example:**

```python
# Store code chunk
doc_id = memory.add_semantic(
    content='''def calculate_total(items):
    """Calculate total price."""
    return sum(item.price for item in items)
''',
    metadata={
        "type": "code_chunk",
        "source_file": "src/utils.py",
        "language": "python",
        "line_range": "10-13"
    }
)

# Store specification
memory.add_semantic(
    content="Users should authenticate using OAuth 2.0",
    metadata={
        "type": "spec",
        "feature": "authentication",
        "status": "approved",
        "priority": "P1"
    }
)

# Store persona voice
memory.add_semantic(
    content="I can help you refactor this code for better readability",
    metadata={"type": "persona_voice"}
)
```

---

#### `query_semantic(query_text: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]`

Perform semantic similarity search.

**Parameters:**

- `query_text` (str): Non-empty query string.
- `k` (int, optional): Number of results to return (must be > 0). Defaults to 5.
- `filter` (dict[str, Any] | None, optional): Metadata filters. Only documents matching ALL filter criteria are returned.

**Returns:**

- List of result dictionaries, each containing:
  - `content` (str): The embedded content
  - `metadata` (dict): All metadata fields
  - `distance` (float | None): Similarity distance (lower = more similar)

**Raises:**

- `ValidationError`: If `query_text` is empty or `k` <= 0.
- `StorageError`: If search operation fails.

**Example:**

```python
# Simple query
results = memory.query_semantic("how to authenticate users", k=5)
for result in results:
    print(result["content"])
    print(f"Source: {result['metadata'].get('source_file', 'N/A')}")
    print(f"Distance: {result['distance']}")

# Query with type filter
specs = memory.query_semantic(
    query_text="authentication requirements",
    k=10,
    filter={"type": "spec"}
)

# Query with multiple filters
approved_auth_specs = memory.query_semantic(
    query_text="authentication",
    k=5,
    filter={"type": "spec", "status": "approved", "feature": "authentication"}
)

# Query persona voices
voice_examples = memory.query_semantic(
    query_text="help with refactoring",
    k=3,
    filter={"type": "persona_voice"}
)
```

---

## Storage Backends

### `SQLiteFactualStore`

SQLite3-based factual storage backend.

```python
from hmc.backends import SQLiteFactualStore

store = SQLiteFactualStore(db_path="path/to/facts.db")
store.setup()  # Create table if not exists
store.set_fact("key", "value")
value = store.get_fact("key")
```

### `ChromaSemanticStore`

ChromaDB-based semantic storage backend.

```python
from hmc.backends import ChromaSemanticStore

store = ChromaSemanticStore(
    collection_name="my_collection",
    persist_directory="path/to/chroma"
)
store.setup()  # Create collection if not exists
doc_id = store.add_semantic("content", {"type": "doc"})
results = store.query_semantic("query", k=5, filter={"type": "doc"})
```

---

## Seeder Utilities

### `seed_project()`

Automatically populate memory from existing project.

```python
from hmc.seeder import seed_project

stats = seed_project(
    project_path="/path/to/project",
    memory_dir=Path(".hmc_memory"),
    project_id="my-project",
    verbose=True
)

print(stats)
# {
#     "persona_facts": 6,
#     "persona_voices": 3,
#     "project_facts": 2,
#     "code_chunks": 25,
#     "files_processed": 10,
#     "warnings": []
# }
```

**What it does:**

1. Parses `persona.md` (if present)
2. Extracts tech stack from dependency files
3. Scans project structure
4. Chunks and embeds source files

---

### `chunk_file_content()`

Split file content into manageable chunks.

```python
from hmc.chunker import chunk_file_content

content = """
def function1():
    pass

def function2():
    pass
"""

chunks = chunk_file_content(content, max_size=2000)
for chunk in chunks:
    print(f"Lines {chunk['line_range']}: {chunk['content']}")
```

---

## CLI Commands

### `hmc seed`

Seed memory from existing project.

```bash
# Basic usage
hmc seed /path/to/project

# Options
hmc seed . --memory-dir /custom/path --project-id my-project --verbose

# Help
hmc seed --help
```

**Options:**

- `path`: Path to project directory (required)
- `--memory-dir`: Custom memory directory (default: `.hmc_memory`)
- `--project-id`: Custom project ID (default: derived from directory name)
- `--verbose` / `-v`: Show detailed progress

---

## Exceptions

### `HMCError`

Base exception for all HMC errors.

### `ValidationError`

Raised when input validation fails.

```python
from hmc.exceptions import ValidationError

try:
    memory.set_fact("", "value")  # Empty key
except ValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Field: {e.field}")
```

### `StorageError`

Raised when storage operations fail.

```python
from hmc.exceptions import StorageError

try:
    memory.get_fact("key")
except StorageError as e:
    print(f"Storage error: {e}")
```

### `SeederError`

Raised when seeding operations fail.

```python
from hmc.exceptions import SeederError
from hmc.seeder import seed_project

try:
    seed_project("/nonexistent/path")
except SeederError as e:
    print(f"Seeding failed: {e}")
```

---

## Type Definitions

### Common Metadata Fields

While metadata can contain any string keys, these are commonly used:

**For Code Chunks:**

```python
{
    "type": "code_chunk",
    "source_file": "src/main.py",
    "language": "py",  # or "js", "ts", "md"
    "chunk_index": 0,
    "line_range": "1-50"
}
```

**For Specifications:**

```python
{
    "type": "spec",
    "feature": "authentication",
    "status": "draft",  # or "review", "approved"
    "priority": "P1",  # or "P2", "P3"
    "author": "developer@example.com"
}
```

**For Plans:**

```python
{
    "type": "plan",
    "feature": "authentication",
    "status": "draft",
    "phase": "implementation"
}
```

**For Tasks:**

```python
{
    "type": "task",
    "feature": "authentication",
    "task_id": "AUTH-123",
    "status": "in_progress"
}
```

**For Persona Voices:**

```python
{
    "type": "persona_voice"
}
```

### Reserved Fact Keys

Keys prefixed with `__` are reserved for HMC metadata:

- `__persona_name__`: Persona name
- `__persona_role__`: Persona role
- `__persona_tone__`: Persona tone/style
- `__persona_user_title__`: How persona addresses user
- `__persona_core_directive__`: Main directive
- `__persona_language_rule__`: Language preferences
- `__tech_stack__`: Technology stack dictionary
- `__project_structure__`: Project structure dictionary
- `__project_root__`: Project root path
- `__seeded_at__`: Seeding timestamp
- `__hmc_version__`: HMC version used

---

## Advanced Usage

### Custom Backends

Implement your own storage backends:

```python
from hmc.interfaces import FactualStorage, SemanticStorage
from typing import Any

class MyFactualStore(FactualStorage):
    def setup(self) -> None:
        # Initialize storage
        pass

    def set_fact(self, key: str, value: Any) -> None:
        # Store fact
        pass

    def get_fact(self, key: str) -> Any | None:
        # Retrieve fact
        pass

class MySemanticStore(SemanticStorage):
    def setup(self) -> None:
        # Initialize storage
        pass

    def add_semantic(self, content: str, metadata: dict[str, Any]) -> str:
        # Embed content
        return "doc_id"

    def query_semantic(
        self,
        query_text: str,
        k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        # Search
        return []

# Use custom backends
memory = HybridMemoryCore(
    project_id="test",
    factual_store=MyFactualStore(),
    semantic_store=MySemanticStore()
)
```

### Batch Operations

```python
# Batch fact storage
facts = {
    "feature_1_status": "complete",
    "feature_2_status": "in_progress",
    "feature_3_status": "planned"
}

for key, value in facts.items():
    memory.set_fact(key, value)

# Batch semantic embedding
documents = [
    ("Spec 1", {"type": "spec", "feature": "A"}),
    ("Spec 2", {"type": "spec", "feature": "B"}),
    ("Spec 3", {"type": "spec", "feature": "C"})
]

for content, metadata in documents:
    memory.add_semantic(content, metadata)
```

### Query Result Processing

```python
results = memory.query_semantic("authentication", k=10)

# Group by type
by_type = {}
for result in results:
    doc_type = result["metadata"].get("type", "unknown")
    if doc_type not in by_type:
        by_type[doc_type] = []
    by_type[doc_type].append(result)

# Filter by distance threshold
relevant = [r for r in results if r["distance"] and r["distance"] < 0.5]

# Extract specific metadata
sources = [r["metadata"].get("source_file") for r in results]
features = list(set(r["metadata"].get("feature") for r in results))
```

---

## Best Practices

1. **Use Descriptive Metadata**: Always include `type` and other relevant fields for better filtering
2. **Consistent Naming**: Use snake_case for fact keys and consistent metadata key names
3. **Filter Before Querying**: Use metadata filters to narrow search space
4. **Reasonable k Values**: Start with k=5-10 for most queries
5. **Idempotent Operations**: safe to call multiple times
6. **Error Handling**: Always catch `ValidationError` and `StorageError`
7. **Type Hints**: Leverage HMC's type hints for IDE autocomplete

---

## Performance Tips

1. **Chunk Size**: Keep chunks under 2000 characters for optimal embedding
2. **Query Specificity**: More specific queries return better results
3. **Metadata Indexing**: Filter by metadata before semantic search when possible
4. **Batch Operations**: Group multiple operations to reduce overhead
5. **Memory Usage**: Monitor `.hmc_memory/` directory size for large projects
