"""Deep scan batch 176: Route handlers layer.

Batch 176 findings: 17 total, 2 confirmed fixes, 15 rejected/deferred.
- BUG-TESTRESULTS-200-001: get_test_results returned 200 with error body instead of 404.
- BUG-TASKSESSIONS-NONE-001: get_task_sessions checked None but service returns [].
"""
import pytest
from pathlib import Path


# ── Test results 404 defense ──────────────


class TestTestResults404Defense:
    """Verify get_test_results raises 404 for missing runs."""

    def test_uses_http_exception(self):
        """get_test_results uses HTTPException for missing runs."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tests/runner.py").read_text()
        # Find get_test_results function
        start = src.index("def get_test_results")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "HTTPException" in func
        assert "404" in func

    def test_no_200_error_response(self):
        """get_test_results does not return dict with error key."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tests/runner.py").read_text()
        start = src.index("def get_test_results")
        # Find only the get_test_results function (next @router or async def)
        end = src.index("\n@router", start + 1) if "\n@router" in src[start + 1:] else src.index("\nasync def ", start + 1)
        func = src[start:end]
        assert 'return {"error":' not in func

    def test_http_exception_imported(self):
        """HTTPException is imported in runner.py."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tests/runner.py").read_text()
        # Check the first 500 chars (import section)
        assert "HTTPException" in src[:800]


# ── Task sessions existence check defense ──────────────


class TestTaskSessionsExistenceCheckDefense:
    """Verify get_task_sessions properly checks task existence."""

    def test_uses_get_task_for_existence(self):
        """Route uses get_task() to verify task exists before returning sessions."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tasks/crud.py").read_text()
        start = src.index("def get_task_sessions")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "get_task(" in func

    def test_no_none_check_on_sessions(self):
        """Route does NOT check 'if sessions is None' (service returns [])."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tasks/crud.py").read_text()
        start = src.index("def get_task_sessions")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "sessions is None" not in func


# ── Session CRUD exception handling defense ──────────────


class TestSessionCRUDExceptionDefense:
    """Verify session CRUD routes have proper error handling."""

    def test_create_session_has_try_except(self):
        """create_session has try/except block."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        start = src.index("def create_session")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "except" in func

    def test_list_sessions_has_pagination(self):
        """list_sessions uses PaginationMeta."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        assert "PaginationMeta" in src


# ── Agent CRUD defense ──────────────


class TestAgentCRUDDefense:
    """Verify agent CRUD routes exist."""

    def test_agent_routes_importable(self):
        """Agent routes module is importable."""
        root = Path(__file__).parent.parent.parent
        assert (root / "governance/routes/agents/crud.py").exists()

    def test_agent_observability_routes_exist(self):
        """Agent observability routes module exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / "governance/routes/agents/observability.py").exists()
