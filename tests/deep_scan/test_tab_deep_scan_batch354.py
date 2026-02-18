"""
Deep Scan Batch 354-357 Defense Tests.

Validates fixes applied in batches 354-357:
- BUG-355-RUL-001: Rules CRUD info disclosure (9 endpoints)
- BUG-357-TDL-001: task_delete confirmation guard
- BUG-356-SRP-001: session_repair str(e) leak
- BUG-355-RSC-002: rule_scope absolute path bypass
- BUG-354-SES-001: sessions service status whitelist
- BUG-357-MCP-001: tasks_crud MCP error logging
- BUG-357-MCP-002: rules_crud MCP error logging
- BUG-357-MCP-003: tasks_crud_verify MCP error logging
"""
import inspect
import re
import pytest


# =============================================================================
# BUG-355-RUL-001: Rules CRUD info disclosure
# =============================================================================

class TestRulesCrudInfoDisclosure:
    """Verify routes/rules/crud.py returns generic 500 messages."""

    def _get_source(self):
        import governance.routes.rules.crud as mod
        return inspect.getsource(mod)

    def test_no_detail_str_e_in_list_rules(self):
        """list_rules must not leak str(e) in HTTP 500."""
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["list_rules"]
        ).list_rules)
        assert "detail=str(e)" not in src

    def test_no_detail_str_e_in_get_rule(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["get_rule"]
        ).get_rule)
        # The 500 handler should use generic message, not str(e)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line, f"Info disclosure in get_rule 500: {line.strip()}"

    def test_no_detail_str_e_in_create_rule(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["create_rule"]
        ).create_rule)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line, f"Info disclosure in create_rule 500: {line.strip()}"

    def test_no_detail_str_e_in_update_rule(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["update_rule"]
        ).update_rule)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line, f"Info disclosure in update_rule 500: {line.strip()}"

    def test_no_detail_str_e_in_delete_rule(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["delete_rule"]
        ).delete_rule)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line, f"Info disclosure in delete_rule 500: {line.strip()}"

    def test_no_detail_str_e_in_dependency_overview(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["dependency_overview"]
        ).dependency_overview)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line

    def test_no_detail_str_e_in_get_rule_tasks(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["get_rule_tasks"]
        ).get_rule_tasks)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line

    def test_no_detail_str_e_in_get_rule_dependencies(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["get_rule_dependencies"]
        ).get_rule_dependencies)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line

    def test_no_detail_str_e_in_create_rule_dependency(self):
        src = inspect.getsource(__import__(
            "governance.routes.rules.crud", fromlist=["create_rule_dependency"]
        ).create_rule_dependency)
        lines_500 = [l for l in src.split("\n") if "status_code=500" in l]
        for line in lines_500:
            assert "str(e)" not in line

    def test_logger_error_with_exc_info(self):
        """All 500 handlers should log with exc_info=True."""
        src = self._get_source()
        # Count logger.error calls with exc_info=True
        log_calls = re.findall(r"logger\.error\(.+exc_info=True\)", src)
        assert len(log_calls) >= 9, f"Expected 9+ logged 500 handlers, found {len(log_calls)}"


# =============================================================================
# BUG-357-TDL-001: task_delete confirmation guard
# =============================================================================

class TestTaskDeleteConfirmation:
    """Verify task_delete requires explicit confirmation."""

    def test_task_delete_has_confirm_parameter(self):
        """task_delete must accept a confirm parameter."""
        src = inspect.getsource(__import__(
            "governance.mcp_tools.tasks_crud", fromlist=["register_task_crud_tools"]
        ))
        # Find task_delete function definition
        match = re.search(r"def task_delete\((.+?)\)", src)
        assert match, "task_delete function not found"
        params = match.group(1)
        assert "confirm" in params, f"confirm parameter missing from task_delete({params})"

    def test_task_delete_default_confirm_false(self):
        """confirm must default to False."""
        src = inspect.getsource(__import__(
            "governance.mcp_tools.tasks_crud", fromlist=["register_task_crud_tools"]
        ))
        assert "confirm: bool = False" in src, "confirm must default to False"

    def test_task_delete_identity_check(self):
        """Must use 'confirm is not True' for strict check."""
        src = inspect.getsource(__import__(
            "governance.mcp_tools.tasks_crud", fromlist=["register_task_crud_tools"]
        ))
        # Extract the task_delete body
        idx = src.index("def task_delete")
        body = src[idx:idx + 1500]
        assert "confirm is not True" in body, "Must use identity check (is not True)"

    def test_task_delete_returns_error_without_confirm(self):
        """Without confirm=True, should return error JSON."""
        src = inspect.getsource(__import__(
            "governance.mcp_tools.tasks_crud", fromlist=["register_task_crud_tools"]
        ))
        idx = src.index("def task_delete")
        body = src[idx:idx + 1500]
        assert "Deletion requires explicit confirmation" in body


