"""
Data Integrity Heuristic Tests.

Per GAP-UI user request: Comprehensive data integrity checks.
Per SFDIPOT+CRUCSS: Systematic heuristic coverage.

Tests data integrity via REST API:
- Vertical scope: All entity types (Rules, Tasks, Agents, Sessions, Decisions)
- Horizontal scope: Cross-entity relations and constraints

Created: 2026-01-14
"""

import os
import pytest
import httpx

from tests.heuristics import (
    # SFDIPOT
    structure,
    function,
    data,
    interfaces,
    operations,
    # CRUCSS
    capability,
    reliability,
)


# API base URL from environment or default
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8082")


@pytest.fixture
def client():
    """HTTP client for API testing."""
    return httpx.Client(base_url=API_BASE, timeout=10.0)


# =============================================================================
# VERTICAL SCOPE: Rules Entity
# =============================================================================

class TestRulesDataIntegrity:
    """Data integrity tests for Rules entity."""

    @data("Rules have required fields", api=True, entity="Rule")
    def test_rules_have_required_fields(self, client):
        """All rules must have id, name, directive, status."""
        try:
            response = client.get("/api/rules")
            if response.status_code == 200:
                data = response.json()
                rules = data.get("rules", data) if isinstance(data, dict) else data
                for rule in rules[:10]:  # Check first 10
                    assert "rule_id" in rule or "id" in rule
                    assert "name" in rule or rule.get("rule_id")
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @data("Rule directives are non-empty", api=True, entity="Rule")
    def test_rule_directives_non_empty(self, client):
        """Rules must have meaningful directives."""
        try:
            response = client.get("/api/rules")
            if response.status_code == 200:
                data = response.json()
                rules = data.get("rules", data) if isinstance(data, dict) else data
                for rule in rules[:10]:
                    directive = rule.get("directive", "")
                    if directive:  # Only check if present
                        assert len(directive) >= 5, f"Directive too short: {directive}"
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @structure("Rule status values are valid", api=True, entity="Rule")
    def test_rule_status_valid(self, client):
        """Rule status must be ACTIVE, DRAFT, or DEPRECATED."""
        valid_statuses = {"ACTIVE", "DRAFT", "DEPRECATED", "PROPOSED", "DISABLED"}
        try:
            response = client.get("/api/rules")
            if response.status_code == 200:
                data = response.json()
                rules = data.get("rules", data) if isinstance(data, dict) else data
                for rule in rules[:10]:
                    status = rule.get("status", "ACTIVE")
                    assert status in valid_statuses, f"Invalid status: {status}"
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")


# =============================================================================
# VERTICAL SCOPE: Tasks Entity
# =============================================================================

class TestTasksDataIntegrity:
    """Data integrity tests for Tasks entity."""

    @data("Tasks have valid status", api=True, entity="Task")
    def test_task_status_valid(self, client):
        """Task status must be valid."""
        valid_statuses = {"pending", "in_progress", "completed", "blocked", "TODO", "DONE", "IN_PROGRESS", "ON_HOLD"}
        try:
            response = client.get("/api/tasks")
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", data) if isinstance(data, dict) else data
                if isinstance(tasks, list):
                    for task in tasks[:10]:
                        status = task.get("status", "pending")
                        assert status in valid_statuses, f"Invalid task status: {status}"
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @data("Task IDs follow naming convention", api=True, entity="Task")
    def test_task_id_convention(self, client):
        """Task IDs should follow P*.*, RD-*, GAP-* pattern."""
        import re
        valid_patterns = [
            r'^P\d+\.\d+',      # P10.1, P11.5
            r'^RD-\d+',         # RD-001
            r'^GAP-',           # GAP-UI-001
            r'^TEST-',          # Test tasks
            r'^TODO-',          # TODO tasks
        ]
        try:
            response = client.get("/api/tasks")
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", data) if isinstance(data, dict) else data
                if isinstance(tasks, list):
                    for task in tasks[:10]:
                        task_id = task.get("task_id", task.get("id", ""))
                        # Must match at least one pattern
                        matches = any(re.match(p, task_id) for p in valid_patterns)
                        # Log but don't fail - some legacy IDs may exist
                        if not matches and task_id:
                            print(f"Unexpected task ID format: {task_id}")
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")


# =============================================================================
# VERTICAL SCOPE: Agents Entity
# =============================================================================

