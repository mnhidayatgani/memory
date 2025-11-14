# Tasks: Hybrid Memory Core (HMC)

**Input**: Design documents from `/specs/001-hmc-core/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/  
**Branch**: `001-hmc-core`  
**Date**: 2025-11-14

**Tests**: Per Constitution Principle 5 (Quality & Standards), comprehensive testing is MANDATORY for this project, including unit tests, integration tests, and contract tests targeting >85% code coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Each user story represents a deployable increment.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths follow `src/hmc/` layout per Constitution Principle 2

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure that all user stories depend on

- [x] T001 Create project directory structure per plan.md (src/hmc/, tests/{contract,integration,unit}/, examples/)
- [x] T002 Create pyproject.toml with all dependencies (chromadb>=0.4.0, typer>=0.9.0, pytest>=7.4.0, mypy>=1.5.0, black>=23.0.0, ruff>=0.1.0)
- [x] T003 Configure project.scripts entry point: `hmc = "hmc.cli:app"` in pyproject.toml
- [x] T004 Create .gitignore (ignore .hmc_memory/, venv/, **pycache**/, .mypy_cache/, .pytest_cache/, htmlcov/, dist/, build/)
- [x] T005 Create README.md with quickstart examples for greenfield and brownfield use cases
- [x] T006 Create LICENSE file (MIT or Apache 2.0)
- [x] T007 [P] Configure pytest in pyproject.toml (testpaths, coverage target 85%, markers for slow/integration/contract tests)
- [x] T008 [P] Configure mypy in pyproject.toml (strict mode, Python 3.10+, disallow_untyped_defs=true)
- [x] T009 [P] Configure black in pyproject.toml (line-length=100, target-version=py310)
- [x] T010 [P] Configure ruff in pyproject.toml (line-length=100, select E/W/F/I/N/UP/B/C4/SIM rules)
- [x] T011 Create src/hmc/py.typed marker file for PEP 561 type stub support
- [x] T012 Create src/hmc/**init**.py with package exports (HybridMemoryCore, exceptions)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core abstractions and exceptions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T013 Create src/hmc/exceptions.py with custom exception hierarchy (HMCError, StorageError, ValidationError, SeederError) including Google-style docstrings
- [x] T014 Create src/hmc/interfaces.py with FactualStorage ABC (setup, set_fact, get_fact methods) including full type hints and Google-style docstrings
- [x] T015 Create src/hmc/interfaces.py with SemanticStorage ABC (setup, add_semantic, query_semantic methods) including full type hints and Google-style docstrings
- [x] T016 Add abstractmethod decorators and proper ABC inheritance to all interface methods in src/hmc/interfaces.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Initialize Memory in Existing Project (Priority: P1) 🎯 MVP

**Goal**: Enable developers to seed HMC memory from existing projects with persona.md, requirements.txt, and source files via CLI command `hmc seed <path>`

**Independent Test**: Run `hmc seed` on a sample project containing Python files, requirements.txt, and persona.md, then verify factual and semantic data is correctly stored and retrievable

**Why MVP**: This is the brownfield use case mandated by Constitution Principle 3 and represents the most common real-world adoption scenario

### Contract Tests for User Story 1 (Write FIRST)

- [x] T017 [P] [US1] Create tests/contract/test_factual_storage_contract.py to verify SQLiteFactualStore implements FactualStorage ABC correctly
- [x] T018 [P] [US1] Create tests/contract/test_semantic_storage_contract.py to verify ChromaSemanticStore implements SemanticStorage ABC correctly

### Backend Implementation for User Story 1

- [x] T019 [P] [US1] Create src/hmc/backends.py with SQLiteFactualStore class skeleton (inherits FactualStorage)
- [x] T020 [US1] Implement SQLiteFactualStore.**init**(db_path) with lazy connection initialization in src/hmc/backends.py
- [x] T021 [US1] Implement SQLiteFactualStore.\_get_connection() method with error handling in src/hmc/backends.py
- [x] T022 [US1] Implement SQLiteFactualStore.setup() to create facts table with schema from contracts/database-schema.sql
- [x] T023 [US1] Implement SQLiteFactualStore.set_fact(key, value) with JSON serialization and INSERT OR REPLACE in src/hmc/backends.py
- [x] T024 [US1] Implement SQLiteFactualStore.get_fact(key) with JSON deserialization and None handling in src/hmc/backends.py
- [x] T025 [US1] Add input validation to SQLiteFactualStore methods (non-empty key, JSON-serializable value) raising ValidationError
- [x] T026 [P] [US1] Create src/hmc/backends.py with ChromaSemanticStore class skeleton (inherits SemanticStorage)
- [x] T027 [US1] Implement ChromaSemanticStore.**init**(collection_name, persist_directory) with lazy client initialization in src/hmc/backends.py
- [x] T028 [US1] Implement ChromaSemanticStore.\_get_client() to initialize chromadb.PersistentClient in src/hmc/backends.py
- [x] T029 [US1] Implement ChromaSemanticStore.\_get_collection() to get_or_create_collection in src/hmc/backends.py
- [x] T030 [US1] Implement ChromaSemanticStore.setup() for idempotent collection creation in src/hmc/backends.py
- [x] T031 [US1] Implement ChromaSemanticStore.add_semantic(content, metadata) with UUID generation and collection.add() in src/hmc/backends.py
- [x] T032 [US1] Implement ChromaSemanticStore.query_semantic(query_text, k, filter) with collection.query() and result transformation in src/hmc/backends.py
- [x] T033 [US1] Add input validation to ChromaSemanticStore methods (non-empty content, k > 0, metadata dict with string keys) raising ValidationError

### Core API for User Story 1

- [x] T034 [US1] Create src/hmc/core.py with HybridMemoryCore class skeleton
- [x] T035 [US1] Implement HybridMemoryCore.**init**(project_id, db_directory, factual_store, semantic_store) with dependency injection support
- [x] T036 [US1] Add project_id validation (alphanumeric + hyphens/underscores) and db_directory creation in HybridMemoryCore.**init**
- [x] T037 [US1] Initialize default backends (SQLiteFactualStore, ChromaSemanticStore) if not provided in HybridMemoryCore.**init**
- [x] T038 [US1] Call setup() on both storage backends in HybridMemoryCore.**init**
- [x] T039 [US1] Implement HybridMemoryCore.set_fact(key, value) delegating to factual store in src/hmc/core.py
- [x] T040 [US1] Implement HybridMemoryCore.get_fact(key) delegating to factual store in src/hmc/core.py
- [x] T041 [US1] Implement HybridMemoryCore.add_semantic(content, metadata) delegating to semantic store in src/hmc/core.py
- [x] T042 [US1] Implement HybridMemoryCore.query_semantic(query_text, k, filter) delegating to semantic store in src/hmc/core.py
- [x] T043 [US1] Add comprehensive Google-style docstrings to all HybridMemoryCore public methods with Args/Returns/Raises sections

### Seeder Utility for User Story 1 (Core brownfield feature)

- [x] T044 [P] [US1] Create src/hmc/chunker.py with chunk_file_content(content, max_size=2000) function implementing paragraph-aware splitting
- [x] T045 [US1] Implement line range tracking in chunker.py for each chunk (returns list[dict] with 'content' and 'line_range')
- [x] T046 [US1] Add logic to split oversized sections by character boundaries in chunker.py
- [x] T047 [P] [US1] Create src/hmc/seeder.py with seed_project(project_path, memory_dir, project_id, verbose) main function skeleton
- [x] T048 [US1] Implement input validation in seed_project (path exists, is directory, readable) raising SeederError
- [x] T049 [US1] Implement project_id sanitization (regex to replace invalid chars) in seed_project
- [x] T050 [US1] Initialize HybridMemoryCore and store seeding metadata (**project_root**, **seeded_at**, **hmc_version**) in seed_project
- [x] T051 [US1] Create parse_persona_md(content) function in src/hmc/seeder.py to extract factual and semantic sections using regex
- [x] T052 [US1] Implement Factual section parsing in parse_persona_md (regex: `## Factual` followed by `- key: value` lines)
- [x] T053 [US1] Implement Semantic section parsing in parse_persona_md (regex: `## Semantic` followed by `- "example"` lines)
- [x] T054 [US1] Add persona seeding logic in seed*project: check for persona.md, parse it, store facts with \_\_persona* prefix, embed voice examples with type="persona_voice"
- [x] T055 [US1] Add graceful error handling for malformed persona.md (log warning, continue with valid sections)
- [x] T056 [US1] Create extract_tech_stack(project_path) function in src/hmc/seeder.py
- [x] T057 [US1] Implement requirements.txt parsing in extract_tech_stack (split lines, skip comments)
- [x] T058 [US1] Implement pyproject.toml parsing in extract_tech_stack using tomli/tomllib (extract dependencies from [project.dependencies])
- [x] T059 [US1] Implement package.json parsing in extract_tech_stack (extract dependencies and devDependencies)
- [x] T060 [US1] Store extracted tech stack as **tech_stack** fact in seed_project
- [x] T061 [US1] Create scan_project_structure(project_path) function in src/hmc/seeder.py
- [x] T062 [US1] Implement directory tree walking with os.walk excluding common dirs (.git, **pycache**, node_modules, venv, .hmc_memory)
- [x] T063 [US1] Collect file metadata (size, line count for text files) in scan_project_structure
- [x] T064 [US1] Store project structure as **project_structure** fact in seed_project
- [x] T065 [US1] Implement source file globbing in seed_project (patterns: _.py, _.js, _.ts, _.md)
- [x] T066 [US1] Process each source file: read content, chunk with chunker.py, embed with metadata (source_file, type="code_chunk", chunk_index, language, line_range)
- [x] T067 [US1] Add statistics tracking in seed_project (persona_facts, persona_voices, project_facts, code_chunks, files_processed, warnings)
- [x] T068 [US1] Implement verbose output in seed_project (print progress for each phase)
- [x] T069 [US1] Return statistics dict from seed_project

