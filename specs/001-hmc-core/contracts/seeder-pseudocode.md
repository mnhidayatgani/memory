# Seeder Pseudocode: CLI `hmc seed` Command

**Date**: 2025-11-14  
**Command**: `hmc seed <path> [--memory-dir DIR] [--project-id ID] [--verbose]`  
**Implementation**: `src/hmc/seeder.py` + `src/hmc/cli.py`

This document provides step-by-step pseudocode for the seeding algorithm that populates HMC memory from an existing project.

---

## High-Level Algorithm

```
FUNCTION seed_project(project_path, memory_dir, project_id, verbose):
    1. Validate inputs (project_path exists, is directory, readable)
    2. Initialize HybridMemoryCore(project_id, db_directory=memory_dir)
    3. Seed persona from persona.md (if exists)
    4. Seed factual project metadata (tech stack, directory structure)
    5. Seed semantic content (code chunks from source files)
    6. Report success metrics (files processed, facts stored, chunks embedded)
END FUNCTION
```

---

## Detailed Implementation

### Step 1: Validate Inputs & Initialize

```python
FUNCTION seed_project(project_path: Path, memory_dir: Path, project_id: str | None, verbose: bool):

    # 1.1 Validate project path
    IF NOT project_path.exists():
        RAISE SeederError(f"Project path does not exist: {project_path}")

    IF NOT project_path.is_dir():
        RAISE SeederError(f"Project path must be directory: {project_path}")

    IF NOT os.access(project_path, os.R_OK):
        RAISE SeederError(f"Project path not readable: {project_path}")

    # 1.2 Determine project_id
    IF project_id IS None:
        project_id = project_path.name  # Use directory name

    # Sanitize project_id (replace invalid chars with hyphens)
    project_id = re.sub(r'[^a-zA-Z0-9_-]', '-', project_id)

    IF verbose:
        PRINT(f"Seeding project: {project_id}")
        PRINT(f"  Project path: {project_path}")
        PRINT(f"  Memory dir: {memory_dir}")

    # 1.3 Initialize HybridMemoryCore
    TRY:
        full_memory_path = project_path / memory_dir
        hmc = HybridMemoryCore(project_id=project_id, db_directory=full_memory_path)
    EXCEPT (ValidationError, StorageError) AS error:
        RAISE SeederError(f"Failed to initialize HMC: {error}")

    # 1.4 Store seeding metadata
    hmc.set_fact("__project_root__", str(project_path.absolute()))
    hmc.set_fact("__seeded_at__", datetime.now(UTC).isoformat())
    hmc.set_fact("__hmc_version__", get_hmc_version())  # From package metadata

    # Initialize counters
    stats = {
        "persona_facts": 0,
        "persona_voices": 0,
        "project_facts": 0,
        "code_chunks": 0,
        "files_processed": 0,
        "warnings": []
    }

    # Continue with seeding steps...
```

### Step 2: Seed Persona from persona.md

```python
    # 2. Seed persona (if persona.md exists)
    persona_path = project_path / "persona.md"

    IF persona_path.exists():
        IF verbose:
            PRINT(f"Found persona.md, parsing...")

        TRY:
            persona_content = persona_path.read_text(encoding='utf-8')
            persona_data = parse_persona_md(persona_content)

            # 2.1 Store factual persona attributes
            FOR key, value IN persona_data['factual'].items():
                fact_key = f"__persona_{key}__"
                hmc.set_fact(fact_key, value)
                stats["persona_facts"] += 1

                IF verbose:
                    PRINT(f"  Stored persona fact: {fact_key} = {value[:50]}...")

            # 2.2 Store semantic persona voice examples
            FOR example IN persona_data['semantic']:
                embedding_id = hmc.add_semantic(
                    content=example,
                    metadata={"type": "persona_voice"}
                )
                stats["persona_voices"] += 1

                IF verbose:
                    PRINT(f"  Embedded voice example: {example[:50]}...")

        EXCEPT Exception AS error:
            warning = f"Failed to parse persona.md: {error}"
            stats["warnings"].append(warning)
            IF verbose:
                PRINT(f"  WARNING: {warning}")

    ELSE:
        IF verbose:
            PRINT("No persona.md found, skipping persona seeding")


FUNCTION parse_persona_md(content: str) -> dict:
    """Parse persona.md into factual attributes and semantic voice examples."""

    result = {
        "factual": {},      # Dict of key -> value
        "semantic": []      # List of voice example strings
    }

    # 2.1 Extract Factual section
    # Pattern: ## Factual\n- key: value\n- key: value\n...
    factual_match = re.search(
        r'##\s*Factual\s*\n(.*?)(?=##|\Z)',
        content,
        re.DOTALL | re.IGNORECASE
    )

    IF factual_match:
        factual_text = factual_match.group(1)

        # Parse each line: - key: "value" or - key: value
        FOR line IN factual_text.split('\n'):
            line = line.strip()

            # Match: - key: value (with optional quotes)
            match = re.match(r'^-\s*(\w+):\s*["\']?(.+?)["\']?\s*$', line)

            IF match:
                key, value = match.groups()
                result["factual"][key] = value.strip()

    # 2.2 Extract Semantic section
    # Pattern: ## Semantic (Voice Examples)\n- "example 1"\n- "example 2"\n...
    semantic_match = re.search(
        r'##\s*Semantic.*?\n(.*?)(?=##|\Z)',
        content,
        re.DOTALL | re.IGNORECASE
    )

    IF semantic_match:
        semantic_text = semantic_match.group(1)

        # Parse each line: - "voice example" or - voice example
        FOR line IN semantic_text.split('\n'):
            line = line.strip()

            IF line.startswith('-'):
                # Remove leading dash and optional quotes
                example = line[1:].strip()
                example = example.strip('"').strip("'")

                IF example:  # Non-empty
                    result["semantic"].append(example)

    RETURN result
```

