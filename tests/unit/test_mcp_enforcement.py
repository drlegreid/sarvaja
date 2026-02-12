"""
Tests for MCP usage enforcement and readiness.

Verifies:
- All service layers exist and are used by REST routes
- MCP server metadata is complete for all servers
- REST routes delegate to service layer (not direct TypeDB)
- MCP readiness endpoint works

Created: 2026-02-01
Updated: 2026-02-01 - Added sessions/rules/agents service layer tests
"""
import pytest
import inspect
from unittest.mock import patch, MagicMock


class TestTaskServiceLayer:
    """Verify task service layer is properly integrated."""

    def test_service_module_exists(self):
        """governance.services.tasks module should be importable."""
        from governance.services import tasks
        assert hasattr(tasks, 'create_task')
        assert hasattr(tasks, 'get_task')
        assert hasattr(tasks, 'update_task')
        assert hasattr(tasks, 'delete_task')
        assert hasattr(tasks, 'list_tasks')

    def test_service_has_monitoring(self):
        """Service layer should include MCP monitoring."""
        from governance.services import tasks
        source = inspect.getsource(tasks)
        assert 'log_monitor_event' in source
        assert '_monitor' in source

    def test_service_has_audit(self):
        """Service layer should record audit events."""
        from governance.services import tasks
        source = inspect.getsource(tasks)
        assert 'record_audit' in source

    def test_service_has_source_tracking(self):
        """Service layer should track operation source (rest/mcp)."""
        from governance.services import tasks
        source = inspect.getsource(tasks)
        assert 'source' in source

    def test_crud_routes_use_service(self):
        """REST task routes should delegate to service layer."""
        from governance.routes.tasks import crud
        source = inspect.getsource(crud)
        assert 'task_service' in source
        assert 'governance.services' in source
        # Should NOT have direct TypeDB calls
        assert 'get_typedb_client()' not in source
        assert 'client.insert_task' not in source


class TestSessionServiceLayer:
    """Verify session service layer is properly integrated."""

    def test_service_module_exists(self):
        """governance.services.sessions module should be importable."""
        from governance.services import sessions
        assert hasattr(sessions, 'create_session')
        assert hasattr(sessions, 'get_session')
        assert hasattr(sessions, 'update_session')
        assert hasattr(sessions, 'delete_session')
        assert hasattr(sessions, 'list_sessions')
        assert hasattr(sessions, 'end_session')

    def test_service_has_monitoring(self):
        """Session service should include MCP monitoring."""
        from governance.services import sessions
        source = inspect.getsource(sessions)
        assert 'log_monitor_event' in source
        assert '_monitor' in source

    def test_service_has_audit(self):
        """Session service should record audit events."""
        from governance.services import sessions
        source = inspect.getsource(sessions)
        assert 'record_audit' in source

    def test_crud_routes_use_service(self):
        """REST session routes should delegate to service layer."""
        from governance.routes.sessions import crud
        source = inspect.getsource(crud)
        assert 'session_service' in source
        assert 'governance.services' in source
        assert 'get_typedb_client()' not in source
        assert 'client.insert_session' not in source


class TestRuleServiceLayer:
    """Verify rule service layer is properly integrated."""

    def test_service_module_exists(self):
        """governance.services.rules module should be importable."""
        from governance.services import rules
        assert hasattr(rules, 'create_rule')
        assert hasattr(rules, 'get_rule')
        assert hasattr(rules, 'update_rule')
        assert hasattr(rules, 'delete_rule')
        assert hasattr(rules, 'list_rules')

    def test_service_has_monitoring(self):
        """Rule service should include MCP monitoring."""
        from governance.services import rules
        source = inspect.getsource(rules)
        assert 'log_monitor_event' in source
        assert '_monitor' in source

    def test_service_has_audit(self):
        """Rule service should record audit events."""
        from governance.services import rules
        source = inspect.getsource(rules)
        assert 'record_audit' in source

    def test_crud_routes_use_service(self):
        """REST rule routes should delegate to service layer."""
        from governance.routes.rules import crud
        source = inspect.getsource(crud)
        assert 'rule_service' in source
        assert 'governance.services' in source
        assert 'get_client()' not in source
        assert 'client.get_all_rules' not in source


class TestAgentServiceLayer:
    """Verify agent service layer is properly integrated."""

    def test_service_module_exists(self):
        """governance.services.agents module should be importable."""
        from governance.services import agents
        assert hasattr(agents, 'list_agents')
        assert hasattr(agents, 'get_agent')
        assert hasattr(agents, 'delete_agent')
        assert hasattr(agents, 'record_task_execution')

    def test_service_has_monitoring(self):
        """Agent service should include MCP monitoring."""
        from governance.services import agents
        source = inspect.getsource(agents)
        assert 'log_monitor_event' in source
        assert '_monitor' in source

    def test_service_has_audit(self):
        """Agent service should record audit events."""
        from governance.services import agents
        source = inspect.getsource(agents)
        assert 'record_audit' in source

    def test_crud_routes_use_service(self):
        """REST agent routes should delegate to service layer."""
        from governance.routes.agents import crud
        source = inspect.getsource(crud)
        assert 'agent_service' in source
        assert 'governance.services' in source
        assert 'get_typedb_client()' not in source
        assert '_agents_store' not in source


