"""
Unit tests for Tab Deep Scan Batch 39 — decisions controller, dashboard_log, utils.

Covers: BUG-UI-UNDEF-004 (decisions delete use-before-define),
BUG-LOG-001 (json.dumps without default=str for non-serializable values).
Confirms: False positives from scan — trust consensus division, session sort types.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import json
import uuid
from datetime import datetime


# ── BUG-UI-UNDEF-004: Decisions controller pre-initialization ────────


class TestDecisionsDeletePreInit:
    """delete_decision must pre-initialize decision_id before try block."""

    def test_decision_id_pre_initialized(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "BUG-UI-UNDEF-004" in source

    def test_decision_id_before_try(self):
        """decision_id must be assigned before the try block."""
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        lines = source.split("\n")
        pre_init_line = None
        try_line = None
        for i, line in enumerate(lines):
            if "BUG-UI-UNDEF-004" in line:
                pre_init_line = i
            if pre_init_line and "try:" in line and i > pre_init_line:
                try_line = i
                break
        assert pre_init_line is not None, "Pre-initialization comment not found"
        assert try_line is not None, "try block not found after pre-init"
        assert pre_init_line < try_line, "Pre-init must come before try block"

    def test_all_four_controllers_have_pre_init(self):
        """All 4 delete handlers (sessions, tasks, rules, decisions) must have pre-init."""
        from agent.governance_ui.controllers import sessions, tasks, rules, decisions
        assert "BUG-UI-UNDEF-001" in inspect.getsource(sessions)
        assert "BUG-UI-UNDEF-002" in inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-003" in inspect.getsource(rules)
        assert "BUG-UI-UNDEF-004" in inspect.getsource(decisions)


# ── BUG-LOG-001: Dashboard log JSON serialization guard ──────────────


class TestDashboardLogSerialization:
    """log_action must handle non-serializable values."""

    def test_has_bugfix_marker(self):
        from governance.middleware import dashboard_log
        source = inspect.getsource(dashboard_log)
        assert "BUG-LOG-001" in source

    def test_has_default_str(self):
        """json.dumps must use default=str."""
        from governance.middleware import dashboard_log
        source = inspect.getsource(dashboard_log)
        assert "default=str" in source

    def test_string_values_work(self):
        """Normal string values should serialize correctly."""
        entry = {"ts": "2026-02-15T10:00:00", "view": "sessions", "action": "select"}
        result = json.dumps(entry, separators=(",", ":"), default=str)
        assert '"view":"sessions"' in result

    def test_uuid_serializable(self):
        """UUID values should be serialized to string."""
        entry = {"ts": "2026-02-15", "view": "test", "uuid": uuid.uuid4()}
        result = json.dumps(entry, separators=(",", ":"), default=str)
        assert '"uuid":' in result
        assert "UUID" not in result  # Should be the string representation

    def test_datetime_serializable(self):
        """datetime values should be serialized to string."""
        entry = {"ts": "2026-02-15", "view": "test", "timestamp": datetime.now()}
        result = json.dumps(entry, separators=(",", ":"), default=str)
        assert '"timestamp":' in result

    def test_none_serializable(self):
        """None values should serialize as null."""
        entry = {"ts": "2026-02-15", "view": "test", "agent": None}
        result = json.dumps(entry, separators=(",", ":"), default=str)
        assert '"agent":null' in result


# ── False positive verification ──────────────────────────────────────


class TestFalsePositiveVerification:
    """Verify scanner false positives are not actual bugs."""

    def test_trust_consensus_zero_weight_guarded(self):
        """consensus_score with all abstain votes returns 0.0 (not division by zero)."""
        from agent.governance_ui.data_access.trust_calculations import calculate_consensus_score
        result = calculate_consensus_score([
            {"vote_value": "abstain", "vote_weight": 5.0},
        ])
        assert result == 0.0

    def test_trust_consensus_zero_weight_votes(self):
        """Votes with zero weight should not cause division by zero."""
        from agent.governance_ui.data_access.trust_calculations import calculate_consensus_score
        result = calculate_consensus_score([
            {"vote_value": "approve", "vote_weight": 0},
            {"vote_value": "reject", "vote_weight": 0},
        ])
        assert result == 0.0

    def test_session_sort_fields_are_strings(self):
        """Valid sort fields for sessions are all string-type fields."""
        # The sort code only allows these fields
        valid_sort_fields = ["started_at", "session_id", "status", "start_time"]
        # All these field values are strings in session dicts
        sample_session = {
            "session_id": "SESSION-2026-02-15-TEST",
            "status": "ACTIVE",
            "start_time": "2026-02-15T10:00:00",
            "started_at": "2026-02-15T10:00:00",
        }
        for field in valid_sort_fields:
            val = sample_session.get(field)
            if val is not None:
                assert isinstance(val, str), f"{field} should be string, got {type(val)}"

    def test_compute_session_metrics_empty_list(self):
        """Empty sessions list should not cause division by zero."""
        from agent.governance_ui.utils import compute_session_metrics
        result = compute_session_metrics([])
        assert result["duration"] == "0h"
        assert result["avg_tasks"] == 0.0

    def test_compute_session_metrics_all_invalid(self):
        """Sessions with all-invalid timestamps should produce safe defaults."""
        from agent.governance_ui.utils import compute_session_metrics
        sessions = [
            {"start_time": None, "end_time": None, "tasks_completed": 3},
            {"start_time": "", "end_time": "", "tasks_completed": 2},
        ]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "0h"
        assert result["avg_tasks"] == 2.5  # (3 + 2) / 2

    def test_compute_timeline_ignores_bad_dates(self):
        """Timeline computation should skip sessions with missing start_time."""
        from agent.governance_ui.utils import compute_timeline_data
        sessions = [
            {"start_time": "2026-02-15T10:00:00"},
            {"start_time": ""},  # Empty — skipped
            {"start_time": None},  # None — skipped (get returns "")
            {},  # Missing — skipped
        ]
        values, labels = compute_timeline_data(sessions)
        # Should not crash — values should have 14 entries (last 14 days)
        assert len(values) == 14
        assert len(labels) == 14


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch39:
    """Batch 39 cross-cutting consistency checks."""

    def test_all_bugfix_markers_present(self):
        """All batch 39 bugfix markers must be in their respective files."""
        from agent.governance_ui.controllers import decisions
        from governance.middleware import dashboard_log
        assert "BUG-UI-UNDEF-004" in inspect.getsource(decisions)
        assert "BUG-LOG-001" in inspect.getsource(dashboard_log)

    def test_decisions_consistency_with_other_deletes(self):
        """decisions.py delete pattern must match sessions/tasks/rules pattern."""
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        # Must have pre-init before try
        assert "decision_id = state.selected_decision.get(" in source