### Step 3: Seed Factual Project Metadata

```python
    # 3. Seed factual project metadata
    IF verbose:
        PRINT("Scanning project structure and dependencies...")

    # 3.1 Scan and store technology stack
    tech_stack = extract_tech_stack(project_path)

    IF tech_stack:
        hmc.set_fact("__tech_stack__", tech_stack)
        stats["project_facts"] += 1

        IF verbose:
            PRINT(f"  Found {len(tech_stack.get('dependencies', []))} dependencies")

    # 3.2 Scan and store project structure
    project_structure = scan_project_structure(project_path)
    hmc.set_fact("__project_structure__", project_structure)
    stats["project_facts"] += 1

    IF verbose:
        PRINT(f"  Scanned {len(project_structure['files'])} files in {len(project_structure['directories'])} directories")


FUNCTION extract_tech_stack(project_path: Path) -> dict:
    """Extract dependencies from requirements.txt, pyproject.toml, package.json."""

    tech_stack = {
        "python_version": None,
        "dependencies": [],
        "dev_dependencies": []
    }

    # 3.1.1 Check requirements.txt
    requirements_path = project_path / "requirements.txt"
    IF requirements_path.exists():
        TRY:
            content = requirements_path.read_text(encoding='utf-8')
            FOR line IN content.split('\n'):
                line = line.strip()

                # Skip comments and empty lines
                IF line AND NOT line.startswith('#'):
                    tech_stack["dependencies"].append(line)

        EXCEPT Exception AS error:
            # Log warning but continue
            PASS

    # 3.1.2 Check pyproject.toml
    pyproject_path = project_path / "pyproject.toml"
    IF pyproject_path.exists():
        TRY:
            import tomli  # or tomllib in Python 3.11+

            WITH OPEN(pyproject_path, 'rb') AS f:
                data = tomli.load(f)

            # Extract Python version
            IF 'project' IN data AND 'requires-python' IN data['project']:
                tech_stack["python_version"] = data['project']['requires-python']

            # Extract dependencies
            IF 'project' IN data AND 'dependencies' IN data['project']:
                tech_stack["dependencies"].extend(data['project']['dependencies'])

            # Extract dev dependencies
            IF 'project' IN data AND 'optional-dependencies' IN data['project']:
                FOR group IN data['project']['optional-dependencies'].values():
                    tech_stack["dev_dependencies"].extend(group)

        EXCEPT Exception AS error:
            # Log warning but continue
            PASS

    # 3.1.3 Check package.json (for JS/TS projects)
    package_json_path = project_path / "package.json"
    IF package_json_path.exists():
        TRY:
            import json

            WITH OPEN(package_json_path) AS f:
                data = json.load(f)

            IF 'dependencies' IN data:
                FOR name, version IN data['dependencies'].items():
                    tech_stack["dependencies"].append(f"{name}@{version}")

            IF 'devDependencies' IN data:
                FOR name, version IN data['devDependencies'].items():
                    tech_stack["dev_dependencies"].append(f"{name}@{version}")

        EXCEPT Exception AS error:
            # Log warning but continue
            PASS

    RETURN tech_stack


FUNCTION scan_project_structure(project_path: Path) -> dict:
    """Scan directory tree and build structure dict."""

    structure = {
        "root": str(project_path.absolute()),
        "directories": [],
        "files": {}
    }

    # Directories to exclude from scanning
    EXCLUDE_DIRS = {
        ".git", "__pycache__", "node_modules", "venv", ".venv",
        ".tox", ".pytest_cache", ".mypy_cache", "dist", "build",
        ".hmc_memory"  # Don't scan our own memory directory!
    }

    # 3.2.1 Walk directory tree
    FOR root, dirs, files IN os.walk(project_path):
        # Filter out excluded directories (modifies dirs in-place)
        dirs[:] = [d FOR d IN dirs IF d NOT IN EXCLUDE_DIRS]

        # Store relative directory paths
        rel_root = Path(root).relative_to(project_path)
        IF str(rel_root) != '.':  # Skip project root itself
            structure["directories"].append(str(rel_root))

        # Store file metadata
        FOR filename IN files:
            file_path = Path(root) / filename
            rel_path = file_path.relative_to(project_path)

            TRY:
                stat = file_path.stat()

                # Count lines for text files
                line_count = None
                IF is_text_file(file_path):
                    TRY:
                        content = file_path.read_text(encoding='utf-8')
                        line_count = content.count('\n') + 1
                    EXCEPT:
                        PASS  # Binary or unreadable file

                structure["files"][str(rel_path)] = {
                    "size": stat.st_size,
                    "lines": line_count
                }

            EXCEPT Exception AS error:
                # Skip files that can't be stat'd
                PASS

    RETURN structure


FUNCTION is_text_file(file_path: Path) -> bool:
    """Check if file is likely a text file based on extension."""

    TEXT_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.txt', '.json',
        '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.sh',
        '.bash', '.zsh', '.css', '.scss', '.html', '.xml', '.sql',
        '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs', '.swift'
    }

    RETURN file_path.suffix.lower() IN TEXT_EXTENSIONS
```

