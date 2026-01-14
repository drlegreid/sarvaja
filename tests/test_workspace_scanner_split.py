"""
TDD Tests for workspace_scanner.py split.

Per GAP-FILE-026: workspace_scanner.py needs to go from 409 to <400 lines.
Per DOC-SIZE-01-v1: Files must stay under 400 lines.

Tests written BEFORE implementation (TDD).

Created: 2026-01-14
"""

import pytest
from pathlib import Path


# Project paths
GOVERNANCE_DIR = Path(__file__).parent.parent / "governance"


class TestWorkspaceScannerSplit:
    """Test workspace scanner module structure after split."""

    def test_scanner_module_exists(self):
        """Verify workspace_scanner.py exists."""
        scanner_file = GOVERNANCE_DIR / "workspace_scanner.py"
        assert scanner_file.exists(), "workspace_scanner.py must exist"

    def test_parsers_module_exists(self):
        """Verify task_parsers.py extraction exists."""
        parsers_file = GOVERNANCE_DIR / "task_parsers.py"
        assert parsers_file.exists(), "task_parsers.py should be extracted"

    def test_scanner_under_400_lines(self):
        """Verify workspace_scanner.py is under 400 lines per DOC-SIZE-01-v1."""
        scanner_file = GOVERNANCE_DIR / "workspace_scanner.py"
        with open(scanner_file, "r") as f:
            lines = len(f.readlines())
        assert lines < 400, f"workspace_scanner.py has {lines} lines, should be <400"


class TestBackwardCompatibility:
    """Test backward compatibility after split."""

    def test_import_parsed_task(self):
        """Verify ParsedTask can still be imported from workspace_scanner."""
        from governance.workspace_scanner import ParsedTask
        assert ParsedTask is not None

    def test_import_scan_workspace(self):
        """Verify scan_workspace can still be imported."""
        from governance.workspace_scanner import scan_workspace
        assert callable(scan_workspace)

    def test_import_capture_workspace_tasks(self):
        """Verify capture_workspace_tasks can still be imported."""
        from governance.workspace_scanner import capture_workspace_tasks
        assert callable(capture_workspace_tasks)


class TestParsersModule:
    """Test the extracted parsers module."""

    def test_normalize_status_exported(self):
        """Verify normalize_status is exported."""
        from governance.task_parsers import normalize_status
        assert callable(normalize_status)

    def test_normalize_status_done(self):
        """Test done status normalization."""
        from governance.task_parsers import normalize_status
        assert normalize_status("DONE") == "DONE"
        assert normalize_status("✅") == "DONE"
        assert normalize_status("✅ DONE") == "DONE"

    def test_normalize_status_in_progress(self):
        """Test in progress status normalization."""
        from governance.task_parsers import normalize_status
        assert normalize_status("IN_PROGRESS") == "IN_PROGRESS"
        assert normalize_status("🚧") == "IN_PROGRESS"

    def test_parse_markdown_table_exported(self):
        """Verify parse_markdown_table is exported."""
        from governance.task_parsers import parse_markdown_table
        assert callable(parse_markdown_table)

    def test_parse_markdown_table_basic(self):
        """Test basic table parsing."""
        from governance.task_parsers import parse_markdown_table

        content = """
| ID | Name | Status |
|----|------|--------|
| T1 | Test | DONE |
| T2 | Two  | TODO |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 2
        assert rows[0]["id"] == "T1"
        assert rows[0]["name"] == "Test"
        assert rows[1]["id"] == "T2"

    def test_extract_task_id_exported(self):
        """Verify extract_task_id is exported."""
        from governance.task_parsers import extract_task_id
        assert callable(extract_task_id)

    def test_extract_gap_id_exported(self):
        """Verify extract_gap_id is exported."""
        from governance.task_parsers import extract_gap_id
        assert callable(extract_gap_id)

    def test_extract_linked_rules_exported(self):
        """Verify extract_linked_rules is exported."""
        from governance.task_parsers import extract_linked_rules
        assert callable(extract_linked_rules)


class TestIntegration:
    """Integration tests for split modules."""

    def test_scanner_uses_parsers_module(self):
        """Verify scanner uses the extracted parsers."""
        # Just verify both modules exist and can work together
        from governance.workspace_scanner import parse_todo_md
        from governance.task_parsers import normalize_status
        assert callable(parse_todo_md)
        assert callable(normalize_status)
