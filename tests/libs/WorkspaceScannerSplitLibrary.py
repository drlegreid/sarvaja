"""
RF-004: Robot Framework Library for Workspace Scanner Split Tests.

Wraps tests/test_workspace_scanner_split.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Files under 400 lines.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class WorkspaceScannerSplitLibrary:
    """Robot Framework library for Workspace Scanner Split tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def scanner_module_exists(self) -> bool:
        """Check if workspace_scanner.py exists."""
        return (GOVERNANCE_DIR / "workspace_scanner.py").exists()

    def parsers_module_exists(self) -> bool:
        """Check if task_parsers.py exists."""
        return (GOVERNANCE_DIR / "task_parsers.py").exists()

    def get_file_line_count(self, filename: str) -> int:
        """Get line count for a file in governance directory."""
        filepath = GOVERNANCE_DIR / filename
        if not filepath.exists():
            return -1
        with open(filepath, "r") as f:
            return len(f.readlines())

    def file_under_limit(self, filename: str, limit: int = 400) -> Dict[str, Any]:
        """Check if file is under line limit."""
        lines = self.get_file_line_count(filename)
        return {
            "filename": filename,
            "lines": lines,
            "limit": limit,
            "under_limit": lines >= 0 and lines < limit
        }

    def import_parsed_task(self) -> bool:
        """Try to import ParsedTask from workspace_scanner."""
        try:
            from governance.workspace_scanner import ParsedTask
            return ParsedTask is not None
        except ImportError:
            return False

    def import_scan_workspace(self) -> bool:
        """Try to import scan_workspace."""
        try:
            from governance.workspace_scanner import scan_workspace
            return callable(scan_workspace)
        except ImportError:
            return False

    def import_capture_workspace_tasks(self) -> bool:
        """Try to import capture_workspace_tasks."""
        try:
            from governance.workspace_scanner import capture_workspace_tasks
            return callable(capture_workspace_tasks)
        except ImportError:
            return False

    def import_normalize_status(self) -> bool:
        """Try to import normalize_status from task_parsers."""
        try:
            from governance.task_parsers import normalize_status
            return callable(normalize_status)
        except ImportError:
            return False

    def test_normalize_status_done(self) -> Dict[str, bool]:
        """Test done status normalization."""
        try:
            from governance.task_parsers import normalize_status
            return {
                "DONE_works": normalize_status("DONE") == "DONE",
                "checkmark_works": normalize_status("✅") == "DONE",
                "checkmark_done_works": normalize_status("✅ DONE") == "DONE"
            }
        except ImportError:
            return {"error": True}

    def test_normalize_status_in_progress(self) -> Dict[str, bool]:
        """Test in progress status normalization."""
        try:
            from governance.task_parsers import normalize_status
            return {
                "IN_PROGRESS_works": normalize_status("IN_PROGRESS") == "IN_PROGRESS",
                "construction_works": normalize_status("🚧") == "IN_PROGRESS"
            }
        except ImportError:
            return {"error": True}

    def import_parse_markdown_table(self) -> bool:
        """Try to import parse_markdown_table."""
        try:
            from governance.task_parsers import parse_markdown_table
            return callable(parse_markdown_table)
        except ImportError:
            return False

    def test_parse_markdown_table_basic(self) -> Dict[str, Any]:
        """Test basic table parsing."""
        try:
            from governance.task_parsers import parse_markdown_table
            content = """
| ID | Name | Status |
|----|------|--------|
| T1 | Test | DONE |
| T2 | Two  | TODO |
"""
            rows = parse_markdown_table(content)
            return {
                "row_count": len(rows),
                "has_two_rows": len(rows) == 2,
                "first_id_correct": rows[0].get("id") == "T1" if rows else False,
                "first_name_correct": rows[0].get("name") == "Test" if rows else False,
                "second_id_correct": rows[1].get("id") == "T2" if len(rows) > 1 else False
            }
        except Exception as e:
            return {"error": str(e)}

    def import_extract_functions(self) -> Dict[str, bool]:
        """Check extract functions are exported."""
        results = {}
        try:
            from governance.task_parsers import extract_task_id
            results["extract_task_id"] = callable(extract_task_id)
        except ImportError:
            results["extract_task_id"] = False

        try:
            from governance.task_parsers import extract_gap_id
            results["extract_gap_id"] = callable(extract_gap_id)
        except ImportError:
            results["extract_gap_id"] = False

        try:
            from governance.task_parsers import extract_linked_rules
            results["extract_linked_rules"] = callable(extract_linked_rules)
        except ImportError:
            results["extract_linked_rules"] = False

        return results

    def verify_integration(self) -> Dict[str, bool]:
        """Verify scanner uses parsers module."""
        try:
            from governance.workspace_scanner import parse_todo_md
            from governance.task_parsers import normalize_status
            return {
                "parse_todo_md": callable(parse_todo_md),
                "normalize_status": callable(normalize_status)
            }
        except ImportError as e:
            return {"error": str(e)}
