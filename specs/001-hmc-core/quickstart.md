# Quickstart Guide: Hybrid Memory Core (HMC)

**Date**: 2025-11-14  
**Package**: hmc v1.0.0  
**Python**: 3.10+

This guide shows you how to use HMC in both **greenfield** (new project) and **brownfield** (existing project) scenarios, per Constitution Principle 3 (Dual-Use Mandate).

---

## Installation

```bash
# Install from PyPI
pip install hmc

# Or install from source
git clone https://github.com/your-org/hmc.git
cd hmc
pip install -e .
```

Verify installation:

```bash
hmc --help
python -c "from hmc import HybridMemoryCore; print('OK')"
```

---

## Use Case 1: Brownfield - Seed Existing Project (Priority: P1)

**Scenario**: You have an existing Python project and want to add AI agent capabilities with memory.

### Step 1: Create a persona.md File

Create `persona.md` in your project root:

```markdown
# Persona: J.A.R.V.I.S.

## Factual

- name: J.A.R.V.I.S.
- role: A sophisticated AI assistant, originally for Tony Stark.
- tone: Polite, witty, British, slightly formal, unfailingly helpful.
- user_title: Sir
- core_directive: Provide information, manage systems, and assist the user.
- language_rule: MUST respond in English, regardless of the user's input language.

## Semantic (Voice Examples)

- "Sir, might I recommend a more... elegant solution?"
- "The diagnostics are complete. All systems are operational."
- "My apologies, Sir, but I must advise against that course of action."
```

### Step 2: Run the Seeder CLI

```bash
# From your project root
cd /path/to/your/project

# Seed the memory (creates .hmc_memory/ directory)
hmc seed . --verbose

# Output:
# Seeding project: your-project
#   Project path: /path/to/your/project
#   Memory dir: .hmc_memory
#
# Found persona.md, parsing...
#   Stored persona fact: __persona_name__ = J.A.R.V.I.S.
#   Stored persona fact: __persona_tone__ = Polite, witty, British...
#   Embedded voice example: Sir, might I recommend...
#
# Scanning project structure and dependencies...
#   Found 15 dependencies
#   Scanned 42 files in 8 directories
#
# Embedding source file content...
#   Processed src/main.py: 3 chunks
#   Processed src/models/user.py: 2 chunks
#   ...
#
# ✓ Seeding complete!
#   Stored 6 persona facts
#   Embedded 3 voice examples
#   Indexed 87 code chunks from 42 files
```

### Step 3: Use the Memory in Your AI Agent

```python
from hmc import HybridMemoryCore

# Initialize HMC (connects to seeded memory)
hmc = HybridMemoryCore(
    project_id="your-project",
    db_directory=".hmc_memory"
)

# Retrieve persona attributes
persona_name = hmc.get_fact("__persona_name__")
persona_tone = hmc.get_fact("__persona_tone__")

print(f"Agent Name: {persona_name}")
print(f"Tone: {persona_tone}")

# Output:
# Agent Name: J.A.R.V.I.S.
# Tone: Polite, witty, British, slightly formal, unfailingly helpful.

# Search for code examples semantically
results = hmc.query_semantic(
    "user authentication code",
    k=3,
    filter={"type": "code_chunk"}
)

for result in results:
    print(f"\nFile: {result['metadata']['source_file']}")
    print(f"Lines: {result['metadata']['line_range']}")
    print(f"Distance: {result['distance']:.3f}")
    print(f"Content preview: {result['content'][:100]}...")
```

---

## Use Case 2: Greenfield - Initialize in New Project (Priority: P3)

**Scenario**: Starting a fresh project and want to set up memory from scratch.

### Step 1: Initialize HybridMemoryCore Programmatically

```python
from hmc import HybridMemoryCore

# Initialize in new project (creates .hmc_memory/ automatically)
hmc = HybridMemoryCore(
    project_id="my-new-agent",
    db_directory=".hmc_memory"
)

# Store persona attributes manually
hmc.set_fact("__persona_name__", "Cortana")
hmc.set_fact("__persona_role__", "Personal AI assistant")
hmc.set_fact("__persona_tone__", "Friendly, professional, concise")

# Store semantic persona voice examples
hmc.add_semantic(
    "I'm here to help you stay organized.",
    metadata={"type": "persona_voice"}
)
hmc.add_semantic(
    "Let me take care of that for you.",
    metadata={"type": "persona_voice"}
)

print("✓ Persona initialized!")
```

### Step 2: Run Seeder on Empty Project (Optional)

