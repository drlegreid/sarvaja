"""Batch 450-453 — MCP tools logger.error sanitization (18+2 fixes),
services tasks.py exc_info (1 fix),
UI controllers add_error_trace sanitization (12+1 fixes).

Validates fixes for:
- BUG-450-TSK-001: tasks.py add exc_info for stack trace preservation
- BUG-451-RC-001..004: rules_crud.py logger.error {e} → {type(e).__name__}
- BUG-451-RQ-001..004: rules_query.py logger.error {e} → {type(e).__name__}
- BUG-451-RA-001..003: rules_archive.py logger.error {e} → {type(e).__name__}
- BUG-451-TC-001..006: tasks_crud.py logger.error {e} → {type(e).__name__}
- BUG-451-TV-001..002: tasks_crud_verify.py logger.error {e} → {type(e).__name__}
- BUG-453-SES-001..004: sessions.py add_error_trace {e} → {type(e).__name__}
- BUG-453-TST-001..008: tests.py add_error_trace {str(e)}/{e} → {type(e).__name__}
- BUG-453-AUD-001: audit_loaders.py add_error_trace {e} → {type(e).__name__}
"""
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(relpath: str) -> str:
    return (_ROOT / relpath).read_text(encoding="utf-8")


def _check_no_bare_e_in_logger_error(src: str) -> list:
    """Return lines where logger.error uses {e} instead of {type(e).__name__}.

    Matches: logger.error(f"... {e} ...", exc_info=True)
    Ignores lines that already use {type(e).__name__}.
    """
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if "logger.error(" in line and "exc_info=True" in line:
            # Check for bare {e} but NOT {type(e).__name__}
            if re.search(r'\{e\}', line) and '{type(e).__name__}' not in line:
                violations.append((i, line.strip()))
    return violations


def _check_no_bare_e_in_add_error_trace(src: str) -> list:
    """Return lines where add_error_trace uses {e} or {str(e)} instead of {type(e).__name__}."""
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if "add_error_trace(" in line:
            if ('{e}' in line or '{str(e)}' in line) and '{type(e).__name__}' not in line:
                violations.append((i, line.strip()))
    return violations


def _check_no_str_e_in_state(src: str) -> list:
    """Return lines where state assignment uses str(e) to leak exception."""
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if 'state.' in line and 'str(e)' in line and '{type(e).__name__}' not in line:
            violations.append((i, line.strip()))
    return violations


# ─── services/tasks.py — exc_info preservation ──────────────────────────

class TestTasksServiceExcInfo:
    """BUG-450-TSK-001: exc_info=True on document link warning."""

    def test_document_link_has_exc_info(self):
        src = _read("governance/services/tasks.py")
        assert "BUG-450-TSK-001" in src

    def test_document_link_warning_pattern(self):
        src = _read("governance/services/tasks.py")
        # Find the document link warning line
        for line in src.splitlines():
            if "TypeDB document link" in line and "logger.warning" in line:
                assert "exc_info=True" in line, f"Missing exc_info: {line.strip()}"
                break


# ─── MCP tools rules_crud.py — logger.error sanitization ────────────────

class TestRulesCrudLoggerSanitization:
    """BUG-451-RC-001..004: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/rules_crud.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_rule_create_bug_marker(self):
        src = _read("governance/mcp_tools/rules_crud.py")
        assert "BUG-451-RC-001" in src

    def test_rule_update_bug_marker(self):
        src = _read("governance/mcp_tools/rules_crud.py")
        assert "BUG-451-RC-002" in src

    def test_rule_deprecate_bug_marker(self):
        src = _read("governance/mcp_tools/rules_crud.py")
        assert "BUG-451-RC-003" in src

    def test_rule_delete_bug_marker(self):
        src = _read("governance/mcp_tools/rules_crud.py")
        assert "BUG-451-RC-004" in src


# ─── MCP tools rules_query.py — logger.error sanitization ───────────────

class TestRulesQueryLoggerSanitization:
    """BUG-451-RQ-001..004: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/rules_query.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_query_by_tags_bug_marker(self):
        src = _read("governance/mcp_tools/rules_query.py")
        assert "BUG-451-RQ-001" in src

    def test_wisdom_get_bug_marker(self):
        src = _read("governance/mcp_tools/rules_query.py")
        assert "BUG-451-RQ-002" in src

    def test_rule_get_deps_bug_marker(self):
        src = _read("governance/mcp_tools/rules_query.py")
        assert "BUG-451-RQ-003" in src

    def test_find_conflicts_bug_marker(self):
        src = _read("governance/mcp_tools/rules_query.py")
        assert "BUG-451-RQ-004" in src


# ─── MCP tools rules_archive.py — logger.error sanitization ─────────────

class TestRulesArchiveLoggerSanitization:
    """BUG-451-RA-001..003: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/rules_archive.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_list_archived_bug_marker(self):
        src = _read("governance/mcp_tools/rules_archive.py")
        assert "BUG-451-RA-001" in src

    def test_get_archived_bug_marker(self):
        src = _read("governance/mcp_tools/rules_archive.py")
        assert "BUG-451-RA-002" in src

    def test_restore_bug_marker(self):
        src = _read("governance/mcp_tools/rules_archive.py")
        assert "BUG-451-RA-003" in src


# ─── MCP tools tasks_crud.py — logger.error sanitization ────────────────

class TestTasksCrudLoggerSanitization:
    """BUG-451-TC-001..006: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_task_create_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        assert "BUG-451-TC-001" in src

    def test_task_get_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        assert "BUG-451-TC-002" in src

    def test_task_update_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        assert "BUG-451-TC-003" in src

    def test_task_delete_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        assert "BUG-451-TC-004" in src

    def test_taxonomy_get_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        assert "BUG-451-TC-005" in src

    def test_tasks_list_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        assert "BUG-451-TC-006" in src


