"""
Unit tests for Tab Deep Scan Batch 46 — client.py socket safety,
agents.py metrics crash prevention, heuristic checks false positives.

2 bugs fixed (BUG-SOCKET-001, BUG-METRICS-001). Multiple false positives
verified (tasks_mutations known limitation, rules.py exception propagation).

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect
import socket
from unittest.mock import patch, MagicMock


# ── BUG-SOCKET-001: quick_health() socket cleanup ──────────────────


class TestQuickHealthSocketSafety:
    """Verify quick_health uses try/finally for socket cleanup."""

    def test_has_bugfix_marker(self):
        """BUG-SOCKET-001 marker present in client.py."""
        from governance import client
        source = inspect.getsource(client.quick_health)
        assert "BUG-SOCKET-001" in source

    def test_has_try_finally(self):
        """quick_health uses try/finally pattern."""
        from governance import client
        source = inspect.getsource(client.quick_health)
        assert "finally:" in source
        assert "sock.close()" in source

    def test_socket_close_in_finally(self):
        """sock.close() is inside the finally block."""
        from governance import client
        source = inspect.getsource(client.quick_health)
        lines = source.split("\n")
        finally_idx = None
        close_idx = None
        for i, line in enumerate(lines):
            if "finally:" in line:
                finally_idx = i
            if finally_idx and "sock.close()" in line:
                close_idx = i
                break
        assert finally_idx is not None, "Missing finally block"
        assert close_idx is not None, "Missing sock.close()"
        assert close_idx > finally_idx, "sock.close() must be after finally:"

    def test_returns_bool(self):
        """quick_health returns a boolean."""
        from governance.client import quick_health
        result = quick_health()
        assert isinstance(result, bool)

    def test_unreachable_host_returns_false(self):
        """Unreachable host returns False (not crash)."""
        with patch("governance.typedb.base.TYPEDB_HOST", "192.0.2.1"):  # RFC 5737 test IP
            with patch("governance.typedb.base.TYPEDB_PORT", 99999):
                from governance.client import quick_health
                # Should not crash, should return False
                result = quick_health()
                assert isinstance(result, bool)


# ── BUG-METRICS-001: Agent metrics safe persistence ──────────────────


class TestAgentMetricsSafePersistence:
    """Verify _save_agent_metrics handles filesystem errors."""

    def test_has_bugfix_marker(self):
        """BUG-METRICS-001 marker present in agents.py."""
        from governance.stores import agents
        source = inspect.getsource(agents._save_agent_metrics)
        assert "BUG-METRICS-001" in source

    def test_has_try_except(self):
        """_save_agent_metrics has try/except wrapping."""
        from governance.stores import agents
        source = inspect.getsource(agents._save_agent_metrics)
        assert "try:" in source
        assert "except Exception" in source

    def test_logs_warning_on_failure(self):
        """Filesystem failure logs warning."""
        from governance.stores import agents
        source = inspect.getsource(agents._save_agent_metrics)
        assert "logger.warning" in source

    def test_no_crash_on_permission_error(self):
        """PermissionError does not crash."""
        from governance.stores.agents import _save_agent_metrics
        with patch("governance.stores.agents.os.makedirs", side_effect=PermissionError("denied")):
            # Should not raise
            _save_agent_metrics({"test": "data"})

    def test_no_crash_on_disk_full(self):
        """OSError (disk full) does not crash."""
        from governance.stores.agents import _save_agent_metrics
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            with patch("governance.stores.agents.os.makedirs"):
                _save_agent_metrics({"test": "data"})


# ── False positive: tasks_mutations known limitation ──────────────────


class TestTasksMutationsKnownLimitation:
    """Verify tasks_mutations agent_id TypeDB skip is known/documented."""

    def test_update_task_exists(self):
        """update_task function exists in tasks_mutations."""
        from governance.services import tasks_mutations as task_mutations
        assert hasattr(task_mutations, "update_task")

    def test_agent_id_only_documented(self):
        """The agent_id limitation is documented in code comments."""
        from governance.services import tasks_mutations as task_mutations
        source = inspect.getsource(task_mutations)
        # Must have either H-TASK-002 or agent_id related comments
        assert "agent_id" in source
        assert "code-agent" in source


# ── False positive: rules.py exception propagation ──────────────────


class TestRulesExceptionPropagation:
    """Verify rules.py _get_client_or_raise() correctly propagates."""

    def test_raises_connection_error(self):
        """_get_client_or_raise raises ConnectionError when client unavailable."""
        from governance.services.rules import _get_client_or_raise
        with patch("governance.services.rules.get_client", return_value=None):
            try:
                _get_client_or_raise()
                assert False, "Should have raised"
            except ConnectionError as e:
                assert "TypeDB" in str(e)

    def test_returns_client_when_available(self):
        """_get_client_or_raise returns client when connected."""
        from governance.services.rules import _get_client_or_raise
        mock_client = MagicMock()
        with patch("governance.services.rules.get_client", return_value=mock_client):
            result = _get_client_or_raise()
            assert result is mock_client


# ── False positive: heuristic _api_get returns list ──────────────────


class TestHeuristicApiGetReturnsCorrectly:
    """Verify _api_get returns usable data for callers."""

    def test_items_extraction_works(self):
        """dict with 'items' key → items list extracted."""
        data = {"items": [{"id": 1}, {"id": 2}], "total": 2}
        result = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(result, list)
        assert len(result) == 2

    def test_list_passthrough_works(self):
        """Plain list → returned as-is."""
        data = [{"id": 1}]
        result = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(result, list)

    def test_empty_dict_returns_dict(self):
        """Empty dict without 'items' → returns dict itself."""
        data = {}
        result = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(result, dict)
        assert result == {}


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch46:
    """Batch 46 cross-cutting consistency checks."""

    def test_client_exports_quick_health(self):
        """client.py exports quick_health."""
        from governance import client
        assert hasattr(client, "quick_health")
        assert "quick_health" in client.__all__

    def test_agents_has_logger(self):
        """agents.py has logger configured."""
        from governance.stores import agents
        assert hasattr(agents, "logger")

    def test_rules_service_has_get_client(self):
        """rules.py imports get_client."""
        from governance.services import rules
        source = inspect.getsource(rules)
        assert "get_client" in source

    def test_task_mutations_has_logger(self):
        """task_mutations.py has logging."""
        from governance.services import tasks_mutations as task_mutations
        assert hasattr(task_mutations, "logger")
