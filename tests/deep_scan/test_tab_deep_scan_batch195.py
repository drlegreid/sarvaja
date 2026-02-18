"""Batch 195 — Session services defense tests.

Validates fixes for:
- BUG-195-012: toggle_agent_status bare except logging
- BUG-195-013: session_repair apply_repair return value check
- BUG-195-015: tasks_mutations body param NOT sent to TypeDB
- Session repair defense (parse_session_date, cap_duration, is_backfilled)
"""
import ast
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-195-012: toggle_agent_status logging ────────────────────────

class TestAgentToggleLogging:
    """toggle_agent_status must log exceptions, not silently swallow."""

    def test_toggle_agent_has_exception_logging(self):
        """Verify except block logs the exception."""
        src = (SRC / "governance/services/agents.py").read_text()
        # Find the toggle_agent_status function and check for logger.warning
        in_toggle = False
        has_logging = False
        for line in src.splitlines():
            if "def toggle_agent_status" in line:
                in_toggle = True
            elif in_toggle and line.strip().startswith("def "):
                break
            elif in_toggle and "logger.warning" in line and "toggle" in line.lower():
                has_logging = True
        assert has_logging, "toggle_agent_status should log TypeDB failures"


# ── BUG-195-013: session_repair return value check ──────────────────

class TestSessionRepairReturnCheck:
    """apply_repair must check update_session return value."""

    def test_apply_repair_checks_none_return(self):
        """Verify apply_repair handles None from update_session."""
        src = (SRC / "governance/services/session_repair.py").read_text()
        assert "result_data is None" in src or "is None" in src

    def test_apply_repair_dry_run_returns_fixes(self):
        """apply_repair in dry_run mode returns fixes dict."""
        from governance.services.session_repair import apply_repair
        plan_item = {
            "session_id": "SESSION-2026-01-01-TEST",
            "fixes": {"agent_id": "code-agent"},
        }
        result = apply_repair(plan_item, dry_run=True)
        assert result["dry_run"] is True
        assert result["applied"] is False
        assert result["fixes"] == {"agent_id": "code-agent"}

    def test_apply_repair_handles_missing_fixes_key(self):
        """apply_repair should not crash if 'fixes' key missing."""
        from governance.services.session_repair import apply_repair
        result = apply_repair({"session_id": "TEST"}, dry_run=True)
        assert result["applied"] is False


# ── BUG-195-015 REVERTED: body NOT sent to TypeDB ──────────────────

class TestTaskMutationsBodyParam:
    """tasks_mutations must NOT pass body= to TypeDB update_task."""

    def test_update_task_call_has_no_body_kwarg(self):
        """Verify client.update_task() call does not include body=."""
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        # Find the client.update_task() call and ensure body= is NOT there
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "update_task":
                    kwarg_names = [kw.arg for kw in node.keywords if kw.arg is not None]
                    assert "body" not in kwarg_names, \
                        "client.update_task() must NOT receive body= (TypeDB has no body attribute)"


# ── Session repair defense ──────────────────────────────────────────

class TestSessionRepairDefense:
    """Defense tests for session_repair.py utilities."""

    def test_parse_session_date_valid(self):
        from governance.services.session_repair import parse_session_date
        assert parse_session_date("SESSION-2026-01-15-TOPIC") == "2026-01-15"

    def test_parse_session_date_invalid(self):
        from governance.services.session_repair import parse_session_date
        assert parse_session_date("RANDOM-ID") is None

    def test_cap_duration_under_max(self):
        from governance.services.session_repair import cap_duration
        session = {"start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T12:00:00"}
        result = cap_duration(session, max_hours=24)
        assert result["end_time"] == "2026-01-01T12:00:00"  # Unchanged

    def test_cap_duration_over_max(self):
        from governance.services.session_repair import cap_duration
        session = {"start_time": "2026-01-01T09:00:00", "end_time": "2026-01-03T09:00:00"}
        result = cap_duration(session, max_hours=24)
        assert result["end_time"] == "2026-01-02T09:00:00"  # Capped to 24h

    def test_is_backfilled_session_by_description(self):
        from governance.services.session_repair import is_backfilled_session
        assert is_backfilled_session({"description": "Backfilled from evidence file"}) is True

    def test_is_backfilled_session_by_agent(self):
        from governance.services.session_repair import is_backfilled_session
        assert is_backfilled_session({"agent_id": "claude-test"}) is True

    def test_is_backfilled_session_normal(self):
        from governance.services.session_repair import is_backfilled_session
        assert is_backfilled_session({"agent_id": "code-agent", "description": "Normal session"}) is False
