# Research: Hybrid Memory Core (HMC)

**Phase 0: Technical Research & Decision Documentation**  
**Date**: 2025-11-14  
**Status**: Complete

## Research Tasks

### R1: ChromaDB Local Persistence Best Practices

**Decision**: Use ChromaDB's `PersistentClient` with directory-based storage

**Rationale**:

- ChromaDB provides `chromadb.PersistentClient(path="...")` for local-first storage
- Data persists to disk automatically, no manual save/load required
- Supports metadata filtering which is essential for our use case (filtering by type, feature, status)
- Default embedding model (all-MiniLM-L6-v2) is sufficient for code/text similarity
- Collection-based organization allows multiple projects in same directory if needed

**Alternatives Considered**:

- **ChromaDB ephemeral client**: Rejected - doesn't persist across sessions
- **FAISS**: Rejected - requires manual serialization, no built-in metadata filtering
- **Weaviate/Qdrant**: Rejected - overkill, requires separate server processes

**Implementation Notes**:

```python
import chromadb
client = chromadb.PersistentClient(path=".hmc_memory/chroma")
collection = client.get_or_create_collection(name=project_id)
```

### R2: SQLite3 Schema Design for Key-Value Storage

**Decision**: Single `facts` table with TEXT key, TEXT json_value, DATETIME updated_at

**Rationale**:

- Simple schema supports arbitrary key-value pairs
- JSON serialization via `json.dumps()` handles Python types (str, int, float, bool, list, dict)
- Primary key on `key` ensures uniqueness and fast lookups
- `updated_at` timestamp enables auditing and debugging
- No need for complex indexing given expected scale (< 1000 factual entries per project)

**Schema**:

```sql
CREATE TABLE IF NOT EXISTS facts (
    key TEXT PRIMARY KEY,
    json_value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Alternatives Considered**:

- **Separate tables per entity type**: Rejected - violates generic storage principle
- **BLOB storage for values**: Rejected - TEXT with JSON is more debuggable
- **Composite keys**: Rejected - simple string keys sufficient, namespacing via key prefixes

### R3: File Chunking Strategy for Code Embedding

**Decision**: Simple max-character chunking (2000 chars) with paragraph/function boundary awareness

**Rationale**:

- ChromaDB default model has ~512 token context (roughly 2000 characters)
- Simple chunking is sufficient for MVP, avoids dependency on AST parsers
- Split on double newlines first (paragraphs/functions), then by character limit
- Preserve metadata: source_file, chunk_index, line_range

**Chunking Algorithm**:

1. Split file content on `\n\n` (paragraph boundaries)
2. For each section:
   - If < 2000 chars, use as-is
   - If > 2000 chars, split at 2000 char boundaries (preserve last newline)
3. Track line numbers for each chunk (for debugging)

**Alternatives Considered**:

- **AST-based chunking (Python ast module)**: Rejected for MVP - adds complexity, language-specific
- **Fixed-line chunking**: Rejected - ignores semantic boundaries
- **Overlap sliding window**: Rejected - creates duplicate embeddings, increases storage

**Future Enhancement**: AST-based chunking for Python files in v2.0

### R4: Persona.md Parsing Strategy

**Decision**: Simple markdown section parser with regex

**Rationale**:

- Format is well-defined: `## Factual` section has `- key: value` pairs
- Format is well-defined: `## Semantic (Voice Examples)` has bullet list items
- Regex sufficient for MVP, no need for full markdown parser dependency
- Fail gracefully on malformed sections (log warning, continue with available data)

**Parsing Logic**:

```python
# Extract Factual section
factual_match = re.search(r'## Factual\s+(.*?)(?=## |\Z)', content, re.DOTALL)
if factual_match:
    for line in factual_match.group(1).split('\n'):
        if match := re.match(r'-\s+(\w+):\s*"?(.+?)"?\s*$', line):
            key, value = match.groups()
            hmc.set_fact(f"__persona_{key}__", value)

# Extract Semantic section
semantic_match = re.search(r'## Semantic.*?\s+(.*?)(?=## |\Z)', content, re.DOTALL)
if semantic_match:
    for line in semantic_match.group(1).split('\n'):
        if line.strip().startswith('-'):
            example = line.strip()[1:].strip().strip('"')
            hmc.add_semantic(example, metadata={"type": "persona_voice"})
```

