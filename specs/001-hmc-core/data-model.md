# Data Model: Hybrid Memory Core (HMC)

**Phase 1: Data Model & Entity Design**  
**Date**: 2025-11-14  
**Status**: Complete

## Core Entities

### 1. HybridMemoryCore (Main API Facade)

**Purpose**: Unified interface coordinating factual and semantic storage backends

**Fields**:

- `project_id: str` - Unique identifier for this memory instance
- `db_directory: str` - Root directory for all storage (.hmc_memory)
- `_factual_store: FactualStorage` - Factual storage backend instance
- `_semantic_store: SemanticStorage` - Semantic storage backend instance

**Relationships**:

- Depends on (via constructor injection): FactualStorage implementation
- Depends on (via constructor injection): SemanticStorage implementation

**State Transitions**: N/A (stateless coordinator)

**Validation Rules**:

- `project_id` must be non-empty string, alphanumeric + hyphens/underscores only
- `db_directory` must be valid writable directory path
- Backend stores must successfully initialize (throw `StorageError` if setup fails)

---

### 2. FactualStorage (Abstract Interface)

**Purpose**: Contract for key-value storage backends

**Methods**:

- `setup() -> None` - Initialize storage (create tables, directories, etc.)
- `set_fact(key: str, value: Any) -> None` - Store key-value pair
- `get_fact(key: str) -> Any | None` - Retrieve value by key

**Validation Rules**:

- `key` must be non-empty string
- `value` must be JSON-serializable (str, int, float, bool, list, dict, None)
- `get_fact` returns None if key doesn't exist (no exception)

**Implementation Contract**:

- Implementations MUST persist data to disk
- Implementations MUST support idempotent setup (safe to call multiple times)
- Implementations MUST serialize/deserialize Python types consistently

---

### 3. SQLiteFactualStore (Concrete Implementation)

**Purpose**: SQLite3-backed factual storage

**Fields**:

- `db_path: str` - Path to SQLite database file
- `_conn: sqlite3.Connection | None` - Database connection (lazy-initialized)

**Database Schema**:

```sql
CREATE TABLE IF NOT EXISTS facts (
    key TEXT PRIMARY KEY,
    json_value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Validation Rules**:

- Before any operation: ensure connection established and table created
- `set_fact`: Use `json.dumps()` for serialization, UPSERT semantics
- `get_fact`: Use `json.loads()` for deserialization, return None if key missing

**Implementation Details**:

- Connection established on first method call (lazy initialization)
- Automatic commit after each `set_fact` (ensures durability)
- Thread-safe via SQLite3's default isolation

---

### 4. SemanticStorage (Abstract Interface)

**Purpose**: Contract for vector storage backends

**Methods**:

- `setup() -> None` - Initialize storage (create collections, indices, etc.)
- `add_semantic(content: str, metadata: dict) -> str` - Store content with embedding, return ID
- `query_semantic(query_text: str, k: int = 5, filter: dict | None = None) -> list[dict]` - Search by similarity

**Return Format for `query_semantic`**:

```python
[
    {
        "id": "embedding_id_123",
        "content": "original text content",
        "metadata": {"source_file": "...", "type": "...", ...},
        "distance": 0.234  # or similarity score
    },
    ...
]
```

**Validation Rules**:

- `content` must be non-empty string
- `metadata` must be dict with string keys
- `k` must be positive integer
- `filter` keys must match expected metadata schema

---

### 5. ChromaSemanticStore (Concrete Implementation)

**Purpose**: ChromaDB-backed semantic storage

**Fields**:

- `collection_name: str` - ChromaDB collection name (typically = project_id)
- `persist_directory: str` - Directory for ChromaDB persistent storage
- `_client: chromadb.PersistentClient | None` - ChromaDB client (lazy-initialized)
- `_collection: chromadb.Collection | None` - Collection handle (lazy-initialized)

**Implementation Details**:

- Client initialized on first method call: `chromadb.PersistentClient(path=persist_directory)`
- Collection created with: `client.get_or_create_collection(name=collection_name)`
- `add_semantic`: Use `collection.add(documents=[content], metadatas=[metadata], ids=[generated_id])`
- `query_semantic`: Use `collection.query(query_texts=[query_text], n_results=k, where=filter)`
- ID generation: UUID4 or sequential counter

**Validation Rules**:

- Metadata keys must be strings (ChromaDB requirement)
- Metadata values must be primitive types (str, int, float, bool)
- Filter dict must use ChromaDB query syntax: `{"key": "value"}` or `{"key": {"$eq": "value"}}`

---

### 6. Persona (Conceptual Entity - Not a Class)

**Purpose**: Represents AI agent persona definition stored in memory

**Factual Attributes** (stored as individual facts with `__persona_` prefix):

- `__persona_name__: str` - Persona name (e.g., "J.A.R.V.I.S.")
- `__persona_role__: str` - Role description
- `__persona_tone__: str` - Communication style
- `__persona_user_title__: str` - How to address user (e.g., "Sir")
- `__persona_core_directive__: str` - Primary mission/purpose
- `__persona_language_rule__: str` - Language handling rules

**Semantic Attributes** (stored as embeddings with metadata):

- Voice examples: Multiple entries with `metadata={"type": "persona_voice"}`

**Validation Rules**:

- Name is required (seeder MUST find this or fail gracefully)
- Other fields optional (seeder uses empty string if missing)
- Voice examples: at least 1 recommended, but not required

---

### 7. WorkflowDocument (Conceptual Entity - Not a Class)

**Purpose**: Represents AI agent workflow artifacts (specs, plans, tasks)

**Storage Format**: Semantic embedding with structured metadata

**Required Metadata Fields**:

- `type: str` - Document type: "spec", "plan", "task", "note"
- `feature: str` - Feature identifier this document relates to
- `status: str` - Document status: "draft", "approved", "complete", "archived"

**Optional Metadata Fields**:

- `source_file: str` - Original file path if seeded from disk
- `created_at: str` - ISO timestamp
- `version: str` - Version identifier

**Validation Rules**:

- `type` must be one of allowed values
- `feature` must be non-empty string
- `status` follows state machine: draft → approved → complete | archived

**Query Patterns**:

```python
# Find all specs for "login" feature
hmc.query_semantic("login specification", k=5, filter={"type": "spec", "feature": "login"})

