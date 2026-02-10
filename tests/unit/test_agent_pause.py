"""Tests for agent pause/resume toggle.

Per GAP-AGENT-PAUSE-001: Agents default PAUSED, operators toggle via UI.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAgentPauseDefaults:
    """All agents should default to PAUSED."""

    def test_all_agents_default_paused(self):
        """Every agent in _AGENT_BASE_CONFIG has default_status=PAUSED."""
        from governance.stores.agents import _AGENT_BASE_CONFIG
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            assert config["default_status"] == "PAUSED", (
                f"Agent {agent_id} should default to PAUSED, got {config['default_status']}"
            )

    def test_built_agents_store_has_paused_status(self):
        """Agents built from config start with PAUSED status."""
        from governance.stores.agents import _build_agents_store
        agents = _build_agents_store()
        for agent_id, agent in agents.items():
            assert agent["status"] == "PAUSED", (
                f"Agent {agent_id} should start PAUSED, got {agent['status']}"
            )

    def test_five_agents_defined(self):
        """There should be exactly 5 base agents."""
        from governance.stores.agents import _AGENT_BASE_CONFIG
        assert len(_AGENT_BASE_CONFIG) == 5

    def test_each_agent_has_capabilities(self):
        """Every agent must define capabilities."""
        from governance.stores.agents import _AGENT_BASE_CONFIG
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            assert len(config.get("capabilities", [])) > 0, (
                f"Agent {agent_id} should have capabilities"
            )


class TestToggleAgentStatus:
    """Test the toggle_agent_status service function."""

    @patch("governance.services.agents.get_typedb_client", return_value=None)
    @patch("governance.services.agents.record_audit")
    def test_toggle_paused_to_active(self, mock_audit, mock_client):
        """Toggling a PAUSED agent sets it to ACTIVE."""
        from governance.services.agents import toggle_agent_status
        from governance.stores.agents import _agents_store

        # Ensure agent starts PAUSED
        _agents_store["code-agent"]["status"] = "PAUSED"

        result = toggle_agent_status("code-agent", source="test")
        assert result is not None
        assert result["status"] == "ACTIVE"
        assert _agents_store["code-agent"]["status"] == "ACTIVE"

    @patch("governance.services.agents.get_typedb_client", return_value=None)
    @patch("governance.services.agents.record_audit")
    def test_toggle_active_to_paused(self, mock_audit, mock_client):
        """Toggling an ACTIVE agent sets it to PAUSED."""
        from governance.services.agents import toggle_agent_status
        from governance.stores.agents import _agents_store

        _agents_store["code-agent"]["status"] = "ACTIVE"

        result = toggle_agent_status("code-agent", source="test")
        assert result is not None
        assert result["status"] == "PAUSED"

    @patch("governance.services.agents.get_typedb_client", return_value=None)
    @patch("governance.services.agents.record_audit")
    def test_toggle_nonexistent_agent_returns_none(self, mock_audit, mock_client):
        """Toggling a non-existent agent returns None."""
        from governance.services.agents import toggle_agent_status
        result = toggle_agent_status("nonexistent-agent", source="test")
        assert result is None

    @patch("governance.services.agents.get_typedb_client", return_value=None)
    @patch("governance.services.agents.record_audit")
    def test_toggle_creates_audit_entry(self, mock_audit, mock_client):
        """Toggling records an audit entry."""
        from governance.services.agents import toggle_agent_status
        from governance.stores.agents import _agents_store

        _agents_store["code-agent"]["status"] = "PAUSED"
        toggle_agent_status("code-agent", source="test")

        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[0][0] == "UPDATE"
        assert call_args[0][1] == "agent"
        assert call_args[0][2] == "code-agent"
        assert call_args[1]["metadata"]["old"] == "PAUSED"
        assert call_args[1]["metadata"]["new"] == "ACTIVE"

    @patch("governance.services.agents.get_typedb_client", return_value=None)
    @patch("governance.services.agents.record_audit")
    def test_double_toggle_returns_to_original(self, mock_audit, mock_client):
        """Toggling twice returns to original status."""
        from governance.services.agents import toggle_agent_status
        from governance.stores.agents import _agents_store

        _agents_store["code-agent"]["status"] = "PAUSED"
        toggle_agent_status("code-agent", source="test")
        assert _agents_store["code-agent"]["status"] == "ACTIVE"
        toggle_agent_status("code-agent", source="test")
        assert _agents_store["code-agent"]["status"] == "PAUSED"


class TestToggleAgentStatusAPI:
    """Test the REST API endpoint for toggling agent status."""

    def test_route_exists(self):
        """PUT /agents/{agent_id}/status/toggle route is registered."""
        from governance.routes.agents.crud import router
        routes = [r.path for r in router.routes]
        assert "/agents/{agent_id}/status/toggle" in routes

    def test_route_method_is_put(self):
        """Toggle endpoint uses PUT method."""
        from governance.routes.agents.crud import router
        for route in router.routes:
            if route.path == "/agents/{agent_id}/status/toggle":
                assert "PUT" in route.methods
                break
        else:
            pytest.fail("Route not found")


class TestTrustControllerPauseTrigger:
    """Test that the toggle_agent_pause trigger is wired in trust controller."""

    def test_trust_controller_imports(self):
        """Trust controller module imports without error."""
        from agent.governance_ui.controllers.trust import register_trust_controllers
        assert register_trust_controllers is not None

    def test_trigger_registered(self):
        """toggle_agent_pause trigger is registered by trust controller."""
        from agent.governance_ui.controllers.trust import register_trust_controllers
        import inspect
        source = inspect.getsource(register_trust_controllers)
        assert "toggle_agent_pause" in source
        assert "toggle" in source.lower()
