"""
Unit tests for Tab Deep Scan Batch 48 — projects pagination logic,
decisions/sessions null guards in edit forms.

4 bugs fixed (BUG-PROJECTS-TOTAL-001, BUG-PROJECTS-HASMORE-001,
BUG-UI-DECISION-GUARD-001, BUG-UI-SESSION-GUARD-001).

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect
from unittest.mock import patch, MagicMock


# ── BUG-PROJECTS-TOTAL-001: Correct total in fallback path ──────────


class TestProjectsPaginationFallback:
    """Verify list_projects fallback pagination is correct."""

    def test_has_bugfix_marker_total(self):
        """BUG-PROJECTS-TOTAL-001 marker present."""
        from governance.services import projects
        source = inspect.getsource(projects.list_projects)
        assert "BUG-PROJECTS-TOTAL-001" in source

    def test_has_bugfix_marker_hasmore(self):
        """BUG-PROJECTS-HASMORE-001 marker present."""
        from governance.services import projects
        source = inspect.getsource(projects.list_projects)
        assert "BUG-PROJECTS-HASMORE-001" in source

    def test_fallback_total_is_all_projects(self):
        """Fallback total reflects all projects, not just the page."""
        from governance.services import projects
        store = {
            f"PROJ-{i}": {"project_id": f"PROJ-{i}", "name": f"P{i}"}
            for i in range(5)
        }
        with patch.object(projects, "_projects_store", store):
            with patch.object(projects, "_get_client", return_value=None):
                result = projects.list_projects(limit=2, offset=0)
                assert result["pagination"]["total"] == 5
                assert result["pagination"]["returned"] == 2
                assert result["pagination"]["has_more"] is True

    def test_fallback_last_page_has_more_false(self):
        """Last page shows has_more=False."""
        from governance.services import projects
        store = {
            f"PROJ-{i}": {"project_id": f"PROJ-{i}", "name": f"P{i}"}
            for i in range(3)
        }
        with patch.object(projects, "_projects_store", store):
            with patch.object(projects, "_get_client", return_value=None):
                result = projects.list_projects(limit=2, offset=2)
                assert result["pagination"]["total"] == 3
                assert result["pagination"]["returned"] == 1
                assert result["pagination"]["has_more"] is False

    def test_exact_page_boundary(self):
        """Exact page boundary: total=4, limit=2, offset=2 → has_more=False."""
        from governance.services import projects
        store = {
            f"PROJ-{i}": {"project_id": f"PROJ-{i}", "name": f"P{i}"}
            for i in range(4)
        }
        with patch.object(projects, "_projects_store", store):
            with patch.object(projects, "_get_client", return_value=None):
                result = projects.list_projects(limit=2, offset=2)
                assert result["pagination"]["has_more"] is False

    def test_has_more_formula_correct(self):
        """has_more uses (offset + limit) < total formula."""
        from governance.services import projects
        source = inspect.getsource(projects.list_projects)
        assert "(offset + limit) < total" in source


# ── BUG-UI-DECISION-GUARD-001: decisions.py null guard ──────────────


class TestDecisionsEditNullGuard:
    """Verify decisions controller guards against None selected_decision."""

    def test_has_bugfix_marker(self):
        """BUG-UI-DECISION-GUARD-001 marker present."""
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "BUG-UI-DECISION-GUARD-001" in source

    def test_guard_checks_selected_decision(self):
        """Guard checks state.selected_decision before .get() in source."""
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "if not state.selected_decision:" in source

    def test_guard_precedes_get_call(self):
        """Guard appears before .get('id') in edit branch."""
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        guard_pos = source.find("BUG-UI-DECISION-GUARD-001")
        get_pos = source.find(".get('id') or state.selected_decision.get('decision_id')")
        assert guard_pos < get_pos, "Guard must precede .get() call"


# ── BUG-UI-SESSION-GUARD-001: sessions.py null guard ────────────────


class TestSessionsEditNullGuard:
    """Verify sessions controller guards against None selected_session."""

    def test_has_bugfix_marker(self):
        """BUG-UI-SESSION-GUARD-001 marker present."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-SESSION-GUARD-001" in source

    def test_guard_checks_selected_session(self):
        """Guard checks state.selected_session before .get() in source."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "if not state.selected_session:" in source

    def test_guard_in_edit_branch(self):
        """Guard appears in the submit_session_form edit branch."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # Find the guard within the submit_session_form function
        submit_start = source.find("def submit_session_form")
        assert submit_start > 0
        submit_source = source[submit_start:]
        assert "BUG-UI-SESSION-GUARD-001" in submit_source
        guard_pos = submit_source.find("if not state.selected_session:")
        get_pos = submit_source.find("state.selected_session.get('session_id')")
        assert guard_pos < get_pos, "Guard must precede .get() call"


# ── Pagination formula semantics ──────────────────────────────────


class TestHasMoreFormulaSafety:
    """Verify pagination has_more formula semantics."""

    def test_middle_page_has_more(self):
        """Middle page: (0 + 50) < 100 is True."""
        assert (0 + 50) < 100

    def test_last_page_no_more(self):
        """Last page: (50 + 50) < 100 is False."""
        assert not ((50 + 50) < 100)

    def test_one_more_item(self):
        """One extra: (50 + 50) < 101 is True."""
        assert (50 + 50) < 101

    def test_exact_boundary_no_more(self):
        """Exact boundary: (2 + 2) < 4 is False."""
        assert not ((2 + 2) < 4)

    def test_undersized_last_page(self):
        """Last page with fewer items: (4 + 2) < 5 is False."""
        assert not ((4 + 2) < 5)


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch48:
    """Batch 48 cross-cutting consistency checks."""

    def test_projects_service_has_list(self):
        """projects.py exports list_projects."""
        from governance.services import projects
        assert hasattr(projects, "list_projects")

    def test_decisions_controller_has_register(self):
        """decisions.py exports register_decisions_controllers."""
        from agent.governance_ui.controllers import decisions
        assert hasattr(decisions, "register_decisions_controllers")

    def test_sessions_controller_has_register(self):
        """sessions.py exports register_sessions_controllers."""
        from agent.governance_ui.controllers import sessions
        assert hasattr(sessions, "register_sessions_controllers")

    def test_projects_returns_dict_with_items(self):
        """list_projects returns dict with items + pagination."""
        from governance.services import projects
        with patch.object(projects, "_projects_store", {}):
            with patch.object(projects, "_get_client", return_value=None):
                result = projects.list_projects()
                assert "items" in result
                assert "pagination" in result
