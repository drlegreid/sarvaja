"""
Unit tests for Tab Deep Scan Batch 33 — Workflows + orchestrator + correlation.

Covers: BUG-ORCH-001 (empty backlog guard), BUG-ORCH-002 (None gap_id filter),
BUG-ORCH-003 (certify_node null-safe task_id), BUG-CORR-001 (division by zero).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect


# ── BUG-ORCH-001: Empty backlog guard ────────────────────────────────


class TestBacklogNodeEmptyGuard:
    """backlog_node must not crash on empty backlog."""

    def test_has_empty_guard(self):
        from governance.workflows.orchestrator import nodes
        source = inspect.getsource(nodes.backlog_node)
        assert "not backlog" in source or "if not backlog" in source

    def test_empty_backlog_returns_stop(self):
        from governance.workflows.orchestrator.nodes import backlog_node
        state = {"backlog": []}
        result = backlog_node(state)
        assert result["gate_decision"] == "stop"

    def test_non_empty_backlog_works(self):
        from governance.workflows.orchestrator.nodes import backlog_node
        state = {"backlog": [{"task_id": "T-1", "priority": "HIGH", "description": "test"}]}
        result = backlog_node(state)
        assert result["current_task"]["task_id"] == "T-1"
        assert result["backlog"] == []

    def test_bugfix_marker(self):
        from governance.workflows.orchestrator import nodes
        source = inspect.getsource(nodes.backlog_node)
        assert "BUG-ORCH-001" in source


# ── BUG-ORCH-002: None gap_id filter ─────────────────────────────────


class TestInjectNodeGapIdFilter:
    """inject_node must skip gaps without valid ID."""

    def test_has_none_guard(self):
        from governance.workflows.orchestrator import nodes
        source = inspect.getsource(nodes.inject_node)
        assert "not gid" in source or "if not gid" in source

    def test_none_gap_id_skipped(self):
        from governance.workflows.orchestrator.nodes import inject_node
        state = {
            "backlog": [],
            "gaps_discovered": [
                {"description": "Gap without ID"},  # No gap_id or task_id
                {"gap_id": "GAP-VALID-001", "priority": "HIGH", "description": "Valid"},
            ],
        }
        result = inject_node(state)
        backlog = result["backlog"]
        assert len(backlog) == 1
        assert backlog[0]["task_id"] == "GAP-VALID-001"

    def test_empty_string_gap_id_skipped(self):
        from governance.workflows.orchestrator.nodes import inject_node
        state = {
            "backlog": [],
            "gaps_discovered": [
                {"gap_id": "", "description": "Empty ID"},
            ],
        }
        result = inject_node(state)
        assert len(result["backlog"]) == 0

    def test_valid_gaps_still_injected(self):
        from governance.workflows.orchestrator.nodes import inject_node
        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH", "description": "existing"}],
            "gaps_discovered": [
                {"gap_id": "GAP-NEW-001", "priority": "MEDIUM", "description": "new gap"},
            ],
        }
        result = inject_node(state)
        ids = [t["task_id"] for t in result["backlog"]]
        assert "GAP-NEW-001" in ids
        assert "T-1" in ids

    def test_bugfix_marker(self):
        from governance.workflows.orchestrator import nodes
        source = inspect.getsource(nodes.inject_node)
        assert "BUG-ORCH-002" in source


# ── BUG-ORCH-003: certify_node null-safe task_id ─────────────────────


class TestCertifyNodeNullSafe:
    """certify_node must use .get() for task_id access."""

    def test_no_bare_bracket_task_id(self):
        """certify_node must not use h["task_id"]."""
        from governance.workflows.orchestrator import nodes
        source = inspect.getsource(nodes.certify_node)
        assert 'h["task_id"]' not in source

    def test_uses_get_pattern(self):
        from governance.workflows.orchestrator import nodes
        source = inspect.getsource(nodes.certify_node)
        assert 'h.get("task_id"' in source

    def test_missing_task_id_in_history(self):
        """certify_node should handle history entries without task_id gracefully."""
        from governance.workflows.orchestrator.nodes import certify_node
        state = {
            "cycle_history": [
                {"status": "parked", "reason": "orphan"},  # No task_id, parked
                {"task_id": "T-2", "implementation": {"summary": "Fixed T-2", "files_changed": ["b.py"]}},
            ],
            "backlog": [],
        }
        result = certify_node(state)
        cert = result["certification"]
        # Entry without task_id is correctly excluded from completed
        assert "T-2" in cert["tasks_completed"]
        # Parked entry without task_id uses "unknown" fallback
        assert "unknown" in cert["tasks_parked"]

    def test_bugfix_marker(self):
        from governance.workflows.orchestrator import nodes
        source = inspect.getsource(nodes.certify_node)
        assert "BUG-ORCH-003" in source


# ── BUG-CORR-001: Division by zero in correlation summary ────────────


class TestCorrelationDivisionGuard:
    """summarize_correlation must guard against empty latency lists."""

    def test_has_empty_guard_server(self):
        from governance.session_metrics import correlation
        source = inspect.getsource(correlation.summarize_correlation)
        assert "not latencies" in source or "if not latencies" in source

    def test_empty_correlated_returns_zeros(self):
        from governance.session_metrics.correlation import summarize_correlation
        result = summarize_correlation([])
        assert result["total_correlated"] == 0
        assert result["avg_latency_ms"] == 0

    def test_normal_correlation_works(self):
        from governance.session_metrics.correlation import summarize_correlation
        from governance.session_metrics.models import CorrelatedToolCall
        from datetime import datetime
        calls = [
            CorrelatedToolCall(
                tool_use_id="tu-1",
                tool_name="Read",
                is_mcp=False,
                use_timestamp=datetime(2026, 2, 16, 10, 0, 0),
                result_timestamp=datetime(2026, 2, 16, 10, 0, 1),
                latency_ms=1000,
                server_name=None,
            ),
            CorrelatedToolCall(
                tool_use_id="tu-2",
                tool_name="mcp__gov-tasks__task_get",
                is_mcp=True,
                use_timestamp=datetime(2026, 2, 16, 10, 0, 0),
                result_timestamp=datetime(2026, 2, 16, 10, 0, 2),
                latency_ms=2000,
                server_name="gov-tasks",
            ),
        ]
        result = summarize_correlation(calls)
        assert result["total_correlated"] == 2
        assert result["avg_latency_ms"] == 1500
        assert result["mcp_avg_latency_ms"] == 2000
        assert "gov-tasks" in result["per_server"]
        assert result["per_tool"]["Read"]["count"] == 1

    def test_bugfix_marker(self):
        from governance.session_metrics import correlation
        source = inspect.getsource(correlation.summarize_correlation)
        assert "BUG-CORR-001" in source


# ── Orchestrator node flow consistency ────────────────────────────────


class TestOrchestratorNodeConsistency:
    """Orchestrator nodes must follow consistent patterns."""

    def test_complete_cycle_sets_current_task_none(self):
        """complete_cycle_node must reset current_task to None."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": {"task_id": "T-1", "priority": "HIGH", "description": "test"},
            "cycles_completed": 0,
            "cycle_history": [],
            "specification": {"task_id": "T-1"},
            "implementation": {"task_id": "T-1"},
            "validation_results": {"tests_passed": True},
        }
        result = complete_cycle_node(state)
        assert result["current_task"] is None
        assert result["cycles_completed"] == 1
        assert len(result["cycle_history"]) == 1

    def test_gate_node_stops_on_empty_backlog(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = {"backlog": [], "cycles_completed": 0, "max_cycles": 10}
        result = gate_node(state)
        assert result["gate_decision"] == "stop"

    def test_gate_node_stops_on_max_cycles(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = {
            "backlog": [{"task_id": "T-1"}],
            "cycles_completed": 10,
            "max_cycles": 10,
        }
        result = gate_node(state)
        assert result["gate_decision"] == "stop"

    def test_gate_node_continues_when_budget_allows(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = {
            "backlog": [{"task_id": "T-1"}],
            "cycles_completed": 1,
            "max_cycles": 10,
        }
        result = gate_node(state)
        assert result["gate_decision"] == "continue"
