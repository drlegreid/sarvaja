"""
Defense tests for deep scan batches 366-369.

Covers:
- BUG-366-DET-001: routes/sessions/detail.py 3× str(e) error sanitization
- BUG-366-TL-001: mcp_tools/tasks_linking.py 10× str(e) error sanitization + logger

Created: 2026-02-18 (batch 366-369)
"""
import importlib
import inspect

import pytest


# =============================================================================
# BUG-366-DET-001: routes/sessions/detail.py error sanitization
# =============================================================================
class TestSessionsDetailErrorSanitization:
    """Verify all 3 HTTPException handlers in sessions/detail.py use type(e).__name__."""

    def test_no_raw_str_e_in_http_exceptions(self):
        src = inspect.getsource(
            importlib.import_module("governance.routes.sessions.detail")
        )
        # Find lines with HTTPException that interpolate exception variable {e}
        http_error_lines = [
            l.strip() for l in src.split("\n")
            if "HTTPException" in l and "Failed to" in l and "{e}" in l
        ]
        for line in http_error_lines:
            assert "type(e).__name__" in line, \
                f"HTTPException uses raw str(e): {line}"

    def test_logger_error_with_exc_info(self):
        src = inspect.getsource(
            importlib.import_module("governance.routes.sessions.detail")
        )
        # Should have exc_info=True for the 3 detail/tools/thoughts handlers
        exc_info_count = src.count("exc_info=True")
        assert exc_info_count >= 3, \
            f"Expected 3+ exc_info=True, found {exc_info_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.routes.sessions.detail")
        )
        assert "BUG-366-DET-001" in src

    def test_type_name_in_detail_endpoint(self):
        """Verify session_detail endpoint specifically uses type(e).__name__."""
        src = inspect.getsource(
            importlib.import_module("governance.routes.sessions.detail")
        )
        assert 'f"Failed to load session detail: {type(e).__name__}"' in src

    def test_type_name_in_tools_endpoint(self):
        """Verify session_tools endpoint specifically uses type(e).__name__."""
        src = inspect.getsource(
            importlib.import_module("governance.routes.sessions.detail")
        )
        assert 'f"Failed to load session tools: {type(e).__name__}"' in src

    def test_type_name_in_thoughts_endpoint(self):
        """Verify session_thoughts endpoint specifically uses type(e).__name__."""
        src = inspect.getsource(
            importlib.import_module("governance.routes.sessions.detail")
        )
        assert 'f"Failed to load session thoughts: {type(e).__name__}"' in src


# =============================================================================
# BUG-366-TL-001: mcp_tools/tasks_linking.py error sanitization
# =============================================================================
class TestTasksLinkingErrorSanitization:
    """Verify all 10 error handlers in tasks_linking.py use type(e).__name__."""

    def test_has_module_level_logger(self):
        mod = importlib.import_module("governance.mcp_tools.tasks_linking")
        assert hasattr(mod, "logger"), "tasks_linking.py must have a module-level logger"

    def test_no_raw_str_e_in_mcp_returns(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.tasks_linking")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        assert len(mcp_error_lines) >= 10, \
            f"Expected 10+ MCP error return lines, found {len(mcp_error_lines)}"
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_no_bare_str_e(self):
        """Verify no format_mcp_result returns use bare str(e) or {e}."""
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.tasks_linking")
        )
        error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and '"error"' in l
        ]
        for line in error_lines:
            # Skip lines that don't interpolate exception (static error messages)
            if "{e}" not in line and "str(e)" not in line:
                continue
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw exception: {line}"

    def test_logger_error_calls(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.tasks_linking")
        )
        logger_error_count = src.count("logger.error(")
        assert logger_error_count >= 10, \
            f"Expected 10+ logger.error calls, found {logger_error_count}"

    def test_exc_info_true(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.tasks_linking")
        )
        exc_info_count = src.count("exc_info=True")
        assert exc_info_count >= 10, \
            f"Expected 10+ exc_info=True, found {exc_info_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.tasks_linking")
        )
        assert "BUG-366-TL-001" in src

    def test_specific_handlers_sanitized(self):
        """Verify each specific handler function has type(e).__name__."""
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.tasks_linking")
        )
        expected_handlers = [
            "task_link_session", "task_link_rule", "task_link_evidence",
            "task_get_evidence", "task_link_commit", "task_get_commits",
            "task_link_document", "task_get_documents",
            "task_update_details", "task_get_details",
        ]
        for handler in expected_handlers:
            assert f'f"{handler} failed: {{type(e).__name__}}"' in src, \
                f"Handler {handler} missing type(e).__name__ pattern"


# =============================================================================
# Previously fixed files: verify no regression
# =============================================================================
class TestBatch366PriorFixesStable:
    """Verify prior batch fixes haven't regressed."""

    def test_sessions_crud_generic_500_messages(self):
        """sessions/crud.py should use generic 500 messages (batch 352 fix)."""
        src = inspect.getsource(
            importlib.import_module("governance.routes.sessions.crud")
        )
        # The generic Exception handlers should NOT expose {e}
        lines_500 = [
            l.strip() for l in src.split("\n")
            if "status_code=500" in l and "{e}" in l
        ]
        assert len(lines_500) == 0, \
            f"Found {len(lines_500)} HTTPException 500 lines exposing {{e}}"

    def test_rules_crud_generic_500_messages(self):
        """rules/crud.py should use generic 500 messages (batch 355 fix)."""
        src = inspect.getsource(
            importlib.import_module("governance.routes.rules.crud")
        )
        lines_500 = [
            l.strip() for l in src.split("\n")
            if "status_code=500" in l and "{e}" in l
        ]
        assert len(lines_500) == 0, \
            f"Found {len(lines_500)} HTTPException 500 lines exposing {{e}}"


# =============================================================================
# Import sanity checks
# =============================================================================
class TestBatch366Imports:
    """Verify all modified modules import cleanly."""

    def test_import_sessions_detail(self):
        importlib.import_module("governance.routes.sessions.detail")

    def test_import_tasks_linking(self):
        importlib.import_module("governance.mcp_tools.tasks_linking")

    def test_import_sessions_crud(self):
        importlib.import_module("governance.routes.sessions.crud")

    def test_import_rules_crud(self):
        importlib.import_module("governance.routes.rules.crud")
