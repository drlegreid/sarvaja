"""Batch 219 — Workspace scanner + evidence defense tests.

Validates fixes for:
- BUG-219-SCAN-001: sync_tasks_to_typedb unchecked return value
- Workspace scanner defense tests
- Evidence scanner defense tests
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
import re

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-219-SCAN-001: sync return value check ─────────────────────────

class TestSyncReturnValueCheck:
    """sync_tasks_to_typedb must check update_task_status return value."""

    def test_update_checks_return_value(self):
        """Source must use return value of update_task_status."""
        src = (SRC / "governance/workspace_scanner.py").read_text()
        # Should assign return value, not just call and ignore
        assert "success = client.update_task_status" in src or \
               "if client.update_task_status" in src, \
            "update_task_status return value not checked"


# ── Workspace scanner defense ──────────────────────────────────────────

class TestWorkspaceScannerDefense:
    """Defense tests for workspace_scanner module."""

    def test_scan_workspace_callable(self):
        from governance.workspace_scanner import scan_workspace
        assert callable(scan_workspace)

    def test_normalize_status_callable(self):
        from governance.workspace_scanner import normalize_status
        assert callable(normalize_status)

    def test_normalize_status_done(self):
        """Per TASK-LIFE-01-v1: 'DONE' maps to CLOSED (case-sensitive map)."""
        from governance.workspace_scanner import normalize_status
        assert normalize_status("DONE") == "CLOSED"
        assert normalize_status("COMPLETED") == "CLOSED"

    def test_normalize_status_in_progress(self):
        from governance.workspace_scanner import normalize_status
        result = normalize_status("in_progress")
        assert result == "IN_PROGRESS"

    def test_normalize_status_todo(self):
        """Per TASK-LIFE-01-v1: 'TODO' maps to OPEN."""
        from governance.workspace_scanner import normalize_status
        assert normalize_status("TODO") == "OPEN"

    def test_extract_task_id_callable(self):
        from governance.workspace_scanner import extract_task_id
        assert callable(extract_task_id)

    def test_extract_task_id_valid(self):
        from governance.workspace_scanner import extract_task_id
        row = {"id": "GAP-UI-001"}
        result = extract_task_id(row)
        assert result == "GAP-UI-001"

    def test_extract_task_id_from_text(self):
        from governance.workspace_scanner import extract_task_id
        row = {"task": "UI-001: Fix navigation"}
        result = extract_task_id(row)
        assert result is not None and "001" in result

    def test_extract_task_id_no_match(self):
        from governance.workspace_scanner import extract_task_id
        row = {"task": "some random text with no ids"}
        result = extract_task_id(row)
        assert result is None

    def test_capture_workspace_tasks_callable(self):
        from governance.workspace_scanner import capture_workspace_tasks
        assert callable(capture_workspace_tasks)

    def test_parsed_task_dataclass(self):
        from governance.workspace_scanner import ParsedTask
        task = ParsedTask(
            task_id="TEST-001", name="Test task",
            status="TODO", phase=None,
        )
        assert task.task_id == "TEST-001"
        assert task.status == "TODO"


# ── Workspace registry defense ─────────────────────────────────────────

class TestWorkspaceRegistryDefense:
    """Defense tests for workspace_registry module."""

    def test_detect_project_type_callable(self):
        from governance.services.workspace_registry import detect_project_type
        assert callable(detect_project_type)

    def test_detect_project_type_nonexistent(self):
        from governance.services.workspace_registry import detect_project_type
        result = detect_project_type("/nonexistent/path/xyz")
        assert result == "generic"

    def test_register_workspace_type_callable(self):
        from governance.services.workspace_registry import register_workspace_type
        assert callable(register_workspace_type)


# ── CC session scanner defense ──────────────────────────────────────────

class TestCCSessionScannerDefense:
    """Defense tests for cc_session_scanner module."""

    def test_discover_cc_projects_callable(self):
        from governance.services.cc_session_scanner import discover_cc_projects
        assert callable(discover_cc_projects)

    def test_discover_filesystem_projects_callable(self):
        from governance.services.cc_session_scanner import discover_filesystem_projects
        assert callable(discover_filesystem_projects)

    def test_find_jsonl_for_session_callable(self):
        from governance.services.cc_session_scanner import find_jsonl_for_session
        assert callable(find_jsonl_for_session)


# ── Evidence scanner defense ────────────────────────────────────────────

class TestEvidenceScannerDefense:
    """Defense tests for evidence scanner modules."""

    def test_linking_module_importable(self):
        import governance.evidence_scanner.linking
        assert governance.evidence_scanner.linking is not None

    def test_backfill_module_importable(self):
        import governance.evidence_scanner.backfill
        assert governance.evidence_scanner.backfill is not None

    def test_extractors_module_importable(self):
        import governance.evidence_scanner.extractors
        assert governance.evidence_scanner.extractors is not None

    def test_apply_evidence_session_links_callable(self):
        from governance.evidence_scanner.linking import apply_evidence_session_links
        assert callable(apply_evidence_session_links)


# ── Rule linker scan defense ────────────────────────────────────────────

class TestRuleLinkerScanDefense:
    """Defense tests for rule_linker_scan module."""

    def test_module_importable(self):
        import governance.rule_linker_scan
        assert governance.rule_linker_scan is not None