# Find all approved plans
hmc.query_semantic("implementation plan", k=10, filter={"type": "plan", "status": "approved"})
```

---

### 8. ProjectStructure (Conceptual Entity - Not a Class)

**Purpose**: Factual representation of project directory hierarchy

**Storage Format**: Single fact with key `"__project_structure__"`

**Value Schema**:

```python
{
    "root": "/path/to/project",
    "directories": [
        "src/",
        "src/models/",
        "tests/",
        ...
    ],
    "files": {
        "src/main.py": {"size": 1234, "lines": 45},
        "requirements.txt": {"size": 567, "lines": 12},
        ...
    }
}
```

**Seeding Logic**:

1. Walk directory tree with `os.walk()`
2. Exclude common directories: `.git/`, `__pycache__/`, `node_modules/`, `venv/`
3. Count lines for text files
4. Store as single JSON blob

---

### 9. TechStack (Conceptual Entity - Not a Class)

**Purpose**: Factual list of project dependencies

**Storage Format**: Single fact with key `"__tech_stack__"`

**Value Schema**:

```python
{
    "python_version": "3.10",  # from pyproject.toml or runtime
    "dependencies": [
        "chromadb>=0.4.0",
        "typer>=0.9.0",
        ...
    ],
    "dev_dependencies": [
        "pytest>=7.4.0",
        ...
    ]
}
```

**Seeding Logic**:

1. Check for `requirements.txt`: parse with `requirements-parser` or simple line split
2. Check for `pyproject.toml`: parse `[project.dependencies]` section
3. Check for `package.json`: parse `dependencies` and `devDependencies`
4. Store as single JSON blob

---

### 10. SemanticChunk (Conceptual Entity - Not a Class)

**Purpose**: Represents embedded code or text chunk from project files

**Storage Format**: Semantic embedding with metadata

**Required Metadata Fields**:

- `source_file: str` - Relative path from project root
- `type: str` - Content type: "code_chunk", "doc_chunk"

**Optional Metadata Fields**:

- `chunk_index: int` - Position in file (0, 1, 2, ...)
- `line_range: str` - Line numbers covered, e.g., "10-50"
- `language: str` - File extension or detected language

**Chunking Strategy** (from research.md):

1. Split file on `\n\n` (paragraph boundaries)
2. For sections > 2000 chars, split at character limit
3. Track line numbers for debugging

**Example**:

```python
hmc.add_semantic(
    chunk_content,
    metadata={
        "source_file": "src/models/user.py",
        "type": "code_chunk",
        "chunk_index": 0,
        "line_range": "1-45",
        "language": "python"
    }
)
```

## Relationships Diagram

```
HybridMemoryCore
├── depends on ──→ FactualStorage (interface)
│                  └── implemented by ──→ SQLiteFactualStore
│                                         └── stores ──→ Persona (factual attrs)
│                                         └── stores ──→ ProjectStructure
│                                         └── stores ──→ TechStack
└── depends on ──→ SemanticStorage (interface)
                   └── implemented by ──→ ChromaSemanticStore
                                          └── stores ──→ Persona (voice examples)
                                          └── stores ──→ WorkflowDocument
                                          └── stores ──→ SemanticChunk
```

## State Machines

### WorkflowDocument Status State Machine

```
     draft
       │
       ↓
   approved ←──┐
       │       │
       ↓       │
   complete    │
       │       │
       └───→ archived
```

**Transitions**:

- draft → approved: Manual approval by user
- approved → complete: Implementation finished
- approved → archived: Feature cancelled
- complete → archived: Old feature retired
- any → draft: Rollback for revisions (optional)

## Validation Rules Summary

| Entity              | Validation Rule                                                 |
| ------------------- | --------------------------------------------------------------- |
| HybridMemoryCore    | project_id alphanumeric+hyphens, db_directory writable          |
| FactualStorage      | key non-empty, value JSON-serializable                          |
| SemanticStorage     | content non-empty, metadata dict, k > 0                         |
| SQLiteFactualStore  | Auto-commit after write, idempotent setup                       |
| ChromaSemanticStore | Metadata keys=str, values=primitives, ChromaDB filter syntax    |
| Persona             | name required, others optional                                  |
| WorkflowDocument    | type in allowed set, feature non-empty, valid status            |
| ProjectStructure    | Valid directory tree, exclude common ignored dirs               |
| TechStack           | Valid dependency format from requirements.txt or pyproject.toml |
| SemanticChunk       | source_file required, chunk_index numeric, line_range format    |

## Implementation Notes

1. **Lazy Initialization**: Both SQLite and ChromaDB connections initialized on first use, not in `__init__`
2. **Idempotent Setup**: All `setup()` methods safe to call multiple times (use `IF NOT EXISTS`, `get_or_create`)
3. **Error Handling**: Validation at API boundaries, custom exceptions for different failure modes
4. **Serialization**: JSON for factual values, ChromaDB handles embedding serialization internally
5. **Metadata Schema**: Enforce consistent metadata keys across seeder and manual API usage
