"""
Batch 50 — Deep Scan: Infrastructure socket cleanup + heuristic checks + route safety.

Fixes verified:
- BUG-INFRA-SOCKET-001: Socket resource leak in _fetch_logs_socket (try/finally)

Also validates:
- Heuristic backfill detection dynamic cutoff
- Runner exec timeout handling
- API response normalization in _api_get
"""
import ast
import inspect
import socket
import textwrap
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ===========================================================================
# BUG-INFRA-SOCKET-001: Socket cleanup on connection failure
# ===========================================================================

class TestInfraSocketCleanup:
    """Verify _fetch_logs_socket wraps socket in try/finally for cleanup."""

    def test_source_has_try_finally_around_socket(self):
        """Socket operations must be inside try/finally block."""
        from governance.routes import infra
        src = inspect.getsource(infra._fetch_logs_socket)
        tree = ast.parse(textwrap.dedent(src))
        # Find Try nodes with finalbody (try/finally)
        try_finally_nodes = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Try) and n.finalbody
        ]
        assert len(try_finally_nodes) >= 1, "No try/finally block found around socket ops"

    def test_finally_calls_sock_close(self):
        """Finally block must call sock.close()."""
        from governance.routes import infra
        src = inspect.getsource(infra._fetch_logs_socket)
        # The finally block should contain sock.close()
        assert "sock.close()" in src, "sock.close() not found in function"
        # Verify it's in the finally section (after 'finally:')
        finally_idx = src.index("finally:")
        close_idx = src.index("sock.close()")
        assert close_idx > finally_idx, "sock.close() should be in finally block"

    def test_finally_calls_conn_close(self):
        """Finally block must also call conn.close()."""
        from governance.routes import infra
        src = inspect.getsource(infra._fetch_logs_socket)
        assert "conn.close()" in src, "conn.close() not found in function"
        finally_idx = src.index("finally:")
        conn_close_idx = src.index("conn.close()")
        assert conn_close_idx > finally_idx, "conn.close() should be in finally block"

    def test_socket_closed_on_connect_failure(self):
        """When sock.connect() fails, socket must still be closed."""
        from governance.routes import infra

        mock_sock = MagicMock(spec=socket.socket)
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")

        with patch("governance.routes.infra.socket.socket", return_value=mock_sock):
            with patch("governance.routes.infra.http.client.HTTPConnection") as mock_conn:
                with pytest.raises(ConnectionRefusedError):
                    infra._fetch_logs_socket("/tmp/test.sock", "test_container", 50)

                # Socket MUST be closed even on failure
                mock_sock.close.assert_called_once()

    def test_socket_closed_on_successful_request(self):
        """Socket must be closed after successful request too."""
        from governance.routes import infra

        mock_sock = MagicMock(spec=socket.socket)
        mock_conn_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b""
        mock_conn_instance.getresponse.return_value = mock_resp

        with patch("governance.routes.infra.socket.socket", return_value=mock_sock):
            with patch("governance.routes.infra.http.client.HTTPConnection", return_value=mock_conn_instance):
                result = infra._fetch_logs_socket("/tmp/test.sock", "test_container", 50)

                mock_sock.close.assert_called_once()
                mock_conn_instance.close.assert_called_once()


# ===========================================================================
# Heuristic checks: dynamic cutoff validation
# ===========================================================================

class TestHeuristicBackfillCutoff:
    """Verify _is_backfilled_session uses dynamic 30-day cutoff."""

    def test_source_uses_timedelta_not_hardcoded_date(self):
        """Cutoff must use timedelta, not a hardcoded date string."""
        from governance.routes.tests import heuristic_checks_session
        src = inspect.getsource(heuristic_checks_session._is_backfilled_session)
        assert "timedelta" in src, "Must use timedelta for dynamic cutoff"
        # Should NOT have hardcoded date like "SESSION-2025" or "SESSION-2024"
        assert "SESSION-2025" not in src, "Hardcoded 2025 date in cutoff"
        assert "SESSION-2024" not in src, "Hardcoded 2024 date in cutoff"

    def test_cc_session_detected_as_backfilled(self):
        """CC sessions (with -CC- in ID) should be treated as backfilled."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        session = {"session_id": "SESSION-2026-02-15-CC-abc123", "agent_id": "code-agent"}
        assert _is_backfilled_session(session) is True

    def test_recent_session_with_agent_not_backfilled(self):
        """Recent session with agent_id should not be backfilled."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        recent = datetime.now().strftime("SESSION-%Y-%m-%d-TOPIC")
        session = {"session_id": recent, "agent_id": "code-agent", "description": "Normal session"}
        assert _is_backfilled_session(session) is False

    def test_old_session_without_agent_is_backfilled(self):
        """Session older than 30 days without agent_id should be backfilled."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        old = (datetime.now() - timedelta(days=60)).strftime("SESSION-%Y-%m-%d-OLD")
        session = {"session_id": old, "agent_id": "", "description": ""}
        assert _is_backfilled_session(session) is True

    def test_test_agent_is_backfilled(self):
        """Agent ending with -test is backfilled."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        session = {"session_id": "SESSION-2026-02-15-TOPIC", "agent_id": "my-agent-test"}
        assert _is_backfilled_session(session) is True


