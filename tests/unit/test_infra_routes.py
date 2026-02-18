"""
Unit tests for Infrastructure API Routes.

Per DOC-SIZE-01-v1: Tests for routes/infra.py module.
Tests: _find_socket, _fetch_logs_socket, _fetch_logs_subprocess,
       _fetch_own_process_logs, get_container_logs, list_containers,
       CONTAINER_NAMES.
"""

from unittest.mock import patch, MagicMock

import pytest

_P = "governance.routes.infra"


# ── CONTAINER_NAMES ──────────────────────────────────────────────


class TestContainerNames:
    def test_has_dashboard(self):
        from governance.routes.infra import CONTAINER_NAMES
        assert "dashboard" in CONTAINER_NAMES

    def test_has_typedb(self):
        from governance.routes.infra import CONTAINER_NAMES
        assert "typedb" in CONTAINER_NAMES

    def test_has_six_entries(self):
        from governance.routes.infra import CONTAINER_NAMES
        assert len(CONTAINER_NAMES) == 6


# ── _find_socket ─────────────────────────────────────────────────


class TestFindSocket:
    def test_found_first(self):
        from governance.routes.infra import _find_socket
        with patch(f"{_P}.os.path.exists", side_effect=lambda p: p == "/run/podman/podman.sock"), \
             patch(f"{_P}.os.path.isdir", return_value=False):
            result = _find_socket()
        assert result == "/run/podman/podman.sock"

    def test_none_available(self):
        from governance.routes.infra import _find_socket
        with patch(f"{_P}.os.path.exists", return_value=False):
            result = _find_socket()
        assert result is None

    def test_skip_directory(self):
        from governance.routes.infra import _find_socket
        with patch(f"{_P}.os.path.exists", return_value=True), \
             patch(f"{_P}.os.path.isdir", return_value=True):
            result = _find_socket()
        assert result is None

    def test_second_path(self):
        from governance.routes.infra import _find_socket
        call_count = [0]

        def exists(p):
            call_count[0] += 1
            return call_count[0] > 1

        with patch(f"{_P}.os.path.exists", side_effect=exists), \
             patch(f"{_P}.os.path.isdir", return_value=False):
            result = _find_socket()
        assert result is not None


# ── _fetch_logs_subprocess ────────────────────────────────────────


