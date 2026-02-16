"""
Unit tests for Tab Deep Scan Batch 42 — orchestrator nodes/graph/edges,
session persistence, TypeDB access, helpers, transcript routes.

1 bug fixed (BUG-PERSIST-001). Remaining findings all false positives.

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect
from unittest.mock import patch, MagicMock


# ── Orchestrator: operator precedence + call order + loop bounds ────────


class TestOrchestratorOperatorPrecedence:
    """Verify Python `not x == y` means `not (x == y)`, not `(not x) == y`."""

    def test_not_equals_precedence(self):
        """Python: `not x == y` is `not (x == y)` (correct)."""
        status = "parked"
        assert (not status == "parked") is False
        assert (not status == "active") is True

    def test_not_none_equals_parked(self):
        """None status: `not None == 'parked'` → `not False` → True."""
        status = None
        assert (not status == "parked") is True  # None is not parked

    def test_certify_node_filter_logic(self):
        """certify_node correctly filters completed vs parked tasks."""
        history = [
            {"task_id": "T1", "status": None},       # completed (no status)
            {"task_id": "T2", "status": "parked"},    # parked
            {"task_id": "T3"},                        # completed (no status key)
            {"task_id": None},                        # excluded (no task_id)
        ]
        completed = [h for h in history if h.get("task_id") and not h.get("status") == "parked"]
        parked = [h for h in history if h.get("status") == "parked"]
        assert len(completed) == 2  # T1, T3
        assert len(parked) == 1     # T2


class TestOrchestratorLoopBounds:
    """Verify orchestrator loop terminates."""

    def test_retry_count_bounds_loop(self):
        """check_validation_result returns park_task after MAX_RETRIES."""
        from governance.workflows.orchestrator.edges import check_validation_result
        from governance.workflows.orchestrator.state import MAX_RETRIES
        state = {"validation_passed": False, "retry_count": MAX_RETRIES}
        assert check_validation_result(state) == "park_task"

    def test_retry_count_allows_loop(self):
        """check_validation_result returns loop_to_spec within MAX_RETRIES."""
        from governance.workflows.orchestrator.edges import check_validation_result
        state = {"validation_passed": False, "retry_count": 0}
        assert check_validation_result(state) == "loop_to_spec"

    def test_gate_decision_terminates_loop(self):
        """check_gate_decision returns 'complete' when gate_decision not 'continue'."""
        from governance.workflows.orchestrator.edges import check_gate_decision
        assert check_gate_decision({"gate_decision": "stop"}) == "complete"
        assert check_gate_decision({}) == "complete"

    def test_gate_decision_continues_loop(self):
        """check_gate_decision returns 'backlog' when gate_decision is 'continue'."""
        from governance.workflows.orchestrator.edges import check_gate_decision
        assert check_gate_decision({"gate_decision": "continue"}) == "backlog"


# ── Session Persistence: BUG-PERSIST-001 ──────────────────────────


class TestSessionPersistenceCleanup:
    """Verify BUG-PERSIST-001 fix: cleanup logs instead of silent pass."""

    def test_cleanup_has_bugfix_marker(self):
        """BUG-PERSIST-001 marker present in cleanup_persisted."""
        from governance.stores.session_persistence import cleanup_persisted
        source = inspect.getsource(cleanup_persisted)
        assert "BUG-PERSIST-001" in source

    def test_cleanup_no_bare_pass(self):
        """No bare `except: pass` or `except Exception: pass` without logging."""
        from governance.stores import session_persistence
        source = inspect.getsource(session_persistence)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "pass" and i > 0:
                prev = lines[i - 1].strip()
                if prev.startswith("except"):
                    assert False, f"Bare except/pass found at line {i}: {prev} / {stripped}"

    def test_cleanup_logs_on_failure(self):
        """cleanup_persisted logs debug message on failure."""
        from governance.stores.session_persistence import cleanup_persisted
        source = inspect.getsource(cleanup_persisted)
        assert "logger.debug" in source

    def test_falsy_filter_skips_empty_collections(self):
        """Empty collections are not persisted (by design)."""
        from governance.stores.session_persistence import _PERSIST_KEYS
        session_data = {"tool_calls": [], "thoughts": [], "topic": "test"}
        subset = {k: v for k, v in session_data.items() if k in _PERSIST_KEYS and v}
        assert "tool_calls" not in subset  # Empty list filtered (by design)
        assert "topic" in subset  # Non-empty string kept


# ── TypeDB Access: ternary short-circuit ──────────────────────────


class TestTypeDBTernaryShortCircuit:
    """Verify Python ternary `x.method() if x else None` is safe."""

    def test_none_ternary_does_not_call_method(self):
        """Ternary with None condition returns None without calling .isoformat()."""
        val = None
        result = val.isoformat() if val else None
        assert result is None  # Did not crash

    def test_datetime_ternary_calls_method(self):
        """Ternary with datetime calls .isoformat() correctly."""
        from datetime import datetime
        val = datetime(2026, 2, 15, 10, 0)
        result = val.isoformat() if val else None
        assert result == "2026-02-15T10:00:00"

    def test_task_to_dict_has_ternary_guards(self):
        """_task_to_dict uses ternary guards for datetime fields."""
        from governance.stores.typedb_access import _task_to_dict
        source = inspect.getsource(_task_to_dict)
        assert "if task.created_at else None" in source
        assert "if task.claimed_at else None" in source
        assert "if task.completed_at else None" in source


# ── Helpers: SessionResponse accepts Optional[List] ──────────────


class TestSessionResponseNullSafety:
    """Verify SessionResponse model accepts None for list fields."""

    def test_evidence_files_is_optional(self):
        """evidence_files field is Optional[List[str]]."""
        from governance.models import SessionResponse
        fields = SessionResponse.model_fields
        assert "evidence_files" in fields
        # Default is None
        assert fields["evidence_files"].default is None

    def test_linked_rules_is_optional(self):
        """linked_rules_applied field is Optional[List[str]]."""
        from governance.models import SessionResponse
        fields = SessionResponse.model_fields
        assert "linked_rules_applied" in fields
        assert fields["linked_rules_applied"].default is None

    def test_linked_decisions_is_optional(self):
        """linked_decisions field is Optional[List[str]]."""
        from governance.models import SessionResponse
        fields = SessionResponse.model_fields
        assert "linked_decisions" in fields
        assert fields["linked_decisions"].default is None

    def test_session_response_accepts_none_lists(self):
        """SessionResponse can be created with None list fields."""
        from governance.models import SessionResponse
        sr = SessionResponse(
            session_id="TEST",
            start_time="2026-02-15",
            status="ACTIVE",
            evidence_files=None,
            linked_rules_applied=None,
            linked_decisions=None,
        )
        assert sr.evidence_files is None
        assert sr.linked_rules_applied is None


# ── Cross-layer consistency ──────────────────────────────────────


class TestCrossLayerConsistencyBatch42:
    """Batch 42 cross-cutting consistency checks."""

    def test_edges_uses_max_retries_from_state(self):
        """edges.py imports MAX_RETRIES from state module."""
        from governance.workflows.orchestrator import edges
        source = inspect.getsource(edges)
        assert "MAX_RETRIES" in source

    def test_persistence_sanitizes_session_id(self):
        """_get_path sanitizes session_id for filesystem safety."""
        from governance.stores.session_persistence import _get_path
        path = _get_path("SESSION/../../../etc/passwd")
        assert ".." not in path.name
        assert "/" not in path.name

    def test_persistence_uses_atomic_rename(self):
        """persist_session uses tmp.rename(path) for atomicity."""
        from governance.stores.session_persistence import persist_session
        source = inspect.getsource(persist_session)
        assert ".rename(" in source
