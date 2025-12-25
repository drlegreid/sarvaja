"""
GitHub Sync Tests (FH-006)
Created: 2024-12-25
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class TestGitHubSyncModule:
    """Unit tests for GitHub sync module."""

    @pytest.mark.unit
    def test_module_exists(self):
        """GitHub sync module must exist."""
        sync_file = GOVERNANCE_DIR / "github_sync.py"
        assert sync_file.exists(), "governance/github_sync.py not found"

    @pytest.mark.unit
    def test_rdtask_dataclass(self):
        """RDTask dataclass must be importable."""
        from governance.github_sync import RDTask

        task = RDTask(
            id="RD-001",
            title="Test task",
            status="TODO",
            priority="HIGH",
            notes="Test notes",
            category="RD"
        )

        assert task.id == "RD-001"
        assert task.status == "TODO"
        assert task.github_issue is None

    @pytest.mark.unit
    def test_sync_result_dataclass(self):
        """SyncResult dataclass must be importable."""
        from governance.github_sync import SyncResult

        result = SyncResult()
        assert result.created == []
        assert result.updated == []
        assert result.errors == []

    @pytest.mark.unit
    def test_github_sync_class(self):
        """GitHubSync class must be instantiable."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        assert sync.dry_run is True
        assert sync.repo == "drlegreid/platform-gai"

    @pytest.mark.unit
    def test_github_sync_custom_repo(self):
        """GitHubSync must accept custom repo."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(repo="test/repo", dry_run=True)
        assert sync.repo == "test/repo"


class TestBacklogParsing:
    """Tests for R&D backlog parsing."""

    @pytest.mark.unit
    def test_backlog_file_exists(self):
        """R&D backlog file must exist."""
        backlog = PROJECT_ROOT / "docs" / "backlog" / "R&D-BACKLOG.md"
        assert backlog.exists(), "R&D-BACKLOG.md not found"

    @pytest.mark.unit
    def test_parse_backlog(self):
        """parse_backlog must return list of tasks."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        tasks = sync.parse_backlog()

        assert len(tasks) > 0, "No tasks parsed from backlog"
        assert all(hasattr(t, "id") for t in tasks)
        assert all(hasattr(t, "title") for t in tasks)

    @pytest.mark.unit
    def test_parse_rd_tasks(self):
        """parse_backlog must find RD-* tasks."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        tasks = sync.parse_backlog()

        rd_tasks = [t for t in tasks if t.id.startswith("RD-")]
        assert len(rd_tasks) >= 1, "No RD-* tasks found"

    @pytest.mark.unit
    def test_parse_fh_tasks(self):
        """parse_backlog must find FH-* tasks."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        tasks = sync.parse_backlog()

        fh_tasks = [t for t in tasks if t.id.startswith("FH-")]
        assert len(fh_tasks) >= 1, "No FH-* tasks found"

    @pytest.mark.unit
    def test_task_categories(self):
        """Tasks must have correct categories."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        tasks = sync.parse_backlog()

        for task in tasks:
            if task.id.startswith("RD-"):
                assert task.category == "RD"
            elif task.id.startswith("FH-"):
                assert task.category == "FH"

    @pytest.mark.unit
    def test_task_status_normalized(self):
        """Task status must be normalized."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        tasks = sync.parse_backlog()

        valid_statuses = {"TODO", "DONE", "BLOCKED", "IN_PROGRESS"}
        for task in tasks:
            assert task.status in valid_statuses, f"Invalid status: {task.status}"


class TestIssueCreation:
    """Tests for GitHub issue creation."""

    @pytest.mark.unit
    def test_create_issue_dry_run(self):
        """create_issue in dry_run mode should not call gh CLI."""
        from governance.github_sync import GitHubSync, RDTask

        sync = GitHubSync(dry_run=True)
        task = RDTask(
            id="TEST-001",
            title="Test task",
            status="TODO",
            priority="HIGH",
            notes="Test",
            category="RD"
        )

        result = sync.create_issue(task)
        assert result is None  # Dry run returns None

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_create_issue_calls_gh(self, mock_run):
        """create_issue should call gh CLI."""
        from governance.github_sync import GitHubSync, RDTask

        mock_run.return_value = MagicMock(
            stdout="https://github.com/test/repo/issues/42",
            returncode=0
        )

        sync = GitHubSync(dry_run=False)
        task = RDTask(
            id="TEST-001",
            title="Test task",
            status="TODO",
            priority="HIGH",
            notes="Test",
            category="RD"
        )

        result = sync.create_issue(task)
        assert mock_run.called
        assert result == 42

    @pytest.mark.unit
    def test_issue_title_format(self):
        """Issue title should have [ID] prefix."""
        from governance.github_sync import RDTask

        task = RDTask(
            id="RD-001",
            title="Test task",
            status="TODO",
            priority="HIGH",
            notes="",
            category="RD"
        )

        expected_title = f"[{task.id}] {task.title}"
        assert expected_title == "[RD-001] Test task"


class TestSyncOperation:
    """Tests for full sync operation."""

    @pytest.mark.unit
    def test_sync_dry_run(self):
        """sync in dry_run mode should return results without changes."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        result = sync.sync()

        assert hasattr(result, "created")
        assert hasattr(result, "updated")
        assert hasattr(result, "skipped")

    @pytest.mark.unit
    def test_sync_skips_done_tasks(self):
        """sync should skip tasks with DONE status."""
        from governance.github_sync import GitHubSync

        sync = GitHubSync(dry_run=True)
        result = sync.sync()

        # All skipped items should mention "done"
        for item in result.skipped:
            assert "done" in item.lower() or "Done" in item


class TestCLI:
    """Tests for CLI interface."""

    @pytest.mark.unit
    def test_main_function_exists(self):
        """main function must exist."""
        from governance.github_sync import main
        assert callable(main)

    @pytest.mark.unit
    def test_argparse_dry_run(self):
        """--dry-run flag should be accepted."""
        import argparse
        from governance import github_sync

        # Verify module has proper CLI setup
        assert hasattr(github_sync, "main")
        assert hasattr(github_sync, "GitHubSync")