### CLI Integration for User Story 1

- [x] T070 [US1] Create src/hmc/cli.py with Typer app initialization
- [x] T071 [US1] Implement seed command with arguments: path (Path, required), memory_dir (Path, optional, default=".hmc_memory"), project_id (str, optional), verbose (bool, optional)
- [x] T072 [US1] Add Typer argument validation (path exists, is directory, readable)
- [x] T073 [US1] Call seed_project from seeder.py in the seed command
- [x] T074 [US1] Add success/error message formatting with typer.secho (green for success, red for errors, yellow for warnings)
- [x] T075 [US1] Add KeyboardInterrupt handling in CLI (exit code 130)
- [x] T076 [US1] Add CLI entry point `if __name__ == "__main__": app()` in src/hmc/cli.py

### Unit Tests for User Story 1

- [x] T077 [P] [US1] Create tests/unit/test_sqlite_store.py with fixtures for temp database
- [x] T078 [P] [US1] Write unit tests for SQLiteFactualStore.setup() (table creation, idempotency)
- [x] T079 [P] [US1] Write unit tests for SQLiteFactualStore.set_fact() (insert, update, JSON serialization)
- [x] T080 [P] [US1] Write unit tests for SQLiteFactualStore.get_fact() (retrieve, None for missing keys, JSON deserialization)
- [x] T081 [P] [US1] Write unit tests for SQLiteFactualStore validation errors (empty key, non-JSON-serializable value)
- [ ] T082 [P] [US1] Create tests/unit/test_chroma_store.py with fixtures for temp ChromaDB directory
- [ ] T083 [P] [US1] Write unit tests for ChromaSemanticStore.setup() (collection creation, idempotency)
- [ ] T084 [P] [US1] Write unit tests for ChromaSemanticStore.add_semantic() (embedding generation, metadata storage, UUID return)
- [ ] T085 [P] [US1] Write unit tests for ChromaSemanticStore.query_semantic() (similarity search, k parameter, filter parameter, result format)
- [ ] T086 [P] [US1] Write unit tests for ChromaSemanticStore validation errors (empty content, k <= 0, invalid metadata)
- [x] T087 [P] [US1] Create tests/unit/test_hybrid_memory_core.py with mock storage backends
- [x] T088 [P] [US1] Write unit tests for HybridMemoryCore.**init**() (project_id validation, directory creation, backend initialization, default backends)
- [x] T089 [P] [US1] Write unit tests for HybridMemoryCore delegation methods (set_fact, get_fact, add_semantic, query_semantic)
- [ ] T090 [P] [US1] Create tests/unit/test_chunker.py
- [ ] T091 [P] [US1] Write unit tests for chunk_file_content() (paragraph splitting, oversized section handling, line range tracking)
- [ ] T092 [P] [US1] Create tests/unit/test_persona_parser.py
- [ ] T093 [P] [US1] Write unit tests for parse_persona_md() (factual section parsing, semantic section parsing, malformed input handling)
- [ ] T094 [P] [US1] Create tests/unit/test_cli.py with Typer CliRunner
- [ ] T095 [P] [US1] Write unit tests for CLI seed command (argument parsing, validation, error messages, exit codes)