**Alternatives Considered**:

- **Full markdown parser (markdown-it-py)**: Rejected - overkill for simple format
- **YAML frontmatter**: Rejected - changes required format from spec
- **Custom DSL**: Rejected - markdown is familiar and readable

### R5: CLI Framework Selection (Typer vs Click)

**Decision**: Typer

**Rationale**:

- Modern Python 3.6+ type hints for automatic validation
- Automatic help generation from docstrings and type hints
- Built on top of Click (inherits maturity and reliability)
- Cleaner syntax for simple commands like `hmc seed <path>`
- Better IDE autocomplete support due to type hints

**Example**:

```python
import typer
app = typer.Typer()

@app.command()
def seed(
    path: str = typer.Argument(..., help="Path to project directory"),
    memory_dir: str = typer.Option(".hmc_memory", help="Memory storage directory")
):
    """Seed HMC memory from existing project files and persona.md"""
    # Implementation
```

**Alternatives Considered**:

- **Click**: Rejected - Typer provides better type safety and modern syntax
- **argparse**: Rejected - more verbose, less user-friendly help output
- **Fire**: Rejected - too magical, less explicit control

### R6: Error Handling and Validation Strategy

**Decision**: Explicit validation with custom exception hierarchy

**Rationale**:

- Clear error messages critical for library usability
- Custom exceptions enable consumers to handle specific cases
- Validate inputs at API boundaries (HybridMemoryCore methods, CLI commands)
- Log warnings for recoverable errors (malformed persona sections), raise for critical failures

**Exception Hierarchy**:

```python
class HMCError(Exception):
    """Base exception for HMC package"""

class StorageError(HMCError):
    """Storage backend errors (DB connection, ChromaDB issues)"""

class ValidationError(HMCError):
    """Input validation failures"""

class SeederError(HMCError):
    """Seeding process errors"""
```

**Validation Points**:

- `HybridMemoryCore.__init__`: Validate db_directory is writable
- `set_fact`: Validate key is non-empty string, value is JSON-serializable
- `query_semantic`: Validate k > 0, filter dict has valid keys
- CLI seed: Validate path exists and is directory

### R7: Testing Strategy and Coverage Targets

**Decision**: Three-layer test structure with >85% coverage requirement

**Rationale**:

- **Contract tests**: Verify ABC implementations satisfy interface contracts
- **Integration tests**: Verify end-to-end workflows (seeding, persistence)
- **Unit tests**: Verify individual component behavior in isolation
- pytest fixtures for shared test data (sample persona.md, mock project structure)
- Coverage target: >85% per Constitution Principle 5

**Test Organization**:

```
tests/
├── contract/
│   ├── test_factual_storage_contract.py  # Verify SQLiteFactualStore satisfies FactualStorage ABC
│   └── test_semantic_storage_contract.py # Verify ChromaSemanticStore satisfies SemanticStorage ABC
├── integration/
│   ├── test_seeder_brownfield.py         # Full seeding workflow with sample project
│   └── test_persistence.py               # Verify data survives session restart
└── unit/
    ├── test_sqlite_store.py              # SQLiteFactualStore methods
    ├── test_chroma_store.py              # ChromaSemanticStore methods
    ├── test_hybrid_memory_core.py        # HybridMemoryCore API
    └── test_cli.py                       # CLI command behavior
```

**Key Test Scenarios**:

- Seeding project with valid persona.md → all facts and semantics stored
- Seeding project without persona.md → graceful skip, project files still processed
- Malformed persona.md → warnings logged, valid sections processed
- Multiple seeding runs → upsert behavior (latest data wins)
- Cross-session persistence → initialize HMC twice, verify data retained

## Summary

All technical unknowns resolved. Key decisions:

1. **ChromaDB PersistentClient** for local vector storage with metadata filtering
2. **Single-table SQLite schema** for factual key-value pairs with JSON serialization
3. **Simple character-based chunking** (2000 chars) with paragraph awareness for MVP
4. **Regex-based persona.md parsing** with graceful error handling
5. **Typer CLI framework** for type-safe command interface
6. **Custom exception hierarchy** for clear error reporting
7. **Three-layer testing** (contract/integration/unit) targeting >85% coverage

Ready to proceed to Phase 1 (Design & Contracts).