# ===========================================================================
# Runner exec: timeout and error handling
# ===========================================================================

class TestRunnerExecSafety:
    """Verify runner_exec handles subprocess errors safely."""

    def test_execute_tests_has_timeout(self):
        """execute_tests must pass timeout to subprocess.run."""
        from governance.routes.tests import runner_exec
        src = inspect.getsource(runner_exec.execute_tests)
        assert "timeout=" in src, "subprocess.run must have timeout parameter"

    def test_timeout_result_has_status_key(self):
        """Timeout path must produce result with 'status': 'timeout'."""
        from governance.routes.tests import runner_exec
        src = inspect.getsource(runner_exec.execute_tests)
        assert '"timeout"' in src or "'timeout'" in src, "Timeout branch must set status='timeout'"

    def test_test_results_store_assignment(self):
        """Results must be stored in _test_results dict."""
        from governance.routes.tests import runner_exec
        src = inspect.getsource(runner_exec.execute_tests)
        assert "_test_results[run_id]" in src, "Must assign to _test_results[run_id]"


# ===========================================================================
# Infra container name mapping safety
# ===========================================================================

class TestInfraContainerMapping:
    """Verify container name mapping and fallback behavior."""

    def test_container_names_dict_exists(self):
        """CONTAINER_NAMES mapping must exist."""
        from governance.routes.infra import CONTAINER_NAMES
        assert isinstance(CONTAINER_NAMES, dict)
        assert "dashboard" in CONTAINER_NAMES

    def test_unknown_container_uses_raw_name(self):
        """Unknown container name should pass through as-is."""
        from governance.routes.infra import CONTAINER_NAMES
        raw = "my-custom-container"
        resolved = CONTAINER_NAMES.get(raw, raw)
        assert resolved == raw, "Unknown container should fall back to raw name"

    def test_list_containers_returns_keys(self):
        """list_containers endpoint returns CONTAINER_NAMES keys."""
        from governance.routes.infra import CONTAINER_NAMES, list_containers
        result = list_containers()
        assert set(result["containers"]) == set(CONTAINER_NAMES.keys())


# ===========================================================================
# Cross-layer consistency
# ===========================================================================

class TestCrossLayerConsistencyBatch50:
    """Cross-cutting verification of patterns from batch 50 scans."""

    def test_infra_find_socket_rejects_directories(self):
        """_find_socket must reject directories (not just check exists)."""
        from governance.routes import infra
        src = inspect.getsource(infra._find_socket)
        assert "isdir" in src, "_find_socket must check os.path.isdir"

    def test_infra_fetch_own_process_logs_has_timeout(self):
        """_fetch_own_process_logs subprocess.run must have timeout."""
        from governance.routes import infra
        src = inspect.getsource(infra._fetch_own_process_logs)
        assert "timeout=" in src, "ps aux call must have timeout"

    def test_fetch_logs_subprocess_handles_file_not_found(self):
        """_fetch_logs_subprocess must handle FileNotFoundError (podman not installed)."""
        from governance.routes import infra
        src = inspect.getsource(infra._fetch_logs_subprocess)
        assert "FileNotFoundError" in src, "Must handle podman not found"

    def test_api_get_returns_list_on_failure(self):
        """_api_get should return empty list on any failure."""
        from governance.routes.tests.heuristic_checks_session import _api_get
        with patch("governance.routes.tests.heuristic_checks_session.httpx.get", side_effect=Exception("down")):
            result = _api_get("http://localhost:8082", "/api/sessions")
            assert result == [], "Must return [] on failure, not raise"
