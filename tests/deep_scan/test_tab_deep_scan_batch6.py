"""
Unit tests for Tab Deep Scan Batch 6 fixes.

Covers: add_error_trace additions across tasks_navigation, sessions,
sessions_detail_loaders, sessions_pagination, tasks, backlog, search.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import ast
import inspect
from unittest.mock import MagicMock


# ── tasks_navigation.py: trace imports + both handlers traced ──────


class TestTasksNavigationTraces:
    def test_has_add_error_trace_import(self):
        """tasks_navigation.py must import add_error_trace."""
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        assert "add_error_trace" in source

    def test_navigate_to_task_has_trace(self):
        """navigate_to_task exception handler must trace."""
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        assert "Navigate to task failed" in source

    def test_navigate_back_to_source_has_trace(self):
        """navigate_back_to_source exception handler must trace."""
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        assert "Navigate back to session failed" in source

    def test_no_bare_except_pass(self):
        """No bare 'except Exception: pass' in tasks_navigation."""
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        # After fix, no except block should just have 'pass'
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if (len(node.body) == 1 and
                        isinstance(node.body[0], ast.Pass)):
                    # Should not happen anymore
                    assert False, "Found bare except: pass"


# ── sessions.py: submit/delete/attach traced ──────────────────────


class TestSessionsControllerTraces:
    def test_save_session_has_trace(self):
        """submit_session_form exception must trace."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "Save session failed" in source

    def test_delete_session_has_trace(self):
        """delete_session exception must trace."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "Delete session failed" in source

    def test_attach_evidence_has_trace(self):
        """attach_evidence exception must trace."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "Attach evidence failed" in source


# ── sessions_detail_loaders.py: session_tasks traced ──────────────


class TestSessionsDetailLoadersTraces:
    def test_load_session_tasks_has_trace(self):
        """load_session_tasks exception must use add_error_trace."""
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert "Load session tasks failed" in source

    def test_no_raw_error_message_in_tasks_loader(self):
        """load_session_tasks should NOT set error_message directly."""
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert "Failed to load session tasks" not in source


# ── sessions_pagination.py: load_sessions_page traced ─────────────


class TestSessionsPaginationTraces:
    def test_load_sessions_page_has_trace(self):
        """load_sessions_page exception must trace."""
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "Load sessions page failed" in source

    def test_compute_pivot_has_trace(self):
        """_compute_pivot already had trace (verify not broken)."""
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "Compute pivot failed" in source


# ── tasks.py: all 7 CRUD exceptions traced ────────────────────────


class TestTasksControllerTraces:
    def test_delete_task_has_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Delete task failed" in source

    def test_claim_task_has_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Claim task failed" in source

    def test_complete_task_has_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Complete task failed" in source

    def test_update_task_has_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Update task failed" in source

    def test_create_task_has_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Create task failed" in source

    def test_attach_document_has_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Attach document failed" in source

    def test_load_tasks_page_has_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Load tasks page failed" in source


# ── backlog.py: all 3 exceptions traced ───────────────────────────


class TestBacklogTraces:
    def test_has_add_error_trace_import(self):
        """backlog.py must import add_error_trace."""
        from agent.governance_ui.controllers import backlog
        source = inspect.getsource(backlog)
        assert "add_error_trace" in source

    def test_claim_backlog_task_has_trace(self):
        from agent.governance_ui.controllers import backlog
        source = inspect.getsource(backlog)
        assert "Claim backlog task failed" in source

    def test_complete_backlog_task_has_trace(self):
        from agent.governance_ui.controllers import backlog
        source = inspect.getsource(backlog)
        assert "Complete backlog task failed" in source

    def test_auto_refresh_has_trace(self):
        from agent.governance_ui.controllers import backlog
        source = inspect.getsource(backlog)
        assert "Start auto-refresh failed" in source


# ── search.py: search exception traced ────────────────────────────


class TestSearchTraces:
    def test_has_add_error_trace_import(self):
        """search.py must import add_error_trace."""
        from agent.governance_ui.controllers import search
        source = inspect.getsource(search)
        assert "add_error_trace" in source

    def test_perform_search_has_trace(self):
        from agent.governance_ui.controllers import search
        source = inspect.getsource(search)
        assert "Evidence search failed" in source