Even in a new project, you can run the seeder to populate from files as they're added:

```bash
# This will gracefully skip persona.md if missing
hmc seed . --verbose

# Output:
# Seeding project: my-new-agent
#   Project path: /path/to/new/project
#   Memory dir: .hmc_memory
#
# No persona.md found, skipping persona seeding
#
# Scanning project structure and dependencies...
#   Found 0 dependencies
#   Scanned 0 files in 0 directories
#
# ✓ Seeding complete!
#   Stored 0 persona facts
#   Embedded 0 voice examples
#   Indexed 0 code chunks from 0 files
```

---

## Use Case 3: AI Agent Workflow - Store Specs & Plans (Priority: P2)

**Scenario**: Your AI agent generates workflow documents (specs, plans, tasks) and needs to store them for future reference.

### Step 1: Initialize Memory

```python
from hmc import HybridMemoryCore

hmc = HybridMemoryCore(
    project_id="agent-workflows",
    db_directory=".hmc_memory"
)
```

### Step 2: Store Workflow Documents

```python
# Agent generates a spec for "login" feature
spec_content = """
# Feature Specification: User Login

## User Story
As a user, I want to log in with email and password
so that I can access my personalized dashboard.

## Requirements
- Email validation
- Password minimum 8 characters
- Session management with JWT
...
"""

# Store spec semantically with metadata
spec_id = hmc.add_semantic(
    content=spec_content,
    metadata={
        "type": "spec",
        "feature": "login",
        "status": "draft",
        "created_at": "2025-11-14T10:00:00Z"
    }
)

print(f"Stored spec with ID: {spec_id}")

# Agent generates an implementation plan
plan_content = """
# Implementation Plan: User Login

## Phase 1: Backend
1. Create User model
2. Implement authentication endpoint
3. Add JWT token generation
...
"""

# Store plan
plan_id = hmc.add_semantic(
    content=plan_content,
    metadata={
        "type": "plan",
        "feature": "login",
        "status": "approved",
        "created_at": "2025-11-14T11:00:00Z"
    }
)

# Track current feature in factual store
hmc.set_fact("current_feature", "login")
hmc.set_fact("task_counter", 0)
```

### Step 3: Query Workflow Documents

```python
# Find all plans for "login" feature
login_plans = hmc.query_semantic(
    "implementation plan for login",
    k=5,
    filter={"type": "plan", "feature": "login"}
)

for plan in login_plans:
    print(f"Plan: {plan['metadata']['feature']}")
    print(f"Status: {plan['metadata']['status']}")
    print(f"Preview: {plan['content'][:100]}...")
    print()

# Find all approved workflow documents
approved_docs = hmc.query_semantic(
    "approved documents",
    k=10,
    filter={"status": "approved"}
)

# Get current feature from factual store
current = hmc.get_fact("current_feature")
print(f"Currently working on: {current}")
```

---

## Advanced Usage

### Custom Storage Backends

```python
from hmc import HybridMemoryCore
from hmc.interfaces import FactualStorage, SemanticStorage

# Implement custom storage backend
class MyCustomFactualStore(FactualStorage):
    def setup(self) -> None:
        # Your custom setup logic
        pass

    def set_fact(self, key: str, value: Any) -> None:
        # Your custom storage logic
        pass

    def get_fact(self, key: str) -> Any | None:
        # Your custom retrieval logic
        pass

# Inject custom backend
hmc = HybridMemoryCore(
    project_id="custom-agent",
    db_directory=".hmc_memory",
    factual_store=MyCustomFactualStore(),  # Custom backend
    # semantic_store defaults to ChromaSemanticStore
)
```

### CLI Options

```bash
# Seed with custom memory directory
hmc seed /path/to/project --memory-dir custom_memory

# Seed with custom project ID
hmc seed /path/to/project --project-id my-custom-id

# Combine options
hmc seed . --memory-dir .agent_memory --project-id jarvis --verbose
```

### Programmatic Seeding

```python
from hmc.seeder import seed_project
from pathlib import Path

# Seed programmatically instead of CLI
stats = seed_project(
    project_path=Path("/path/to/project"),
    memory_dir=Path(".hmc_memory"),
    project_id="my-agent",
    verbose=True
)

print(f"Processed {stats['files_processed']} files")
print(f"Created {stats['code_chunks']} code chunks")
```

---

## Common Patterns

### Pattern 1: Persona-Driven Responses

