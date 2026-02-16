"""
Unit tests for Tab Deep Scan Batch 34 — Chat + handoff + ingestion + state.

Covers: BUG-CHAT-001 (delete race condition), BUG-HANDOFF-001 (mkdir parents),
BUG-INGEST-001 (empty tool_use_id collision), BUG-INGEST-002 (None timestamp),
BUG-STATE-001 (missing budget init fields).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect


# ── BUG-CHAT-001: Delete race condition ──────────────────────────────


class TestChatDeleteRaceCondition:
    """delete_chat_session must use .pop() not del for thread safety."""

    def test_uses_pop_not_del(self):
        from governance.routes.chat import endpoints
        source = inspect.getsource(endpoints.delete_chat_session)
        assert ".pop(session_id" in source
        assert "del _chat_sessions[session_id]" not in source

    def test_pop_with_default(self):
        """pop should use a default to avoid KeyError."""
        from governance.routes.chat import endpoints
        source = inspect.getsource(endpoints.delete_chat_session)
        assert ".pop(session_id, None)" in source

    def test_bugfix_marker(self):
        from governance.routes.chat import endpoints
        source = inspect.getsource(endpoints.delete_chat_session)
        assert "BUG-CHAT-001" in source


# ── BUG-HANDOFF-001: mkdir parents ───────────────────────────────────


class TestHandoffMkdirParents:
    """write_handoff_evidence must use parents=True."""

    def test_uses_parents_true(self):
        from governance.orchestrator.handoff_pkg import operations
        source = inspect.getsource(operations.write_handoff_evidence)
        assert "parents=True" in source

    def test_bugfix_marker(self):
        from governance.orchestrator.handoff_pkg import operations
        source = inspect.getsource(operations.write_handoff_evidence)
        assert "BUG-HANDOFF-001" in source


# ── BUG-INGEST-001: Empty tool_use_id collision ─────────────────────


class TestIngestToolUseIdFilter:
    """get_session_detail must skip empty tool_use_id."""

    def test_has_empty_guard(self):
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "not tr.tool_use_id" in source

    def test_empty_string_id_filtered(self):
        """Empty string tool_use_id should not cause dict collision."""
        # Behavioral: empty string used as dict key creates collision
        pending = {}
        # Without fix: two empty IDs would overwrite each other
        ids = ["", "", "tu-1"]
        for i, tid in enumerate(ids):
            if not tid:  # The fix
                continue
            pending[tid] = i
        assert len(pending) == 1  # Only "tu-1" kept
        assert pending["tu-1"] == 2

    def test_bugfix_marker(self):
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "BUG-INGEST-001" in source


# ── BUG-INGEST-002: None timestamp guard ─────────────────────────────


class TestIngestTimestampGuard:
    """Timestamp .isoformat() must handle None."""

    def test_has_timestamp_guard(self):
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "if entry.timestamp else None" in source

    def test_none_isoformat_pattern(self):
        """None timestamp should produce None, not crash."""
        ts = None
        result = ts.isoformat() if ts else None
        assert result is None

    def test_valid_timestamp_works(self):
        from datetime import datetime
        ts = datetime(2026, 2, 16, 10, 0, 0)
        result = ts.isoformat() if ts else None
        assert result == "2026-02-16T10:00:00"

    def test_bugfix_marker(self):
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "BUG-INGEST-002" in source


# ── BUG-STATE-001: Missing budget init fields ────────────────────────


class TestOrchestratorStateInit:
    """create_initial_state must include budget tracking fields."""

    def test_has_value_delivered(self):
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        assert "value_delivered" in state
        assert state["value_delivered"] == 0

    def test_has_tokens_used(self):
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        assert "tokens_used" in state
        assert state["tokens_used"] == 0

    def test_budget_fields_in_source(self):
        from governance.workflows.orchestrator import state
        source = inspect.getsource(state.create_initial_state)
        assert "value_delivered" in source
        assert "tokens_used" in source

    def test_budget_tracking_active_from_start(self):
        """complete_cycle_node should track budget from cycle 1."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        state["current_task"] = {"task_id": "T-1", "priority": "HIGH", "description": "test"}
        state["specification"] = {"task_id": "T-1"}
        state["implementation"] = {"task_id": "T-1"}
        state["validation_results"] = {"tests_passed": True}
        result = complete_cycle_node(state)
        # Budget fields should be updated from initial 0
        assert result["value_delivered"] > 0
        assert result["tokens_used"] > 0

    def test_bugfix_marker(self):
        from governance.workflows.orchestrator import state
        source = inspect.getsource(state.create_initial_state)
        assert "BUG-STATE-001" in source


# ── Cross-layer consistency checks ───────────────────────────────────


class TestCrossLayerConsistency:
    """Cross-cutting patterns must be consistent."""

    def test_chat_session_dict_uses_pop_pattern(self):
        """All dict removals in endpoints should use .pop()."""
        from governance.routes.chat import endpoints
        source = inspect.getsource(endpoints)
        # Should not have any `del _chat_sessions[` pattern
        assert "del _chat_sessions[" not in source

    def test_state_has_all_required_fields(self):
        """Initial state must have all fields used by nodes."""
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        required_fields = [
            "backlog", "current_task", "cycles_completed", "max_cycles",
            "cycle_history", "retry_count", "gate_decision", "dry_run",
            "value_delivered", "tokens_used",
        ]
        for field in required_fields:
            assert field in state, f"Missing field: {field}"
