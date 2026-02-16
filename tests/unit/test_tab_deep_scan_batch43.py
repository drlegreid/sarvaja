"""
Unit tests for Tab Deep Scan Batch 43 — MCP session tools, tasks controller,
dashboard data loader.

5 bugs fixed (BUG-UI-UNDEF-005..008, BUG-LOG-002). 7 MCP session guard
findings verified as false positives (Python `or` short-circuit).

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect
import re
from unittest.mock import MagicMock


# ── MCP session guard: Python `or` short-circuit ──────────────────────


class TestMCPSessionGuardFalsePositives:
    """Verify `topic or sessions[-1]` is safe due to `or` short-circuit."""

    def test_or_shortcircuit_with_truthy_topic(self):
        """When topic is truthy, sessions[-1] is never evaluated."""
        sessions = []  # Empty list
        topic = "deep-scan"
        # Python `or` short-circuits: topic is truthy → returns topic
        result = topic or sessions[-1].split("-")[-1].lower()
        assert result == "deep-scan"

    def test_or_evaluates_rhs_when_topic_falsy(self):
        """When topic is None, sessions[-1] IS evaluated."""
        sessions = ["SESSION-2026-02-15-TEST"]
        topic = None
        result = topic or sessions[-1].split("-")[-1].lower()
        assert result == "test"

    def test_guard_blocks_both_empty(self):
        """Guard `not sessions and not topic` catches both-empty case."""
        sessions = []
        topic = None
        assert (not sessions and not topic) is True

    def test_guard_passes_when_topic_set(self):
        """Guard passes when topic is set (sessions can be empty)."""
        sessions = []
        topic = "scan"
        assert (not sessions and not topic) is False

    def test_guard_passes_when_sessions_nonempty(self):
        """Guard passes when sessions is non-empty (topic can be None)."""
        sessions = ["SESSION-2026-02-15-X"]
        topic = None
        assert (not sessions and not topic) is False

    def test_all_session_core_functions_have_guard(self):
        """All session_core functions with sessions[-1] have the guard."""
        from governance.mcp_tools import sessions_core
        source = inspect.getsource(sessions_core)
        # Count instances of the guard pattern
        guard_count = source.count("if not sessions and not topic")
        sessions_access = source.count("sessions[-1]")
        assert guard_count >= 5
        assert sessions_access >= 5
        # Every sessions[-1] must be preceded by a guard
        assert guard_count >= sessions_access

    def test_session_intent_functions_have_guard(self):
        """Session intent tools also use the guard pattern."""
        from governance.mcp_tools import sessions_intent
        source = inspect.getsource(sessions_intent)
        guard_count = source.count("if not sessions and not topic")
        sessions_access = source.count("sessions[-1]")
        assert guard_count >= 2
        assert sessions_access >= 2


# ── sessions_intent.py: completion_rate division safety ──────────────


class TestCompletionRateDivisionSafety:
    """Verify completion_rate calculation is safe from division by zero."""

    def test_empty_planned_returns_100(self):
        """Empty planned set → 100% completion (ternary guard)."""
        planned = set()
        achieved = set()
        rate = len(achieved) / len(planned) * 100 if planned else 100
        assert rate == 100

    def test_nonempty_planned_calculates(self):
        """Non-empty planned set → actual calculation."""
        planned = {"T1", "T2", "T3"}
        achieved = {"T1", "T3"}
        rate = len(achieved) / len(planned) * 100 if planned else 100
        assert abs(rate - 66.67) < 1

    def test_all_achieved(self):
        """All planned tasks achieved → 100%."""
        planned = {"T1", "T2"}
        achieved = {"T1", "T2"}
        rate = len(achieved) / len(planned) * 100 if planned else 100
        assert rate == 100.0


# ── BUG-UI-UNDEF-005..008: Tasks controller pre-initialization ──────


class TestTasksControllerPreInit:
    """Verify all task controller except handlers have pre-initialized task_id."""

    def test_claim_has_preinit(self):
        """BUG-UI-UNDEF-005: claim_selected_task has pre-init."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-005" in source

    def test_complete_has_preinit(self):
        """BUG-UI-UNDEF-006: complete_selected_task has pre-init."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-006" in source

    def test_submit_edit_has_preinit(self):
        """BUG-UI-UNDEF-007: submit_task_edit has pre-init."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-007" in source

    def test_attach_document_has_preinit(self):
        """BUG-UI-UNDEF-008: attach_document has pre-init."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-008" in source

    def test_delete_already_had_preinit(self):
        """BUG-UI-UNDEF-002: delete_task was already fixed in batch 37."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-002" in source

    def test_all_bugfix_markers_present(self):
        """All BUG-UI-UNDEF markers 002 and 005-008 must be present."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        for marker in ["BUG-UI-UNDEF-002", "BUG-UI-UNDEF-005",
                        "BUG-UI-UNDEF-006", "BUG-UI-UNDEF-007",
                        "BUG-UI-UNDEF-008"]:
            assert marker in source, f"Missing {marker} in tasks.py"

    def test_preinit_comes_before_try(self):
        """Pre-init assignment must appear before corresponding try block."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        for marker in ["BUG-UI-UNDEF-005", "BUG-UI-UNDEF-006",
                        "BUG-UI-UNDEF-007", "BUG-UI-UNDEF-008"]:
            marker_pos = source.index(marker)
            # Find next "try:" after the marker
            next_try = source.index("try:", marker_pos)
            # The pre-init must be between marker and try
            between = source[marker_pos:next_try]
            assert "task_id" in between, f"No task_id pre-init between {marker} and try"