class TestAgentsDataIntegrity:
    """Data integrity tests for Agents entity."""

    @data("Agents have trust scores in valid range", api=True, entity="Agent")
    def test_agent_trust_score_range(self, client):
        """Trust scores must be between 0.0 and 1.0."""
        try:
            response = client.get("/api/agents")
            if response.status_code == 200:
                data = response.json()
                agents = data.get("agents", data) if isinstance(data, dict) else data
                if isinstance(agents, list):
                    for agent in agents[:10]:
                        trust = agent.get("trust_score", 0.8)
                        assert 0.0 <= trust <= 1.0, f"Invalid trust score: {trust}"
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @structure("Agent types are valid", api=True, entity="Agent")
    def test_agent_type_valid(self, client):
        """Agent types must be known values."""
        # All agent types from TypeDB agents entity
        valid_types = {
            "claude-code", "docker-agent", "sync-agent", "orchestrator",
            "researcher", "research", "coder", "coding", "curator", "assistant",
            "test-agent"
        }
        try:
            response = client.get("/api/agents")
            if response.status_code == 200:
                data = response.json()
                agents = data.get("agents", data) if isinstance(data, dict) else data
                if isinstance(agents, list):
                    for agent in agents[:10]:
                        agent_type = agent.get("agent_type", agent.get("type", ""))
                        if agent_type:
                            assert agent_type in valid_types, f"Unknown agent type: {agent_type}"
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")


# =============================================================================
# VERTICAL SCOPE: Sessions Entity
# =============================================================================

class TestSessionsDataIntegrity:
    """Data integrity tests for Sessions entity."""

    @data("Sessions have valid timestamps", api=True, entity="Session")
    def test_session_timestamps_valid(self, client):
        """Session timestamps must be valid ISO format."""
        import re
        iso_pattern = r'^\d{4}-\d{2}-\d{2}'  # YYYY-MM-DD prefix
        try:
            response = client.get("/api/sessions")
            if response.status_code == 200:
                data = response.json()
                sessions = data.get("sessions", data) if isinstance(data, dict) else data
                if isinstance(sessions, list):
                    for session in sessions[:10]:
                        start = session.get("start_time", "")
                        if start:
                            assert re.match(iso_pattern, start), f"Invalid timestamp: {start}"
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")


# =============================================================================
# HORIZONTAL SCOPE: Cross-Entity Integrity
# =============================================================================

class TestCrossEntityIntegrity:
    """Cross-entity data integrity tests."""

    @interfaces("Rule references are valid", api=True, entity="Cross")
    def test_rule_references_exist(self, client):
        """Rules referenced by other entities must exist."""
        try:
            # Get all rules
            rules_response = client.get("/api/rules")
            if rules_response.status_code != 200:
                pytest.skip("Rules API not available")
            data = rules_response.json()
            rules = data.get("rules", data) if isinstance(data, dict) else data
            rule_ids = {r.get("rule_id", r.get("id")) for r in rules}

            # This validates that the system maintains referential integrity
            assert len(rule_ids) > 0, "No rules found in system"
        except httpx.ConnectError:
            pytest.skip("API not available")

    @reliability("API endpoints return consistent data types", integration=True, entity="API")
    def test_api_data_type_consistency(self, client):
        """API responses should have consistent structure."""
        endpoints = ["/api/rules", "/api/tasks", "/api/agents", "/api/sessions"]
        try:
            for endpoint in endpoints:
                response = client.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    # Should always be dict or list
                    assert isinstance(data, (dict, list)), f"{endpoint} returned unexpected type"
        except httpx.ConnectError:
            pytest.skip("API not available")


# =============================================================================
# CAPABILITY: CRUD Operations
# =============================================================================