### Integration Tests for User Story 1

- [x] T096 [US1] Create tests/integration/test_seeder_brownfield.py with sample project fixture (Python files, requirements.txt, persona.md)
- [x] T097 [US1] Write integration test: seed sample project, verify .hmc_memory directory created
- [x] T098 [US1] Write integration test: verify persona facts stored with correct keys (**persona_name**, **persona_tone**, etc.)
- [x] T099 [US1] Write integration test: verify persona voice examples embedded with type="persona_voice" metadata
- [x] T100 [US1] Write integration test: verify tech stack extracted and stored as **tech_stack** fact
- [x] T101 [US1] Write integration test: verify project structure stored as **project_structure** fact
- [x] T102 [US1] Write integration test: verify source files chunked and embedded with correct metadata
- [x] T103 [US1] Write integration test: semantic search for code functionality returns correct chunks with source file metadata
- [x] T104 [US1] Write integration test: multiple seeding runs (upsert behavior verification)
- [x] T105 [US1] Write integration test: malformed persona.md handling (warnings logged, valid sections processed)

**Checkpoint**: User Story 1 (brownfield seeding) is fully functional and independently testable. This represents the MVP.

---

## Phase 4: User Story 2 - Use Memory API in AI Agent Application (Priority: P2)

**Goal**: Enable AI agents to programmatically store and retrieve workflow documents (specs, plans, tasks) using factual and semantic storage

