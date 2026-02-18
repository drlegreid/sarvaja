"""
Unit tests for CC Auto-Discovery startup handler.

Per GAP-SESSION-CC-AUTO-DISCOVERY: Tests for discover_cc_sessions()
in api_startup.py — auto-discovers CC projects and ingests sessions
on API startup.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path


class TestDiscoverCcSessions:
    """Tests for discover_cc_sessions() startup handler."""

    @pytest.mark.asyncio
    async def test_runs_in_background_thread(self):
        """Auto-discovery runs in thread pool to avoid blocking startup."""
        import asyncio
        from governance.api_startup import discover_cc_sessions

        mock_loop = MagicMock()
        # Production code uses get_running_loop() (not get_event_loop)
        with patch("asyncio.get_running_loop", return_value=mock_loop):
            await discover_cc_sessions()

        mock_loop.run_in_executor.assert_called_once()
        # First arg is ThreadPoolExecutor, second is the callable
        args = mock_loop.run_in_executor.call_args
        assert args[0][0] is not None  # ThreadPoolExecutor
        assert callable(args[0][1])  # _discover_and_ingest function

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    @patch("governance.services.cc_session_ingestion.ingest_all")
    @patch("governance.services.projects.get_project")
    @patch("governance.services.projects.create_project")
    @patch("governance.services.workspace_registry.detect_project_type")
    def test_creates_missing_projects(
        self, mock_detect, mock_create, mock_get, mock_ingest, mock_discover,
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
        mock_get.return_value = None  # Project doesn't exist
        mock_detect.return_value = "python"
        mock_create.return_value = {"project_id": "PROJ-SARVAJA-PLATFORM"}
        mock_ingest.return_value = [{"session_id": "SESSION-2026-01-01-CC-TEST"}]

        # Call the inner function directly (bypass thread pool)
        from governance.api_startup import discover_cc_sessions
        import types

        # Extract _discover_and_ingest from closure
        inner = discover_cc_sessions.__code__.co_consts
        # Simpler: just test the logic by importing and calling with mocks
        with patch(
            "governance.services.cc_session_scanner.discover_filesystem_projects",
            return_value=[],
        ):
            # Execute the inner function by triggering it
            from governance.api_startup import discover_cc_sessions as fn
            import asyncio

            # Patch asyncio to run synchronously
            def sync_executor(executor, func):
                func()

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = sync_executor
                asyncio.get_event_loop = mock_loop
                loop = asyncio.new_event_loop()
                loop.run_until_complete(fn())
                loop.close()

        mock_create.assert_called_once_with(
            project_id="PROJ-SARVAJA-PLATFORM",
            name="Sarvaja Platform",
            path="/home/user/project",
            project_type="python",
        )

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    @patch("governance.services.cc_session_ingestion.ingest_all")
    @patch("governance.services.projects.get_project")
    def test_skips_existing_projects(self, mock_get, mock_ingest, mock_discover):
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
        mock_get.return_value = {"project_id": "PROJ-SARVAJA-PLATFORM"}  # Exists
        mock_ingest.return_value = []

        with patch(
            "governance.services.projects.create_project"
        ) as mock_create, patch(
            "governance.services.cc_session_scanner.discover_filesystem_projects",
            return_value=[],
        ):
            import asyncio

            def sync_executor(executor, func):
                func()

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = sync_executor
                from governance.api_startup import discover_cc_sessions
                loop = asyncio.new_event_loop()
                loop.run_until_complete(discover_cc_sessions())
                loop.close()

            mock_create.assert_not_called()

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    @patch("governance.services.cc_session_ingestion.ingest_all")
    @patch("governance.services.projects.get_project")
    @patch("governance.services.projects.create_project")
    def test_ingests_sessions_for_each_project(
        self, mock_create, mock_get, mock_ingest, mock_discover,
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
        mock_get.return_value = {"project_id": "exists"}  # Both exist
        mock_ingest.return_value = [{"session_id": "s1"}]

        with patch(
            "governance.services.cc_session_scanner.discover_filesystem_projects",
            return_value=[],
        ):
            import asyncio

            def sync_executor(executor, func):
                func()

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = sync_executor
                from governance.api_startup import discover_cc_sessions
                loop = asyncio.new_event_loop()
                loop.run_until_complete(discover_cc_sessions())
                loop.close()

        assert mock_ingest.call_count == 2
        # Check directories passed
        calls = mock_ingest.call_args_list
        assert calls[0].kwargs["directory"] == Path("/tmp/cc-a")
        assert calls[1].kwargs["directory"] == Path("/tmp/cc-b")

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    def test_handles_no_cc_projects(self, mock_discover):
        """Gracefully handles empty CC directory."""
        mock_discover.return_value = []

        import asyncio

        def sync_executor(executor, func):
            func()

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = sync_executor
            from governance.api_startup import discover_cc_sessions
            loop = asyncio.new_event_loop()
            loop.run_until_complete(discover_cc_sessions())
            loop.close()
        # No exception raised

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    def test_handles_import_error(self, mock_discover):
        """Gracefully handles missing dependencies."""
        mock_discover.side_effect = ImportError("no module")

        import asyncio

        def sync_executor(executor, func):
            func()

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = sync_executor
            from governance.api_startup import discover_cc_sessions
            loop = asyncio.new_event_loop()
            loop.run_until_complete(discover_cc_sessions())
            loop.close()
        # No exception raised — caught inside handler

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    @patch("governance.services.cc_session_ingestion.ingest_all")
    @patch("governance.services.projects.get_project")
    @patch("governance.services.projects.create_project")
    def test_discovers_filesystem_projects(
        self, mock_create, mock_get, mock_ingest, mock_discover,
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
        mock_ingest.return_value = []
        mock_create.return_value = {"project_id": "PROJ-GAME"}

        with patch(
            "governance.services.cc_session_scanner.discover_filesystem_projects",
            return_value=[
                {
                    "project_id": "PROJ-GAME",
                    "name": "Game",
                    "path": "/home/user/game",
                    "project_type": "godot",
                },
            ],
        ):
            import asyncio

            def sync_executor(executor, func):
                func()

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = sync_executor
                from governance.api_startup import discover_cc_sessions
                loop = asyncio.new_event_loop()
                loop.run_until_complete(discover_cc_sessions())
                loop.close()

        # FS project should be created
        mock_create.assert_called_once_with(
            project_id="PROJ-GAME",
            name="Game",
            path="/home/user/game",
            project_type="godot",
        )

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    @patch("governance.services.cc_session_ingestion.ingest_all")
    @patch("governance.services.projects.get_project")
    @patch("governance.services.projects.create_project")
    def test_no_cc_directory_skips_ingestion(
        self, mock_create, mock_get, mock_ingest, mock_discover,
    ):
        """Projects without cc_directory skip ingestion."""
        mock_discover.return_value = [
            {
                "project_id": "PROJ-TEST",
                "name": "Test",
                "path": "/test",
                # No cc_directory
                "session_count": 0,
            },
        ]
        mock_get.return_value = {"project_id": "PROJ-TEST"}

        with patch(
            "governance.services.cc_session_scanner.discover_filesystem_projects",
            return_value=[],
        ):
            import asyncio

            def sync_executor(executor, func):
                func()

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = sync_executor
                from governance.api_startup import discover_cc_sessions
                loop = asyncio.new_event_loop()
                loop.run_until_complete(discover_cc_sessions())
                loop.close()

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
