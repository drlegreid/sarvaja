"""
Unit tests for Service Health Checks.

Per DOC-SIZE-01-v1: Tests for health/checks.py module.
Tests: ServiceStatus, check_port, check_podman, check_typedb,
       check_chromadb, check_all_services, are_core_services_healthy,
       get_failed_services.
"""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from governance.health.checks import (
    ServiceStatus,
    check_port,
    check_podman,
    check_typedb,
    check_chromadb,
    check_governance_api,
    check_all_services,
    are_core_services_healthy,
    get_failed_services,
    CORE_SERVICES,
)


# ---------------------------------------------------------------------------
# ServiceStatus
# ---------------------------------------------------------------------------
class TestServiceStatus:
    """Tests for ServiceStatus dataclass."""

    def test_required_fields(self):
        s = ServiceStatus(name="test", ok=True, status="OK")
        assert s.name == "test"
        assert s.ok is True
        assert s.status == "OK"

    def test_defaults(self):
        s = ServiceStatus(name="test", ok=True, status="OK")
        assert s.port is None
        assert s.error is None

    def test_with_all_fields(self):
        s = ServiceStatus(name="typedb", ok=False, status="DOWN", port=1729, error="refused")
        assert s.port == 1729
        assert s.error == "refused"


# ---------------------------------------------------------------------------
# check_port
# ---------------------------------------------------------------------------
class TestCheckPort:
    """Tests for check_port()."""

    @patch("governance.health.checks.socket.socket")
    def test_port_open(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket_cls.return_value = mock_sock
        assert check_port("localhost", 1729) is True
        mock_sock.close.assert_called_once()

    @patch("governance.health.checks.socket.socket")
    def test_port_closed(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111  # connection refused
        mock_socket_cls.return_value = mock_sock
        assert check_port("localhost", 9999) is False

    @patch("governance.health.checks.socket.socket")
    def test_socket_exception(self, mock_socket_cls):
        mock_socket_cls.side_effect = OSError("network error")
        assert check_port("localhost", 1729) is False


# ---------------------------------------------------------------------------
# check_podman
# ---------------------------------------------------------------------------
class TestCheckPodman:
    """Tests for check_podman()."""

    @patch("governance.health.checks.subprocess.run")
    def test_podman_ok(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = check_podman()
        assert result.ok is True
        assert result.name == "podman"
        assert result.status == "OK"

    @patch("governance.health.checks.subprocess.run")
    def test_podman_down(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        result = check_podman()
        assert result.ok is False
        assert result.status == "DOWN"

    @patch("governance.health.checks.subprocess.run")
    def test_podman_exception(self, mock_run):
        mock_run.side_effect = FileNotFoundError("podman not found")
        result = check_podman()
        assert result.ok is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# check_typedb / check_chromadb
# ---------------------------------------------------------------------------
class TestCheckTypedb:
    """Tests for check_typedb()."""

    @patch("governance.health.checks.check_port", return_value=True)
    def test_typedb_ok(self, mock_port):
        result = check_typedb()
        assert result.ok is True
        assert result.name == "typedb"

    @patch("governance.health.checks.check_port", return_value=False)
    def test_typedb_down(self, mock_port):
        result = check_typedb()
        assert result.ok is False
        assert result.status == "DOWN"


class TestCheckChromadb:
    """Tests for check_chromadb()."""

    @patch("governance.health.checks.check_port", return_value=True)
    def test_chromadb_ok(self, mock_port):
        result = check_chromadb()
        assert result.ok is True
        assert result.name == "chromadb"

    @patch("governance.health.checks.check_port", return_value=False)
    def test_chromadb_down(self, mock_port):
        result = check_chromadb()
        assert result.ok is False


# ---------------------------------------------------------------------------
# check_all_services
# ---------------------------------------------------------------------------
class TestCheckAllServices:
    """Tests for check_all_services()."""

    @patch("governance.health.checks.check_governance_api")
    @patch("governance.health.checks.check_chromadb")
    @patch("governance.health.checks.check_typedb")
    @patch("governance.health.checks.check_podman")
    def test_all_healthy(self, mock_podman, mock_typedb, mock_chromadb, mock_api):
        mock_podman.return_value = ServiceStatus("podman", True, "OK")
        mock_typedb.return_value = ServiceStatus("typedb", True, "OK", port=1729)
        mock_chromadb.return_value = ServiceStatus("chromadb", True, "OK", port=8001)
        mock_api.return_value = ServiceStatus("governance-api", True, "OK", port=8082)
        services = check_all_services()
        assert services["podman"].ok is True
        assert services["typedb"].ok is True
        assert services["chromadb"].ok is True

    @patch("governance.health.checks.check_podman")
    def test_podman_down_cascades(self, mock_podman):
        mock_podman.return_value = ServiceStatus("podman", False, "DOWN")
        services = check_all_services()
        assert services["typedb"].status == "PODMAN_DOWN"
        assert services["chromadb"].status == "PODMAN_DOWN"
        assert services["typedb"].ok is False


# ---------------------------------------------------------------------------
# are_core_services_healthy / get_failed_services
# ---------------------------------------------------------------------------
class TestCoreServicesHelpers:
    """Tests for are_core_services_healthy() and get_failed_services()."""

    def test_all_healthy(self):
        services = {
            "podman": ServiceStatus("podman", True, "OK"),
            "typedb": ServiceStatus("typedb", True, "OK"),
            "chromadb": ServiceStatus("chromadb", True, "OK"),
        }
        assert are_core_services_healthy(services) is True

    def test_one_down(self):
        services = {
            "podman": ServiceStatus("podman", True, "OK"),
            "typedb": ServiceStatus("typedb", False, "DOWN"),
            "chromadb": ServiceStatus("chromadb", True, "OK"),
        }
        assert are_core_services_healthy(services) is False

    def test_missing_service(self):
        services = {"podman": ServiceStatus("podman", True, "OK")}
        assert are_core_services_healthy(services) is False

    def test_get_failed_services_none(self):
        services = {
            "podman": ServiceStatus("podman", True, "OK"),
            "typedb": ServiceStatus("typedb", True, "OK"),
            "chromadb": ServiceStatus("chromadb", True, "OK"),
        }
        assert get_failed_services(services) == []

    def test_get_failed_services_some(self):
        services = {
            "podman": ServiceStatus("podman", True, "OK"),
            "typedb": ServiceStatus("typedb", False, "DOWN"),
            "chromadb": ServiceStatus("chromadb", False, "DOWN"),
        }
        failed = get_failed_services(services)
        assert "typedb" in failed
        assert "chromadb" in failed
        assert "podman" not in failed

    def test_core_services_list(self):
        assert "podman" in CORE_SERVICES
        assert "typedb" in CORE_SERVICES
        assert "chromadb" in CORE_SERVICES