**Independent Test**: Import HybridMemoryCore in a Python script, store workflow documents with metadata, retrieve via factual keys and semantic queries with filters

**Why Next**: Validates the primary consumption pattern for the library and demonstrates value of the hybrid storage model

### Implementation for User Story 2

**Note**: Core API already implemented in Phase 3 (US1). This phase focuses on testing workflow document patterns and creating examples.

- [x] T106 [P] [US2] Create examples/workflow_documents.py demonstrating spec/plan/task storage with structured metadata
- [x] T107 [P] [US2] Add example in examples/workflow_documents.py showing factual tracking (current_feature, task_counter)
- [x] T108 [P] [US2] Add example in examples/workflow_documents.py showing semantic queries with metadata filters (type="spec", feature="login")
- [x] T109 [P] [US2] Add example in examples/workflow_documents.py showing retrieval of all approved documents (status="approved" filter)

### Integration Tests for User Story 2

- [ ] T110 [P] [US2] Create tests/integration/test_workflow_documents.py
- [ ] T111 [P] [US2] Write integration test: store spec document with metadata (type='spec', feature='login', status='draft')
- [ ] T112 [P] [US2] Write integration test: query for specs by feature name with filter, verify correct results
- [ ] T113 [P] [US2] Write integration test: store multiple document types (spec, plan, task), query with type filter
- [ ] T114 [P] [US2] Write integration test: update document status (draft → approved), verify query with status filter
- [ ] T115 [P] [US2] Write integration test: factual key-value tracking (current_feature, task_counter) for workflow state
- [ ] T116 [P] [US2] Write integration test: semantic search ranking (verify most relevant document returned first)
- [ ] T117 [P] [US2] Write integration test: metadata preservation (all original metadata fields returned in query results)

