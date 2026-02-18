"""
Batch 80 — Security Patterns + Error Propagation.

Triage: TypeQL injection (0 real vulns) + Error handling (1 confirmed).
Fix: BUG-PROJECTS-NOHANDLER — Projects CRUD now catches ConnectionError→503.

Also validates: TypeQL escaping patterns, decision escaping at caller,
route exception handler consistency.
"""
import inspect

import pytest


# ===========================================================================
# FIX: BUG-PROJECTS-NOHANDLER — Projects routes now have exception handlers
# ===========================================================================

class TestProjectsCRUDExceptionHandlers:
    """Verify all project CRUD routes catch exceptions properly."""

    def test_list_projects_catches_connection_error(self):
        """list_projects route catches ConnectionError → 503."""
        from governance.routes.projects.crud import list_projects
        src = inspect.getsource(list_projects)
        assert "except ConnectionError" in src
        assert "503" in src

    def test_create_project_catches_connection_error(self):
        """create_project route catches ConnectionError → 503."""
        from governance.routes.projects.crud import create_project
        src = inspect.getsource(create_project)
        assert "except ConnectionError" in src
        assert "503" in src

    def test_get_project_catches_connection_error(self):
        """get_project route catches ConnectionError → 503."""
        from governance.routes.projects.crud import get_project
        src = inspect.getsource(get_project)
        assert "except ConnectionError" in src
        assert "503" in src

    def test_delete_project_catches_connection_error(self):
        """delete_project route catches ConnectionError → 503."""
        from governance.routes.projects.crud import delete_project
        src = inspect.getsource(delete_project)
        assert "except ConnectionError" in src
        assert "503" in src

    def test_list_projects_catches_generic_exception(self):
        """list_projects has catch-all → 500."""
        from governance.routes.projects.crud import list_projects
        src = inspect.getsource(list_projects)
        assert "except Exception" in src
        assert "500" in src

    def test_crud_routes_re_raise_http_exception(self):
        """Routes that catch Exception must re-raise HTTPException."""
        from governance.routes.projects.crud import (
            create_project, get_project, delete_project,
        )
        for fn in [create_project, get_project, delete_project]:
            src = inspect.getsource(fn)
            assert "except HTTPException:" in src, f"{fn.__name__} missing HTTPException re-raise"
            assert "raise" in src


# ===========================================================================
# Rejected: TypeQL injection — all values properly escaped
# ===========================================================================

class TestTypeQLEscapingPatterns:
    """Verify TypeQL escaping is consistently applied across CRUD operations."""

    def test_decision_update_pre_escapes_values(self):
        """update_decision() escapes all values BEFORE passing to _update_decision_attr."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries.update_decision)
        # Line 209: list comprehension escapes all values
        assert 'val.replace(\'"\', \'\\\\"\')' in src or \
               'val.replace(\'"\',' in src

    def test_create_decision_escapes_all_fields(self):
        """create_decision() escapes name, context, rationale, and decision_id."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries.create_decision)
        for field in ["name_escaped", "context_escaped", "rationale_escaped", "decision_id_escaped"]:
            assert field in src

    def test_task_update_attribute_escapes(self):
        """Task _update_attribute helper escapes new_value."""
        from governance.typedb.queries.tasks import crud as task_crud
        src = inspect.getsource(task_crud)
        # BUG-393-CRUD-001: _strip_ctl wraps new_value before .replace
        assert "new_escaped = _strip_ctl(new_value).replace" in src

    def test_rule_create_escapes_fields(self):
        """Rule create_rule() escapes name, directive, and rule_id."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.create_rule)
        assert "name_escaped" in src
        assert "directive_escaped" in src
        assert "rule_id_escaped" in src

    def test_session_insert_escapes_fields(self):
        """Session insert_session() escapes all interpolated fields."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.insert_session)
        assert 'replace(\'"\', \'\\\\"\')' in src or \
               'replace(\'"\',' in src


# ===========================================================================
# Rejected: Error propagation design choices
# ===========================================================================

class TestErrorPropagationDesign:
    """Confirm error handling patterns are intentional design."""

    def test_rules_service_raises_on_missing(self):
        """Rules service raises KeyError for missing rules."""
        from governance.services.rules import get_rule
        src = inspect.getsource(get_rule)
        assert "KeyError" in src

    def test_tasks_service_has_fallback(self):
        """Task service falls back to in-memory store on TypeDB failure."""
        from governance.services.tasks_mutations import update_task
        src = inspect.getsource(update_task)
        assert "_tasks_store" in src
        assert "using fallback" in src

    def test_sessions_service_has_fallback(self):
        """Session service falls back via allow_fallback=True."""
        from governance.services.sessions import get_session
        src = inspect.getsource(get_session)
        assert "allow_fallback=True" in src

    def test_rules_route_catches_connection_error(self):
        """Rules route catches ConnectionError → 503."""
        from governance.routes.rules.crud import get_rule as route_fn
        src = inspect.getsource(route_fn)
        assert "except ConnectionError" in src
        assert "503" in src

    def test_tasks_route_catches_connection_error(self):
        """Tasks route list catches ConnectionError → 503."""
        from governance.routes.tasks.crud import list_tasks
        src = inspect.getsource(list_tasks)
        assert "503" in src
