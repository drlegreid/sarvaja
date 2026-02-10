"""Tests for dashboard file watcher.

Per GAP-WORKFLOW-RELOAD-001: Dashboard hot-reload via watchdog.
"""

import os
import signal
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestDashboardReloader:
    """Test the DashboardReloader class."""

    def test_import(self):
        """Watcher module imports successfully."""
        from agent.dashboard_watcher import DashboardReloader
        assert DashboardReloader is not None

    def test_reloader_init(self):
        """Reloader initializes with process args."""
        from agent.dashboard_watcher import DashboardReloader
        reloader = DashboardReloader(["python", "-m", "test"])
        assert reloader.process_args == ["python", "-m", "test"]
        assert reloader.process is None
        assert reloader._last_event_time == 0.0

    @patch("subprocess.Popen")
    def test_start_process(self, mock_popen):
        """start_process launches subprocess."""
        from agent.dashboard_watcher import DashboardReloader
        reloader = DashboardReloader(["python", "-m", "test"])
        reloader.start_process()
        mock_popen.assert_called_once_with(["python", "-m", "test"])
        assert reloader.process is mock_popen.return_value

    @patch("subprocess.Popen")
    def test_restart_kills_old_process(self, mock_popen):
        """Restarting sends SIGTERM to old process first."""
        from agent.dashboard_watcher import DashboardReloader
        reloader = DashboardReloader(["python", "-m", "test"])

        # First start
        old_proc = MagicMock()
        old_proc.poll.return_value = None  # Still running
        mock_popen.return_value = old_proc
        reloader.start_process()

        # Second start should kill old
        new_proc = MagicMock()
        mock_popen.return_value = new_proc
        reloader.start_process()

        old_proc.send_signal.assert_called_once_with(signal.SIGTERM)
        old_proc.wait.assert_called()

    def test_ignores_non_python_files(self):
        """File changes to non-.py files are ignored."""
        from agent.dashboard_watcher import DashboardReloader
        reloader = DashboardReloader(["python", "-m", "test"])
        reloader.start_process = MagicMock()

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/app/agent/test.html"
        reloader.on_modified(event)

        reloader.start_process.assert_not_called()

    def test_ignores_directories(self):
        """Directory events are ignored."""
        from agent.dashboard_watcher import DashboardReloader
        reloader = DashboardReloader(["python", "-m", "test"])
        reloader.start_process = MagicMock()

        event = MagicMock()
        event.is_directory = True
        event.src_path = "/app/agent/__pycache__"
        reloader.on_modified(event)

        reloader.start_process.assert_not_called()

    def test_debounce(self):
        """Rapid changes are debounced."""
        from agent.dashboard_watcher import DashboardReloader, DEBOUNCE_SECONDS
        reloader = DashboardReloader(["python", "-m", "test"])
        reloader.start_process = MagicMock()

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/app/agent/views/test.py"

        # First call triggers restart
        reloader._handle_change(event)
        assert reloader.start_process.call_count == 1

        # Immediate second call is debounced
        reloader._handle_change(event)
        assert reloader.start_process.call_count == 1

    def test_python_file_triggers_restart(self):
        """Python file change triggers restart after debounce."""
        from agent.dashboard_watcher import DashboardReloader
        reloader = DashboardReloader(["python", "-m", "test"])
        reloader.start_process = MagicMock()
        reloader._last_event_time = 0  # Force no debounce

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/app/agent/governance_ui/state/constants.py"
        reloader.on_modified(event)

        reloader.start_process.assert_called_once()

    def test_on_created_also_triggers(self):
        """New .py file creation triggers restart."""
        from agent.dashboard_watcher import DashboardReloader
        reloader = DashboardReloader(["python", "-m", "test"])
        reloader.start_process = MagicMock()
        reloader._last_event_time = 0

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/app/agent/new_module.py"
        reloader.on_created(event)

        reloader.start_process.assert_called_once()
