"""Batch 409 — exc_info hardening, MCP error sanitization, log level upgrade tests.

Validates fixes for:
- BUG-406-LNK-001..005: cc_link_miner.py exc_info + type(e).__name__ in errors list
- BUG-407-PRJ-001..005: projects.py exc_info additions
- BUG-407-RUL-001: rules.py _monitor exc_info
- BUG-407-EVD-001..003: session_evidence.py exc_info additions
- BUG-408-SES-001..003: sessions.py exc_info additions
- BUG-408-SLC-001..003: sessions_lifecycle.py exc_info additions
- BUG-408-TSK-001..004: tasks.py exc_info additions
- BUG-408-TM-001..002: tasks_mutations.py exc_info additions
- BUG-409-RQ-001..002: rules_query.py debug→warning + exc_info
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info_on_warning(src, error_fragment):
    """Find logger.warning line containing fragment, verify exc_info=True."""
    idx = src.index(error_fragment)
    line_end = src.index("\n", idx)
    line_start = src.rindex("\n", 0, idx) + 1
    line = src[line_start:line_end]
    assert "exc_info=True" in line, f"Missing exc_info=True in: {line.strip()}"


def _check_exc_info_on_error(src, error_fragment):
    """Find logger.error line containing fragment, verify exc_info=True."""
    idx = src.index(error_fragment)
    line_end = src.index("\n", idx)
    line_start = src.rindex("\n", 0, idx) + 1
    line = src[line_start:line_end]
    assert "exc_info=True" in line, f"Missing exc_info=True in: {line.strip()}"


# ── BUG-406-LNK-001..005: cc_link_miner.py MCP error sanitization ────

class TestLinkMinerErrorSanitization:
    """Link error messages in result['errors'] must use type(e).__name__."""

    def test_task_link_error_sanitized(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        # Find task link error append
        idx = src.index('result["errors"].append(f"Task link {task_id}')
        line_end = src.index("\n", idx)
        line = src[idx:line_end]
        assert "type(e).__name__" in line, f"Task link error not sanitized: {line}"

    def test_gap_link_error_sanitized(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        idx = src.index('result["errors"].append(f"Gap link {gap_id}')
        line_end = src.index("\n", idx)
        line = src[idx:line_end]
        assert "type(e).__name__" in line

    def test_rule_link_error_sanitized(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        idx = src.index('result["errors"].append(f"Rule link {rule_id}')
        line_end = src.index("\n", idx)
        line = src[idx:line_end]
        assert "type(e).__name__" in line

    def test_decision_link_error_sanitized(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        idx = src.index('result["errors"].append(f"Decision link {decision_id}')
        line_end = src.index("\n", idx)
        line = src[idx:line_end]
        assert "type(e).__name__" in line

    def test_validation_exc_info(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB validation failed for")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        for i in range(1, 6):
            assert f"BUG-406-LNK-00{i}" in src, f"Missing BUG-406-LNK-00{i}"


# ── BUG-407-PRJ-001..005: projects.py exc_info additions ─────────────

class TestProjectsExcInfo:
    """All TypeDB warning handlers in projects.py must have exc_info=True."""

    def test_insert_exc_info(self):
        src = (SRC / "governance/services/projects.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB insert project failed")

    def test_get_exc_info(self):
        src = (SRC / "governance/services/projects.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB get project failed")

    def test_list_exc_info(self):
        src = (SRC / "governance/services/projects.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB list projects failed")

    def test_delete_exc_info(self):
        src = (SRC / "governance/services/projects.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB delete project failed")

    def test_link_session_exc_info(self):
        src = (SRC / "governance/services/projects.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB link session to project failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/projects.py").read_text()
        for i in range(1, 6):
            assert f"BUG-407-PRJ-00{i}" in src, f"Missing BUG-407-PRJ-00{i}"


# ── BUG-407-RUL-001: rules.py _monitor exc_info ──────────────────────

class TestRulesMonitorExcInfo:
    def test_monitor_exc_info(self):
        src = (SRC / "governance/services/rules.py").read_text()
        _check_exc_info_on_warning(src, "Monitor event failed for rule")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/rules.py").read_text()
        assert "BUG-407-RUL-001" in src


# ── BUG-407-EVD-001..003: session_evidence.py exc_info additions ──────

class TestSessionEvidenceExcInfo:
    def test_validate_dir_exc_info(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        _check_exc_info_on_error(src, "Failed to validate output_dir")

    def test_create_dir_exc_info(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        _check_exc_info_on_error(src, "Failed to create evidence directory")

    def test_write_file_exc_info(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        _check_exc_info_on_error(src, "Failed to write evidence file")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        for i in range(1, 4):
            assert f"BUG-407-EVD-00{i}" in src, f"Missing BUG-407-EVD-00{i}"


# ── BUG-408-SES-001..003: sessions.py exc_info additions ─────────────

class TestSessionsExcInfo:
    def test_insert_exc_info(self):
        src = (SRC / "governance/services/sessions.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB session insert failed")

    def test_update_exc_info(self):
        src = (SRC / "governance/services/sessions.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB session update failed")

    def test_sync_exc_info(self):
        src = (SRC / "governance/services/sessions.py").read_text()
        _check_exc_info_on_warning(src, "Failed to sync session")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/sessions.py").read_text()
        for i in range(1, 4):
            assert f"BUG-408-SES-00{i}" in src, f"Missing BUG-408-SES-00{i}"


# ── BUG-408-SLC-001..003: sessions_lifecycle.py exc_info additions ────

class TestSessionsLifecycleExcInfo:
    def test_delete_exc_info(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB session delete failed")

    def test_auto_evidence_exc_info(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        _check_exc_info_on_warning(src, "Auto-evidence failed")

    def test_end_session_exc_info(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB session end failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        for i in range(1, 4):
            assert f"BUG-408-SLC-00{i}" in src, f"Missing BUG-408-SLC-00{i}"


# ── BUG-408-TSK-001..004: tasks.py exc_info additions ────────────────

class TestTasksExcInfo:
    def test_insert_exc_info(self):
        src = (SRC / "governance/services/tasks.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB task insert failed")

    def test_get_exc_info(self):
        src = (SRC / "governance/services/tasks.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB task get failed")

    def test_details_get_exc_info(self):
        src = (SRC / "governance/services/tasks.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB task details get failed")

    def test_details_update_exc_info(self):
        src = (SRC / "governance/services/tasks.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB task details update failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/tasks.py").read_text()
        for i in range(1, 5):
            assert f"BUG-408-TSK-00{i}" in src, f"Missing BUG-408-TSK-00{i}"


# ── BUG-408-TM-001..002: tasks_mutations.py exc_info additions ───────

class TestTasksMutationsWarningExcInfo:
    def test_update_warning_exc_info(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB task update failed")

    def test_delete_warning_exc_info(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        _check_exc_info_on_warning(src, "TypeDB task delete failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        assert "BUG-408-TM-001" in src
        assert "BUG-408-TM-002" in src


# ── BUG-409-RQ-001..002: rules_query.py log level + exc_info ─────────

class TestRulesQueryLogLevel:
    """TypeDB failure handlers must use WARNING (not DEBUG) with exc_info."""

    def test_rules_query_uses_warning(self):
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        idx = src.index("rules_query TypeDB failed")
        line_start = src.rindex("\n", 0, idx) + 1
        line_end = src.index("\n", idx)
        line = src[line_start:line_end]
        assert "logger.warning" in line, f"rules_query should use logger.warning: {line.strip()}"
        assert "exc_info=True" in line

    def test_rule_get_uses_warning(self):
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        idx = src.index("rule_get TypeDB failed")
        line_start = src.rindex("\n", 0, idx) + 1
        line_end = src.index("\n", idx)
        line = src[line_start:line_end]
        assert "logger.warning" in line, f"rule_get should use logger.warning: {line.strip()}"
        assert "exc_info=True" in line

    def test_no_inline_import_logging(self):
        """Should use module-level logger, not inline import logging."""
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        assert "import logging as _logging" not in src

    def test_bug_markers_present(self):
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        assert "BUG-409-RQ-001" in src
        assert "BUG-409-RQ-002" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch409Imports:
    def test_cc_link_miner_importable(self):
        import governance.services.cc_link_miner
        assert governance.services.cc_link_miner is not None

    def test_projects_importable(self):
        import governance.services.projects
        assert governance.services.projects is not None

    def test_rules_importable(self):
        import governance.services.rules
        assert governance.services.rules is not None

    def test_sessions_importable(self):
        import governance.services.sessions
        assert governance.services.sessions is not None

    def test_sessions_lifecycle_importable(self):
        import governance.services.sessions_lifecycle
        assert governance.services.sessions_lifecycle is not None

    def test_tasks_importable(self):
        import governance.services.tasks
        assert governance.services.tasks is not None

    def test_rules_query_importable(self):
        import governance.mcp_tools.rules_query
        assert governance.mcp_tools.rules_query is not None

    def test_session_evidence_importable(self):
        import governance.services.session_evidence
        assert governance.services.session_evidence is not None
