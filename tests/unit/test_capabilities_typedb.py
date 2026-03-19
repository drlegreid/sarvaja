"""
Unit tests for TypeDB capability queries and service-level TypeDB integration.

Tests:
- CapabilityQueries mixin methods (mocked TypeDB driver)
- Service layer TypeDB persistence (bind/unbind/toggle/sync/load)
- Controller triggers (bind_capability, unbind_capability, toggle_capability_status)
"""

from unittest.mock import MagicMock, patch, call
import pytest

_SVC = "governance.services.capabilities"


# =============================================================================
# CapabilityQueries mixin tests
# =============================================================================


class TestCapabilityQueriesCreate:
    """Tests for CapabilityQueries.create_capability()."""

    def _make_client(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        client = CapabilityQueries()
        client.database = "test-db"
        client._driver = MagicMock()
        return client

    def test_create_capability_success(self):
        client = self._make_client()
        mock_tx = MagicMock()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        mock_tx.query.return_value.resolve.return_value = None

        result = client.create_capability("code-agent", "TEST-GUARD-01", "coding", "active")
        assert result is True
        mock_tx.commit.assert_called_once()

    def test_create_capability_query_has_correct_entities(self):
        client = self._make_client()
        mock_tx = MagicMock()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        mock_tx.query.return_value.resolve.return_value = None

        client.create_capability("my-agent", "MY-RULE", "testing", "active")

        query_arg = mock_tx.query.call_args[0][0]
        assert '"my-agent"' in query_arg
        assert '"MY-RULE"' in query_arg
        assert "agent-capability" in query_arg
        assert "capable-agent" in query_arg
        assert "governing-rule" in query_arg
        assert '"testing"' in query_arg

    def test_create_capability_failure(self):
        client = self._make_client()
        client._driver.transaction.side_effect = Exception("connection error")

        result = client.create_capability("agent", "rule")
        assert result is False

    def test_create_escapes_special_chars(self):
        client = self._make_client()
        mock_tx = MagicMock()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        mock_tx.query.return_value.resolve.return_value = None

        client.create_capability('a"gent', 'r\\ule')
        query_arg = mock_tx.query.call_args[0][0]
        assert 'a\\"gent' in query_arg
        assert 'r\\\\ule' in query_arg


class TestCapabilityQueriesDelete:
    """Tests for CapabilityQueries.delete_capability()."""

    def _make_client(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        client = CapabilityQueries()
        client.database = "test-db"
        client._driver = MagicMock()
        return client

    def test_delete_capability_success(self):
        client = self._make_client()
        mock_tx = MagicMock()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        mock_tx.query.return_value.resolve.return_value = None

        result = client.delete_capability("code-agent", "TEST-GUARD-01")
        assert result is True
        mock_tx.commit.assert_called_once()

    def test_delete_capability_failure(self):
        client = self._make_client()
        client._driver.transaction.side_effect = Exception("fail")

        result = client.delete_capability("agent", "rule")
        assert result is False

    def test_delete_query_structure(self):
        client = self._make_client()
        mock_tx = MagicMock()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        mock_tx.query.return_value.resolve.return_value = None

        client.delete_capability("agent-x", "RULE-Y")
        query_arg = mock_tx.query.call_args[0][0]
        assert "delete $c" in query_arg
        assert '"agent-x"' in query_arg
        assert '"RULE-Y"' in query_arg


class TestCapabilityQueriesUpdateStatus:
    """Tests for CapabilityQueries.update_capability_status()."""

    def _make_client(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        client = CapabilityQueries()
        client.database = "test-db"
        client._driver = MagicMock()
        return client

    def test_update_status_success(self):
        client = self._make_client()
        mock_tx = MagicMock()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        mock_tx.query.return_value.resolve.return_value = None

        result = client.update_capability_status("agent", "rule", "suspended")
        assert result is True
        mock_tx.commit.assert_called_once()
        # Should have 2 queries: delete old status + insert new
        assert mock_tx.query.call_count == 2

    def test_update_status_failure(self):
        client = self._make_client()
        client._driver.transaction.side_effect = Exception("fail")

        result = client.update_capability_status("a", "r", "active")
        assert result is False


class TestCapabilityQueriesGet:
    """Tests for CapabilityQueries.get_capabilities_for_agent() and get_agents_for_rule()."""

    def _make_client(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        client = CapabilityQueries()
        client.database = "test-db"
        client._driver = MagicMock()
        client._execute_query = MagicMock()
        return client

    def test_get_capabilities_for_agent_returns_list(self):
        client = self._make_client()
        client._execute_query.return_value = [
            {"rid": "RULE-01", "cat": "coding", "stat": "active"},
            {"rid": "RULE-02", "cat": "testing", "stat": "suspended"},
        ]

        result = client.get_capabilities_for_agent("code-agent")
        assert len(result) == 2
        assert result[0]["agent_id"] == "code-agent"
        assert result[0]["rule_id"] == "RULE-01"
        assert result[0]["category"] == "coding"
        assert result[1]["status"] == "suspended"

    def test_get_capabilities_for_agent_empty(self):
        client = self._make_client()
        client._execute_query.return_value = []

        result = client.get_capabilities_for_agent("unknown")
        assert result == []

    def test_get_capabilities_for_agent_error(self):
        client = self._make_client()
        client._execute_query.side_effect = Exception("fail")

        result = client.get_capabilities_for_agent("agent")
        assert result == []

    def test_get_agents_for_rule_returns_list(self):
        client = self._make_client()
        client._execute_query.return_value = [
            {"aid": "agent-a", "cat": "coding", "stat": "active"},
        ]

        result = client.get_agents_for_rule("TEST-GUARD-01")
        assert len(result) == 1
        assert result[0]["agent_id"] == "agent-a"
        assert result[0]["rule_id"] == "TEST-GUARD-01"

    def test_get_all_capabilities(self):
        client = self._make_client()
        client._execute_query.return_value = [
            {"aid": "a1", "rid": "R1", "cat": "coding", "stat": "active"},
            {"aid": "a2", "rid": "R2", "cat": "security", "stat": "active"},
        ]

        result = client.get_all_capabilities()
        assert len(result) == 2
        assert result[0]["agent_id"] == "a1"
        assert result[1]["rule_id"] == "R2"


# =============================================================================
# Service layer TypeDB integration tests
# =============================================================================


@pytest.fixture(autouse=True)
def _reset_store():
    """Reset in-memory capabilities store for each test."""
    with patch(f"{_SVC}._capabilities_store", {}) as store, \
         patch(f"{_SVC}.record_audit"):
        yield store


class TestServiceTypeDBPersist:
    """Tests for service-level TypeDB persistence on bind/unbind/toggle."""

    @patch(f"{_SVC}.get_typedb_client")
    def test_bind_calls_typedb_create(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import bind_rule_to_agent
        bind_rule_to_agent("new-agent", "NEW-RULE", category="testing")

        mock_client.create_capability.assert_called_once_with(
            "new-agent", "NEW-RULE", "testing", "active"
        )

    @patch(f"{_SVC}.get_typedb_client")
    def test_bind_duplicate_skips_typedb(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import bind_rule_to_agent
        bind_rule_to_agent("agt", "RULE-01")
        mock_client.create_capability.reset_mock()
        bind_rule_to_agent("agt", "RULE-01")  # duplicate
        mock_client.create_capability.assert_not_called()

    @patch(f"{_SVC}.get_typedb_client")
    def test_unbind_calls_typedb_delete(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import bind_rule_to_agent, unbind_rule_from_agent
        bind_rule_to_agent("agt", "RULE-01")
        unbind_rule_from_agent("agt", "RULE-01")

        mock_client.delete_capability.assert_called_once_with("agt", "RULE-01")

    @patch(f"{_SVC}.get_typedb_client")
    def test_update_status_calls_typedb(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import bind_rule_to_agent, update_capability_status
        bind_rule_to_agent("agt", "RULE-01")
        update_capability_status("agt", "RULE-01", "suspended")

        mock_client.update_capability_status.assert_called_once_with(
            "agt", "RULE-01", "suspended"
        )

    @patch(f"{_SVC}.get_typedb_client")
    def test_typedb_failure_doesnt_break_service(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.create_capability.side_effect = Exception("TypeDB down")
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import bind_rule_to_agent
        result = bind_rule_to_agent("agt", "RULE-01")
        # Should succeed in-memory even if TypeDB fails
        assert result["agent_id"] == "agt"
        assert result["rule_id"] == "RULE-01"

    @patch(f"{_SVC}.get_typedb_client")
    def test_no_client_skips_persist(self, mock_get_client):
        mock_get_client.return_value = None

        from governance.services.capabilities import bind_rule_to_agent
        result = bind_rule_to_agent("agt", "RULE-01")
        assert result is not None


class TestServiceSync:
    """Tests for sync_to_typedb and load_from_typedb."""

    @patch(f"{_SVC}.get_typedb_client")
    def test_sync_to_typedb_all_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.create_capability.return_value = True
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import sync_to_typedb
        result = sync_to_typedb()
        assert result["synced"] > 0
        assert result["failed"] == 0
        assert result["skipped"] == 0

    @patch(f"{_SVC}.get_typedb_client")
    def test_sync_to_typedb_partial_failure(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.create_capability.side_effect = [True, False, True, True,
                                                       True, True, True, True,
                                                       True, True, True, True,
                                                       True, True]
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import sync_to_typedb
        result = sync_to_typedb()
        assert result["failed"] >= 1

    @patch(f"{_SVC}.get_typedb_client")
    def test_sync_no_client(self, mock_get_client):
        mock_get_client.return_value = None

        from governance.services.capabilities import sync_to_typedb
        result = sync_to_typedb()
        assert result["skipped"] > 0
        assert result["synced"] == 0

    @patch(f"{_SVC}.get_typedb_client")
    def test_load_from_typedb_merges(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_all_capabilities.return_value = [
            {"agent_id": "ext-agent", "rule_id": "EXT-RULE",
             "category": "custom", "status": "active"},
        ]
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import load_from_typedb, _capabilities_store
        loaded = load_from_typedb()
        assert loaded == 1
        assert "ext-agent::EXT-RULE" in _capabilities_store

    @patch(f"{_SVC}.get_typedb_client")
    def test_load_from_typedb_no_dupes(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_all_capabilities.return_value = [
            {"agent_id": "agt", "rule_id": "R1",
             "category": "c", "status": "active"},
        ]
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import (
            load_from_typedb, _capabilities_store, _key,
        )
        # Pre-populate
        _capabilities_store[_key("agt", "R1")] = {
            "agent_id": "agt", "rule_id": "R1",
            "category": "existing", "status": "active",
            "created_at": "2026-01-01",
        }
        loaded = load_from_typedb()
        assert loaded == 0
        # Should keep existing category
        assert _capabilities_store[_key("agt", "R1")]["category"] == "existing"

    @patch(f"{_SVC}.get_typedb_client")
    def test_load_from_typedb_no_client(self, mock_get_client):
        mock_get_client.return_value = None

        from governance.services.capabilities import load_from_typedb
        loaded = load_from_typedb()
        assert loaded == 0

    @patch(f"{_SVC}.get_typedb_client")
    def test_load_from_typedb_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_all_capabilities.side_effect = Exception("fail")
        mock_get_client.return_value = mock_client

        from governance.services.capabilities import load_from_typedb
        loaded = load_from_typedb()
        assert loaded == 0


# =============================================================================
# Controller trigger tests
# =============================================================================


class TestCapabilityControllerTriggers:
    """Tests for bind/unbind/toggle controller triggers."""

    def _setup_controller(self):
        from unittest.mock import MagicMock

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_decorator(name):
            def wrapper(fn):
                triggers[name] = fn
                return fn
            return wrapper

        ctrl.trigger = trigger_decorator
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        return state, triggers

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    def test_bind_capability_success(self, mock_httpx_class):
        state, triggers = self._setup_controller()
        mock_client = MagicMock()
        mock_httpx_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_client.post.return_value = mock_resp
        # load_agent_capabilities call
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = []
        mock_client.get.return_value = mock_get_resp

        triggers["bind_capability"]("code-agent", "NEW-RULE", "coding")
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "capabilities" in call_args[0][0]

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    def test_unbind_capability_success(self, mock_httpx_class):
        state, triggers = self._setup_controller()
        mock_client = MagicMock()
        mock_httpx_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client.delete.return_value = mock_resp
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = []
        mock_client.get.return_value = mock_get_resp

        triggers["unbind_capability"]("code-agent", "RULE-01")
        mock_client.delete.assert_called_once()
        assert "code-agent/RULE-01" in mock_client.delete.call_args[0][0]

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    def test_toggle_capability_active_to_suspended(self, mock_httpx_class):
        state, triggers = self._setup_controller()
        mock_client = MagicMock()
        mock_httpx_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client.put.return_value = mock_resp
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = []
        mock_client.get.return_value = mock_get_resp

        triggers["toggle_capability_status"]("code-agent", "RULE-01", "active")
        mock_client.put.assert_called_once()
        put_args = mock_client.put.call_args
        assert put_args[1]["json"]["status"] == "suspended"

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    def test_toggle_capability_suspended_to_active(self, mock_httpx_class):
        state, triggers = self._setup_controller()
        mock_client = MagicMock()
        mock_httpx_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client.put.return_value = mock_resp
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = []
        mock_client.get.return_value = mock_get_resp

        triggers["toggle_capability_status"]("agent", "rule", "suspended")
        put_args = mock_client.put.call_args
        assert put_args[1]["json"]["status"] == "active"

    def test_bind_empty_agent_noop(self):
        state, triggers = self._setup_controller()
        # Should not raise
        triggers["bind_capability"]("", "RULE-01", "coding")
        triggers["bind_capability"](None, "RULE-01", "coding")

    def test_unbind_empty_agent_noop(self):
        state, triggers = self._setup_controller()
        triggers["unbind_capability"]("", "RULE-01")
        triggers["unbind_capability"](None, "RULE-01")

    def test_toggle_empty_agent_noop(self):
        state, triggers = self._setup_controller()
        triggers["toggle_capability_status"]("", "RULE-01", "active")


# =============================================================================
# Updated UI tests
# =============================================================================


class TestCapabilitiesUIUpdated:
    """Verify new interactive controls are present in the UI."""

    def test_has_toggle_btn_testid(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "capability-toggle-btn" in source

    def test_has_unbind_btn_testid(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "capability-unbind-btn" in source

    def test_has_add_capability_row(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "add-capability-row" in source

    def test_has_bind_trigger(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "bind_capability" in source

    def test_has_unbind_trigger(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "unbind_capability" in source

    def test_has_toggle_trigger(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "toggle_capability_status" in source

    def test_has_rule_input_testid(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "add-capability-rule-input" in source

    def test_has_category_select_testid(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "add-capability-category-select" in source

    def test_has_bind_btn_testid(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "add-capability-bind-btn" in source

    def test_has_link_off_icon(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "mdi-link-off" in source

    def test_has_pause_play_icons(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "mdi-pause-circle-outline" in source
        assert "mdi-play-circle-outline" in source

    def test_has_link_plus_icon(self):
        import inspect
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "mdi-link-plus" in source


class TestCapabilitiesStateVariables:
    """Verify new state variables are present."""

    def test_new_capability_rule_id_in_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "new_capability_rule_id" in state
        assert state["new_capability_rule_id"] == ""

    def test_new_capability_category_in_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "new_capability_category" in state
        assert state["new_capability_category"] == "general"


# =============================================================================
# Escape function tests
# =============================================================================


class TestEscapeId:
    """Tests for _escape_id helper."""

    def test_no_special_chars(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        cq = CapabilityQueries()
        assert cq._escape_id("simple") == "simple"

    def test_escape_quotes(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        cq = CapabilityQueries()
        assert cq._escape_id('a"b') == 'a\\"b'

    def test_escape_backslash(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        cq = CapabilityQueries()
        assert cq._escape_id("a\\b") == "a\\\\b"

    def test_escape_both(self):
        from governance.typedb.queries.capabilities import CapabilityQueries

        cq = CapabilityQueries()
        # Backslash first, then quotes
        assert cq._escape_id('a\\b"c') == 'a\\\\b\\"c'
