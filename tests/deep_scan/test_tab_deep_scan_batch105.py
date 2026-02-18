"""Deep scan batch 105: Workflow + DSM + stores + utilities.

Batch 105 findings: 34 total, 0 confirmed fixes, 34 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Orchestrator node state access defense ──────────────


class TestOrchestratorNodeStateAccess:
    """Verify orchestrator nodes handle state correctly."""

    def test_implement_node_guards_missing_task(self):
        """implement_node returns error if no current_task."""
        from governance.workflows.orchestrator.nodes import implement_node

        result = implement_node({"specification": {"files_to_modify": []}})
        assert result["current_phase"] == "impl_error"

    def test_backlog_node_handles_empty_backlog(self):
        """backlog_node returns stop on empty backlog."""
        from governance.workflows.orchestrator.nodes import backlog_node

        result = backlog_node({"backlog": []})
        assert result["gate_decision"] == "stop"
        assert "empty" in result["current_phase"]

    def test_backlog_node_pops_first_task(self):
        """backlog_node selects and removes first task."""
        from governance.workflows.orchestrator.nodes import backlog_node

        tasks = [
            {"task_id": "T-001", "description": "First"},
            {"task_id": "T-002", "description": "Second"},
        ]
        result = backlog_node({"backlog": tasks})
        assert result["current_task"]["task_id"] == "T-001"
        assert len(result["backlog"]) == 1
        assert result["backlog"][0]["task_id"] == "T-002"


# ── DSM tracker defense ──────────────


class TestDSMTrackerDefense:
    """Verify DSM tracker handles lifecycle correctly."""

    def test_abort_cycle_clears_current(self):
        """abort_cycle sets current_cycle to None."""
        from governance.dsm.tracker import DSMTracker

        tracker = DSMTracker.__new__(DSMTracker)
        tracker.completed_cycles = []
        tracker._state_file = None

        # Create minimal cycle mock
        cycle = MagicMock()
        cycle.metrics = {}
        tracker.current_cycle = cycle

        with patch.object(tracker, "_save_state"):
            tracker.abort_cycle("test reason")

        assert tracker.current_cycle is None

    def test_get_status_no_cycle(self):
        """get_status returns inactive when no cycle."""
        from governance.dsm.tracker import DSMTracker

        tracker = DSMTracker.__new__(DSMTracker)
        tracker.current_cycle = None
        tracker.completed_cycles = []

        status = tracker.get_status()
        assert status["active"] is False

    def test_phase_order_not_empty(self):
        """DSPPhase.phase_order() always returns non-empty list."""
        from governance.dsm.phases import DSPPhase

        phases = DSPPhase.phase_order()
        assert len(phases) > 0
        assert all(isinstance(p, DSPPhase) for p in phases)


# ── Compute session duration defense ──────────────


class TestComputeSessionDuration:
    """Verify session duration handles edge cases."""

    def test_negative_duration_uses_abs(self):
        """Reversed timestamps produce positive duration."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-15T13:00:00",
            "2026-02-15T09:00:00",
        )
        # abs() produces 4h, which matches repair artifact pattern
        assert result != ""
        assert "invalid" not in result.lower() if result else True

    def test_ongoing_session_no_end(self):
        """Session without end_time shows 'ongoing'."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration("2026-02-15T09:00:00", None)
        assert result == "ongoing"

    def test_no_start_returns_empty(self):
        """Session without start_time returns empty string."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(None, None)
        assert result == ""

    def test_repair_artifact_detected(self):
        """Repair-generated timestamps show estimate suffix."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-15T09:00:00",
            "2026-02-15T13:00:00",
        )
        assert "~4h (est)" in result

    def test_normal_4h_session(self):
        """Non-repair 4h session shows correct duration."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-15T10:30:00",
            "2026-02-15T14:30:00",
        )
        assert "4h 0m" in result


# ── Format timestamp defense ──────────────


class TestFormatTimestamp:
    """Verify timestamp formatting handles edge cases."""

    def test_none_returns_empty(self):
        """None input returns empty string."""
        from agent.governance_ui.utils import format_timestamp

        assert format_timestamp(None) == ""

    def test_empty_string_returns_empty(self):
        """Empty string returns empty string."""
        from agent.governance_ui.utils import format_timestamp

        assert format_timestamp("") == ""

    def test_valid_iso_formatted(self):
        """Valid ISO timestamp formatted to YYYY-MM-DD HH:MM."""
        from agent.governance_ui.utils import format_timestamp

        result = format_timestamp("2026-02-15T14:30:00")
        assert result == "2026-02-15 14:30"

    def test_nanosecond_stripped(self):
        """TypeDB nanosecond timestamps handled correctly."""
        from agent.governance_ui.utils import format_timestamp

        result = format_timestamp("2026-02-15T14:30:00.123456789")
        assert result == "2026-02-15 14:30"

    def test_malformed_returns_original(self):
        """Malformed timestamp returns original value."""
        from agent.governance_ui.utils import format_timestamp

        result = format_timestamp("not-a-timestamp")
        # Function catches exception and returns original
        assert "not-a-timestamp" in result


# ── Audit retention defense ──────────────


class TestAuditRetentionDefense:
    """Verify audit retention keeps recent entries."""

    def test_retention_keeps_recent(self):
        """Entries within retention window are kept."""
        import governance.stores.audit as audit_mod

        original = audit_mod._audit_store[:]
        try:
            audit_mod._audit_store.clear()
            audit_mod._audit_store.extend([
                {"timestamp": datetime.now().isoformat(), "action": "TEST"},
            ])
            audit_mod._apply_retention(days=7)
            assert len(audit_mod._audit_store) == 1
        finally:
            audit_mod._audit_store.clear()
            audit_mod._audit_store.extend(original)


# ── Orchestrator budget defense ──────────────


class TestOrchestratorBudgetDefense:
    """Verify budget calculation handles edge cases."""

    def test_budget_without_token_budget(self):
        """compute_budget works without token_budget in state."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "cycles_completed": 5,
            "max_cycles": 10,
            "backlog": [{"task_id": "T-001", "priority": "HIGH"}],
        })
        assert isinstance(result.get("should_continue"), bool)

    def test_budget_empty_backlog_stops(self):
        """compute_budget stops on empty backlog."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "cycles_completed": 5,
            "max_cycles": 10,
        })
        assert result.get("should_continue") is False
        assert result.get("reason") == "backlog_empty"
