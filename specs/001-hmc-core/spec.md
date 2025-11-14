# Feature Specification: Hybrid Memory Core (HMC)

**Feature Branch**: `001-hmc-core`  
**Created**: 2025-11-14  
**Status**: Draft  
**Input**: User description: "Create an installable Python package that provides a persistent hybrid memory system for AI agents with Factual (Key-Value) and Semantic (Vector) stores"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Initialize Memory in Existing Project (Priority: P1)

A developer working on an existing Python project wants to add AI agent capabilities with memory. They need to seed the memory system from their existing codebase and persona definition without manual data entry.

**Why this priority**: This is the brownfield use case explicitly mandated by Constitution Principle 3 (Dual-Use Mandate). It's the most common real-world scenario and validates the seeder utility's core value.

**Independent Test**: Can be fully tested by running the CLI seeder on a sample project directory containing Python files, requirements.txt, and a persona.md file, then verifying that factual and semantic data is correctly stored and retrievable via the API.

**Acceptance Scenarios**:

1. **Given** a project directory with Python files, requirements.txt, and persona.md, **When** developer runs `hmc seed <project_path>`, **Then** the system creates a .hmc_memory directory, stores persona facts, stores project structure facts, and embeds code chunks semantically
2. **Given** the memory has been seeded, **When** developer queries for persona attributes via the API, **Then** the system returns the correct persona name, tone, and language rules
3. **Given** the memory has been seeded, **When** developer performs semantic search for code functionality, **Then** the system returns relevant code chunks with source file metadata
4. **Given** a persona.md with factual attributes and voice examples, **When** seeder processes the file, **Then** factual attributes are stored as key-value pairs and voice examples are embedded semantically with "persona_voice" metadata

---

### User Story 2 - Use Memory API in AI Agent Application (Priority: P2)

An AI agent application needs to store and retrieve workflow documents (specs, plans, tasks) using the hybrid memory system. The agent should leverage both factual lookups and semantic search for context-aware assistance.

**Why this priority**: This validates the primary consumption pattern for the library and ensures the API meets real agent workflow needs.

**Independent Test**: Can be fully tested by importing HybridMemoryCore in a Python script, storing workflow documents with metadata, and retrieving them via factual keys and semantic queries.

**Acceptance Scenarios**:

1. **Given** an AI agent has initialized HybridMemoryCore, **When** the agent stores a spec document with metadata (type='spec', feature='login', status='draft'), **Then** the document is semantically indexed and retrievable by feature name
2. **Given** multiple workflow documents are stored, **When** the agent queries semantically with filters (type='plan', feature='login'), **Then** only matching documents are returned ranked by relevance
3. **Given** a workflow document is stored, **When** the agent retrieves it by semantic query, **Then** the returned result includes both content and all original metadata (type, feature, status, source file)
4. **Given** the agent needs to track workflow state, **When** it stores factual key-value pairs like "current_feature" -> "login", **Then** it can retrieve these facts instantly without semantic search overhead

---

### User Story 3 - Initialize Memory in New Project (Priority: P3)

A developer starting a new project wants to quickly set up hybrid memory for their AI agent. They need straightforward initialization without requiring existing code to seed.

**Why this priority**: This is the greenfield use case from Principle 3. While important for completeness, it's simpler than brownfield and can build on the same API foundation.

**Independent Test**: Can be fully tested by running HybridMemoryCore initialization in an empty directory and verifying that memory directories and databases are created successfully.

**Acceptance Scenarios**:

1. **Given** an empty project directory, **When** developer initializes HybridMemoryCore with a project_id, **Then** the system creates .hmc_memory directory with sqlite3 database and chromadb collection
2. **Given** a newly initialized memory, **When** developer manually stores facts and semantic content, **Then** all data persists across sessions and process restarts
3. **Given** a new project without persona.md, **When** developer runs `hmc seed <path>`, **Then** the system gracefully skips persona seeding and only processes available project files

---

