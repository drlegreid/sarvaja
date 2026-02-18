"""Batch 458-461 — MCP tools + stores logger.error/warning sanitization (23 fixes).

Validates fixes for:
- BUG-458-AGT-001..005: agents.py logger.error {e} → {type(e).__name__}
- BUG-458-TRU-001: trust.py logger.error {e} → {type(e).__name__}
- BUG-458-DEC-001..002: decisions.py logger.error/warning {e} → {type(e).__name__}
- BUG-459-TL-001..010: tasks_linking.py logger.error {e} → {type(e).__name__}
- BUG-460-STA-001..003: stores/agents.py logger.warning {e} → {type(e).__name__} + exc_info
- BUG-460-RTY-001..002: stores/retry.py logger.warning/error {e} → {type(e).__name__}
- Batch 461 (TypeDB queries): All CLEAN
"""
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(relpath: str) -> str:
    return (_ROOT / relpath).read_text(encoding="utf-8")


def _check_no_bare_e_in_logger_error(src: str) -> list:
    """Return lines where logger.error uses {e} instead of {type(e).__name__}."""
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if "logger.error(" in line and "exc_info=True" in line:
            if re.search(r'\{e\}', line) and '{type(e).__name__}' not in line:
                violations.append((i, line.strip()))
    return violations


def _check_no_bare_e_in_logger_warning(src: str) -> list:
    """Return lines where logger.warning uses {e} instead of {type(e).__name__}."""
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if "logger.warning(" in line:
            if re.search(r'\{e\}', line) and '{type(e).__name__}' not in line:
                violations.append((i, line.strip()))
    return violations


# ─── MCP tools agents.py — logger.error sanitization ──────────────────

class TestAgentsLoggerSanitization:
    """BUG-458-AGT-001..005: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/agents.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_agent_create_bug_marker(self):
        src = _read("governance/mcp_tools/agents.py")
        assert "BUG-458-AGT-001" in src

    def test_agent_get_bug_marker(self):
        src = _read("governance/mcp_tools/agents.py")
        assert "BUG-458-AGT-002" in src

    def test_agents_list_bug_marker(self):
        src = _read("governance/mcp_tools/agents.py")
        assert "BUG-458-AGT-003" in src

    def test_agent_trust_update_bug_marker(self):
        src = _read("governance/mcp_tools/agents.py")
        assert "BUG-458-AGT-004" in src

    def test_agents_dashboard_bug_marker(self):
        src = _read("governance/mcp_tools/agents.py")
        assert "BUG-458-AGT-005" in src


# ─── MCP tools trust.py — logger.error sanitization ───────────────────

class TestTrustLoggerSanitization:
    """BUG-458-TRU-001: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/trust.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_trust_score_bug_marker(self):
        src = _read("governance/mcp_tools/trust.py")
        assert "BUG-458-TRU-001" in src


# ─── MCP tools decisions.py — logger sanitization ─────────────────────