**Checkpoint**: User Story 2 (workflow API) is fully functional and independently testable

---

## Phase 5: User Story 3 - Initialize Memory in New Project (Priority: P3)

**Goal**: Enable developers to easily set up HMC in greenfield projects without existing code to seed

**Independent Test**: Initialize HybridMemoryCore in an empty directory, verify memory directories created, manually store facts and semantic content, verify persistence

**Why Last**: Simpler than brownfield, builds on same API foundation from US1

### Implementation for User Story 3

**Note**: Core initialization already implemented in Phase 3 (US1). This phase focuses on greenfield-specific documentation and testing.

- [x] T118 [P] [US3] Create examples/greenfield_init.py demonstrating HybridMemoryCore initialization in empty project
- [x] T119 [P] [US3] Add example in examples/greenfield_init.py showing manual persona attribute storage
- [x] T120 [P] [US3] Add example in examples/greenfield_init.py showing manual voice example embedding
- [x] T121 [P] [US3] Add example in examples/greenfield_init.py demonstrating persistence verification (initialize twice, retrieve data)

### Integration Tests for User Story 3

- [ ] T122 [P] [US3] Create tests/integration/test_seeder_greenfield.py
- [ ] T123 [P] [US3] Write integration test: initialize HMC in empty directory, verify .hmc_memory created with sqlite and chroma subdirectories
- [ ] T124 [P] [US3] Write integration test: run `hmc seed` on empty project (no persona.md), verify graceful skip with appropriate message
- [ ] T125 [P] [US3] Write integration test: manually store facts, verify retrieval after HMC re-initialization (persistence)
- [ ] T126 [P] [US3] Write integration test: manually embed content, verify semantic search works after HMC re-initialization
- [ ] T127 [P] [US3] Write integration test: idempotent initialization (call HybridMemoryCore.**init** multiple times, verify no errors)

### Persistence Tests (Cross-Story)

- [x] T128 [P] [US3] Create tests/integration/test_persistence.py
- [x] T129 [P] [US3] Write integration test: store data, close HMC, create new HMC instance, verify all data persists (factual and semantic)
- [x] T130 [P] [US3] Write integration test: verify SQLite database file persistence across sessions
- [x] T131 [P] [US3] Write integration test: verify ChromaDB collection persistence across sessions

**Checkpoint**: User Story 3 (greenfield init) is fully functional and independently testable

---

## Phase 6: Examples and Documentation

**Purpose**: Complete examples and user-facing documentation

- [x] T132 [P] Create examples/sample_persona.md with well-formed example (Factual and Semantic sections)
- [x] T133 [P] Create examples/brownfield_seed.py with complete seeding example and output explanation
- [x] T134 [P] Update README.md with installation instructions (pip install, from source)
- [x] T135 [P] Update README.md with quick start for brownfield use case (US1)
- [x] T136 [P] Update README.md with quick start for greenfield use case (US3)
- [x] T137 [P] Update README.md with workflow documents example (US2)
- [ ] T138 [P] Add troubleshooting section to README.md (common errors, solutions)
- [ ] T139 [P] Add API reference section to README.md or create separate API.md

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final quality improvements, performance optimization, and release preparation