# =============================================================================
# BUG-356-SRP-001: session_repair str(e) leak
# =============================================================================

class TestSessionRepairErrorLeak:
    """Verify session_repair.py doesn't leak internal errors."""

    def test_apply_repair_no_str_e_in_error(self):
        """apply_repair must not return str(e) in error field."""
        from governance.services.session_repair import apply_repair
        src = inspect.getsource(apply_repair)
        # Should use generic message, not str(e)
        assert '"error": str(e)' not in src, "apply_repair still leaks str(e)"
        assert "'error': str(e)" not in src, "apply_repair still leaks str(e)"

    def test_apply_repair_uses_generic_error(self):
        """apply_repair should use generic error message."""
        from governance.services.session_repair import apply_repair
        src = inspect.getsource(apply_repair)
        assert "internal error" in src.lower() or "Repair failed" in src

    def test_apply_repair_logs_full_error(self):
        """apply_repair should log full error with exc_info."""
        from governance.services.session_repair import apply_repair
        src = inspect.getsource(apply_repair)
        assert "exc_info=True" in src


# =============================================================================
# BUG-355-RSC-002: rule_scope absolute path bypass
# =============================================================================

class TestRuleScopeAbsolutePath:
    """Verify rule_scope.py strips leading '/' from absolute paths."""

    def test_absolute_path_matches_relative_scope(self):
        """Absolute path '/governance/foo.py' should match scope 'governance/**'."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(["governance/**"], "/governance/foo.py") is True

    def test_absolute_path_stripped(self):
        """Leading '/' should be stripped before matching."""
        from governance.services.rule_scope import rule_applies_to_path
        # '/agent/bar.py' should match 'agent/**'
        assert rule_applies_to_path(["agent/**"], "/agent/bar.py") is True

    def test_double_slash_path(self):
        """'//governance/foo.py' should still match."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(["governance/**"], "//governance/foo.py") is True

    def test_relative_path_still_works(self):
        """Regular relative paths should still match."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(["governance/**"], "governance/foo.py") is True

    def test_no_scope_still_global(self):
        """None scope still means global (applies everywhere)."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(None, "/any/path.py") is True

    def test_lstrip_in_source(self):
        """Source must contain path.lstrip('/') for absolute path handling."""
        from governance.services.rule_scope import rule_applies_to_path
        src = inspect.getsource(rule_applies_to_path)
        assert 'lstrip("/")' in src or "lstrip('/')" in src


# =============================================================================
# BUG-354-SES-001: sessions service status whitelist
# =============================================================================

class TestSessionsStatusWhitelist:
    """Verify sessions service validates status values."""

    def test_status_whitelist_exists(self):
        """list_sessions must have a status whitelist."""
        from governance.services.sessions import list_sessions
        src = inspect.getsource(list_sessions)
        assert "_VALID_STATUSES" in src, "Status whitelist not found"

    def test_whitelist_contains_standard_statuses(self):
        """Whitelist must include ACTIVE, COMPLETED, ENDED."""
        from governance.services.sessions import list_sessions
        src = inspect.getsource(list_sessions)
        assert '"ACTIVE"' in src
        assert '"COMPLETED"' in src
        assert '"ENDED"' in src

    def test_invalid_status_ignored(self):
        """Invalid status values should be silently ignored."""
        from governance.services.sessions import list_sessions
        src = inspect.getsource(list_sessions)
        # After whitelist check, invalid status should be set to None
        assert "status = None" in src, "Invalid status should be nullified"


# =============================================================================
# BUG-357-MCP-001: tasks_crud MCP error logging
# =============================================================================

class TestTasksCrudMcpErrorLogging:
    """Verify tasks_crud.py logs errors and uses type(e).__name__."""

    def _get_source(self):
        import governance.mcp_tools.tasks_crud as mod
        return inspect.getsource(mod)

    def test_has_logger_import(self):
        """Module must import logging and create logger."""
        src = self._get_source()
        assert "import logging" in src
        assert "logger = logging.getLogger" in src

    def test_error_handlers_log_before_return(self):
        """All MCP exception handlers should log the error."""
        src = self._get_source()
        # Count logger.error calls
        log_count = len(re.findall(r"logger\.error\(", src))
        assert log_count >= 6, f"Expected 6+ logger.error calls, found {log_count}"

    def test_error_returns_use_type_name(self):
        """format_mcp_result error returns should use type(e).__name__ not str(e)."""
        src = self._get_source()
        # Only check format_mcp_result lines, not logger.error lines
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, f"MCP error return uses raw str(e): {line}"
        assert len(mcp_error_lines) >= 6, f"Expected 6+ MCP error returns, found {len(mcp_error_lines)}"


# =============================================================================
# BUG-357-MCP-002: rules_crud MCP error logging
# =============================================================================

class TestRulesCrudMcpErrorLogging:
    """Verify rules_crud.py logs errors and uses type(e).__name__."""

    def _get_source(self):
        import governance.mcp_tools.rules_crud as mod
        return inspect.getsource(mod)

    def test_has_logger_import(self):
        src = self._get_source()
        assert "import logging" in src
        assert "logger = logging.getLogger" in src

    def test_error_handlers_log_before_return(self):
        src = self._get_source()
        log_count = len(re.findall(r"logger\.error\(", src))
        assert log_count >= 4, f"Expected 4+ logger.error calls, found {log_count}"

    def test_error_returns_use_type_name(self):
        src = self._get_source()
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, f"MCP error return uses raw str(e): {line}"
        assert len(mcp_error_lines) >= 4, f"Expected 4+ MCP error returns, found {len(mcp_error_lines)}"


# =============================================================================
# BUG-357-MCP-003: tasks_crud_verify MCP error logging
# =============================================================================

class TestTasksCrudVerifyMcpErrorLogging:
    """Verify tasks_crud_verify.py logs errors and uses type(e).__name__."""

    def _get_source(self):
        import governance.mcp_tools.tasks_crud_verify as mod
        return inspect.getsource(mod)

    def test_has_logger_import(self):
        src = self._get_source()
        assert "import logging" in src
        assert "logger = logging.getLogger" in src

    def test_error_handlers_log_before_return(self):
        src = self._get_source()
        log_count = len(re.findall(r"logger\.error\(", src))
        assert log_count >= 2, f"Expected 2+ logger.error calls, found {log_count}"

    def test_error_returns_use_type_name(self):
        src = self._get_source()
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, f"MCP error return uses raw str(e): {line}"
        assert len(mcp_error_lines) >= 2, f"Expected 2+ MCP error returns, found {len(mcp_error_lines)}"


# =============================================================================
# Import sanity tests
# =============================================================================

class TestBatch354Imports:
    """Verify all modified modules still import correctly."""

    def test_import_rules_crud_routes(self):
        import governance.routes.rules.crud  # noqa: F401

    def test_import_tasks_crud_mcp(self):
        import governance.mcp_tools.tasks_crud  # noqa: F401

    def test_import_rules_crud_mcp(self):
        import governance.mcp_tools.rules_crud  # noqa: F401

    def test_import_tasks_crud_verify(self):
        import governance.mcp_tools.tasks_crud_verify  # noqa: F401

    def test_import_session_repair(self):
        import governance.services.session_repair  # noqa: F401

    def test_import_rule_scope(self):
        import governance.services.rule_scope  # noqa: F401

    def test_import_sessions_service(self):
        import governance.services.sessions  # noqa: F401