### Step 4: Seed Semantic Content (Code Chunks)

```python
    # 4. Seed semantic content from source files
    IF verbose:
        PRINT("Embedding source file content...")

    SOURCE_PATTERNS = ['*.py', '*.js', '*.ts', '*.md', '*.txt']

    FOR pattern IN SOURCE_PATTERNS:
        FOR file_path IN project_path.rglob(pattern):
            # Skip excluded directories
            IF any(part IN EXCLUDE_DIRS FOR part IN file_path.parts):
                CONTINUE

            # Skip the memory directory
            IF '.hmc_memory' IN str(file_path):
                CONTINUE

            TRY:
                content = file_path.read_text(encoding='utf-8')
                rel_path = file_path.relative_to(project_path)

                # Chunk the file content
                chunks = chunk_file_content(content, max_size=2000)

                # Embed each chunk
                FOR index, chunk IN ENUMERATE(chunks):
                    metadata = {
                        "source_file": str(rel_path),
                        "type": "code_chunk",
                        "chunk_index": index,
                        "language": file_path.suffix[1:],  # Remove leading dot
                        "line_range": chunk['line_range']
                    }

                    hmc.add_semantic(
                        content=chunk['content'],
                        metadata=metadata
                    )
                    stats["code_chunks"] += 1

                stats["files_processed"] += 1

                IF verbose:
                    PRINT(f"  Processed {rel_path}: {len(chunks)} chunks")

            EXCEPT Exception AS error:
                warning = f"Failed to process {file_path}: {error}"
                stats["warnings"].append(warning)
                IF verbose:
                    PRINT(f"  WARNING: {warning}")


FUNCTION chunk_file_content(content: str, max_size: int = 2000) -> list[dict]:
    """Split file content into chunks with line tracking."""

    chunks = []
    current_chunk = []
    current_size = 0
    start_line = 1
    current_line = 1

    # Split into paragraphs/sections (on double newlines)
    sections = content.split('\n\n')

    FOR section IN sections:
        section_lines = section.count('\n') + 1
        section_size = len(section)

        # If adding this section exceeds max_size, finalize current chunk
        IF current_size + section_size > max_size AND current_chunk:
            chunks.append({
                'content': '\n\n'.join(current_chunk),
                'line_range': f"{start_line}-{current_line - 1}"
            })
            current_chunk = []
            current_size = 0
            start_line = current_line

        # If section itself is too large, split by character limit
        IF section_size > max_size:
            # Split long section into smaller parts
            FOR i IN RANGE(0, len(section), max_size):
                part = section[i:i + max_size]
                part_lines = part.count('\n') + 1

                chunks.append({
                    'content': part,
                    'line_range': f"{current_line}-{current_line + part_lines - 1}"
                })
                current_line += part_lines
        ELSE:
            current_chunk.append(section)
            current_size += section_size
            current_line += section_lines

    # Finalize last chunk
    IF current_chunk:
        chunks.append({
            'content': '\n\n'.join(current_chunk),
            'line_range': f"{start_line}-{current_line - 1}"
        })

    RETURN chunks
```

