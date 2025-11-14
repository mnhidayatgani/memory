<!--
  SYNC IMPACT REPORT
  ==================
  Version Change: INITIAL → 1.0.0
  Ratification Date: 2025-11-14
  
  Principles Added:
  - Principle 1: Strict Separation of Concerns
  - Principle 2: Package-First Design
  - Principle 3: The Dual-Use Mandate
  - Principle 4: Strict Abstraction
  - Principle 5: Quality & Standards
  - Principle 6: Technology Stack
  
  Templates Updated:
  ✅ plan-template.md - Added detailed Constitution Check section with all 6 principles
  ✅ spec-template.md - Reviewed (aligns with user story requirements, no changes needed)
  ✅ tasks-template.md - Updated to mandate testing per Principle 5 (Quality & Standards)
  ✅ agent-file-template.md - Reviewed (general-purpose template, no changes needed)
  ✅ checklist-template.md - Reviewed (general-purpose template, no changes needed)
  
  Follow-up TODOs:
  - None
--># Hybrid Memory Core (HMC) Constitution

## Core Principles

### Principle 1: Strict Separation of Concerns (NON-NEGOTIABLE)

This is the most critical architectural rule. The HMC project MUST maintain clear boundaries between three distinct layers:

1. **The Storage (`hmc` package)**: A "database" tool that is implementation-agnostic. It MUST only provide storage and retrieval capabilities without any domain logic.
2. **The Data (Persona & Specs)**: The content stored within the `hmc` system (e.g., `persona.md` content, user-generated specifications).
3. **The Application (The AI Agent)**: The business logic that uses the `hmc` package to store/retrieve data and implement persona behavior.

**Rationale**: This separation ensures the `hmc` package remains reusable across different AI agents and applications. Agent-specific logic (e.g., "how to be Jarvis") MUST NOT be embedded in the storage layer.

**Enforcement**: Code reviews MUST reject any storage layer code that contains application or persona logic.

### Principle 2: Package-First Design (NON-NEGOTIABLE)

This project MUST be built as an installable Python package using modern packaging standards:

- MUST use `pyproject.toml` for project configuration
- MUST follow `src/hmc` layout convention
- MUST be installable via `pip install`
- MUST NOT be a single-file script or collection of loose modules

**Rationale**: Package structure ensures portability, proper dependency management, and professional distribution. It enables the library to be integrated into diverse projects and published to PyPI.

**Enforcement**: Project structure MUST conform to Python packaging best practices. Any deviation requires explicit justification and approval.

### Principle 3: The Dual-Use Mandate (NON-NEGOTIABLE)

The system MUST serve two primary use cases with equal priority:

1. **Greenfield**: Easy initialization and setup in new, empty projects
2. **Brownfield (Seeder Utility)**: A first-class utility that can scan existing codebases and `persona.md` files to populate the memory system

**Rationale**: Many AI agents will be introduced to existing projects. The seeder utility is not an afterthought but a core feature that determines the system's real-world utility.

**Enforcement**: Both use cases MUST be documented, tested, and maintained. The seeder utility MUST receive the same level of attention as the core storage API.

### Principle 4: Strict Abstraction (NON-NEGOTIABLE)

The core `HybridMemoryCore` class MUST interact with storage backends exclusively through defined Abstract Base Classes (ABCs):

- Storage backend implementations MUST be swappable without modifying the core API
- All backend-specific code MUST be isolated behind abstraction interfaces
- The system MUST support multiple backend implementations (e.g., ChromaDB, LanceDB) simultaneously

**Rationale**: This enables future extensibility, testing with mock backends, and migration between storage technologies without breaking client code.

**Enforcement**: No direct backend dependencies in core classes. All storage operations MUST go through defined interfaces.

### Principle 5: Quality & Standards (NON-NEGOTIABLE)

All code MUST meet professional software engineering standards:

- **Type Safety**: All Python code MUST be fully type-hinted (Python 3.10+ type system)
- **Documentation**: All public classes and methods MUST include Google-style docstrings
- **Testability**: The project MUST be fully testable, including the seeder utility
- **Code Quality**: Linting (ruff/pylint), formatting (black), and type checking (mypy) MUST pass

**Rationale**: High-quality code ensures maintainability, reduces bugs, and provides clear contracts for library users.

**Enforcement**: CI/CD pipelines MUST enforce type checking, linting, and test coverage. PRs failing these checks MUST be rejected.

### Principle 6: Technology Stack

The following technology choices are mandated for consistency and reliability:

- **Language**: Python 3.10+
- **Factual Store Backend**: `sqlite3` (built-in, file-based)
- **Semantic Store Backend**: `chromadb` (local, persistent)
- **CLI Utility**: `typer` or `click`

**Rationale**: These choices prioritize zero external dependencies for core functionality (sqlite3 is built-in), local-first operation (no required cloud services), and proven Python CLI patterns.

**Enforcement**: Alternative technologies require explicit justification documenting why the mandated stack is insufficient.

## Development Standards

### Code Organization

- MUST follow `src/hmc` package layout
- MUST separate concerns: models, storage, utilities, CLI
- MUST include comprehensive tests in `tests/` directory
- MUST provide clear examples and documentation

### Testing Requirements

- Unit tests MUST cover all public APIs
- Integration tests MUST verify storage backend interactions
- The seeder utility MUST have dedicated test scenarios
- Contract tests MUST validate abstraction boundaries

### Documentation Requirements

- README MUST include quickstart guide for both greenfield and brownfield use cases
- API documentation MUST be generated from docstrings
- Architecture decision records MUST document major design choices
- Migration guides MUST be provided for breaking changes

## Governance

### Amendment Process

1. Proposed amendments MUST be documented with rationale
2. Amendments MUST include impact analysis on existing code and templates
3. Version bumping MUST follow semantic versioning:
   - **MAJOR**: Backward-incompatible principle removal or redefinition
   - **MINOR**: New principle added or materially expanded guidance
   - **PATCH**: Clarifications, wording improvements, non-semantic refinements
4. All stakeholders MUST review and approve amendments before ratification

### Compliance

- All pull requests MUST be reviewed for constitutional compliance
- Constitution violations MUST be explicitly justified and documented in Complexity Tracking sections
- This constitution supersedes all conflicting practices or guidelines

### Version Control

Constitution changes MUST be tracked in version control with:

- Clear commit messages referencing the amendment nature
- Updated version number and amendment date
- Sync impact report documenting affected templates and artifacts

**Version**: 1.0.0 | **Ratified**: 2025-11-14 | **Last Amended**: 2025-11-14