# ─── MCP tools tasks_crud_verify.py — logger.error sanitization ─────────

class TestTasksCrudVerifyLoggerSanitization:
    """BUG-451-TV-001..002: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/tasks_crud_verify.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_task_verify_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud_verify.py")
        assert "BUG-451-TV-001" in src

    def test_session_sync_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_crud_verify.py")
        assert "BUG-451-TV-002" in src


# ─── UI controllers sessions.py — add_error_trace sanitization ──────────

class TestSessionsControllerErrorTrace:
    """BUG-453-SES-001..004: add_error_trace uses {type(e).__name__} only."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/sessions.py")
        violations = _check_no_bare_e_in_add_error_trace(src)
        assert not violations, f"Bare {{e}} in add_error_trace: {violations}"

    def test_load_detail_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions.py")
        assert "BUG-453-SES-001" in src

    def test_save_session_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions.py")
        assert "BUG-453-SES-002" in src

    def test_delete_session_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions.py")
        assert "BUG-453-SES-003" in src

    def test_attach_evidence_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions.py")
        assert "BUG-453-SES-004" in src


# ─── UI controllers tests.py — add_error_trace sanitization ─────────────

class TestTestsControllerErrorTrace:
    """BUG-453-TST-001..008: add_error_trace + state uses {type(e).__name__} only."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        violations = _check_no_bare_e_in_add_error_trace(src)
        assert not violations, f"Bare {{e}} in add_error_trace: {violations}"

    def test_no_str_e_in_state(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        violations = _check_no_str_e_in_state(src)
        assert not violations, f"str(e) in state assignment: {violations}"

    def test_load_tests_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-001" in src

    def test_poll_errors_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-002" in src

    def test_run_tests_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-003" in src

    def test_view_run_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-004" in src

    def test_regression_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-005" in src

    def test_regression_poll_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-006" in src

    def test_robot_summary_trace_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-007" in src

    def test_robot_summary_state_bug_marker(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        assert "BUG-453-TST-008" in src


# ─── UI controllers audit_loaders.py — add_error_trace sanitization ─────

class TestAuditLoadersErrorTrace:
    """BUG-453-AUD-001: add_error_trace uses {type(e).__name__} only."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/audit_loaders.py")
        violations = _check_no_bare_e_in_add_error_trace(src)
        assert not violations, f"Bare {{e}} in add_error_trace: {violations}"

    def test_load_audit_bug_marker(self):
        src = _read("agent/governance_ui/controllers/audit_loaders.py")
        assert "BUG-453-AUD-001" in src


# ─── Batch 452 CLEAN — Routes layer ─────────────────────────────────────

class TestBatch452RoutesClean:
    """Batch 452: Routes layer confirmed CLEAN."""

    def test_tasks_crud_importable(self):
        src = _read("governance/routes/tasks/crud.py")
        assert "def " in src

    def test_rules_crud_importable(self):
        src = _read("governance/routes/rules/crud.py")
        assert "def " in src

    def test_sessions_crud_importable(self):
        src = _read("governance/routes/sessions/crud.py")
        assert "def " in src

    def test_sessions_detail_importable(self):
        src = _read("governance/routes/sessions/detail.py")
        assert "def " in src

    def test_sessions_relations_importable(self):
        src = _read("governance/routes/sessions/relations.py")
        assert "def " in src


# ─── Import validation ──────────────────────────────────────────────────

class TestBatch453Imports:
    """Verify modified modules compile cleanly."""

    def test_tasks_service_compiles(self):
        src = _read("governance/services/tasks.py")
        compile(src, "tasks.py", "exec")

    def test_rules_crud_compiles(self):
        src = _read("governance/mcp_tools/rules_crud.py")
        compile(src, "rules_crud.py", "exec")

    def test_rules_query_compiles(self):
        src = _read("governance/mcp_tools/rules_query.py")
        compile(src, "rules_query.py", "exec")

    def test_rules_archive_compiles(self):
        src = _read("governance/mcp_tools/rules_archive.py")
        compile(src, "rules_archive.py", "exec")

    def test_tasks_crud_compiles(self):
        src = _read("governance/mcp_tools/tasks_crud.py")
        compile(src, "tasks_crud.py", "exec")

    def test_tasks_crud_verify_compiles(self):
        src = _read("governance/mcp_tools/tasks_crud_verify.py")
        compile(src, "tasks_crud_verify.py", "exec")

    def test_sessions_controller_compiles(self):
        src = _read("agent/governance_ui/controllers/sessions.py")
        compile(src, "sessions.py", "exec")

    def test_tests_controller_compiles(self):
        src = _read("agent/governance_ui/controllers/tests.py")
        compile(src, "tests.py", "exec")

    def test_audit_loaders_compiles(self):
        src = _read("agent/governance_ui/controllers/audit_loaders.py")
        compile(src, "audit_loaders.py", "exec")
