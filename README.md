# Hybrid Memory Core (HMC)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**HMC** is a persistent hybrid memory system for AI agents that combines factual (key-value) storage via SQLite3 and semantic (vector) storage via ChromaDB. It supports both greenfield (new projects) and brownfield (existing projects) initialization.

## Features

- **Hybrid Storage**: Factual key-value pairs (SQLite3) + semantic vector search (ChromaDB)
- **Local-First**: All data stored on disk, no cloud dependencies
- **Type-Safe**: Full type hints for Python 3.10+
- **Swappable Backends**: Abstract interfaces for easy backend replacement
- **CLI Seeding**: Automatically populate memory from existing projects
- **Persistent**: Data survives process restarts

## Installation

### From PyPI (when published)

```bash
pip install hmc
```

### From Source

```bash
git clone <repository-url>
cd memory
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Brownfield: Seed from Existing Project

Use the CLI to automatically populate memory from an existing codebase:

```bash
# Seed from current directory
hmc seed .

# Seed from specific path with custom memory location
hmc seed /path/to/project --memory-dir /path/to/.hmc_memory

# Verbose output
hmc seed . --verbose
```

The seeder will:
1. Parse `persona.md` for factual attributes and voice examples
2. Extract technology stack from `requirements.txt`, `pyproject.toml`, or `package.json`
3. Scan project structure
4. Chunk and embed source files (`.py`, `.js`, `.ts`, `.md`)

### Greenfield: Initialize in New Project

Use the API to manually set up memory in a new project:

```python
from hmc import HybridMemoryCore

# Initialize memory
memory = HybridMemoryCore(
    project_id="my-project",
    db_directory="./.hmc_memory"
)

# Store factual data (key-value)
memory.set_fact("__persona_name__", "CodeAssistant")
memory.set_fact("__persona_tone__", "professional and helpful")
memory.set_fact("current_feature", "authentication")

# Retrieve factual data
persona_name = memory.get_fact("__persona_name__")
print(f"Persona: {persona_name}")

# Store semantic data (embedded content)
memory.add_semantic(
    content="User authentication using JWT tokens",
    metadata={
        "type": "spec",
        "feature": "authentication",
        "status": "draft"
    }
)

# Semantic search
results = memory.query_semantic(
    query_text="How does authentication work?",
    k=5,
    filter={"type": "spec"}
)

for result in results:
    print(f"Content: {result['content']}")
    print(f"Source: {result['metadata']['source_file']}")
```

### Workflow Documents Example

Store and retrieve workflow artifacts like specs, plans, and tasks:

```python
from hmc import HybridMemoryCore

memory = HybridMemoryCore(project_id="my-agent")

# Store a spec document
memory.add_semantic(
    content="""
    # Login Feature Specification
    
    Users should be able to authenticate using email and password.
    Implement JWT-based session management.
    """,
    metadata={
        "type": "spec",
        "feature": "login",
        "status": "approved",
        "author": "developer@example.com"
    }
)

# Query with filters
specs = memory.query_semantic(
    query_text="authentication requirements",
    k=10,
    filter={"type": "spec", "feature": "login"}
)

# Track workflow state
memory.set_fact("current_feature", "login")
memory.set_fact("task_counter", 5)
```

## Project Structure

```
.hmc_memory/               # Memory storage directory
├── sqlite/
│   └── facts.db           # SQLite3 factual store
└── chroma/                # ChromaDB semantic store
    └── <collections>
```

## Persona.md Format

Create a `persona.md` file in your project root:

```markdown
# Project Persona

## Factual

- name: CodeAssistant
- role: Senior Python Developer
- tone: Professional and concise
- user_title: Developer
- core_directive: Help with code quality and best practices
- language_rule: Use Python 3.10+ syntax

## Semantic (Voice Examples)

- "I recommend using type hints for better code clarity"
- "Let's break this down into smaller, testable functions"
- "Consider the SOLID principles when designing this class"
```

## Development

### Run Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/hmc
```

### Code Formatting

```bash
black src/hmc tests examples
```

### Linting

```bash
ruff check src/hmc tests examples
```

### Coverage Report

```bash
pytest --cov=hmc --cov-report=html
open htmlcov/index.html
```

## API Reference

### HybridMemoryCore

Main interface for hybrid memory operations.

#### `__init__(project_id: str, db_directory: str = "./.hmc_memory")`

Initialize memory core.

- `project_id`: Unique identifier for the project (alphanumeric, hyphens, underscores)
- `db_directory`: Path to memory storage directory

#### `set_fact(key: str, value: Any) -> None`

Store a factual key-value pair.

#### `get_fact(key: str) -> Any | None`

Retrieve a factual value by key. Returns `None` if key doesn't exist.

#### `add_semantic(content: str, metadata: dict[str, Any]) -> str`

Embed content semantically. Returns unique document ID.

- `content`: Text content to embed
- `metadata`: Dictionary with metadata (e.g., `type`, `feature`, `status`, `source_file`)

#### `query_semantic(query_text: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict]`

Perform semantic search.

- `query_text`: Query string
- `k`: Number of results to return
- `filter`: Optional metadata filters (e.g., `{"type": "spec", "status": "approved"}`)

Returns list of results with `content`, `metadata`, and `distance` fields.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure:

1. All code has type hints
2. Google-style docstrings for public APIs
3. Tests maintain >85% coverage
4. Code passes `mypy`, `black`, and `ruff` checks

## Troubleshooting

### ChromaDB Installation Issues

If you encounter issues installing ChromaDB, ensure you have:
- Python 3.10 or higher
- C++ build tools (for some dependencies)

On macOS:
```bash
xcode-select --install
```

On Ubuntu/Debian:
```bash
sudo apt-get install build-essential
```

### Memory Directory Permissions

Ensure the `.hmc_memory` directory is writable:
```bash
chmod -R u+w .hmc_memory
```

### Import Errors

If you get import errors after installation, ensure the package is installed in your active environment:
```bash
pip show hmc
```
