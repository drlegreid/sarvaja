"""
Defense tests for deep scan batches 362-365.

Covers:
- BUG-362-RQ-001: rules_query.py 4× str(e) error sanitization
- BUG-362-RA-001: rules_archive.py 3× str(e) error sanitization
- BUG-362-SL-001: sessions_linking.py 4× str(e) error sanitization
- BUG-362-DEC-001: decisions.py str(e) error sanitization
- BUG-362-AGT-001: agents.py 5× str(e) error sanitization
- BUG-365-RT-001: routes/tasks/crud.py 4× str(e) error sanitization
- BUG-364-CRUD-001: tasks/crud.py 2× silent exception → logger.debug
- BUG-364-LINK-001: tasks/linking.py 3× silent exception → logger.debug

Created: 2026-02-18 (batch 362-365)
"""
import importlib
import inspect
import re

import pytest


# =============================================================================
# BUG-362-RQ-001: rules_query.py error sanitization
# =============================================================================
class TestRulesQueryErrorSanitization:
    """Verify all error handlers in rules_query.py use type(e).__name__."""

    def test_has_module_level_logger(self):
        mod = importlib.import_module("governance.mcp_tools.rules_query")
        assert hasattr(mod, "logger"), "rules_query.py must have a module-level logger"

    def test_no_raw_str_e_in_mcp_returns(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.rules_query")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_logger_error_calls(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.rules_query")
        )
        # At least 4 logger.error calls (rules_query_by_tags, wisdom_get, rule_get_deps, rules_find_conflicts)
        logger_error_count = src.count("logger.error(")
        assert logger_error_count >= 4, \
            f"Expected 4+ logger.error calls, found {logger_error_count}"

    def test_exc_info_true(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.rules_query")
        )
        exc_info_count = src.count("exc_info=True")
        assert exc_info_count >= 4, \
            f"Expected 4+ exc_info=True, found {exc_info_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.rules_query")
        )
        assert "BUG-362-RQ-001" in src


# =============================================================================
# BUG-362-RA-001: rules_archive.py error sanitization
# =============================================================================
class TestRulesArchiveErrorSanitization:
    """Verify all 3 error handlers in rules_archive.py use type(e).__name__."""

    def test_has_module_level_logger(self):
        mod = importlib.import_module("governance.mcp_tools.rules_archive")
        assert hasattr(mod, "logger"), "rules_archive.py must have a module-level logger"

    def test_no_raw_str_e_in_mcp_returns(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.rules_archive")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        assert len(mcp_error_lines) >= 3, \
            f"Expected 3+ MCP error return lines, found {len(mcp_error_lines)}"
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_logger_error_calls(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.rules_archive")
        )
        logger_error_count = src.count("logger.error(")
        assert logger_error_count >= 3, \
            f"Expected 3+ logger.error calls, found {logger_error_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.rules_archive")
        )
        assert "BUG-362-RA-001" in src


# =============================================================================
# BUG-362-SL-001: sessions_linking.py error sanitization
# =============================================================================
class TestSessionsLinkingErrorSanitization:
    """Verify all 4 error handlers in sessions_linking.py use type(e).__name__."""

    def test_has_module_level_logger(self):
        mod = importlib.import_module("governance.mcp_tools.sessions_linking")
        assert hasattr(mod, "logger"), "sessions_linking.py must have a module-level logger"

    def test_no_raw_str_e_in_mcp_returns(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.sessions_linking")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        assert len(mcp_error_lines) >= 4, \
            f"Expected 4+ MCP error return lines, found {len(mcp_error_lines)}"
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_logger_error_calls(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.sessions_linking")
        )
        logger_error_count = src.count("logger.error(")
        assert logger_error_count >= 4, \
            f"Expected 4+ logger.error calls, found {logger_error_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.sessions_linking")
        )
        assert "BUG-362-SL-001" in src


# =============================================================================
# BUG-362-DEC-001: decisions.py error sanitization
# =============================================================================
class TestDecisionsErrorSanitization:
    """Verify governance_get_decision_impacts uses type(e).__name__."""

    def test_no_raw_str_e_in_decision_impacts(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.decisions")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "decision_impacts failed:" in l
        ]
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_logger_error_call(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.decisions")
        )
        assert "logger.error(" in src, "decisions.py must use logger.error"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.decisions")
        )
        assert "BUG-362-DEC-001" in src