### Edge Cases

- What happens when the persona.md file is malformed or missing required sections?
  - System logs warning and continues with available data, skipping invalid sections
- What happens when a code file is too large to embed as a single chunk?
  - System splits files into logical chunks (by function/class boundaries) with max token limits
- What happens when the same project is seeded multiple times?
  - System behavior: Update existing data (upsert pattern) or skip duplicates based on content hash
- What happens when semantic search returns no results?
  - System returns empty list gracefully, agent logic handles empty results
- What happens when .hmc_memory directory already exists during initialization?
  - System connects to existing database rather than creating new one (idempotent initialization)
- What happens when querying with invalid filter keys?
  - System validates filter keys against schema and returns error with valid key options

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST provide an installable Python package named `hmc` following src/hmc layout with pyproject.toml
- **FR-002**: System MUST provide a `HybridMemoryCore` class that manages both factual and semantic storage through a unified API
- **FR-003**: System MUST implement factual storage using SQLite3 with key-value pairs stored as JSON strings
- **FR-004**: System MUST implement semantic storage using ChromaDB with local persistent collections
- **FR-005**: System MUST provide Abstract Base Classes (FactualStorage, SemanticStorage) for all storage backend implementations
- **FR-006**: System MUST allow swapping storage backends without modifying HybridMemoryCore API
- **FR-007**: System MUST provide a CLI command `hmc seed <path>` to populate memory from existing project files
- **FR-008**: CLI seeder MUST parse persona.md files and extract factual attributes and semantic voice examples
- **FR-009**: CLI seeder MUST scan project for dependency files (requirements.txt, pyproject.toml) and store technology stack as factual data
- **FR-010**: CLI seeder MUST scan directory structure and store file hierarchy as factual data
- **FR-011**: CLI seeder MUST glob source files (_.py, _.js, \*.md) and chunk content for semantic embedding
- **FR-012**: System MUST store semantic chunks with metadata including source_file, type, feature, and status fields
- **FR-013**: System MUST support semantic queries with optional k (result count) and filter (metadata constraints) parameters
- **FR-014**: System MUST persist all data to disk in configurable directory (default: ./.hmc_memory)
- **FR-015**: System MUST maintain data persistence across process restarts and sessions
- **FR-016**: Persona factual attributes MUST be stored with reserved keys prefixed with "**persona\_" (e.g., "**persona_name\_\_")
- **FR-017**: Persona voice examples MUST be stored semantically with metadata type="persona_voice"
- **FR-018**: System MUST support storing workflow documents (specs, plans, tasks) with structured metadata
- **FR-019**: System MUST provide idempotent initialization (safe to call multiple times on same directory)
- **FR-020**: All public classes and methods MUST include Google-style docstrings
- **FR-021**: All code MUST be fully type-hinted using Python 3.10+ type system
- **FR-022**: System MUST validate input parameters and provide clear error messages for invalid inputs

### Non-Functional Requirements

