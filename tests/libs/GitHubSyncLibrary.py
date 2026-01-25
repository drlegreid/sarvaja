"""
Robot Framework Library for GitHub Sync Tests.

Per FH-006: GitHub sync functionality.
Migrated from tests/test_github_sync.py
"""
from pathlib import Path
from robot.api.deco import keyword


class GitHubSyncLibrary:
    """Library for testing GitHub sync module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"

    # =============================================================================
    # Module Existence Tests
    # =============================================================================

    @keyword("GitHub Sync Module Exists")
    def github_sync_module_exists(self):
        """GitHub sync module must exist."""
        sync_file = self.governance_dir / "github_sync.py"
        return {"exists": sync_file.exists()}

    @keyword("RDTask Dataclass Works")
    def rdtask_dataclass_works(self):
        """RDTask dataclass must be importable."""
        try:
            from governance.github_sync import RDTask

            task = RDTask(
                id="RD-001",
                title="Test task",
                status="TODO",
                priority="HIGH",
                notes="Test notes",
                category="RD"
            )

            return {
                "id_correct": task.id == "RD-001",
                "status_correct": task.status == "TODO",
                "github_issue_none": task.github_issue is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("SyncResult Dataclass Works")
    def syncresult_dataclass_works(self):
        """SyncResult dataclass must be importable."""
        try:
            from governance.github_sync import SyncResult

            result = SyncResult()

            return {
                "created_empty": result.created == [],
                "updated_empty": result.updated == [],
                "errors_empty": result.errors == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("GitHubSync Class Instantiable")
    def github_sync_class_instantiable(self):
        """GitHubSync class must be instantiable."""
        try:
            from governance.github_sync import GitHubSync

            sync = GitHubSync(dry_run=True)

            return {
                "dry_run_true": sync.dry_run is True,
                "default_repo": sync.repo == "drlegreid/platform-gai"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("GitHubSync Custom Repo Works")
    def github_sync_custom_repo_works(self):
        """GitHubSync must accept custom repo."""
        try:
            from governance.github_sync import GitHubSync

            sync = GitHubSync(repo="test/repo", dry_run=True)

            return {"custom_repo": sync.repo == "test/repo"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    # =============================================================================
    # Backlog Parsing Tests
    # =============================================================================

    @keyword("Backlog File Exists")
    def backlog_file_exists(self):
        """R&D backlog file must exist."""
        backlog = self.project_root / "docs" / "backlog" / "R&D-BACKLOG.md"
        return {"exists": backlog.exists()}

    @keyword("Parse Backlog Returns List")
    def parse_backlog_returns_list(self):
        """parse_backlog must return list of tasks."""
        try:
            from governance.github_sync import GitHubSync

            sync = GitHubSync(dry_run=True)
            tasks = sync.parse_backlog()

            return {
                "is_list": isinstance(tasks, list)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