- [ ] T140 [P] Add type checking with mypy to all modules, fix any type errors
- [ ] T141 [P] Run black formatter on all source files (src/hmc/, tests/, examples/)
- [ ] T142 [P] Run ruff linter on all source files, fix all violations
- [ ] T143 [P] Review all Google-style docstrings for completeness and accuracy
- [ ] T144 [P] Run pytest with coverage report, ensure >85% coverage for src/hmc/ modules
- [ ] T145 [P] Fix any coverage gaps by adding unit tests for uncovered code paths
- [ ] T146 [P] Performance test: seed sample 50-file project, verify <30 second completion (SC-002)
- [ ] T147 [P] Performance test: query 10,000 semantic chunks, verify <100ms response (SC-009)
- [ ] T148 [P] Test backend swappability: create mock backend, inject into HybridMemoryCore, verify works (SC-008)
- [ ] T149 [P] Create CHANGELOG.md documenting v1.0.0 features
- [ ] T150 [P] Add package version to src/hmc/**init**.py (**version** = "1.0.0")
- [ ] T151 [P] Create .pre-commit-config.yaml with black, ruff, mypy hooks (optional but recommended)
- [ ] T152 Verify all Constitution principles: run checklist from plan.md Constitution Check section
- [ ] T153 Run full test suite (contract + integration + unit) and verify all pass
- [ ] T154 Build distribution packages (python -m build) and verify wheel/sdist created
- [ ] T155 Test installation from built wheel in fresh virtual environment

---

## Dependencies & Execution Strategy

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ↓
                  Phase 3 (US1 - P1) ← MVP FIRST
                      ↓
                  Phase 4 (US2 - P2)
                      ↓
                  Phase 5 (US3 - P3)
                      ↓
              Phase 6 (Examples) → Phase 7 (Polish)
```

**Independent Stories**: US1, US2, and US3 can technically be implemented in parallel after Phase 2, but sequential order by priority is recommended for clearest MVP path.

### Parallel Execution Opportunities

**Within Phase 1 (Setup)**:

- Tasks T007-T011 can run in parallel (tool configurations)

**Within Phase 2 (Foundational)**:

- All tasks (T013-T016) are sequential (interfaces must be complete before backends)

**Within Phase 3 (US1)**:

- Contract tests T017-T018 can run in parallel
- Backend implementations can be partially parallel:
  - T019-T025 (SQLite) can run parallel to T026-T033 (Chroma)
- Chunker (T044-T046) can run parallel to early backend work
- All unit test files (T077-T095) can be written in parallel once implementation complete

**Within Phase 4 (US2)**:

- All tasks (T106-T117) can run in parallel (examples and tests)

**Within Phase 5 (US3)**:

- All tasks (T118-T131) can run in parallel (examples and tests)

**Within Phase 6 (Examples)**:

- All tasks (T132-T139) can run in parallel (documentation)

**Within Phase 7 (Polish)**:

- Tasks T140-T151 can run in parallel (linting, formatting, docs)
- Tasks T152-T155 must be sequential (verification, build, test install)

### Suggested Implementation Order (MVP-First)

1. **Week 1**: Phase 1-2 (Setup + Foundational) → Establish project structure and core abstractions
2. **Week 2-3**: Phase 3 (US1) → Implement brownfield seeding (MVP)
   - Focus first on backends (T019-T033) and core API (T034-T043)
   - Then seeder utility (T044-T069) and CLI (T070-T076)
   - Finally tests (T077-T105)
3. **Week 4**: Phase 4 (US2) → Add workflow document support and examples
4. **Week 5**: Phase 5 (US3) → Complete greenfield support and persistence tests
5. **Week 6**: Phase 6-7 (Examples + Polish) → Documentation, optimization, release prep

**Total Tasks**: 155 tasks organized across 7 phases

---

## Task Statistics

- **Phase 1 (Setup)**: 12 tasks
- **Phase 2 (Foundational)**: 4 tasks
- **Phase 3 (US1 - MVP)**: 89 tasks
  - Contract tests: 2
  - Backend implementation: 15 (SQLite) + 8 (Chroma)
  - Core API: 10
  - Seeder utility: 26
  - CLI: 7
  - Unit tests: 19
  - Integration tests: 10
- **Phase 4 (US2)**: 12 tasks
- **Phase 5 (US3)**: 14 tasks
- **Phase 6 (Examples)**: 8 tasks
- **Phase 7 (Polish)**: 16 tasks

**Total**: 155 tasks

**Parallelizable**: ~60 tasks marked with [P] (39%)

**MVP Scope**: Phases 1-3 (105 tasks) deliver a fully functional brownfield seeding solution
**Full Release**: All 155 tasks deliver complete dual-use system with comprehensive testing and documentation