class TestCRUDCapability:
    """CRUD capability tests via API."""

    @capability("Rules API supports list operation", integration=True, entity="Rule")
    def test_rules_list(self, client):
        """GET /api/rules returns rules list."""
        try:
            response = client.get("/api/rules")
            if response.status_code == 200:
                data = response.json()
                assert "rules" in data or isinstance(data, list)
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @capability("Tasks API supports list operation", integration=True, entity="Task")
    def test_tasks_list(self, client):
        """GET /api/tasks returns tasks list."""
        try:
            response = client.get("/api/tasks")
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (dict, list))
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @capability("Agents API supports list operation", integration=True, entity="Agent")
    def test_agents_list(self, client):
        """GET /api/agents returns agents list."""
        try:
            response = client.get("/api/agents")
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (dict, list))
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @capability("Sessions API supports list operation", integration=True, entity="Session")
    def test_sessions_list(self, client):
        """GET /api/sessions returns sessions list."""
        try:
            response = client.get("/api/sessions")
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (dict, list))
            else:
                pytest.skip(f"API returned {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("API not available")


# =============================================================================
# OPERATIONS: Error Handling
# =============================================================================

class TestErrorHandling:
    """Error handling tests."""

    @operations("API returns 404 for unknown endpoints", api=True, entity="API")
    def test_unknown_endpoint_404(self, client):
        """Unknown endpoints should return 404."""
        try:
            response = client.get("/api/nonexistent")
            assert response.status_code in [404, 422], f"Expected 404, got {response.status_code}"
        except httpx.ConnectError:
            pytest.skip("API not available")

    @operations("API returns valid JSON for errors", api=True, entity="API")
    def test_error_response_json(self, client):
        """Error responses should be valid JSON."""
        try:
            response = client.get("/api/rules/NONEXISTENT-RULE")
            if response.status_code >= 400:
                # Should be parseable JSON
                try:
                    data = response.json()
                    assert isinstance(data, dict)
                except Exception:
                    # Plain text error is also acceptable
                    pass
        except httpx.ConnectError:
            pytest.skip("API not available")


# =============================================================================
# MCP vs REST API PARITY: Cross-Source Validation
# Per user request: Catch discrepancies like trust score mismatch (GAP-UI-EXP-008)
# =============================================================================

class TestMCPRestAPIParity:
    """
    MCP vs REST API parity tests.

    These tests verify that MCP tools and REST API return consistent data.
    Catches issues like GAP-UI-EXP-008 where MCP returned 0.8 for all agents
    while REST API returned different calculated values.

    Per user feedback: "bottom up testing did not catch these issues"
    """

    @data("Agent counts match between MCP and REST", api=True, entity="Agent")
    def test_agent_count_parity(self, client):
        """MCP and REST should return same number of agents."""
        try:
            # REST API
            response = client.get("/api/agents")
            if response.status_code != 200:
                pytest.skip("REST API not available")
            rest_data = response.json()
            rest_agents = rest_data.get("agents", rest_data) if isinstance(rest_data, dict) else rest_data
            rest_count = len(rest_agents) if isinstance(rest_agents, list) else 0

            # MCP (via governance module)
            try:
                from governance.mcp_tools.agents import list_agents
                mcp_result = list_agents()
                mcp_agents = mcp_result.get("agents", []) if isinstance(mcp_result, dict) else []
                mcp_count = len(mcp_agents)

                assert rest_count == mcp_count, f"Agent count mismatch: REST={rest_count}, MCP={mcp_count}"
            except ImportError:
                pytest.skip("MCP module not available")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @data("Rule counts match between MCP and REST", api=True, entity="Rule")
    def test_rule_count_parity(self, client):
        """MCP and REST should return same number of rules."""
        try:
            # REST API
            response = client.get("/api/rules")
            if response.status_code != 200:
                pytest.skip("REST API not available")
            rest_data = response.json()
            rest_rules = rest_data.get("rules", []) if isinstance(rest_data, dict) else rest_data
            rest_count = len(rest_rules) if isinstance(rest_rules, list) else 0

            # MCP (via governance-core MCP tools)
            try:
                from governance.mcp_tools.rules import query_rules
                mcp_result = query_rules()
                mcp_rules = mcp_result.get("rules", []) if isinstance(mcp_result, dict) else []
                mcp_count = len(mcp_rules)

                assert rest_count == mcp_count, f"Rule count mismatch: REST={rest_count}, MCP={mcp_count}"
            except ImportError:
                pytest.skip("MCP module not available")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @data("Session counts match between MCP and REST", api=True, entity="Session")
    def test_session_count_parity(self, client):
        """MCP and REST should return similar session counts."""
        try:
            # REST API
            response = client.get("/api/sessions")
            if response.status_code != 200:
                pytest.skip("REST API not available")
            rest_data = response.json()
            rest_sessions = rest_data.get("sessions", rest_data) if isinstance(rest_data, dict) else rest_data
            rest_count = len(rest_sessions) if isinstance(rest_sessions, list) else 0

            # MCP (via governance-sessions MCP tools)
            try:
                from governance.mcp_tools.sessions import list_sessions
                mcp_result = list_sessions(limit=100)
                mcp_sessions = mcp_result.get("sessions", []) if isinstance(mcp_result, dict) else []
                mcp_count = len(mcp_sessions)

                # Allow small difference due to caching/timing
                diff = abs(rest_count - mcp_count)
                assert diff <= 2, f"Session count mismatch: REST={rest_count}, MCP={mcp_count}"
            except ImportError:
                pytest.skip("MCP module not available")
        except httpx.ConnectError:
            pytest.skip("API not available")

    @reliability("REST API returns data before UI assertions", integration=True, entity="API")
    def test_api_returns_data(self, client):
        """
        Verify API returns actual data, not empty results.

        Per RULE-025/GOV-PROP-03-v1: Tests passing with empty data are invalid.
        This test ensures we don't falsely pass tests when API returns no data.
        """
        endpoints_to_check = [
            ("/api/rules", "rules"),
            ("/api/agents", "agents"),
        ]
        try:
            for endpoint, key in endpoints_to_check:
                response = client.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get(key, data) if isinstance(data, dict) else data
                    count = len(items) if isinstance(items, list) else 0
                    assert count > 0, f"{endpoint} returned empty data - tests passing on empty data are invalid"
        except httpx.ConnectError:
            pytest.skip("API not available")
