"""
Unit tests for Infrastructure Data Loader Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/infra_loaders.py.
Tests: load_infra_status, start_service, start_all_services, restart_stack,
       load_container_logs, cleanup_zombies, load_python_processes.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers


def _make_state(**attrs):
    s = MagicMock()
    for k, v in attrs.items():
        setattr(s, k, v)
    return s


def _make_ctrl():
    ctrl = MagicMock()
    triggers = {}

    def trigger_decorator(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    ctrl.trigger = trigger_decorator
    ctrl._triggers = triggers
    return ctrl


def _setup(**state_attrs):
    state = _make_state(**state_attrs)
    ctrl = _make_ctrl()
    loaders = register_infra_loader_controllers(state, ctrl, "http://localhost:8082")
    return state, ctrl, loaders


# ── Registration ───────────────────────────────────────


class TestRegistration:
    def test_returns_infra_loader(self):
        _, _, loaders = _setup()
        assert "load_infra_status" in loaders

    def test_registers_all_triggers(self):
        _, ctrl, _ = _setup()
        expected = {"load_infra_status", "start_service", "start_all_services",
                    "restart_stack", "load_container_logs", "cleanup_zombies",
                    "load_python_processes"}
        assert expected.issubset(set(ctrl._triggers.keys()))


# ── start_service ──────────────────────────────────────


class TestStartService:
    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_success(self, mock_sub):
        state, ctrl, _ = _setup()
        ctrl._triggers["start_service"]("typedb")

        mock_sub.Popen.assert_called_once()
        args = mock_sub.Popen.call_args[0][0]
        assert "typedb" in args
        assert "Starting typedb" in state.infra_last_action

    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_failure(self, mock_sub):
        mock_sub.Popen.side_effect = FileNotFoundError("podman not found")
        state, ctrl, _ = _setup()
        ctrl._triggers["start_service"]("typedb")

        assert "Failed" in state.infra_last_action


# ── start_all_services ─────────────────────────────────


class TestStartAllServices:
    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_success(self, mock_sub):
        state, ctrl, _ = _setup()
        ctrl._triggers["start_all_services"]()

        mock_sub.Popen.assert_called_once()
        assert "Starting all" in state.infra_last_action

    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_failure(self, mock_sub):
        mock_sub.Popen.side_effect = Exception("fail")
        state, ctrl, _ = _setup()
        ctrl._triggers["start_all_services"]()

        assert "Failed" in state.infra_last_action


# ── restart_stack ──────────────────────────────────────


class TestRestartStack:
    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_success(self, mock_sub):
        state, ctrl, _ = _setup()
        ctrl._triggers["restart_stack"]()

        mock_sub.Popen.assert_called_once()
        assert "Restarting" in state.infra_last_action

    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_failure(self, mock_sub):
        mock_sub.Popen.side_effect = Exception("fail")
        state, ctrl, _ = _setup()
        ctrl._triggers["restart_stack"]()

        assert "Failed" in state.infra_last_action


# ── cleanup_zombies ────────────────────────────────────


class TestCleanupZombies:
    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_success(self, mock_sub):
        state, ctrl, _ = _setup()
        ctrl._triggers["cleanup_zombies"]()

        mock_sub.run.assert_called_once()
        assert "Cleaned up" in state.infra_last_action

    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    def test_failure(self, mock_sub):
        mock_sub.run.side_effect = Exception("permission denied")
        state, ctrl, _ = _setup()
        ctrl._triggers["cleanup_zombies"]()

        assert "failed" in state.infra_last_action.lower()


# ── load_container_logs ────────────────────────────────


class TestLoadContainerLogs:
    @patch("agent.governance_ui.controllers.infra_loaders.os")
    def test_success(self, mock_os):
        mock_os.environ.get.return_value = "http://localhost:8082"
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"lines": ["line1", "line2"]}
            mock_get.return_value = mock_resp

            state, ctrl, _ = _setup()
            ctrl._triggers["load_container_logs"]("dashboard", 50, "")

            assert state.infra_log_lines == ["line1", "line2"]
            assert state.infra_log_container == "dashboard"

    @patch("agent.governance_ui.controllers.infra_loaders.os")
    def test_exception(self, mock_os):
        mock_os.environ.get.return_value = "http://localhost:8082"
        with patch("httpx.get", side_effect=Exception("timeout")):
            state, ctrl, _ = _setup()
            ctrl._triggers["load_container_logs"]()

            assert "Failed" in state.infra_log_lines[0]


# ── load_infra_status ──────────────────────────────────


class TestLoadInfraStatus:
    @patch("agent.governance_ui.controllers.infra_loaders.Path")
    @patch("agent.governance_ui.controllers.infra_loaders.socket")
    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    @patch("agent.governance_ui.controllers.infra_loaders.os")
    def test_healthy_when_all_up(self, mock_os, mock_sub, mock_sock, mock_path):
        mock_os.path.exists.return_value = False  # Not in container

        # Podman OK
        mock_sub.run.return_value = MagicMock(returncode=0)

        # All ports open
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0
        mock_sock.socket.return_value = mock_socket
        mock_sock.AF_INET = 2
        mock_sock.SOCK_STREAM = 1

        # State file + evidence dir mock
        mock_state_file = MagicMock()
        mock_state_file.exists.return_value = False
        # Override Path() calls — return non-existing paths
        mock_path.return_value = mock_state_file
        mock_path.__truediv__ = MagicMock(return_value=mock_state_file)

        state, _, loaders = _setup()
        loaders["load_infra_status"]()

        services = state.infra_services
        assert services["podman"]["ok"] is True
        assert services["typedb"]["ok"] is True
        assert state.infra_loading is False

    @patch("agent.governance_ui.controllers.infra_loaders.Path")
    @patch("agent.governance_ui.controllers.infra_loaders.socket")
    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    @patch("agent.governance_ui.controllers.infra_loaders.os")
    def test_in_container_checks_container_hosts(self, mock_os, mock_sub, mock_sock, mock_path):
        mock_os.path.exists.return_value = True  # In container

        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0
        mock_sock.socket.return_value = mock_socket
        mock_sock.AF_INET = 2
        mock_sock.SOCK_STREAM = 1

        mock_state_file = MagicMock()
        mock_state_file.exists.return_value = False
        mock_path.return_value = mock_state_file
        mock_path.__truediv__ = MagicMock(return_value=mock_state_file)

        state, _, loaders = _setup()
        loaders["load_infra_status"]()

        # In container, podman is always True
        assert state.infra_services["podman"]["ok"] is True

    @patch("agent.governance_ui.controllers.infra_loaders.Path")
    @patch("agent.governance_ui.controllers.infra_loaders.socket")
    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    @patch("agent.governance_ui.controllers.infra_loaders.os")
    def test_required_down_status(self, mock_os, mock_sub, mock_sock, mock_path):
        mock_os.path.exists.return_value = False
        mock_sub.run.return_value = MagicMock(returncode=1)  # podman down

        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1  # All ports closed
        mock_sock.socket.return_value = mock_socket
        mock_sock.AF_INET = 2
        mock_sock.SOCK_STREAM = 1

        mock_state_file = MagicMock()
        mock_state_file.exists.return_value = False
        mock_path.return_value = mock_state_file
        mock_path.__truediv__ = MagicMock(return_value=mock_state_file)

        state, _, loaders = _setup()
        loaders["load_infra_status"]()

        assert state.infra_stats["status"] == "down"


# ── load_python_processes fallback ─────────────────────


class TestLoadPythonProcessesFallback:
    """GAP-INFRA-PROCS-002: ps aux fallback when /proc scan finds nothing."""

    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    @patch("agent.governance_ui.controllers.infra_loaders.Path")
    def test_falls_back_to_ps_aux(self, mock_path, mock_sub):
        """When /proc scan finds nothing, should try ps aux."""
        # /proc iterdir returns nothing useful
        mock_proc = MagicMock()
        mock_proc.iterdir.return_value = []
        mock_path.return_value = mock_proc

        # ps aux returns python processes (11 columns: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND)
        mock_sub.run.return_value = MagicMock(
            stdout=(
                "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n"
                "root       123  1.0  2.5 100000 25600 ?        Ss   00:00   0:05 python3 -m governance.api\n"
                "root       456  0.5  1.2  80000 12800 ?        S    00:01   0:02 python3 -m uvicorn\n"
            ),
            returncode=0,
        )

        state, ctrl, _ = _setup()
        ctrl._triggers["load_python_processes"]()

        procs = state.infra_python_procs
        assert len(procs) == 2
        assert procs[0]["pid"] == "123"
        assert "python3" in procs[0]["command"]

    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    @patch("agent.governance_ui.controllers.infra_loaders.Path")
    def test_proc_scan_succeeds_no_fallback(self, mock_path, mock_sub):
        """When /proc scan finds processes, should NOT call ps aux."""
        # /proc has a python process
        pid_dir = MagicMock()
        pid_dir.name = "42"
        cmdline_file = MagicMock()
        cmdline_file.read_text.return_value = "python3\x00-m\x00uvicorn"
        pid_dir.__truediv__ = lambda self, key: cmdline_file

        mock_proc = MagicMock()
        mock_proc.iterdir.return_value = [pid_dir]
        mock_path.return_value = mock_proc

        state, ctrl, _ = _setup()
        ctrl._triggers["load_python_processes"]()

        procs = state.infra_python_procs
        assert len(procs) >= 1
        # subprocess.run should NOT have been called for ps aux
        mock_sub.run.assert_not_called()

    @patch("agent.governance_ui.controllers.infra_loaders.subprocess")
    @patch("agent.governance_ui.controllers.infra_loaders.Path")
    def test_both_fail_returns_empty(self, mock_path, mock_sub):
        """When both /proc and ps aux fail, should return empty list."""
        mock_proc = MagicMock()
        mock_proc.iterdir.return_value = []
        mock_path.return_value = mock_proc
        mock_sub.run.side_effect = FileNotFoundError("ps not found")

        state, ctrl, _ = _setup()
        ctrl._triggers["load_python_processes"]()

        assert state.infra_python_procs == []
