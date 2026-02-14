"""
Tests for infrastructure health controller (pure functions).

Per PLAN-UI-OVERHAUL-001 Task 6.3: Infra Health Intent.
Batch 166: New coverage for controllers/infra.py (0->16 tests).
"""
import pytest
from unittest.mock import MagicMock, patch


class TestIsInContainer:
    @patch("os.path.exists", return_value=False)
    def test_returns_false_on_host(self, mock_exists):
        from agent.governance_ui.controllers.infra import is_in_container
        assert is_in_container() is False

    @patch("os.path.exists", side_effect=lambda p: p == "/.dockerenv")
    def test_returns_true_for_dockerenv(self, mock_exists):
        from agent.governance_ui.controllers.infra import is_in_container
        assert is_in_container() is True


class TestConstants:
    def test_mcp_servers_list(self):
        from agent.governance_ui.controllers.infra import MCP_SERVERS
        assert isinstance(MCP_SERVERS, list)
        assert "gov-core" in MCP_SERVERS
        assert "gov-tasks" in MCP_SERVERS

    def test_mcp_server_meta(self):
        from agent.governance_ui.controllers.infra import MCP_SERVER_META
        assert isinstance(MCP_SERVER_META, dict)
        assert "gov-core" in MCP_SERVER_META
        assert "tools" in MCP_SERVER_META["gov-core"]

    def test_service_config(self):
        from agent.governance_ui.controllers.infra import SERVICE_CONFIG
        assert "typedb" in SERVICE_CONFIG
        assert "chromadb" in SERVICE_CONFIG

    def test_required_services(self):
        from agent.governance_ui.controllers.infra import REQUIRED_SERVICES
        assert "typedb" in REQUIRED_SERVICES
        assert "chromadb" in REQUIRED_SERVICES


class TestCheckPort:
    @patch("socket.create_connection")
    def test_open_port_returns_true(self, mock_conn):
        mock_conn.return_value.__enter__ = MagicMock()
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        from agent.governance_ui.controllers.infra import check_port
        assert check_port("localhost", 1729) is True

    @patch("socket.create_connection", side_effect=OSError("refused"))
    def test_closed_port_returns_false(self, mock_conn):
        from agent.governance_ui.controllers.infra import check_port
        assert check_port("localhost", 9999) is False


class TestCheckPodmanHealth:
    @patch("subprocess.run")
    def test_running_returns_true(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from agent.governance_ui.controllers.infra import check_podman_health
        assert check_podman_health() is True

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_missing_podman_returns_false(self, mock_run):
        from agent.governance_ui.controllers.infra import check_podman_health
        assert check_podman_health() is False


class TestCheckServiceHealth:
    @patch("agent.governance_ui.controllers.infra.check_port", return_value=True)
    def test_healthy_service(self, mock_port):
        from agent.governance_ui.controllers.infra import check_service_health
        result = check_service_health("typedb")
        assert result["ok"] is True
        assert result["status"] == "OK"

    @patch("agent.governance_ui.controllers.infra.check_port", return_value=False)
    def test_unhealthy_service(self, mock_port):
        from agent.governance_ui.controllers.infra import check_service_health
        result = check_service_health("typedb")
        assert result["ok"] is False

    def test_unknown_service(self):
        from agent.governance_ui.controllers.infra import check_service_health
        result = check_service_health("nonexistent")
        assert result["ok"] is False


class TestGetSystemStats:
    @patch("agent.governance_ui.controllers.infra.check_all_services")
    def test_returns_dict(self, mock_services):
        mock_services.return_value = {}
        from agent.governance_ui.controllers.infra import get_system_stats
        result = get_system_stats()
        assert isinstance(result, dict)
        assert "memory_pct" in result or "python_procs" in result or "frankel_hash" in result
