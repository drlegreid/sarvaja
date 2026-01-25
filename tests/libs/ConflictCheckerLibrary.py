"""
RF-004: Robot Framework Library for Conflict Checker.

Wraps .claude/hooks/checkers/conflict_checker.py for Robot Framework tests.
Per MULTI-007: Merge conflict detection for multi-agent workflows.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHECKERS_DIR = PROJECT_ROOT / ".claude" / "hooks" / "checkers"
sys.path.insert(0, str(CHECKERS_DIR))
sys.path.insert(0, str(PROJECT_ROOT))


class ConflictCheckerLibrary:
    """Robot Framework library for Conflict Checker functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def check_merge_conflicts(self) -> Dict[str, Any]:
        """Run check_merge_conflicts and return result."""
        from conflict_checker import check_merge_conflicts
        return check_merge_conflicts()

    def get_conflict_summary(self) -> Dict[str, Any]:
        """Run get_conflict_summary and return result."""
        from conflict_checker import get_conflict_summary
        return get_conflict_summary()

    def check_merge_state(self) -> Dict[str, Any]:
        """Run _check_merge_state and return result."""
        from conflict_checker import _check_merge_state
        return _check_merge_state()

    def scan_for_conflict_markers(self) -> Dict[str, Any]:
        """Run scan_for_conflict_markers and return result."""
        from conflict_checker import scan_for_conflict_markers
        return scan_for_conflict_markers()

    def check_merge_conflicts_with_mock(self, mock_output: str) -> Dict[str, Any]:
        """Run check_merge_conflicts with mocked git output."""
        from conflict_checker import check_merge_conflicts

        with patch("conflict_checker.run_git_command") as mock_git:
            mock_git.return_value = (0, mock_output, "")
            return check_merge_conflicts()

    def check_merge_conflicts_with_error(self, error_msg: str) -> Dict[str, Any]:
        """Run check_merge_conflicts with mocked git error."""
        from conflict_checker import check_merge_conflicts

        with patch("conflict_checker.run_git_command") as mock_git:
            mock_git.return_value = (-1, "", error_msg)
            return check_merge_conflicts()

    def verify_module_imports(self) -> bool:
        """Verify all required functions can be imported."""
        try:
            from conflict_checker import (
                check_merge_conflicts,
                get_conflict_summary,
                scan_for_conflict_markers
            )
            return (
                callable(check_merge_conflicts) and
                callable(get_conflict_summary) and
                callable(scan_for_conflict_markers)
            )
        except ImportError:
            return False

    def verify_api_endpoint_exists(self) -> bool:
        """Verify the API endpoint is registered."""
        from governance.routes.agents.observability import router
        routes = [r.path for r in router.routes]
        return "/agents/status/conflicts" in routes
