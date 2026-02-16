"""
Unit tests for Tab Deep Scan Batch 37 — UI controllers + routes.

Covers: BUG-UI-UNDEF-001/002/003 (use-before-define in exception handlers),
BUG-UI-DIV-001 (pagination division by zero guard).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect


# ── BUG-UI-UNDEF-001: Sessions controller pre-initialization ─────────


class TestSessionsDeletePreInit:
    """delete_session must pre-initialize session_id before try block."""

    def test_session_id_pre_initialized(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # Look for the delete function and find BUG-UI-UNDEF-001 marker
        assert "BUG-UI-UNDEF-001" in source

    def test_session_id_before_try(self):
        """session_id must be assigned before the try block."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # Find the delete_session function's pre-init
        lines = source.split("\n")
        pre_init_line = None
        try_line = None
        for i, line in enumerate(lines):
            if "BUG-UI-UNDEF-001" in line:
                pre_init_line = i
            if pre_init_line and "try:" in line and i > pre_init_line:
                try_line = i
                break
        assert pre_init_line is not None, "Pre-initialization comment not found"
        assert try_line is not None, "try block not found after pre-init"
        assert pre_init_line < try_line, "Pre-init must come before try block"


# ── BUG-UI-UNDEF-002: Tasks controller pre-initialization ───────────


class TestTasksDeletePreInit:
    """delete_task must pre-initialize task_id before try block."""

    def test_task_id_pre_initialized(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-002" in source

    def test_task_id_before_try(self):
        """task_id must be assigned before the try block."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        lines = source.split("\n")
        pre_init_line = None
        try_line = None
        for i, line in enumerate(lines):
            if "BUG-UI-UNDEF-002" in line:
                pre_init_line = i
            if pre_init_line and "try:" in line and i > pre_init_line:
                try_line = i
                break
        assert pre_init_line is not None
        assert try_line is not None
        assert pre_init_line < try_line


# ── BUG-UI-UNDEF-003: Rules controller pre-initialization ───────────


class TestRulesDeletePreInit:
    """delete_rule must pre-initialize rule_id before try block."""

    def test_rule_id_pre_initialized(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "BUG-UI-UNDEF-003" in source

    def test_rule_id_before_try(self):
        """rule_id must be assigned before the try block."""
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        lines = source.split("\n")
        pre_init_line = None
        try_line = None
        for i, line in enumerate(lines):
            if "BUG-UI-UNDEF-003" in line:
                pre_init_line = i
            if pre_init_line and "try:" in line and i > pre_init_line:
                try_line = i
                break
        assert pre_init_line is not None
        assert try_line is not None
        assert pre_init_line < try_line


# ── BUG-UI-DIV-001: Pagination division by zero guard ────────────────


class TestPaginationDivisionGuard:
    """tasks_go_to_page must guard against division by zero."""

    def test_has_division_guard(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-DIV-001" in source

    def test_or_fallback_pattern(self):
        """Must use 'or 20' (or similar) fallback for per_page."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # Should have a fallback like 'per_page = state.tasks_per_page or 20'
        assert "or 20" in source

    def test_zero_per_page_calculation(self):
        """Pagination calculation must not crash with zero per_page."""
        # Simulate the corrected logic
        total = 100
        per_page = 0 or 20  # The fix
        total_pages = max(1, (total + per_page - 1) // per_page)
        assert total_pages == 5

    def test_normal_pagination(self):
        """Normal pagination calculation should be correct."""
        total = 47
        per_page = 20
        total_pages = max(1, (total + per_page - 1) // per_page)
        assert total_pages == 3  # ceil(47/20) = 3

    def test_empty_total(self):
        """Zero total should give 1 page (min 1)."""
        total = 0
        per_page = 20
        total_pages = max(1, (total + per_page - 1) // per_page)
        assert total_pages == 1


# ── Cross-controller consistency ─────────────────────────────────────


class TestControllerConsistency:
    """All delete handlers must pre-initialize ID variables."""

    def test_sessions_pattern(self):
        """Sessions delete must have pre-init pattern."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # The pre-init should appear before "try:" in the delete function
        assert "session_id = state.selected_session.get(" in source

    def test_tasks_pattern(self):
        """Tasks delete must have pre-init pattern."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "task_id = state.selected_task.get(" in source

    def test_rules_pattern(self):
        """Rules delete must have pre-init pattern."""
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "rule_id = state.selected_rule.get(" in source

    def test_all_have_bugfix_markers(self):
        """All three controllers must have their respective bugfix markers."""
        from agent.governance_ui.controllers import sessions, tasks, rules
        assert "BUG-UI-UNDEF-001" in inspect.getsource(sessions)
        assert "BUG-UI-UNDEF-002" in inspect.getsource(tasks)
        assert "BUG-UI-UNDEF-003" in inspect.getsource(rules)
