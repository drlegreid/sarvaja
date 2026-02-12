"""
Unit tests for GitHub Sync for R&D Issues.

Per DOC-SIZE-01-v1: Tests for github_sync.py module.
Tests: RDTask, SyncResult, GitHubSync.parse_backlog, STATUS_MAP.
"""

from governance.github_sync import RDTask, SyncResult, GitHubSync


class TestRDTask:
    def test_defaults(self):
        t = RDTask(id="RD-001", title="Test", status="TODO",
                   priority="HIGH", notes="", category="RD")
        assert t.github_issue is None

    def test_with_issue(self):
        t = RDTask(id="RD-001", title="Test", status="TODO",
                   priority="HIGH", notes="", category="RD", github_issue=42)
        assert t.github_issue == 42


class TestSyncResult:
    def test_defaults(self):
        r = SyncResult()
        assert r.created == []
        assert r.updated == []
        assert r.skipped == []
        assert r.errors == []


class TestGitHubSync:
    def test_init_defaults(self):
        s = GitHubSync()
        assert s.repo == "drlegreid/platform-gai"
        assert s.dry_run is False

    def test_init_custom(self):
        s = GitHubSync(repo="custom/repo", dry_run=True)
        assert s.repo == "custom/repo"
        assert s.dry_run is True

    def test_status_map(self):
        assert GitHubSync.STATUS_MAP["📋 TODO"] == "TODO"
        assert GitHubSync.STATUS_MAP["✅ DONE"] == "DONE"
        assert len(GitHubSync.STATUS_MAP) == 4

    def test_parse_backlog_missing_file(self, tmp_path):
        s = GitHubSync()
        s.BACKLOG_PATH = tmp_path / "nonexistent.md"
        import pytest
        with pytest.raises(FileNotFoundError):
            s.parse_backlog()

    def test_parse_backlog_with_table(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text(
            "| ID | Title | Status | Priority | Notes |\n"
            "|----|-------|--------|----------|-------|\n"
            "| RD-001 | Fix Bug | 📋 TODO | HIGH | |\n"
            "| RD-002 | Add Feature | ✅ DONE | MEDIUM | done |\n"
        )
        s = GitHubSync()
        s.BACKLOG_PATH = backlog
        tasks = s.parse_backlog()
        assert len(tasks) == 2
        assert tasks[0].id == "RD-001"
        assert tasks[0].status == "TODO"
        assert tasks[1].status == "DONE"
        assert tasks[0].category == "RD"

    def test_parse_skips_headers(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text(
            "| ID | Title | Status | Priority | Notes |\n"
            "|-----|-------|--------|----------|-------|\n"
        )
        s = GitHubSync()
        s.BACKLOG_PATH = backlog
        tasks = s.parse_backlog()
        assert len(tasks) == 0

    def test_category_detection(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text(
            "| ID | Title | Status | Priority | Notes |\n"
            "|----|-------|--------|----------|-------|\n"
            "| FH-001 | Factor Hub | TODO | HIGH | |\n"
            "| TEST-001 | Tests | TODO | LOW | |\n"
            "| ORCH-001 | Orchestrator | TODO | HIGH | |\n"
        )
        s = GitHubSync()
        s.BACKLOG_PATH = backlog
        tasks = s.parse_backlog()
        assert tasks[0].category == "FH"
        assert tasks[1].category == "TEST"
        assert tasks[2].category == "ORCH"
