"""DSP-06: DONE Gate Integration Tests.

Tests the full update_task() flow on DONE transition:
1. DoD validation blocks incomplete tasks (per type)
2. Resolution notes auto-populated (P17)
3. Auto-evidence for test tasks (SRVJ-FEAT-008)
4. CLOSED→DONE normalization at service boundary
5. completed_at auto-set on DONE
6. H-TASK-002 agent auto-assignment on IN_PROGRESS
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# =============================================================================
# 1. DoD Validation Blocks Incomplete Tasks
# =============================================================================


class TestDoneGateBlocks:
    """update_task() raises ValueError when DONE gate fails."""

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_bug_without_evidence_blocked(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        """Bug type requires evidence for DONE gate."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["BUG-GATE-001"] = {
            "task_id": "BUG-GATE-001",
            "description": "test > done > gate",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > done > gate > bug",
            "linked_sessions": ["S-1"],
            "task_type": "bug",
            "evidence": None,  # Missing!
        }

        with pytest.raises(ValueError, match="DONE gate"):
            update_task("BUG-GATE-001", status="DONE")

        _tasks_store.pop("BUG-GATE-001", None)

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_feature_without_documents_blocked(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["FEAT-GATE-001"] = {
            "task_id": "FEAT-GATE-001",
            "description": "test > done > gate > feature",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > done > gate > feature",
            "linked_sessions": ["S-1"],
            "linked_documents": [],  # Empty!
            "task_type": "feature",
        }

        with pytest.raises(ValueError, match="DONE gate"):
            update_task("FEAT-GATE-001", status="DONE")

        _tasks_store.pop("FEAT-GATE-001", None)

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_chore_with_minimal_passes(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        """Chore requires only summary + agent_id."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["CHORE-GATE-001"] = {
            "task_id": "CHORE-GATE-001",
            "description": "test > done > gate > chore",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > done > gate > chore",
            "linked_sessions": [],
            "task_type": "chore",
        }

        result = update_task("CHORE-GATE-001", status="DONE")
        assert result["status"] == "DONE"

        _tasks_store.pop("CHORE-GATE-001", None)


# =============================================================================
# 2. Resolution Notes Auto-Population (P17)
# =============================================================================


class TestResolutionNotesAutoPopulation:
    """Resolution notes generated on DONE when empty."""

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_bug_resolution_notes_generated(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["BUG-RN-001"] = {
            "task_id": "BUG-RN-001",
            "description": "test > resolution > notes",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > resolution > notes > bug",
            "linked_sessions": ["S-1"],
            "task_type": "bug",
            "evidence": "Stack trace fixed",
            "resolution_notes": None,
        }

        result = update_task("BUG-RN-001", status="DONE")
        assert result["resolution_notes"] is not None
        assert "Resolution Summary" in result["resolution_notes"]

        _tasks_store.pop("BUG-RN-001", None)

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_existing_resolution_notes_preserved(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["CHORE-RN-002"] = {
            "task_id": "CHORE-RN-002",
            "description": "test > rn > preserve",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > rn > preserve > chore",
            "linked_sessions": [],
            "task_type": "chore",
            "resolution_notes": "Manual: everything good",
        }

        result = update_task("CHORE-RN-002", status="DONE")
        assert result["resolution_notes"] == "Manual: everything good"

        _tasks_store.pop("CHORE-RN-002", None)


# =============================================================================
# 3. Auto-Evidence for Test Tasks (SRVJ-FEAT-008)
# =============================================================================


class TestAutoEvidenceTestTasks:
    """Test tasks auto-get evidence on DONE transition.

    SRVJ-FEAT-008 FIX: Auto-evidence now runs BEFORE the DONE gate (moved
    from after, where it was dead code). Test tasks with no evidence get
    auto-stamped, then the gate sees the auto-evidence and passes.
    """

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_test_task_auto_evidence_passes_done_gate(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        """Test tasks with NO evidence now auto-generate and pass the gate."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["TEST-EV-001"] = {
            "task_id": "TEST-EV-001",
            "description": "test > auto > evidence",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > auto > evidence > test",
            "linked_sessions": [],
            "task_type": "test",
            "evidence": None,  # No evidence — auto-evidence kicks in
        }

        result = update_task("TEST-EV-001", status="DONE")
        assert result["evidence"] is not None
        assert "[Verification: Auto]" in result["evidence"]

        _tasks_store.pop("TEST-EV-001", None)

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_test_task_explicit_evidence_preserved(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        """When store already has evidence, auto-evidence does NOT overwrite."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["TEST-EV-002"] = {
            "task_id": "TEST-EV-002",
            "description": "test > existing > evidence",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > existing > evidence > test",
            "linked_sessions": [],
            "task_type": "test",
            "evidence": "42/42 tests pass",  # Explicit — should be preserved
        }

        result = update_task("TEST-EV-002", status="DONE")
        # Explicit evidence preserved — auto-evidence does NOT overwrite
        assert result["evidence"] == "42/42 tests pass"

        _tasks_store.pop("TEST-EV-002", None)

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_non_test_task_without_evidence_still_blocked(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        """Bug tasks without evidence are still blocked (auto-evidence is test-only)."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["BUG-EV-003"] = {
            "task_id": "BUG-EV-003",
            "description": "test > bug > no evidence",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > bug > no evidence > blocked",
            "linked_sessions": ["S-1"],
            "task_type": "bug",
            "evidence": None,
        }

        with pytest.raises(ValueError, match="DONE gate"):
            update_task("BUG-EV-003", status="DONE")

        _tasks_store.pop("BUG-EV-003", None)


# =============================================================================
# 4. completed_at Auto-Set
# =============================================================================


class TestCompletedAtAutoSet:
    """completed_at timestamp set on DONE transition."""

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._preload_task_from_typedb")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_completed_at_set_on_done(
        self, mock_log, mock_audit, mock_preload, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["CHORE-CA-001"] = {
            "task_id": "CHORE-CA-001",
            "description": "test > completed > at",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > completed > at > chore",
            "linked_sessions": [],
            "task_type": "chore",
            "completed_at": None,
        }

        result = update_task("CHORE-CA-001", status="DONE")
        assert result.get("completed_at") is not None

        _tasks_store.pop("CHORE-CA-001", None)


# =============================================================================
# 5. H-TASK-002: Agent Auto-Assignment
# =============================================================================


class TestHTask002AgentAutoAssign:
    """Auto-assign agent_id when IN_PROGRESS without agent."""

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_in_progress_without_agent_gets_default(
        self, mock_log, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["H002-001"] = {
            "task_id": "H002-001",
            "description": "test > auto > agent",
            "status": "OPEN",
            "agent_id": None,
            "linked_sessions": [],
        }

        result = update_task("H002-001", status="IN_PROGRESS")
        assert result["agent_id"] is not None

        _tasks_store.pop("H002-001", None)

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.log_event")
    def test_in_progress_with_agent_preserved(
        self, mock_log, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["H002-002"] = {
            "task_id": "H002-002",
            "description": "test > keep > agent",
            "status": "OPEN",
            "agent_id": "research-agent",
            "linked_sessions": [],
        }

        result = update_task("H002-002", status="IN_PROGRESS")
        # Original agent preserved
        assert result["agent_id"] == "research-agent"

        _tasks_store.pop("H002-002", None)
