"""Example: Brownfield seeding from an existing project.

This demonstrates using the CLI and API to seed memory from existing code.
"""

from pathlib import Path

from hmc import HybridMemoryCore

# Step 1: Use CLI to seed project (run this from terminal)
print("Step 1: Run CLI seeder")
print("=" * 50)
print("$ hmc seed /path/to/project --verbose")
print()
print("This will:")
print("  - Parse persona.md for attributes and voice examples")
print("  - Extract tech stack from requirements.txt/pyproject.toml")
print("  - Scan project structure")
print("  - Chunk and embed source files")
print()

# Step 2: Access seeded data via API
print("Step 2: Access seeded data via API")
print("=" * 50)

# Note: Replace with actual path after seeding
project_path = Path(__file__).parent.parent / "test_project"
if (project_path / ".hmc_memory").exists():
    memory = HybridMemoryCore(
        project_id="test_project",
        db_directory=str(project_path / ".hmc_memory")
    )

    # Retrieve persona facts
    print("\n📋 Persona Facts:")
    for key in ["name", "role", "tone"]:
        value = memory.get_fact(f"__persona_{key}__")
        if value:
            print(f"  {key}: {value}")

    # Retrieve tech stack
    print("\n🔧 Tech Stack:")
    tech_stack = memory.get_fact("__tech_stack__")
    if tech_stack:
        for dep in tech_stack[:5]:  # Show first 5
            print(f"  - {dep}")

    # Query semantic content
    print("\n🔍 Semantic Search - Find testing-related code:")
    results = memory.query_semantic("testing code", k=3)
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        content_preview = result["content"][:100].replace("\n", " ")
        print(f"    Content: {content_preview}...")
        print(f"    Source: {result['metadata'].get('source_file', 'N/A')}")
        print(f"    Type: {result['metadata'].get('type', 'N/A')}")

    print("\n✅ Brownfield seeding demonstration complete!")
else:
    print("\n⚠ Test project not seeded yet. Run:")
    print("  python -m hmc.cli test_project --verbose")
