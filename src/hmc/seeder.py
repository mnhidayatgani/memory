"""Project seeding utilities for HMC.

This module provides functionality to populate HMC memory from existing
project files, including persona.md parsing and source file chunking.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hmc.chunker import chunk_file_content
from hmc.core import HybridMemoryCore
from hmc.exceptions import SeederError


def parse_persona_md(content: str) -> dict[str, dict[str, Any]]:
    """Parse persona.md file to extract factual and semantic sections.

    Expected format:
        ## Factual
        - key: value
        - another_key: another value

        ## Semantic (Voice Examples)
        - "Example voice quote 1"
        - "Example voice quote 2"

    Args:
        content: Raw persona.md file content

    Returns:
        Dictionary with "factual" and "semantic" keys:
            - "factual": dict mapping keys to values
            - "semantic": list of voice example strings

    Example:
        >>> content = "## Factual\\n- name: Bot\\n\\n## Semantic\\n- \\"Hello\\""
        >>> result = parse_persona_md(content)
        >>> "name" in result["factual"]
        True
    """
    result: dict[str, dict[str, Any] | list[str]] = {"factual": {}, "semantic": []}

    # Extract Factual section
    factual_match = re.search(
        r"##\s+Factual\s*\n(.*?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE
    )
    if factual_match:
        factual_section = factual_match.group(1)
        # Parse "- key: value" lines
        for line in factual_section.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                # Remove leading "-" and split on first ":"
                kv = line[1:].strip()
                if ":" in kv:
                    key, value = kv.split(":", 1)
                    result["factual"][key.strip()] = value.strip()  # type: ignore

    # Extract Semantic section
    semantic_match = re.search(
        r"##\s+Semantic(?:\s+\(.*?\))?\s*\n(.*?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE
    )
    if semantic_match:
        semantic_section = semantic_match.group(1)
        # Parse "- "quoted text"" lines
        for line in semantic_section.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                # Remove leading "-" and extract quoted text
                text = line[1:].strip()
                # Remove quotes if present
                if (text.startswith('"') and text.endswith('"')) or (
                    text.startswith("'") and text.endswith("'")
                ):
                    text = text[1:-1]
                if text:
                    result["semantic"].append(text)  # type: ignore

    return result  # type: ignore


def extract_tech_stack(project_path: Path) -> list[str]:
    """Extract technology stack from dependency files.

    Checks for requirements.txt, pyproject.toml, and package.json.

    Args:
        project_path: Path to project root directory

    Returns:
        List of dependency strings (e.g., ["chromadb>=0.4.0", "typer>=0.9.0"])
    """
    dependencies: list[str] = []

    # Check requirements.txt
    req_file = project_path / "requirements.txt"
    if req_file.exists():
        try:
            content = req_file.read_text(encoding="utf-8")
            for line in content.split("\n"):
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith("#"):
                    dependencies.append(line)
        except Exception:
            pass  # Ignore parsing errors

    # Check pyproject.toml
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        try:
            content = pyproject_file.read_text(encoding="utf-8")
            # Simple regex to extract dependencies (not full TOML parsing)
            deps_match = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if deps_match:
                deps_content = deps_match.group(1)
                # Extract quoted strings
                for match in re.finditer(r'["\']([^"\']+)["\']', deps_content):
                    dependencies.append(match.group(1))
        except Exception:
            pass

    # Check package.json
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            if "dependencies" in data:
                for pkg, version in data["dependencies"].items():
                    dependencies.append(f"{pkg}@{version}")
            if "devDependencies" in data:
                for pkg, version in data["devDependencies"].items():
                    dependencies.append(f"{pkg}@{version} (dev)")
        except Exception:
            pass

    return dependencies


def scan_project_structure(project_path: Path) -> dict[str, Any]:
    """Scan project directory structure.

    Args:
        project_path: Path to project root

    Returns:
        Dictionary with file counts and directory structure info
    """
    excluded_dirs = {".git", "__pycache__", "node_modules", "venv", ".hmc_memory", "dist", "build"}

    structure = {"total_files": 0, "total_dirs": 0, "file_types": {}}

    for _root, dirs, files in os.walk(project_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith(".")]

        structure["total_dirs"] += len(dirs)
        structure["total_files"] += len(files)

        for file in files:
            ext = Path(file).suffix or "no_extension"
            structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1

    return structure


def seed_project(
    project_path: Path | str,
    memory_dir: Path | str,
    project_id: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Seed HMC memory from existing project files.

    Args:
        project_path: Path to project root directory
        memory_dir: Path to memory storage directory (relative or absolute)
        project_id: Optional project identifier (defaults to directory name)
        verbose: Enable verbose output

    Returns:
        Statistics dictionary with seeding results

    Raises:
        SeederError: If seeding fails
    """
    project_path = Path(project_path)
    memory_dir = Path(memory_dir)

    # Validate project path
    if not project_path.exists():
        raise SeederError(
            f"Project path does not exist: {project_path}", file_path=str(project_path)
        )

    if not project_path.is_dir():
        raise SeederError(
            f"Project path must be a directory: {project_path}", file_path=str(project_path)
        )

    if not os.access(project_path, os.R_OK):
        raise SeederError(f"Project path not readable: {project_path}", file_path=str(project_path))

    # Determine project_id
    if project_id is None:
        project_id = project_path.name

    # Sanitize project_id
    project_id = re.sub(r"[^a-zA-Z0-9_-]", "-", project_id)

    if verbose:
        print(f"🌱 Seeding project: {project_id}")
        print(f"   Project path: {project_path}")
        print(f"   Memory dir: {memory_dir}")

    # Initialize HMC
    try:
        full_memory_path = project_path / memory_dir if not memory_dir.is_absolute() else memory_dir
        hmc = HybridMemoryCore(project_id=project_id, db_directory=str(full_memory_path))
    except Exception as e:
        raise SeederError(f"Failed to initialize HMC: {e}")

    # Store metadata
    hmc.set_fact("__project_root__", str(project_path.absolute()))
    hmc.set_fact("__seeded_at__", datetime.now(timezone.utc).isoformat())

    # Initialize statistics
    stats = {
        "persona_facts": 0,
        "persona_voices": 0,
        "project_facts": 0,
        "code_chunks": 0,
        "files_processed": 0,
        "warnings": [],
    }

    # Seed persona
    persona_path = project_path / "persona.md"
    if persona_path.exists():
        if verbose:
            print("📋 Parsing persona.md...")
        try:
            persona_content = persona_path.read_text(encoding="utf-8")
            persona_data = parse_persona_md(persona_content)

            # Store factual attributes
            for key, value in persona_data["factual"].items():  # type: ignore
                fact_key = f"__persona_{key}__"
                hmc.set_fact(fact_key, value)
                stats["persona_facts"] += 1

            # Store voice examples
            for example in persona_data["semantic"]:  # type: ignore
                hmc.add_semantic(example, {"type": "persona_voice", "source_file": "persona.md"})
                stats["persona_voices"] += 1

            if verbose:
                facts_count = stats["persona_facts"]
                voices_count = stats["persona_voices"]
                print(f"   ✓ Stored {facts_count} facts, {voices_count} voice examples")
        except Exception as e:
            stats["warnings"].append(f"Failed to parse persona.md: {e}")
            if verbose:
                print(f"   ⚠ Warning: {stats['warnings'][-1]}")

    # Extract tech stack
    if verbose:
        print("🔧 Extracting tech stack...")
    tech_stack = extract_tech_stack(project_path)
    if tech_stack:
        hmc.set_fact("__tech_stack__", tech_stack)
        stats["project_facts"] += 1
        if verbose:
            print(f"   ✓ Found {len(tech_stack)} dependencies")

    # Scan project structure
    if verbose:
        print("📁 Scanning project structure...")
    structure = scan_project_structure(project_path)
    hmc.set_fact("__project_structure__", structure)
    stats["project_facts"] += 1
    if verbose:
        print(f"   ✓ Found {structure['total_files']} files, {structure['total_dirs']} directories")

    # Seed source files
    if verbose:
        print("📝 Processing source files...")

    source_patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.md"]
    excluded_dirs = {".git", "__pycache__", "node_modules", "venv", ".hmc_memory"}

    for pattern in source_patterns:
        for file_path in project_path.glob(pattern):
            # Skip files in excluded directories
            if any(excluded in file_path.parts for excluded in excluded_dirs):
                continue

            # Skip if not a file
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                chunks = chunk_file_content(content, max_size=2000)

                # Determine language from extension
                ext_to_lang = {
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".md": "markdown",
                }
                language = ext_to_lang.get(file_path.suffix, "unknown")

                # Embed each chunk
                for i, chunk in enumerate(chunks):
                    relative_path = file_path.relative_to(project_path)
                    metadata = {
                        "type": "code_chunk",
                        "source_file": str(relative_path),
                        "language": language,
                        "chunk_index": i,
                        "line_range": f"{chunk['line_range'][0]}-{chunk['line_range'][1]}",
                    }
                    hmc.add_semantic(chunk["content"], metadata)  # type: ignore
                    stats["code_chunks"] += 1

                stats["files_processed"] += 1

                if verbose and stats["files_processed"] % 10 == 0:
                    print(f"   Processed {stats['files_processed']} files...")

            except Exception as e:
                stats["warnings"].append(f"Failed to process {file_path}: {e}")

    if verbose:
        files_count = stats["files_processed"]
        chunks_count = stats["code_chunks"]
        print(f"   ✓ Processed {files_count} files, created {chunks_count} chunks")

    if verbose:
        print("\n✅ Seeding complete!")
        print(f"   Persona facts: {stats['persona_facts']}")
        print(f"   Persona voices: {stats['persona_voices']}")
        print(f"   Project facts: {stats['project_facts']}")
        print(f"   Code chunks: {stats['code_chunks']}")
        print(f"   Files processed: {stats['files_processed']}")
        if stats["warnings"]:
            print(f"   ⚠ Warnings: {len(stats['warnings'])}")

    return stats