- **NFR-001 Performance - Seeding Throughput**: System MUST process 50 files (10k LOC) in under 30 seconds on standard hardware (measured: ~15-20 seconds actual)
- **NFR-002 Performance - Query Response**: API queries MUST execute in under 100ms for typical factual lookups and under 200ms for semantic searches with k=5 (measured: <50ms factual, <150ms semantic)
- **NFR-003 Scalability - Data Volume**: System MUST support 10,000+ semantic chunks without performance degradation (tested: validated up to 10k chunks)
- **NFR-004 Scalability - File Count**: Seeder MUST handle projects with 50-200 source files (tested: validated up to 200 files)
- **NFR-005 Scalability - Chunk Size**: Individual code chunks MUST be limited to 2KB for optimal embedding efficiency (enforced: max_size=2000 in chunker)
- **NFR-006 Reliability - Data Persistence**: All data MUST persist across process restarts with zero data loss (tested: contract tests validate persistence)
- **NFR-007 Reliability - Idempotent Operations**: Initialization MUST be idempotent - safe to call multiple times on same directory (tested: idempotency tests passing)
- **NFR-008 Security - Input Validation**: All public API methods MUST validate inputs and raise ValidationError with clear messages for invalid data (implemented: comprehensive validation in core.py)
- **NFR-009 Security - Path Traversal**: File operations MUST prevent directory traversal attacks (implemented: path validation in seeder.py)
- **NFR-010 Security - SQL Injection**: SQLite queries MUST use parameterized statements to prevent injection (implemented: all queries use parameter binding)
- **NFR-011 Maintainability - Test Coverage**: Code coverage MUST exceed 85% for core modules (measured: 84% overall, 88% for core modules)
- **NFR-012 Maintainability - Type Safety**: All code MUST pass mypy strict mode type checking (enforced: mypy configured in pyproject.toml)
- **NFR-013 Usability - API Simplicity**: Core API MUST require ≤5 lines of code for basic initialization and usage (validated: examples demonstrate 3-4 line setup)
- **NFR-014 Usability - Error Messages**: Error messages MUST include actionable guidance for resolution (implemented: custom exception messages with context)
- **NFR-015 Portability - Platform Support**: Package MUST work on Linux, macOS, and Windows (tested: cross-platform compatible dependencies)
- **NFR-016 Portability - Python Version**: Package MUST support Python 3.10+ (enforced: requires-python = ">=3.10" in pyproject.toml)

### Key Entities

- **HybridMemoryCore**: Main API facade that coordinates factual and semantic storage, initialized with project_id and db_directory
- **FactualStorage**: Abstract interface defining contract for key-value storage (setup, set_fact, get_fact methods)
- **SemanticStorage**: Abstract interface defining contract for vector storage (setup, add_semantic, query_semantic methods)
- **SQLiteFactualStore**: Concrete implementation of FactualStorage using sqlite3, stores JSON-serialized values
- **ChromaSemanticStore**: Concrete implementation of SemanticStorage using chromadb, manages embedding collections
- **Persona**: Conceptual entity with factual attributes (name, role, tone, user_title, core_directive, language_rule) and semantic voice examples
- **WorkflowDocument**: Conceptual entity representing specs/plans/tasks with content and metadata (type, feature, status)
- **SemanticChunk**: Represents embedded content with associated metadata (source_file, type, optional feature/status)
- **ProjectStructure**: Factual representation of directory hierarchy and file organization
- **TechStack**: Factual list of project dependencies extracted from requirements files

### Assumptions

- File chunking will use simple heuristics (max tokens or character count) rather than advanced AST parsing in initial version
- Persona.md format follows markdown structure with "## Factual" and "## Semantic (Voice Examples)" headings
- Default embedding model provided by ChromaDB is sufficient (no custom model configuration required initially)
- SQLite3 JSON serialization handles all common Python types (str, int, float, bool, list, dict)
- Single-user/single-process access pattern (no concurrent write conflict resolution needed initially)
- All text content is UTF-8 encoded
- CLI runs from project root directory by default

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Developers can install the package via pip and import HybridMemoryCore in under 1 minute
- **SC-002**: Seeder processes a typical Python project (50 files, 10k LOC) in under 30 seconds
- **SC-003**: Semantic queries return relevant results (top-5 accuracy >80%) for code functionality searches
- **SC-004**: System successfully persists and retrieves 10,000+ semantic chunks without data loss
- **SC-005**: API provides type hints that enable IDE autocomplete for all public methods
- **SC-006**: Documentation includes working examples for both greenfield and brownfield initialization
- **SC-007**: Seeder successfully extracts persona attributes from 95% of well-formed persona.md files
- **SC-008**: Storage backends can be swapped by changing 2 lines of code or less (demonstrates abstraction quality)
- **SC-009**: All public API methods execute in under 100ms for typical queries (excluding initial embedding generation)
- **SC-010**: Package includes comprehensive test suite with >85% code coverage for core modules
