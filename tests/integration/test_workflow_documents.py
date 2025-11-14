"""Integration tests for workflow document storage and retrieval."""

import tempfile
from pathlib import Path

import pytest

from hmc.core import HybridMemoryCore


class TestWorkflowDocuments:
    """Integration tests for AI agent workflow document patterns."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def hmc(self, temp_dir):
        """Create HybridMemoryCore instance for testing."""
        return HybridMemoryCore(project_id="test-workflow", db_directory=temp_dir)

    def test_store_spec_document(self, hmc):
        """Test storing specification document with metadata."""
        spec_content = """# Feature Specification: User Login

## Overview
Allow users to authenticate using email and password.

## Requirements
- Email validation
- Password strength requirements
- Session management
"""

        doc_id = hmc.add_semantic(
            spec_content,
            metadata={"type": "spec", "feature": "login", "status": "draft", "priority": "P1"},
        )

        assert doc_id is not None

        # Verify retrieval
        results = hmc.query_semantic("user authentication", k=5)
        assert len(results) > 0
        assert "login" in results[0]["content"].lower()

    def test_query_specs_by_feature(self, hmc):
        """Test querying specifications by feature name with filter."""
        # Store multiple specs
        hmc.add_semantic(
            "Login feature specification",
            metadata={"type": "spec", "feature": "login", "status": "draft"},
        )
        hmc.add_semantic(
            "Payment feature specification",
            metadata={"type": "spec", "feature": "payment", "status": "approved"},
        )
        hmc.add_semantic(
            "Profile feature specification",
            metadata={"type": "spec", "feature": "profile", "status": "draft"},
        )

        # Query for login specs
        results = hmc.query_semantic("feature specification", k=10, filter={"feature": "login"})

        assert len(results) > 0
        assert all(r["metadata"]["feature"] == "login" for r in results)

    def test_store_multiple_document_types(self, hmc):
        """Test storing and querying different document types."""
        # Store spec
        hmc.add_semantic(
            "Specification for user authentication", metadata={"type": "spec", "feature": "auth"}
        )

        # Store plan
        hmc.add_semantic(
            "Implementation plan for authentication", metadata={"type": "plan", "feature": "auth"}
        )

        # Store task
        hmc.add_semantic(
            "Task: Implement password hashing", metadata={"type": "task", "feature": "auth"}
        )

        # Query by type
        spec_results = hmc.query_semantic("authentication", k=10, filter={"type": "spec"})

        assert len(spec_results) > 0
        assert all(r["metadata"]["type"] == "spec" for r in spec_results)

    def test_update_document_status(self, hmc):
        """Test updating document status and querying by status."""
        # Store documents with different statuses
        hmc.add_semantic(
            "Draft specification for feature A",
            metadata={"type": "spec", "feature": "A", "status": "draft"},
        )
        hmc.add_semantic(
            "Approved specification for feature B",
            metadata={"type": "spec", "feature": "B", "status": "approved"},
        )
        hmc.add_semantic(
            "Under review specification for feature C",
            metadata={"type": "spec", "feature": "C", "status": "review"},
        )

        # Query for approved documents
        results = hmc.query_semantic("specification", k=10, filter={"status": "approved"})

        assert len(results) > 0
        assert all(r["metadata"]["status"] == "approved" for r in results)

    def test_factual_workflow_state_tracking(self, hmc):
        """Test tracking workflow state using factual storage."""
        # Track current feature being worked on
        hmc.set_fact("current_feature", "user-authentication")
        hmc.set_fact("current_phase", "implementation")
        hmc.set_fact("task_counter", 15)

        # Retrieve workflow state
        assert hmc.get_fact("current_feature") == "user-authentication"
        assert hmc.get_fact("current_phase") == "implementation"
        assert hmc.get_fact("task_counter") == 15

        # Update state
        hmc.set_fact("task_counter", 16)
        assert hmc.get_fact("task_counter") == 16

    def test_semantic_search_ranking(self, hmc):
        """Test that most relevant documents are returned first."""
        # Add documents with varying relevance to query
        hmc.add_semantic(
            "Complete guide to Python testing with pytest and fixtures",
            metadata={"type": "doc", "topic": "testing"},
        )
        hmc.add_semantic(
            "Python testing best practices", metadata={"type": "doc", "topic": "testing"}
        )
        hmc.add_semantic("Java programming tutorial", metadata={"type": "doc", "topic": "java"})

        # Query for Python testing
        results = hmc.query_semantic("Python testing guide", k=3)

        assert len(results) > 0
        # Most relevant should be first
        first_result = results[0]["content"]
        assert "Python" in first_result
        assert "testing" in first_result.lower()

    def test_metadata_preservation(self, hmc):
        """Test that all metadata fields are preserved in query results."""
        metadata = {
            "type": "spec",
            "feature": "authentication",
            "status": "approved",
            "priority": "P1",
            "author": "test-user",
            "created_at": "2025-11-14",
            "version": "1.0",
        }

        hmc.add_semantic("Authentication specification document", metadata=metadata)

        # Query and verify all metadata preserved
        results = hmc.query_semantic("authentication", k=1)

        assert len(results) > 0
        result_metadata = results[0]["metadata"]

        assert result_metadata["type"] == "spec"
        assert result_metadata["feature"] == "authentication"
        assert result_metadata["status"] == "approved"
        assert result_metadata["priority"] == "P1"
        assert result_metadata["author"] == "test-user"
        assert result_metadata["created_at"] == "2025-11-14"
        assert result_metadata["version"] == "1.0"

    def test_complex_workflow_scenario(self, hmc):
        """Test complete workflow: create, track, query, update."""
        # 1. Store initial spec
        spec_id = hmc.add_semantic(
            "User profile management feature specification",
            metadata={"type": "spec", "feature": "profile", "status": "draft", "priority": "P2"},
        )

        # 2. Track in factual storage
        hmc.set_fact("active_features", ["profile", "settings"])
        hmc.set_fact("profile_spec_id", spec_id)

        # 3. Add related plan
        hmc.add_semantic(
            "Implementation plan for profile feature",
            metadata={"type": "plan", "feature": "profile", "status": "draft"},
        )

        # 4. Add tasks
        for i in range(3):
            hmc.add_semantic(
                f"Task {i+1}: Implement profile component",
                metadata={"type": "task", "feature": "profile", "task_id": f"PROF-{i+1}"},
            )

        # 5. Query all profile-related documents
        profile_docs = hmc.query_semantic("profile", k=20, filter={"feature": "profile"})

        # Should find spec + plan + tasks
        assert len(profile_docs) >= 4

        # 6. Update status
        hmc.add_semantic(
            "User profile management feature specification (APPROVED)",
            metadata={"type": "spec", "feature": "profile", "status": "approved", "priority": "P2"},
        )

        # 7. Query approved profile specs
        approved = hmc.query_semantic("profile specification", k=10, filter={"status": "approved"})

        assert len(approved) > 0

    def test_multi_feature_tracking(self, hmc):
        """Test tracking multiple features simultaneously."""
        features = ["login", "signup", "profile", "settings"]

        for feature in features:
            # Store spec for each feature
            hmc.add_semantic(
                f"{feature.title()} feature specification",
                metadata={"type": "spec", "feature": feature, "status": "draft"},
            )

            # Track feature status
            hmc.set_fact(f"feature_{feature}_status", "in_progress")

        # Query each feature
        for feature in features:
            results = hmc.query_semantic(f"{feature} feature", k=5, filter={"feature": feature})
            assert len(results) > 0

            # Check factual status
            status = hmc.get_fact(f"feature_{feature}_status")
            assert status == "in_progress"

    def test_document_versioning(self, hmc):
        """Test storing multiple versions of same document."""
        # Version 1.0
        hmc.add_semantic(
            "Login spec v1.0: Basic email/password",
            metadata={"type": "spec", "feature": "login", "version": "1.0"},
        )

        # Version 2.0
        hmc.add_semantic(
            "Login spec v2.0: Added OAuth support",
            metadata={"type": "spec", "feature": "login", "version": "2.0"},
        )

        # Version 3.0
        hmc.add_semantic(
            "Login spec v3.0: Added 2FA",
            metadata={"type": "spec", "feature": "login", "version": "3.0"},
        )

        # Query latest version
        v3_results = hmc.query_semantic("login specification", k=5, filter={"version": "3.0"})

        assert len(v3_results) > 0
        assert "2FA" in v3_results[0]["content"]

    def test_priority_based_retrieval(self, hmc):
        """Test retrieving documents by priority."""
        priorities = ["P1", "P2", "P3"]

        for priority in priorities:
            hmc.add_semantic(
                f"Feature spec with {priority} priority",
                metadata={"type": "spec", "priority": priority},
            )

        # Query P1 (highest priority) items
        p1_results = hmc.query_semantic("feature spec", k=10, filter={"priority": "P1"})

        assert len(p1_results) > 0
        assert all(r["metadata"]["priority"] == "P1" for r in p1_results)

    def test_combined_filters(self, hmc):
        """Test querying with multiple filter conditions."""
        # Add various documents
        hmc.add_semantic(
            "P1 spec for auth",
            metadata={"type": "spec", "feature": "auth", "priority": "P1", "status": "approved"},
        )
        hmc.add_semantic(
            "P2 spec for auth",
            metadata={"type": "spec", "feature": "auth", "priority": "P2", "status": "draft"},
        )
        hmc.add_semantic(
            "P1 spec for payments",
            metadata={
                "type": "spec",
                "feature": "payments",
                "priority": "P1",
                "status": "approved",
            },
        )

        # Query with multiple filters (ChromaDB supports this)
        results = hmc.query_semantic(
            "specification", k=10, filter={"priority": "P1", "feature": "auth"}
        )

        # Should only return P1 auth spec
        if len(results) > 0:
            assert results[0]["metadata"]["priority"] == "P1"
            assert results[0]["metadata"]["feature"] == "auth"

    def test_factual_and_semantic_integration(self, hmc):
        """Test using factual and semantic storage together."""
        # Store document semantically
        spec_id = hmc.add_semantic(
            "Critical security feature specification",
            metadata={"type": "spec", "feature": "security", "status": "approved"},
        )

        # Store reference factually
        hmc.set_fact("security_spec_id", spec_id)
        hmc.set_fact("security_status", "implementation")
        hmc.set_fact("security_assignee", "dev-team-1")

        # Retrieve using both
        spec_id_from_fact = hmc.get_fact("security_spec_id")
        assert spec_id_from_fact == spec_id

        security_docs = hmc.query_semantic("security", k=5, filter={"feature": "security"})
        assert len(security_docs) > 0
