"""
Tests for merge conflict checker (MULTI-007).

Per MULTI-007: Merge conflict detection for multi-agent workflows.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add checkers to path
_checkers_dir = Path(__file__).parent.parent.parent / ".claude" / "hooks" / "checkers"
if str(_checkers_dir) not in sys.path:
    sys.path.insert(0, str(_checkers_dir))


@pytest.mark.unit
class TestConflictChecker:
    """Unit tests for conflict_checker module."""

    def test_module_imports(self):
        """Verify the module can be imported."""
        from conflict_checker import (
            check_merge_conflicts,
            get_conflict_summary,
            scan_for_conflict_markers
        )
        assert callable(check_merge_conflicts)
        assert callable(get_conflict_summary)
        assert callable(scan_for_conflict_markers)

    def test_check_merge_conflicts_returns_dict(self):
        """Verify check_merge_conflicts returns expected structure."""
        from conflict_checker import check_merge_conflicts

        result = check_merge_conflicts()

        assert isinstance(result, dict)
        assert "has_conflicts" in result
        assert "conflicts" in result
        assert isinstance(result["has_conflicts"], bool)
        assert isinstance(result["conflicts"], list)

    def test_get_conflict_summary_returns_dict(self):
        """Verify get_conflict_summary returns expected structure."""
        from conflict_checker import get_conflict_summary

        result = get_conflict_summary()

        assert isinstance(result, dict)
        assert "has_conflicts" in result
        assert "conflict_count" in result
        assert "conflicts" in result
        assert "marker_files" in result
        assert "merge_state" in result
        assert "alerts" in result
        assert "status" in result

    def test_no_conflicts_returns_ok_status(self):
        """Verify clean repo returns OK status."""
        from conflict_checker import get_conflict_summary

        result = get_conflict_summary()

        # In clean repo, should be OK (or WARNING if in merge state)
        assert result["status"] in ["OK", "WARNING"]

    @patch("conflict_checker.run_git_command")
    def test_detects_unmerged_files(self, mock_git):
        """Verify UU status is detected as conflict."""
        from conflict_checker import check_merge_conflicts

        # Simulate git status with unmerged file
        mock_git.return_value = (0, "UU conflicted_file.py\n", "")

        result = check_merge_conflicts()

        assert result["has_conflicts"] is True
        assert result["conflict_count"] == 1
        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["file"] == "conflicted_file.py"
        assert result["conflicts"][0]["status"] == "UU"
        assert result["conflicts"][0]["status_meaning"] == "both modified"

    @patch("conflict_checker.run_git_command")
    def test_detects_both_added(self, mock_git):
        """Verify AA status (both added) is detected."""
        from conflict_checker import check_merge_conflicts

        mock_git.return_value = (0, "AA new_file.py\n", "")

        result = check_merge_conflicts()

        assert result["has_conflicts"] is True
        assert result["conflicts"][0]["status"] == "AA"
        assert result["conflicts"][0]["status_meaning"] == "both added"

    @patch("conflict_checker.run_git_command")
    def test_ignores_normal_modifications(self, mock_git):
        """Verify normal M (modified) status is not flagged as conflict."""
        from conflict_checker import check_merge_conflicts

        mock_git.return_value = (0, " M modified_file.py\nM  staged_file.py\n", "")

        result = check_merge_conflicts()

        assert result["has_conflicts"] is False
        assert result["conflict_count"] == 0

    @patch("conflict_checker.run_git_command")
    def test_handles_git_error(self, mock_git):
        """Verify graceful handling of git errors."""
        from conflict_checker import check_merge_conflicts

        mock_git.return_value = (-1, "", "fatal: not a git repository")

        result = check_merge_conflicts()

        assert result["has_conflicts"] is False
        assert "error" in result

    def test_merge_state_detection(self):
        """Verify merge state detection works."""
        from conflict_checker import _check_merge_state

        state = _check_merge_state()

        assert isinstance(state, dict)
        assert "in_merge" in state
        assert "in_rebase" in state
        assert "in_cherry_pick" in state
        assert "in_revert" in state
        assert "in_conflicted_state" in state


@pytest.mark.unit
class TestConflictCheckerAPI:
    """Tests for conflict checker API integration."""

    def test_api_endpoint_exists(self):
        """Verify the API endpoint is registered."""
        from governance.routes.agents.observability import router

        routes = [r.path for r in router.routes]
        assert "/agents/status/conflicts" in routes

    def test_summary_includes_conflicts(self):
        """Verify summary endpoint includes conflict info when available."""
        import sys
        from pathlib import Path

        # Ensure checkers path is available
        _checkers_dir = (
            Path(__file__).parent.parent.parent / ".claude" / "hooks" / "checkers"
        )
        if str(_checkers_dir) not in sys.path:
            sys.path.insert(0, str(_checkers_dir))

        # Re-import to pick up the path
        import importlib
        import governance.routes.agents.observability as obs_module

        importlib.reload(obs_module)

        # Verify CONFLICT_CHECKER_AVAILABLE is True after reload
        assert obs_module.CONFLICT_CHECKER_AVAILABLE is True
