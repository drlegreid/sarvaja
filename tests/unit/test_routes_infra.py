"""Tests for governance/routes/infra.py — Infrastructure endpoints.

Covers: _find_socket, _fetch_logs_subprocess, _fetch_own_process_logs,
CONTAINER_NAMES, list_containers, get_container_logs.
"""

import unittest
from unittest.mock import patch, MagicMock

from governance.routes.infra import (
    _find_socket,
    _fetch_logs_subprocess,
    _fetch_own_process_logs,
    CONTAINER_NAMES,
    list_containers,
    get_container_logs,
)


class TestContainerNames(unittest.TestCase):
    """Tests for CONTAINER_NAMES constant."""

    def test_known_containers(self):
        self.assertIn("dashboard", CONTAINER_NAMES)
        self.assertIn("typedb", CONTAINER_NAMES)
        self.assertIn("chromadb", CONTAINER_NAMES)
        self.assertIn("litellm", CONTAINER_NAMES)
        self.assertIn("ollama", CONTAINER_NAMES)

    def test_list_containers(self):
        result = list_containers()
        self.assertIn("containers", result)
        self.assertIn("dashboard", result["containers"])


class TestFindSocket(unittest.TestCase):
    """Tests for _find_socket."""

    @patch("os.path.isdir", return_value=False)
    @patch("os.path.exists", return_value=False)
    def test_no_socket(self, mock_exists, mock_isdir):
        self.assertIsNone(_find_socket())

    @patch("os.path.isdir", return_value=False)
    @patch("os.path.exists", side_effect=lambda p: p == "/run/podman/podman.sock")
    def test_finds_first_socket(self, mock_exists, mock_isdir):
        result = _find_socket()
        self.assertEqual(result, "/run/podman/podman.sock")

    @patch("os.path.isdir", return_value=True)
    @patch("os.path.exists", return_value=True)
    def test_skips_directories(self, mock_exists, mock_isdir):
        """Socket path that is a directory should be skipped."""
        self.assertIsNone(_find_socket())


class TestFetchLogsSubprocess(unittest.TestCase):
    """Tests for _fetch_logs_subprocess."""

    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="line1\nline2\nline3",
            stderr="",
        )
        result = _fetch_logs_subprocess("container", 10)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "line1")

    @patch("subprocess.run")
    def test_with_stderr(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="stdout-line",
            stderr="stderr-line",
        )
        result = _fetch_logs_subprocess("container", 10)
        self.assertEqual(len(result), 2)

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_podman_not_found(self, mock_run):
        result = _fetch_logs_subprocess("container", 10)
        self.assertEqual(result, [])

    @patch("subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
        result = _fetch_logs_subprocess("container", 10)
        self.assertIn("Timeout", result[0])

    @patch("subprocess.run")
    def test_no_output(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", stderr="")
        result = _fetch_logs_subprocess("container", 10)
        self.assertEqual(result, ["No log output from container"])


class TestFetchOwnProcessLogs(unittest.TestCase):
    """Tests for _fetch_own_process_logs."""

    @patch("subprocess.run")
    def test_with_python_processes(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="  PID TTY      STAT   TIME COMMAND\n"
                   "    1 ?        S      0:00 python3 -m governance.api\n"
                   "  100 ?        S      0:00 /bin/bash",
        )
        result = _fetch_own_process_logs(50)
        self.assertGreater(len(result), 0)
        # Should include header and python process
        combined = "\n".join(result)
        self.assertIn("python", combined.lower())

    @patch("subprocess.run", side_effect=Exception("ps failed"))
    def test_fallback(self, mock_run):
        result = _fetch_own_process_logs(50)
        self.assertGreater(len(result), 0)
        self.assertIn("container", result[0].lower())


class TestGetContainerLogs(unittest.TestCase):
    """Tests for get_container_logs endpoint."""

    @patch("governance.routes.infra._fetch_own_process_logs", return_value=["process info"])
    @patch("governance.routes.infra._fetch_logs_subprocess", return_value=[])
    @patch("governance.routes.infra._find_socket", return_value=None)
    def test_all_fallbacks(self, mock_socket, mock_cli, mock_own):
        result = get_container_logs(container="dashboard", tail=50)
        self.assertEqual(result["source"], "process-info")

    @patch("governance.routes.infra._fetch_logs_subprocess")
    @patch("governance.routes.infra._find_socket", return_value=None)
    def test_cli_success(self, mock_socket, mock_cli):
        mock_cli.return_value = ["log line 1", "log line 2"]
        result = get_container_logs(container="dashboard", tail=50, level="")
        self.assertEqual(result["source"], "cli")
        self.assertEqual(len(result["lines"]), 2)

    @patch("governance.routes.infra._fetch_logs_socket", return_value=["socket log"])
    @patch("governance.routes.infra._find_socket", return_value="/run/podman/podman.sock")
    def test_socket_success(self, mock_find, mock_fetch):
        result = get_container_logs(container="dashboard", tail=50, level="")
        self.assertEqual(result["source"], "/run/podman/podman.sock")
        self.assertEqual(result["lines"], ["socket log"])

    @patch("governance.routes.infra._fetch_logs_socket", return_value=[
        "INFO: request ok",
        "ERROR: something broke",
        "WARNING: low memory",
    ])
    @patch("governance.routes.infra._find_socket", return_value="/run/podman/podman.sock")
    def test_level_filter(self, mock_find, mock_fetch):
        result = get_container_logs(container="dashboard", tail=50, level="ERROR")
        self.assertEqual(len(result["lines"]), 1)
        self.assertIn("ERROR", result["lines"][0])

    def test_unknown_container(self):
        """Unknown container name must be rejected with 400."""
        # BUG-ROUTE-LOGIC-010: Strict whitelist — no fallback to raw input
        from fastapi.exceptions import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            get_container_logs(container="unknown-container", tail=10)
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