class TestFetchLogsSubprocess:
    def test_success_stdout(self):
        from governance.routes.infra import _fetch_logs_subprocess
        result_mock = MagicMock()
        result_mock.stdout = "line1\nline2"
        result_mock.stderr = ""
        with patch(f"{_P}.subprocess.run", return_value=result_mock):
            lines = _fetch_logs_subprocess("container", 10)
        assert lines == ["line1", "line2"]

    def test_success_stderr(self):
        from governance.routes.infra import _fetch_logs_subprocess
        result_mock = MagicMock()
        result_mock.stdout = ""
        result_mock.stderr = "err1\nerr2"
        with patch(f"{_P}.subprocess.run", return_value=result_mock):
            lines = _fetch_logs_subprocess("container", 10)
        assert lines == ["err1", "err2"]

    def test_no_output(self):
        from governance.routes.infra import _fetch_logs_subprocess
        result_mock = MagicMock()
        result_mock.stdout = ""
        result_mock.stderr = ""
        with patch(f"{_P}.subprocess.run", return_value=result_mock):
            lines = _fetch_logs_subprocess("container", 10)
        assert lines == ["No log output from container"]

    def test_file_not_found(self):
        from governance.routes.infra import _fetch_logs_subprocess
        with patch(f"{_P}.subprocess.run", side_effect=FileNotFoundError):
            lines = _fetch_logs_subprocess("container", 10)
        assert lines == []

    def test_timeout(self):
        import subprocess
        from governance.routes.infra import _fetch_logs_subprocess
        with patch(f"{_P}.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
            lines = _fetch_logs_subprocess("container", 10)
        assert "Timeout" in lines[0]

    def test_generic_exception(self):
        from governance.routes.infra import _fetch_logs_subprocess
        with patch(f"{_P}.subprocess.run", side_effect=RuntimeError("oops")):
            lines = _fetch_logs_subprocess("container", 10)
        assert "CLI fallback error" in lines[0]


# ── _fetch_own_process_logs ──────────────────────────────────────


class TestFetchOwnProcessLogs:
    def test_with_python_processes(self):
        from governance.routes.infra import _fetch_own_process_logs
        result_mock = MagicMock()
        result_mock.stdout = "PID TTY\n1234 python3 app.py\n5678 bash"
        with patch(f"{_P}.subprocess.run", return_value=result_mock):
            lines = _fetch_own_process_logs(50)
        assert any("python" in ln.lower() or "PID" in ln for ln in lines)

    def test_ps_failure(self):
        from governance.routes.infra import _fetch_own_process_logs
        with patch(f"{_P}.subprocess.run", side_effect=Exception("ps failed")):
            lines = _fetch_own_process_logs(50)
        assert any("container" in ln.lower() for ln in lines)

    def test_tail_limit(self):
        from governance.routes.infra import _fetch_own_process_logs
        result_mock = MagicMock()
        result_mock.stdout = "\n".join([f"PID line {i}" for i in range(20)])
        with patch(f"{_P}.subprocess.run", return_value=result_mock):
            lines = _fetch_own_process_logs(5)
        assert len(lines) <= 5


# ── get_container_logs ───────────────────────────────────────────


class TestGetContainerLogs:
    def test_socket_strategy(self):
        from governance.routes.infra import get_container_logs
        with patch(f"{_P}._find_socket", return_value="/run/podman/podman.sock"), \
             patch(f"{_P}._fetch_logs_socket", return_value=["log1", "log2"]):
            result = get_container_logs(container="dashboard", tail=50, level="")
        assert result["source"] == "/run/podman/podman.sock"
        assert result["lines"] == ["log1", "log2"]

    def test_socket_with_level_filter(self):
        from governance.routes.infra import get_container_logs
        with patch(f"{_P}._find_socket", return_value="/sock"), \
             patch(f"{_P}._fetch_logs_socket", return_value=["INFO msg", "ERROR fail", "DEBUG ok"]):
            result = get_container_logs(container="dashboard", tail=50, level="ERROR")
        assert result["lines"] == ["ERROR fail"]

    def test_cli_fallback(self):
        from governance.routes.infra import get_container_logs
        with patch(f"{_P}._find_socket", return_value=None), \
             patch(f"{_P}._fetch_logs_subprocess", return_value=["cli-line1"]):
            result = get_container_logs(container="typedb", tail=50, level="")
        assert result["source"] == "cli"

    def test_process_info_fallback(self):
        from governance.routes.infra import get_container_logs
        with patch(f"{_P}._find_socket", return_value=None), \
             patch(f"{_P}._fetch_logs_subprocess", return_value=["CLI fallback error: fail"]), \
             patch(f"{_P}._fetch_own_process_logs", return_value=["process info"]):
            result = get_container_logs(container="dashboard", tail=50, level="")
        assert result["source"] == "process-info"

    def test_socket_exception_falls_through(self):
        from governance.routes.infra import get_container_logs
        with patch(f"{_P}._find_socket", return_value="/sock"), \
             patch(f"{_P}._fetch_logs_socket", side_effect=Exception("socket err")), \
             patch(f"{_P}._fetch_logs_subprocess", return_value=["cli ok"]):
            result = get_container_logs(container="dashboard", tail=50, level="")
        assert result["source"] == "cli"

    def test_unknown_container_rejected(self):
        from governance.routes.infra import get_container_logs
        from fastapi import HTTPException
        # BUG-ROUTE-LOGIC-010: Unknown container names are now rejected
        with pytest.raises(HTTPException) as exc_info:
            get_container_logs(container="custom-name", tail=50, level="")
        assert exc_info.value.status_code == 400

    def test_cli_with_level_filter(self):
        from governance.routes.infra import get_container_logs
        with patch(f"{_P}._find_socket", return_value=None), \
             patch(f"{_P}._fetch_logs_subprocess", return_value=["INFO msg", "WARNING warn"]):
            result = get_container_logs(container="dashboard", tail=50, level="WARNING")
        assert result["lines"] == ["WARNING warn"]


# ── list_containers ──────────────────────────────────────────────


class TestListContainers:
    def test_returns_all(self):
        from governance.routes.infra import list_containers
        result = list_containers()
        assert "dashboard" in result["containers"]
        assert len(result["containers"]) == 6
