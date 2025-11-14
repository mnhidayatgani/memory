# pyproject.toml - Complete Configuration

**Date**: 2025-11-14  
**Package**: hmc (Hybrid Memory Core)  
**Python**: 3.10+

This is the complete content for the `pyproject.toml` file at repository root.

---

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "hmc"
version = "1.0.0"
description = "Hybrid Memory Core: Persistent factual and semantic memory for AI agents"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "HMC Contributors", email = "hmc@example.com"}
]
maintainers = [
    {name = "HMC Maintainers", email = "maintainers@example.com"}
]
keywords = [
    "ai",
    "memory",
    "vector-database",
    "chromadb",
    "sqlite",
    "agent",
    "semantic-search",
    "knowledge-base"
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
requires-python = ">=3.10"

# Runtime dependencies
dependencies = [
    "chromadb>=0.4.0,<1.0.0",    # Semantic vector storage
    "typer[all]>=0.9.0,<1.0.0",  # CLI framework (includes rich for formatting)
]

[project.optional-dependencies]
# Development dependencies
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.5.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "pre-commit>=3.3.0",
]

# Testing dependencies (subset of dev)
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
]

# Documentation dependencies
docs = [
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.3.0",
    "sphinx-autodoc-typehints>=1.24.0",
]

[project.urls]
Homepage = "https://github.com/your-org/hmc"
Documentation = "https://hmc.readthedocs.io"
Repository = "https://github.com/your-org/hmc"
"Bug Tracker" = "https://github.com/your-org/hmc/issues"
Changelog = "https://github.com/your-org/hmc/blob/main/CHANGELOG.md"

# CLI entry points
[project.scripts]
hmc = "hmc.cli:app"

# Package discovery (for setuptools)
[tool.setuptools.packages.find]
where = ["src"]
include = ["hmc*"]
exclude = ["tests*"]

# Package data (include py.typed for PEP 561)
[tool.setuptools.package-data]
hmc = ["py.typed"]

# ============================================================================
# Tool Configurations
# ============================================================================

# --- pytest configuration ---
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",                     # Show summary of all test outcomes
    "--strict-markers",        # Fail on unknown markers
    "--strict-config",         # Fail on config errors
    "--cov=hmc",              # Measure coverage for hmc package
    "--cov-report=term-missing:skip-covered",  # Show missing lines
    "--cov-report=html",       # Generate HTML report
    "--cov-report=xml",        # Generate XML report (for CI)
    "--cov-fail-under=85",     # Fail if coverage below 85%
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "contract: marks tests as contract tests for ABCs",
]

# --- mypy configuration ---
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
strict = true

# Per-module options
[[tool.mypy.overrides]]
module = "chromadb.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
disallow_incomplete_defs = false

# --- black configuration ---
[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.mypy_cache
  | \.pytest_cache
  | \.tox
  | \.venv
  | venv
  | dist
  | build
  | __pycache__
)/
'''

# --- ruff configuration ---
[tool.ruff]
line-length = 100
target-version = "py310"

# Enable specific rule sets
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "N",   # pep8-naming
    "UP",  # pyupgrade (modern syntax)
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
    "TCH", # flake8-type-checking
]

# Ignore specific rules
ignore = [
    "E501",  # Line too long (handled by black)
    "B008",  # Do not perform function calls in argument defaults (Typer uses this)
]

# Exclude directories
exclude = [
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
"tests/**/*.py" = ["N802", "N803"]  # Allow non-lowercase function names in tests

[tool.ruff.isort]
known-first-party = ["hmc"]
force-single-line = false
lines-after-imports = 2

# --- coverage configuration ---
[tool.coverage.run]
source = ["src/hmc"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]

[tool.coverage.html]
directory = "htmlcov"

# --- pre-commit hook configuration (optional but recommended) ---
# Create .pre-commit-config.yaml separately with:
# repos:
#   - repo: https://github.com/psf/black
#     rev: 23.x.x
#     hooks:
#       - id: black
#   - repo: https://github.com/charliermarsh/ruff-pre-commit
#     rev: v0.1.x
#     hooks:
#       - id: ruff
#   - repo: https://github.com/pre-commit/mirrors-mypy
#     rev: v1.5.x
#     hooks:
#       - id: mypy
```

---

## Installation Instructions

### For End Users

```bash
# Install from PyPI (once published)
pip install hmc

# Or install from source
git clone https://github.com/your-org/hmc.git
cd hmc
pip install .

# Install with development dependencies
pip install -e ".[dev]"

# Install only test dependencies
pip install -e ".[test]"
```

### For Developers

```bash
# Clone repository
git clone https://github.com/your-org/hmc.git
cd hmc

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with all dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pre-commit install

# Run tests
pytest

# Run type checking
mypy src/hmc

# Run linting
ruff check src/hmc tests

# Format code
black src/hmc tests
```

## Verify Installation

```bash
# Check CLI is available
hmc --help

# Output should show:
# Usage: hmc [OPTIONS] COMMAND [ARGS]...
#
#   Hybrid Memory Core CLI
#
# Options:
#   --help  Show this message and exit.
#
# Commands:
#   seed  Seed HMC memory from existing project files and persona.md

# Verify package import
python -c "from hmc import HybridMemoryCore; print('HMC installed successfully!')"
```

## Build and Publish

```bash
# Build distribution packages
python -m build

# This creates:
# - dist/hmc-1.0.0-py3-none-any.whl (wheel)
# - dist/hmc-1.0.0.tar.gz (source distribution)

# Publish to PyPI (requires twine and credentials)
python -m twine upload dist/*

# Publish to Test PyPI first (recommended)
python -m twine upload --repository testpypi dist/*
```

## Key Configuration Highlights

1. **Entry Point**: `hmc = "hmc.cli:app"` creates the `hmc` CLI command
2. **Type Checking**: `mypy` configured for strict mode with Python 3.10+ features
3. **Code Quality**: `black` (formatting) + `ruff` (fast linting) + `pytest` (testing)
4. **Coverage Target**: 85% minimum per Constitution Principle 5
5. **Python Version**: Requires 3.10+ for modern type hints (`X | Y` syntax)
6. **Package Layout**: Uses `src/hmc` layout per Constitution Principle 2
7. **Type Stub**: Includes `py.typed` marker for PEP 561 compliance

All configuration adheres to Constitution principles and modern Python best practices (PEP 517, PEP 621, PEP 561).