class TestMCPServerMeta:
    """Verify MCP server metadata is complete."""

    def test_all_servers_have_metadata(self):
        """Every MCP server should have metadata entry."""
        from agent.governance_ui.controllers.infra import MCP_SERVERS, MCP_SERVER_META
        for name in MCP_SERVERS:
            assert name in MCP_SERVER_META, f"Missing metadata for {name}"

    def test_metadata_has_required_fields(self):
        """Each server metadata should have tools, depends_on, desc."""
        from agent.governance_ui.controllers.infra import MCP_SERVER_META
        for name, meta in MCP_SERVER_META.items():
            assert 'tools' in meta, f"{name} missing 'tools'"
            assert 'depends_on' in meta, f"{name} missing 'depends_on'"
            assert 'desc' in meta, f"{name} missing 'desc'"
            assert meta['tools'] > 0, f"{name} has 0 tools"

    def test_gov_tasks_tools_count(self):
        """gov-tasks should have substantial tool count."""
        from agent.governance_ui.controllers.infra import MCP_SERVER_META
        assert MCP_SERVER_META["gov-tasks"]["tools"] >= 20

    def test_gov_sessions_tools_count(self):
        """gov-sessions should have substantial tool count."""
        from agent.governance_ui.controllers.infra import MCP_SERVER_META
        assert MCP_SERVER_META["gov-sessions"]["tools"] >= 25


class TestMCPReadinessEndpoint:
    """Test the MCP readiness API endpoint."""

    def test_endpoint_exists(self):
        """GET /api/mcp/readiness should exist."""
        from governance.api import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/api/mcp/readiness")
        assert response.status_code == 200

    def test_response_structure(self):
        """Response should have status, backends, mcp_servers, service_layer."""
        from governance.api import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        data = client.get("/api/mcp/readiness").json()
        assert "status" in data
        assert "backends" in data
        assert "mcp_servers" in data
        assert "service_layer" in data
        assert "total_tools" in data

    def test_all_service_layers_detected(self):
        """Service layer audit should detect all 4 service layers."""
        from governance.api import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        data = client.get("/api/mcp/readiness").json()
        for domain in ("tasks", "sessions", "rules", "agents"):
            assert data["service_layer"][domain] == "SERVICE_LAYER", \
                f"{domain} not detected as SERVICE_LAYER"


class TestAgentDefaults:
    """Verify agent default status configuration."""

    def test_all_agents_paused_by_default(self):
        """All agents should be PAUSED by default. Per GAP-AGENT-PAUSE-001."""
        from governance.stores.agents import get_all_agents
        agents = get_all_agents()
        paused = [a for a in agents if a["status"] == "PAUSED"]
        assert len(paused) == len(agents), (
            f"Expected all {len(agents)} agents PAUSED, got {len(paused)}"
        )

    def test_code_agent_has_workflow_config(self):
        """code-agent should have description and model from agents.yaml."""
        from governance.stores.agents import get_agent
        agent = get_agent("code-agent")
        assert agent is not None
        assert agent.get("description"), "code-agent missing description"
        assert agent.get("model"), "code-agent missing model"


class TestMCPReadinessContainerAware:
    """GAP-MCP-READINESS-001: Backend checks must be container-aware."""

    def test_readiness_uses_container_host_in_container(self):
        """In-container: should check container hostnames, not localhost."""
        from governance.api_startup import mcp_readiness_handler

        with patch("agent.governance_ui.controllers.infra.is_in_container", return_value=True), \
             patch("agent.governance_ui.controllers.infra.check_port") as mock_port:
            mock_port.return_value = True
            result = mcp_readiness_handler()

        # Should have checked container hostnames (typedb, chromadb, etc.)
        hostnames_checked = [call[0][0] for call in mock_port.call_args_list]
        assert "typedb" in hostnames_checked, f"Expected 'typedb' in {hostnames_checked}"
        assert "chromadb" in hostnames_checked, f"Expected 'chromadb' in {hostnames_checked}"
        assert result["status"] == "READY"

    def test_readiness_uses_localhost_on_host(self):
        """On host: should check localhost with host ports."""
        from governance.api_startup import mcp_readiness_handler

        with patch("agent.governance_ui.controllers.infra.is_in_container", return_value=False), \
             patch("agent.governance_ui.controllers.infra.check_port") as mock_port:
            mock_port.return_value = True
            result = mcp_readiness_handler()

        hostnames_checked = [call[0][0] for call in mock_port.call_args_list]
        assert all(h == "localhost" for h in hostnames_checked), \
            f"Expected all 'localhost', got {hostnames_checked}"
        assert result["status"] == "READY"

    def test_get_mcp_server_details_container_aware(self):
        """get_mcp_server_details uses container hosts when in container."""
        from agent.governance_ui.controllers.infra import get_mcp_server_details

        with patch("agent.governance_ui.controllers.infra.is_in_container", return_value=True), \
             patch("agent.governance_ui.controllers.infra.check_port", return_value=True) as mock_port:
            get_mcp_server_details()

        hostnames_checked = [call[0][0] for call in mock_port.call_args_list]
        assert "typedb" in hostnames_checked
        assert "chromadb" in hostnames_checked
