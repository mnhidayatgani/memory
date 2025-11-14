"""Example: Greenfield initialization of HMC in a new project.

This demonstrates setting up HMC memory from scratch without existing code.
"""

from hmc import HybridMemoryCore

# Initialize HMC in a new project
memory = HybridMemoryCore(
    project_id="new-project",
    db_directory="./.hmc_memory"
)

print("✅ HMC initialized in new project")

# Manually store persona attributes
memory.set_fact("__persona_name__", "AssistantBot")
memory.set_fact("__persona_role__", "AI Development Assistant")
memory.set_fact("__persona_tone__", "Professional and helpful")
memory.set_fact("__persona_core_directive__", "Help developers write better code")

print("✅ Persona attributes stored")

# Manually add voice examples
voice_examples = [
    "I'm here to help you write better code",
    "Let me assist you with that implementation",
    "Consider using design patterns for better maintainability"
]

for example in voice_examples:
    memory.add_semantic(example, {"type": "persona_voice"})

print(f"✅ {len(voice_examples)} voice examples stored")

# Store workflow state
memory.set_fact("current_feature", "initialization")
memory.set_fact("task_counter", 0)

print("✅ Workflow state initialized")

# Verify persistence by creating a new instance
print("\n--- Testing persistence ---")
memory2 = HybridMemoryCore(
    project_id="new-project",
    db_directory="./.hmc_memory"
)

persona_name = memory2.get_fact("__persona_name__")
print(f"✅ Retrieved persona name: {persona_name}")

results = memory2.query_semantic("help with code", k=2)
print(f"✅ Semantic search found {len(results)} results")

print("\n✅ Greenfield initialization complete!")
print("   All data persists across sessions")