```python
# Load persona attributes
name = hmc.get_fact("__persona_name__")
tone = hmc.get_fact("__persona_tone__")

# Query voice examples for style matching
examples = hmc.query_semantic(
    "greeting user",
    k=3,
    filter={"type": "persona_voice"}
)

# Use in prompt construction
prompt = f"""
You are {name}.
Tone: {tone}
Example responses:
{chr(10).join(ex['content'] for ex in examples)}

User query: {user_input}
"""
```

### Pattern 2: Context-Aware Code Assistance

```python
# User asks: "How do we handle user authentication?"

# Search codebase semantically
auth_code = hmc.query_semantic(
    "user authentication login password",
    k=5,
    filter={"type": "code_chunk"}
)

# Present relevant code to user or include in agent context
for chunk in auth_code:
    print(f"Found in: {chunk['metadata']['source_file']}")
    print(chunk['content'])
    print("-" * 80)
```

### Pattern 3: Multi-Project Memory

```python
# Agent works on multiple projects
project_a = HybridMemoryCore("project-a", ".hmc_memory_a")
project_b = HybridMemoryCore("project-b", ".hmc_memory_b")

# Each project has isolated memory
project_a.set_fact("current_task", "implement login")
project_b.set_fact("current_task", "fix payment bug")

# Switch between projects seamlessly
```

---

## File Structure After Seeding

```
your-project/
├── .hmc_memory/              # HMC storage directory
│   ├── facts.db              # SQLite database (factual store)
│   └── chroma/               # ChromaDB directory (semantic store)
│       ├── chroma.sqlite3    # ChromaDB index
│       └── ...               # Embedding data
├── persona.md                # Your persona definition
├── src/                      # Your project source code
├── requirements.txt          # Dependencies
└── ...
```

**Tip**: Add `.hmc_memory/` to `.gitignore` if memory data should not be version-controlled.

---

## Troubleshooting

### Error: "Failed to initialize ChromaDB client"

**Cause**: ChromaDB can't create collection or persistence directory

**Solution**: Ensure directory is writable, or specify custom path:

```python
hmc = HybridMemoryCore("my-agent", db_directory="/tmp/hmc_test")
```

### Error: "project_id must be alphanumeric with hyphens/underscores only"

**Cause**: Invalid characters in project_id

**Solution**: Use only letters, numbers, hyphens, and underscores:

```python
# Bad: "my agent!" → Good: "my-agent"
hmc = HybridMemoryCore("my-agent", ".hmc_memory")
```

### Warning: "Failed to parse persona.md"

**Cause**: Malformed persona.md (missing headers, invalid syntax)

**Solution**: Check persona.md format:

- Must have `## Factual` and/or `## Semantic (Voice Examples)` headers
- Factual items: `- key: value` format
- Semantic items: `- "example text"` format

### Seeder Skips Files

**Cause**: Files in excluded directories or non-text file types

**Solution**: Check that files are in included paths and have supported extensions:

- Included: `*.py`, `*.js`, `*.ts`, `*.md`, `*.txt`
- Excluded dirs: `.git`, `__pycache__`, `node_modules`, `venv`, `.hmc_memory`

---

## Next Steps

1. **Read the Full Documentation**: [https://hmc.readthedocs.io](https://hmc.readthedocs.io)
2. **Explore Examples**: Check `examples/` directory in the repository
3. **Customize**: Implement custom storage backends for your specific needs
4. **Contribute**: Report issues or contribute at [https://github.com/your-org/hmc](https://github.com/your-org/hmc)

---

## Quick Reference

### API Cheat Sheet

```python
from hmc import HybridMemoryCore

# Initialize
hmc = HybridMemoryCore("project-id", ".hmc_memory")

# Factual storage (key-value)
hmc.set_fact("key", "value")          # Store
value = hmc.get_fact("key")            # Retrieve (returns None if missing)

# Semantic storage (vector embeddings)
id = hmc.add_semantic(                 # Store with embedding
    "text content",
    metadata={"type": "spec", "feature": "login"}
)

results = hmc.query_semantic(          # Search by similarity
    "query text",
    k=5,                               # Max results
    filter={"type": "spec"}            # Metadata filter
)
```

### CLI Cheat Sheet

```bash
# Seed project
hmc seed <path> [--memory-dir DIR] [--project-id ID] [--verbose]

# Examples
hmc seed .                             # Seed current directory
hmc seed /path/to/project --verbose    # Verbose output
hmc seed . --project-id my-agent       # Custom project ID
```

---

**Happy Memory Building! 🚀**