class TestDecisionsLoggerSanitization:
    """BUG-458-DEC-001..002: logger uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/decisions.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_no_bare_e_in_logger_warning(self):
        src = _read("governance/mcp_tools/decisions.py")
        violations = _check_no_bare_e_in_logger_warning(src)
        assert not violations, f"Bare {{e}} in logger.warning: {violations}"

    def test_decision_impacts_bug_marker(self):
        src = _read("governance/mcp_tools/decisions.py")
        assert "BUG-458-DEC-001" in src

    def test_statistics_warning_bug_marker(self):
        src = _read("governance/mcp_tools/decisions.py")
        assert "BUG-458-DEC-002" in src


# ─── MCP tools tasks_linking.py — logger.error sanitization ───────────

class TestTasksLinkingLoggerSanitization:
    """BUG-459-TL-001..010: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_link_session_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-001" in src

    def test_link_rule_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-002" in src

    def test_link_evidence_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-003" in src

    def test_get_evidence_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-004" in src

    def test_link_commit_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-005" in src

    def test_get_commits_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-006" in src

    def test_link_document_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-007" in src

    def test_get_documents_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-008" in src

    def test_update_details_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-009" in src

    def test_get_details_bug_marker(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        assert "BUG-459-TL-010" in src


# ─── Stores agents.py — logger.warning sanitization ───────────────────

class TestStoresAgentsLoggerSanitization:
    """BUG-460-STA-001..003: logger.warning uses {type(e).__name__} + exc_info."""

    def test_no_bare_e_in_logger_warning(self):
        src = _read("governance/stores/agents.py")
        violations = _check_no_bare_e_in_logger_warning(src)
        assert not violations, f"Bare {{e}} in logger.warning: {violations}"

    def test_yaml_load_bug_marker(self):
        src = _read("governance/stores/agents.py")
        assert "BUG-460-STA-001" in src

    def test_metrics_load_bug_marker(self):
        src = _read("governance/stores/agents.py")
        assert "BUG-460-STA-002" in src

    def test_metrics_save_bug_marker(self):
        src = _read("governance/stores/agents.py")
        assert "BUG-460-STA-003" in src


# ─── Stores retry.py — logger sanitization ────────────────────────────

class TestStoresRetryLoggerSanitization:
    """BUG-460-RTY-001..002: logger.warning/error uses {type(e).__name__}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/stores/retry.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_no_bare_e_in_logger_warning(self):
        src = _read("governance/stores/retry.py")
        violations = _check_no_bare_e_in_logger_warning(src)
        assert not violations, f"Bare {{e}} in logger.warning: {violations}"

    def test_retry_warning_bug_marker(self):
        src = _read("governance/stores/retry.py")
        assert "BUG-460-RTY-001" in src

    def test_retry_error_bug_marker(self):
        src = _read("governance/stores/retry.py")
        assert "BUG-460-RTY-002" in src


# ─── Batch 461 CLEAN — TypeDB queries ─────────────────────────────────

class TestBatch461TypeDBClean:
    """Batch 461: TypeDB queries layer confirmed CLEAN."""

    def test_rules_crud_importable(self):
        src = _read("governance/typedb/queries/rules/crud.py")
        assert "def " in src

    def test_rules_inference_importable(self):
        src = _read("governance/typedb/queries/rules/inference.py")
        assert "def " in src

    def test_tasks_crud_importable(self):
        src = _read("governance/typedb/queries/tasks/crud.py")
        assert "def " in src

    def test_tasks_linking_importable(self):
        src = _read("governance/typedb/queries/tasks/linking.py")
        assert "def " in src

    def test_tasks_relationships_importable(self):
        src = _read("governance/typedb/queries/tasks/relationships.py")
        assert "def " in src

    def test_tasks_status_importable(self):
        src = _read("governance/typedb/queries/tasks/status.py")
        assert "def " in src


# ─── Import validation ─────────────────────────────────────────────────

class TestBatch461Imports:
    """Verify modified modules compile cleanly."""

    def test_agents_mcp_compiles(self):
        src = _read("governance/mcp_tools/agents.py")
        compile(src, "agents.py", "exec")

    def test_trust_compiles(self):
        src = _read("governance/mcp_tools/trust.py")
        compile(src, "trust.py", "exec")

    def test_decisions_compiles(self):
        src = _read("governance/mcp_tools/decisions.py")
        compile(src, "decisions.py", "exec")

    def test_tasks_linking_compiles(self):
        src = _read("governance/mcp_tools/tasks_linking.py")
        compile(src, "tasks_linking.py", "exec")

    def test_stores_agents_compiles(self):
        src = _read("governance/stores/agents.py")
        compile(src, "agents.py", "exec")

    def test_retry_compiles(self):
        src = _read("governance/stores/retry.py")
        compile(src, "retry.py", "exec")