# =============================================================================
# BUG-362-AGT-001: agents.py error sanitization
# =============================================================================
class TestAgentsErrorSanitization:
    """Verify all 5 error handlers in agents.py use type(e).__name__."""

    def test_no_raw_str_e_in_mcp_returns(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.agents")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        assert len(mcp_error_lines) >= 5, \
            f"Expected 5+ MCP error return lines, found {len(mcp_error_lines)}"
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_logger_error_calls(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.agents")
        )
        logger_error_count = src.count("logger.error(")
        assert logger_error_count >= 5, \
            f"Expected 5+ logger.error calls, found {logger_error_count}"

    def test_exc_info_true(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.agents")
        )
        exc_info_count = src.count("exc_info=True")
        assert exc_info_count >= 5, \
            f"Expected 5+ exc_info=True, found {exc_info_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.agents")
        )
        assert "BUG-362-AGT-001" in src


# =============================================================================
# BUG-365-RT-001: routes/tasks/crud.py error sanitization
# =============================================================================
class TestRoutesTasksCrudErrorSanitization:
    """Verify all 4 HTTPException handlers in tasks crud use type(e).__name__."""

    def test_no_raw_str_e_in_http_exceptions(self):
        src = inspect.getsource(
            importlib.import_module("governance.routes.tasks.crud")
        )
        # Find lines with HTTPException that interpolate exception variable {e}
        # (skip static error messages that don't reference exception)
        http_error_lines = [
            l.strip() for l in src.split("\n")
            if "HTTPException" in l and "Failed to" in l and "{e}" in l
        ]
        # If any lines still use raw {e}, they should use type(e).__name__
        for line in http_error_lines:
            assert "type(e).__name__" in line, \
                f"HTTPException uses raw str(e): {line}"

    def test_logger_error_with_exc_info(self):
        src = inspect.getsource(
            importlib.import_module("governance.routes.tasks.crud")
        )
        # Should have logger.error with exc_info=True for the 4 handlers
        exc_info_count = src.count("exc_info=True")
        assert exc_info_count >= 4, \
            f"Expected 4+ exc_info=True, found {exc_info_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.routes.tasks.crud")
        )
        assert "BUG-365-RT-001" in src


# =============================================================================
# BUG-364-CRUD-001: tasks/crud.py silent exception logging
# =============================================================================
class TestTasksCrudSilentException:
    """Verify silent exception suppression is replaced with logging in delete_task."""

    def test_no_bare_except_pass_in_delete(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.crud")
        )
        # Extract delete_task method
        delete_start = src.find("def delete_task(")
        assert delete_start > 0, "delete_task method must exist"
        delete_section = src[delete_start:]
        # No bare pass in delete_task
        bare_pass_count = len(re.findall(
            r"except\s+Exception\s*:\s*\n\s*pass", delete_section
        ))
        assert bare_pass_count == 0, \
            f"Found {bare_pass_count} bare except Exception: pass in delete_task"

    def test_has_logger_debug_in_delete(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.crud")
        )
        delete_start = src.find("def delete_task(")
        delete_section = src[delete_start:]
        debug_count = delete_section.count("logger.debug(")
        assert debug_count >= 2, \
            f"Expected 2+ logger.debug in delete_task, found {debug_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.crud")
        )
        assert "BUG-364-CRUD-001" in src


# =============================================================================
# BUG-364-LINK-001: tasks/linking.py silent exception logging
# =============================================================================
class TestTasksLinkingSilentException:
    """Verify silent exception suppression is replaced with logging."""

    def test_no_bare_except_pass(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.linking")
        )
        bare_pass_count = len(re.findall(
            r"except\s+Exception\s*:\s*\n\s*pass", src
        ))
        assert bare_pass_count == 0, \
            f"Found {bare_pass_count} bare except Exception: pass — should use logger.debug"

    def test_has_logger_debug_for_entity_inserts(self):
        """Entity insert try/except blocks should log at debug level."""
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.linking")
        )
        # Should have logger.debug for evidence, commit, and document entity inserts
        debug_count = src.count("logger.debug(")
        assert debug_count >= 3, \
            f"Expected 3+ logger.debug calls, found {debug_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.linking")
        )
        assert "BUG-364-LINK-001" in src


# =============================================================================
# Import sanity checks
# =============================================================================
class TestBatch362Imports:
    """Verify all modified modules import cleanly."""

    def test_import_rules_query(self):
        importlib.import_module("governance.mcp_tools.rules_query")

    def test_import_rules_archive(self):
        importlib.import_module("governance.mcp_tools.rules_archive")

    def test_import_sessions_linking(self):
        importlib.import_module("governance.mcp_tools.sessions_linking")

    def test_import_decisions(self):
        importlib.import_module("governance.mcp_tools.decisions")

    def test_import_agents(self):
        importlib.import_module("governance.mcp_tools.agents")

    def test_import_routes_tasks_crud(self):
        importlib.import_module("governance.routes.tasks.crud")

    def test_import_typedb_tasks_crud(self):
        importlib.import_module("governance.typedb.queries.tasks.crud")

    def test_import_typedb_tasks_linking(self):
        importlib.import_module("governance.typedb.queries.tasks.linking")
