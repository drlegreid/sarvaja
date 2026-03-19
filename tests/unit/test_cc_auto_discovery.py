"""
Unit tests for CC Auto-Discovery startup handler.

Per GAP-SESSION-CC-AUTO-DISCOVERY: Tests for discover_cc_sessions()
in api_startup.py — auto-discovers CC projects and ingests sessions
on API startup.

Per P2-10: Discovery logic now lives in ingestion_scheduler.run_discovery_scan().
discover_cc_sessions() delegates to IngestionScheduler.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from governance.services.ingestion_scheduler import run_discovery_scan


class TestDiscoverCcSessions:
    """Tests for run_discovery_scan() — the core discovery logic.

    Per P2-10: discover_cc_sessions() now delegates to the scheduler,
    which calls run_discovery_scan(). These tests target the scan function directly.
    """

    @pytest.mark.asyncio
    async def test_startup_delegates_to_scheduler(self):
        """discover_cc_sessions() starts the ingestion scheduler."""
        from governance.api_startup import discover_cc_sessions

        mock_sched = MagicMock()
        with patch(
            "governance.services.ingestion_scheduler.get_scheduler",
            return_value=mock_sched,
        ):
            await discover_cc_sessions()
        mock_sched.start.assert_called_once()

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects", return_value=[])
    @patch("governance.services.ingestion_scheduler.detect_project_type", return_value="python")
    @patch("governance.services.ingestion_scheduler.create_project")
    @patch("governance.services.ingestion_scheduler.get_project", return_value=None)
    @patch("governance.services.ingestion_scheduler.ingest_all")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_creates_missing_projects(
        self, mock_discover, mock_ingest, mock_get, mock_create, mock_detect, mock_fs,
    ):
        """Creates project entities for discovered CC projects."""
        mock_discover.return_value = [
            {
                "project_id": "PROJ-SARVAJA-PLATFORM",
                "name": "Sarvaja Platform",
                "path": "/home/user/project",
                "cc_directory": "/home/user/.claude/projects/encoded",
                "session_count": 5,
            },
        ]
        mock_ingest.return_value = [{"session_id": "SESSION-2026-01-01-CC-TEST"}]

        result = run_discovery_scan()

        mock_create.assert_called_once_with(
            project_id="PROJ-SARVAJA-PLATFORM",
            name="Sarvaja Platform",
            path="/home/user/project",
            project_type="python",
        )
        assert result.projects_created == 1
        assert result.sessions_ingested == 1

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects", return_value=[])
    @patch("governance.services.ingestion_scheduler.ingest_all", return_value=[])
    @patch("governance.services.ingestion_scheduler.get_project")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_skips_existing_projects(self, mock_discover, mock_get, mock_ingest, mock_fs):
        """Does not re-create projects that already exist."""
        mock_discover.return_value = [
            {
                "project_id": "PROJ-SARVAJA-PLATFORM",
                "name": "Sarvaja Platform",
                "path": "/home/user/project",
                "cc_directory": "/tmp/cc-test",
                "session_count": 3,
            },
        ]
        mock_get.return_value = {"project_id": "PROJ-SARVAJA-PLATFORM"}

        with patch("governance.services.ingestion_scheduler.create_project") as mock_create:
            result = run_discovery_scan()
            mock_create.assert_not_called()

        assert result.projects_created == 0

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects", return_value=[])
    @patch("governance.services.ingestion_scheduler.get_project", return_value={"id": "exists"})
    @patch("governance.services.ingestion_scheduler.ingest_all")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_ingests_sessions_for_each_project(
        self, mock_discover, mock_ingest, mock_get, mock_fs,
    ):
        """Calls ingest_all for each discovered CC project."""
        mock_discover.return_value = [
            {
                "project_id": "PROJ-A",
                "name": "Project A",
                "path": "/a",
                "cc_directory": "/tmp/cc-a",
                "session_count": 2,
            },
            {
                "project_id": "PROJ-B",
                "name": "Project B",
                "path": "/b",
                "cc_directory": "/tmp/cc-b",
                "session_count": 3,
            },
        ]
        mock_ingest.return_value = [{"session_id": "s1"}]

        result = run_discovery_scan()

        assert mock_ingest.call_count == 2
        calls = mock_ingest.call_args_list
        assert calls[0].kwargs["directory"] == Path("/tmp/cc-a")
        assert calls[1].kwargs["directory"] == Path("/tmp/cc-b")
        assert result.sessions_ingested == 2

    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_handles_no_cc_projects(self, mock_discover):
        """Gracefully handles empty CC directory."""
        mock_discover.return_value = []
        result = run_discovery_scan()
        assert result.projects_created == 0
        assert result.sessions_ingested == 0

    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_handles_import_error(self, mock_discover):
        """Gracefully handles discovery failures."""
        mock_discover.side_effect = ImportError("no module")
        result = run_discovery_scan()
        assert len(result.errors) > 0

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects")
    @patch("governance.services.ingestion_scheduler.ingest_all", return_value=[])
    @patch("governance.services.ingestion_scheduler.get_project")
    @patch("governance.services.ingestion_scheduler.create_project")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_discovers_filesystem_projects(
        self, mock_discover, mock_create, mock_get, mock_ingest, mock_fs,
    ):
        """Also discovers filesystem projects (game projects etc.)."""
        mock_discover.return_value = [
            {
                "project_id": "PROJ-PLATFORM",
                "name": "Platform",
                "path": "/home/user/project",
                "cc_directory": "/tmp/cc-test",
                "session_count": 1,
            },
        ]
        mock_get.side_effect = [
            {"project_id": "PROJ-PLATFORM"},  # CC project exists
            None,  # FS project doesn't exist
        ]
        mock_fs.return_value = [
            {
                "project_id": "PROJ-GAME",
                "name": "Game",
                "path": "/home/user/game",
                "project_type": "godot",
            },
        ]

        result = run_discovery_scan()

        mock_create.assert_called_once_with(
            project_id="PROJ-GAME",
            name="Game",
            path="/home/user/game",
            project_type="godot",
        )
        assert result.projects_created == 1

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects", return_value=[])
    @patch("governance.services.ingestion_scheduler.get_project", return_value={"id": "exists"})
    @patch("governance.services.ingestion_scheduler.ingest_all")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_no_cc_directory_skips_ingestion(
        self, mock_discover, mock_ingest, mock_get, mock_fs,
    ):
        """Projects without cc_directory skip ingestion."""
        mock_discover.return_value = [
            {
                "project_id": "PROJ-TEST",
                "name": "Test",
                "path": "/test",
                "session_count": 0,
            },
        ]

        result = run_discovery_scan()
        mock_ingest.assert_not_called()


class TestApiStartupIntegration:
    """Tests for the startup hook wiring in api.py."""

    def test_discover_cc_sessions_importable(self):
        """discover_cc_sessions is importable from api_startup."""
        from governance.api_startup import discover_cc_sessions
        assert callable(discover_cc_sessions)

    def test_api_imports_discovery(self):
        """api.py imports the discovery handler."""
        from governance import api
        assert hasattr(api, '_discover_cc_sessions')
        assert callable(api._discover_cc_sessions)

    def test_startup_handler_registered(self):
        """auto_discover_cc_sessions is a registered startup handler."""
        from governance.api import app
        # FastAPI stores startup handlers in router.on_startup
        handler_names = [h.__name__ for h in app.router.on_startup]
        assert "auto_discover_cc_sessions" in handler_names