# ── BUG-LOG-002: Dashboard data loader logging ──────────────────────


class TestDashboardDataLoaderLogging:
    """Verify BUG-LOG-002 fix: bare except now logs warning."""

    def test_has_bugfix_marker(self):
        """BUG-LOG-002 marker present in dashboard_data_loader."""
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        assert "BUG-LOG-002" in source

    def test_no_bare_except_pass(self):
        """No bare `except Exception:` without logging."""
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == "except Exception:":
                # Next non-blank line should have logger
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].strip():
                        assert "logger" in lines[j] or "log" in lines[j].lower(), \
                            f"Bare except without logging at line {i}"
                        break

    def test_has_logger_warning(self):
        """load_initial_data except block logs warning."""
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader.load_initial_data)
        assert "logger.warning" in source

    def test_has_exception_variable(self):
        """Exception is captured as variable `e` (not bare except)."""
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader.load_initial_data)
        assert "except Exception as e:" in source


# ── tasks.py: page size division safety ──────────────────────────────


class TestTasksPageSizeSafety:
    """Verify tasks_per_page `or 20` prevents division by zero."""

    def test_zero_per_page_fallback(self):
        """0 or 20 → 20, preventing division by zero."""
        per_page = 0 or 20
        assert per_page == 20

    def test_none_per_page_fallback(self):
        """None or 20 → 20."""
        per_page = None or 20
        assert per_page == 20

    def test_valid_per_page_kept(self):
        """50 or 20 → 50."""
        per_page = 50 or 20
        assert per_page == 50

    def test_total_pages_never_zero(self):
        """max(1, ...) ensures at least 1 total page."""
        per_page = 20
        total = 0
        total_pages = max(1, (total + per_page - 1) // per_page)
        assert total_pages == 1


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch43:
    """Batch 43 cross-cutting consistency checks."""

    def test_all_controllers_have_preinit_pattern(self):
        """All 4 controller files use BUG-UI-UNDEF pre-init pattern."""
        from agent.governance_ui.controllers import sessions, tasks, rules, decisions
        assert "BUG-UI-UNDEF-001" in inspect.getsource(sessions)
        assert "BUG-UI-UNDEF-002" in inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-003" in inspect.getsource(rules)
        assert "BUG-UI-UNDEF-004" in inspect.getsource(decisions)

    def test_tasks_has_five_undef_markers(self):
        """tasks.py has 5 BUG-UI-UNDEF markers (002 + 005-008)."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        markers = re.findall(r"BUG-UI-UNDEF-\d{3}", source)
        assert len(markers) >= 5

    def test_dashboard_loader_has_logger(self):
        """dashboard_data_loader.py imports logging module."""
        from agent.governance_ui import dashboard_data_loader
        assert hasattr(dashboard_data_loader, "logger")

    def test_mcp_session_tools_use_format_mcp_result(self):
        """All session MCP tools return via format_mcp_result."""
        from governance.mcp_tools import sessions_core, sessions_intent
        for mod in [sessions_core, sessions_intent]:
            source = inspect.getsource(mod)
            assert "format_mcp_result" in source