### Step 5: Report Results

```python
    # 5. Report seeding results
    IF verbose:
        PRINT("\nSeeding complete!")
        PRINT(f"  Persona facts: {stats['persona_facts']}")
        PRINT(f"  Persona voices: {stats['persona_voices']}")
        PRINT(f"  Project facts: {stats['project_facts']}")
        PRINT(f"  Code chunks: {stats['code_chunks']}")
        PRINT(f"  Files processed: {stats['files_processed']}")

        IF stats['warnings']:
            PRINT(f"\n  Warnings ({len(stats['warnings'])}):")
            FOR warning IN stats['warnings']:
                PRINT(f"    - {warning}")

    RETURN stats

END FUNCTION
```

---

## Complete CLI Integration

```python
# src/hmc/cli.py

import typer
from pathlib import Path
from .seeder import seed_project
from .exceptions import SeederError

app = typer.Typer(help="Hybrid Memory Core CLI")


@app.command()
def seed(
    path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    memory_dir: Path = typer.Option(".hmc_memory", "--memory-dir", "-m"),
    project_id: str | None = typer.Option(None, "--project-id", "-p"),
    verbose: bool = typer.Option(False, "--verbose", "-v")
) -> None:
    """Seed HMC memory from existing project files and persona.md."""

    TRY:
        stats = seed_project(
            project_path=path,
            memory_dir=memory_dir,
            project_id=project_id,
            verbose=verbose
        )

        # Success message
        typer.secho("✓ Seeding complete!", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"  Stored {stats['persona_facts']} persona facts")
        typer.echo(f"  Embedded {stats['persona_voices']} voice examples")
        typer.echo(f"  Indexed {stats['code_chunks']} code chunks from {stats['files_processed']} files")

        IF stats['warnings']:
            typer.secho(f"\n⚠ {len(stats['warnings'])} warnings", fg=typer.colors.YELLOW)

    EXCEPT SeederError AS error:
        typer.secho(f"✗ Seeding failed: {error}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(1)

    EXCEPT KeyboardInterrupt:
        typer.secho("\n✗ Seeding interrupted by user", fg=typer.colors.YELLOW)
        raise typer.Exit(130)


IF __name__ == "__main__":
    app()
```

---

## Example Execution Flow

```bash
$ hmc seed /home/user/my_project --verbose

Seeding project: my_project
  Project path: /home/user/my_project
  Memory dir: .hmc_memory

Found persona.md, parsing...
  Stored persona fact: __persona_name__ = J.A.R.V.I.S.
  Stored persona fact: __persona_role__ = A sophisticated AI assistant...
  Stored persona fact: __persona_tone__ = Polite, witty, British...
  Embedded voice example: Sir, might I recommend a more... elegant solution?
  Embedded voice example: The diagnostics are complete. All systems are...

Scanning project structure and dependencies...
  Found 15 dependencies
  Scanned 42 files in 8 directories

Embedding source file content...
  Processed src/main.py: 3 chunks
  Processed src/models/user.py: 2 chunks
  Processed src/utils/helpers.py: 1 chunks
  ...

Seeding complete!
  Persona facts: 6
  Persona voices: 3
  Project facts: 2
  Code chunks: 87
  Files processed: 42

✓ Seeding complete!
  Stored 6 persona facts
  Embedded 3 voice examples
  Indexed 87 code chunks from 42 files
```

---

## Summary

The seeder implements a robust, multi-phase algorithm:

1. ✅ Validates inputs and initializes HMC
2. ✅ Parses persona.md with regex (factual + semantic sections)
3. ✅ Extracts tech stack from requirements.txt / pyproject.toml / package.json
4. ✅ Scans project structure (directories and files)
5. ✅ Chunks and embeds source files (_.py, _.js, \*.md)
6. ✅ Reports detailed statistics and warnings
7. ✅ Graceful error handling (continues on individual file failures)
8. ✅ Verbose mode for debugging and transparency

All logic respects Constitution Principle 1 (Separation of Concerns) - the seeder is pure data extraction and storage, with no agent logic.
