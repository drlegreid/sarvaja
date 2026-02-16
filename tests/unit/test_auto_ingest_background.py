"""TDD Tests for P3 fix: Auto-ingest runs in background thread.

Validates that _auto_ingest_cc_sessions is called via daemon thread
in _load_projects, not blocking the startup path.
"""
import threading
from unittest.mock import patch, MagicMock

import pytest


class TestAutoIngestBackground:
    """Auto-ingest runs in background, not blocking startup."""

    @patch("governance.services.cc_session_scanner.discover_cc_projects")
    @patch("governance.services.cc_session_scanner.discover_filesystem_projects")
    def test_auto_ingest_spawns_daemon_thread(self, mock_fs, mock_cc):
        """_load_projects spawns daemon thread for auto-ingest."""
        mock_fs.return_value = []
        mock_cc.return_value = [
            {
                "project_id": "PROJ-TEST",
                "name": "Test",
                "path": "/tmp/test",
                "cc_directory": "/tmp/cc",
                "session_count": 1,
            },
        ]

        spawned_threads = []
        original_thread_init = threading.Thread.__init__

        def track_thread(self, *args, **kwargs):
            original_thread_init(self, *args, **kwargs)
            if kwargs.get("daemon"):
                spawned_threads.append(self)

        from agent.governance_ui.dashboard_data_loader import _load_projects

        state = MagicMock()
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": [
            {"project_id": "PROJ-TEST", "name": "Test", "path": "/tmp/test"},
        ]}
        mock_client.get.return_value = mock_resp

        with patch.object(threading.Thread, "__init__", track_thread):
            with patch.object(threading.Thread, "start"):
                _load_projects(state, mock_client, "http://localhost:8082")

        # At least one daemon thread spawned for auto-ingest
        assert len(spawned_threads) >= 1

    def test_auto_ingest_function_handles_missing_cc_dir(self):
        """_auto_ingest_cc_sessions returns early if no cc_directory."""
        from agent.governance_ui.dashboard_data_loader import _auto_ingest_cc_sessions

        # Should not raise, just return
        _auto_ingest_cc_sessions({"project_id": "PROJ-X"})

    @patch("governance.services.cc_session_ingestion.ingest_all")
    def test_auto_ingest_function_calls_ingest_all(self, mock_ingest):
        """_auto_ingest_cc_sessions calls ingest_all with correct params."""
        mock_ingest.return_value = ["session1"]

        from agent.governance_ui.dashboard_data_loader import _auto_ingest_cc_sessions

        _auto_ingest_cc_sessions({
            "project_id": "PROJ-MY-PROJ",
            "cc_directory": "/tmp/cc-dir",
        })

        mock_ingest.assert_called_once()
        call_kwargs = mock_ingest.call_args
        assert call_kwargs.kwargs.get("dry_run") is False
