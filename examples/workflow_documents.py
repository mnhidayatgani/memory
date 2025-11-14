"""Example: Storing and querying workflow documents.

This demonstrates using HMC for AI agent workflow management
with specs, plans, and tasks.
"""

from hmc import HybridMemoryCore

# Initialize memory for agent workflow
memory = HybridMemoryCore(
    project_id="agent-workflow",
    db_directory="./.hmc_memory"
)

print("🤖 Agent Workflow Example")
print("=" * 50)

# Store a spec document
spec_content = """
# User Authentication Feature

## Requirements
- Users can register with email and password
- JWT-based authentication
- Password reset functionality
- Email verification

## Technical Details
- Use bcrypt for password hashing
- JWT tokens expire after 24 hours
- Refresh tokens for extended sessions
"""

spec_id = memory.add_semantic(
    content=spec_content,
    metadata={
        "type": "spec",
        "feature": "authentication",
        "status": "approved",
        "author": "developer@example.com",
        "created": "2025-11-14"
    }
)
print(f"✅ Stored spec: {spec_id[:8]}...")

# Store a plan document
plan_content = """
# Implementation Plan: Authentication

## Phase 1: Database Schema
1. Create users table
2. Create sessions table
3. Add indexes for performance

## Phase 2: Core Logic
1. Implement password hashing
2. Implement JWT generation
3. Implement token validation

## Phase 3: API Endpoints
1. POST /register
2. POST /login
3. POST /refresh-token
"""

plan_id = memory.add_semantic(
    content=plan_content,
    metadata={
        "type": "plan",
        "feature": "authentication",
        "status": "in_progress"
    }
)
print(f"✅ Stored plan: {plan_id[:8]}...")

# Store task documents
tasks = [
    ("Create database schema for users", "completed"),
    ("Implement password hashing with bcrypt", "completed"),
    ("Implement JWT token generation", "in_progress"),
    ("Add email verification endpoint", "todo")
]

for task_desc, status in tasks:
    memory.add_semantic(
        content=task_desc,
        metadata={
            "type": "task",
            "feature": "authentication",
            "status": status
        }
    )
print(f"✅ Stored {len(tasks)} tasks")

# Track workflow state with factual storage
memory.set_fact("current_feature", "authentication")
memory.set_fact("tasks_completed", 2)
memory.set_fact("tasks_total", 4)
print("✅ Stored workflow state")

print("\n🔍 Query Examples:")
print("-" * 50)

# Query 1: Find all specs for authentication
print("\n1. All approved specs:")
specs = memory.query_semantic(
    query_text="authentication requirements",
    k=5,
    filter={"type": "spec", "status": "approved"}
)
print(f"   Found {len(specs)} spec(s)")

# Query 2: Find in-progress tasks
print("\n2. In-progress tasks:")
in_progress = memory.query_semantic(
    query_text="task",
    k=10,
    filter={"type": "task", "status": "in_progress"}
)
for task in in_progress:
    print(f"   - {task['content']}")

# Query 3: Find all authentication-related documents
print("\n3. All authentication documents:")
auth_docs = memory.query_semantic(
    query_text="authentication",
    k=10,
    filter={"feature": "authentication"}
)
for doc in auth_docs[:3]:  # Show top 3
    doc_type = doc['metadata'].get('type', 'unknown')
    content_preview = doc['content'][:60].replace("\n", " ")
    print(f"   [{doc_type}] {content_preview}...")

# Retrieve workflow state
print("\n📊 Workflow State:")
current_feature = memory.get_fact("current_feature")
tasks_completed = memory.get_fact("tasks_completed")
tasks_total = memory.get_fact("tasks_total")
print(f"   Feature: {current_feature}")
print(f"   Progress: {tasks_completed}/{tasks_total} tasks completed")

print("\n✅ Workflow documents example complete!")
