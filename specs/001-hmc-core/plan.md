# Implementation Plan: Hybrid Memory Core (HMC)

**Branch**: `001-hmc-core` | **Date**: 2025-11-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-hmc-core/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create an installable Python package (`hmc`) that provides a persistent hybrid memory system combining factual (key-value) storage via SQLite3 and semantic (vector) storage via ChromaDB. The system serves two primary use cases: (1) CLI-driven seeding from existing projects with persona.md files (brownfield), and (2) programmatic API usage for AI agents to store/retrieve workflow documents. The architecture strictly separates storage concerns from application logic through Abstract Base Classes, enabling backend swappability while maintaining a unified HybridMemoryCore API facade.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**:

- `chromadb` (>=0.4.0) - Semantic vector storage with local persistence
- `typer` (>=0.9.0) - CLI framework for `hmc seed` command
- `pytest` (>=7.4.0) - Testing framework
- `pytest-cov` (>=4.1.0) - Coverage reporting
- `mypy` (>=1.5.0) - Type checking
- `black` (>=23.0.0) - Code formatting
- `ruff` (>=0.1.0) - Fast linting

**Storage**:

- SQLite3 (built-in) - Factual key-value store, single file database
- ChromaDB collections - Semantic embeddings with metadata filtering

**Testing**: pytest with contract, integration, and unit test layers  
**Target Platform**: Cross-platform (Linux, macOS, Windows) - Python package
**Project Type**: Single Python package (library + CLI)  
**Performance Goals**:

- Seeder: Process 50 files (10k LOC) in <30 seconds
- API queries: <100ms for typical factual/semantic lookups
- Semantic search: Top-5 accuracy >80% for code functionality queries

**Constraints**:

- Local-first: No cloud services required, all data stored on disk
- Single-user: No concurrent write conflict resolution needed initially
- File-based: All state in .hmc_memory directory (portable, version-controllable)

**Scale/Scope**:

- Support 10,000+ semantic chunks without degradation
- Handle projects with 50-200 source files
- Persona.md files up to 5KB
- Individual code chunks max 2KB (for embedding efficiency)

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Principle 1: Strict Separation of Concerns ✓

- [x] Storage layer code contains NO application or persona logic
- [x] Clear boundaries maintained between: Storage (`hmc`), Data (persona/specs), Application (agent logic)
- [x] No domain-specific behavior in storage implementations

**Validation**: The `hmc` package provides only storage primitives (set_fact, get_fact, add_semantic, query_semantic). Persona interpretation and agent workflow logic reside in consumer applications, not in the storage layer.

### Principle 2: Package-First Design ✓

- [x] Project uses `pyproject.toml` configuration
- [x] Follows `src/hmc` layout convention
- [x] Installable via pip
- [x] NOT implemented as single-file script

**Validation**: Full `pyproject.toml` with dependencies, entry points, and metadata. Source in `src/hmc/`, installable with `pip install -e .` or from PyPI.

### Principle 3: Dual-Use Mandate ✓

- [x] Greenfield initialization documented and tested
- [x] Brownfield seeder utility implemented with equal priority
- [x] Both use cases covered in acceptance criteria

**Validation**: User Story 1 (P1) covers brownfield seeding, User Story 3 (P3) covers greenfield initialization. CLI seeder is first-class feature with dedicated test scenarios.

### Principle 4: Strict Abstraction ✓

- [x] Core classes use Abstract Base Classes for storage backends
- [x] Backend-specific code isolated behind interfaces
- [x] No direct backend dependencies in core API

**Validation**: `FactualStorage` and `SemanticStorage` ABCs defined. `HybridMemoryCore` depends only on abstractions, not concrete implementations. SQLite and ChromaDB details isolated in `backends.py`.

### Principle 5: Quality & Standards ✓

- [x] All code fully type-hinted (Python 3.10+)
- [x] Public classes/methods have Google-style docstrings
- [x] Test coverage includes unit, integration, and seeder scenarios
- [x] Linting, formatting, type checking configured

**Validation**: Full type hints on all signatures. Google-style docstrings mandatory. pytest + mypy + black + ruff in dev dependencies. Test structure includes contract/, integration/, unit/ directories.

### Principle 6: Technology Stack ✓

- [x] Uses Python 3.10+
- [x] Factual store: sqlite3
- [x] Semantic store: chromadb
- [x] CLI: typer or click
- [x] Any deviations explicitly justified

**Validation**: Python 3.10+ (using modern type hints with `|` union syntax). SQLite3 (built-in). ChromaDB for vectors. Typer for CLI (chosen for modern syntax and automatic help generation).

## Project Structure

### Documentation (this feature)

```text
specs/001-hmc-core/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── api-signatures.md      # Detailed Python API contracts
│   ├── database-schema.sql    # SQLite schema
│   └── seeder-pseudocode.md   # CLI seeder algorithm
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Python package structure (src layout)
src/
└── hmc/
    ├── __init__.py           # Package exports: HybridMemoryCore
    ├── interfaces.py         # ABCs: FactualStorage, SemanticStorage
    ├── backends.py           # Concrete: SQLiteFactualStore, ChromaSemanticStore
    ├── core.py               # Main API: HybridMemoryCore class
    ├── cli.py                # Typer CLI app: seed command
    ├── seeder.py             # Seeding logic: PersonaParser, ProjectScanner
    ├── chunker.py            # File chunking utilities
    └── py.typed              # PEP 561 type marker

tests/
├── contract/
│   ├── test_factual_storage_contract.py    # ABC contract verification
│   └── test_semantic_storage_contract.py   # ABC contract verification
├── integration/
│   ├── test_seeder_brownfield.py           # Full seeding workflow
│   ├── test_seeder_greenfield.py           # Empty project initialization
│   └── test_persistence.py                 # Cross-session data persistence
└── unit/
    ├── test_sqlite_store.py                # SQLiteFactualStore unit tests
    ├── test_chroma_store.py                # ChromaSemanticStore unit tests
    ├── test_hybrid_memory_core.py          # HybridMemoryCore unit tests
    ├── test_persona_parser.py              # PersonaParser unit tests
    ├── test_chunker.py                     # File chunking unit tests
    └── test_cli.py                         # CLI command unit tests

# Configuration and package metadata
pyproject.toml            # Package config, dependencies, entry points
README.md                 # Quickstart for both greenfield and brownfield
LICENSE                   # MIT or Apache 2.0
.gitignore                # Ignore .hmc_memory/, venv/, __pycache__/, etc.

# Development tools config
.mypy.ini or pyproject.toml [tool.mypy]    # Type checking config
.ruff.toml or pyproject.toml [tool.ruff]   # Linting config
pytest.ini or pyproject.toml [tool.pytest] # Test config

# Example usage
examples/
├── greenfield_init.py    # Initialize in new project
├── brownfield_seed.py    # Seed existing project
└── sample_persona.md     # Example persona file
```

**Structure Decision**: Single Python package structure (Option 1) selected because:

- This is a library package, not a web/mobile application
- All code is Python, no frontend/backend split needed
- Follows `src/hmc` layout per Constitution Principle 2
- Testable via pytest with clear test layer separation (contract/integration/unit)
- CLI distributed as package entry point via pyproject.toml [project.scripts]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: ✅ No constitutional violations detected. All principles satisfied by design.
