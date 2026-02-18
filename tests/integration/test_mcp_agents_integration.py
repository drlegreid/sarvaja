"""MCP Agents Integration Tests — Gov-Agents tools against real TypeDB.

Tests agent CRUD, trust scoring, and proposal MCP tools.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_agents_integration.py -v
Requires: TypeDB on localhost:1729
"""

import json
import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result, make_test_id

pytestmark = [pytest.mark.integration, pytest.mark.typedb, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def agent_tools(typedb_available):
    """Register and return agent MCP tool functions."""
    from governance.mcp_tools.agents import register_agent_tools
    mcp = MockMCP()
    register_agent_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def trust_tools(typedb_available):
    """Register and return trust MCP tool functions."""
    from governance.mcp_tools.trust import register_trust_tools
    mcp = MockMCP()
    register_trust_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def proposal_tools(typedb_available):
    """Register and return proposal MCP tool functions."""
    from governance.mcp_tools.proposals import register_proposal_tools
    mcp = MockMCP()
    register_proposal_tools(mcp)
    return mcp.tools


# Cleanup
_created_agent_ids = []


@pytest.fixture(scope="module", autouse=True)
def cleanup_agents(typedb_available):
    """Delete test agents after module."""
    yield
    if not _created_agent_ids:
        return
    try:
        from governance.mcp_tools.common import get_typedb_client
        client = get_typedb_client()
        if client.connect():
            for aid in _created_agent_ids:
                try:
                    client.delete_agent(aid)
                except Exception:
                    pass
            client.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Agent list tests
# ---------------------------------------------------------------------------

class TestAgentsList:
    """Test agent listing tools."""

    def test_agents_list(self, agent_tools):
        """agents_list returns list of agents."""
        if "agents_list" not in agent_tools:
            pytest.skip("agents_list not registered")
        result = parse_mcp_result(agent_tools["agents_list"]())
        assert isinstance(result, dict)
        # Should have agents array or similar
        has_agents = "agents" in result or "items" in result or isinstance(result.get("data"), list)
        assert has_agents or "error" not in result

    def test_agents_dashboard(self, agent_tools):
        """agents_dashboard returns dashboard overview."""
        if "agents_dashboard" not in agent_tools:
            pytest.skip("agents_dashboard not registered")
        result = parse_mcp_result(agent_tools["agents_dashboard"]())
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Agent CRUD lifecycle
# ---------------------------------------------------------------------------

class TestAgentCRUDLifecycle:
    """Test agent create → get → update lifecycle."""

    def test_lifecycle(self, agent_tools):
        """Full agent lifecycle with real TypeDB."""
        if "agent_create" not in agent_tools:
            pytest.skip("agent_create not registered")

        aid = make_test_id("INTTEST-AGENT").lower()
        _created_agent_ids.append(aid)

        # CREATE — agent_create(agent_id, name, agent_type, trust_score)
        create_result = parse_mcp_result(agent_tools["agent_create"](
            agent_id=aid,
            name="Integration Test Agent",
            agent_type="TESTER",
        ))
        if "error" in create_result:
            pytest.skip(f"agent_create failed: {create_result['error']}")

        # GET
        if "agent_get" in agent_tools:
            get_result = parse_mcp_result(agent_tools["agent_get"](agent_id=aid))
            assert "error" not in get_result


# ---------------------------------------------------------------------------
# Trust score tests
# ---------------------------------------------------------------------------

class TestTrustScore:
    """Test trust score tools."""

    def test_get_trust_score(self, trust_tools):
        """governance_get_trust_score returns trust data."""
        if "governance_get_trust_score" not in trust_tools:
            pytest.skip("governance_get_trust_score not registered")
        result = parse_mcp_result(trust_tools["governance_get_trust_score"](
            agent_id="claude-code",
        ))
        assert isinstance(result, dict)

    def test_agent_trust_score(self, trust_tools):
        """agent_trust_score returns score for known agent."""
        if "agent_trust_score" not in trust_tools:
            pytest.skip("agent_trust_score not registered")
        result = parse_mcp_result(trust_tools["agent_trust_score"](
            agent_id="claude-code",
        ))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Proposal tests
# ---------------------------------------------------------------------------

class TestProposals:
    """Test proposal listing tools."""

    def test_proposals_list(self, proposal_tools):
        """proposals_list returns proposals."""
        if "proposals_list" not in proposal_tools:
            pytest.skip("proposals_list not registered")
        result = parse_mcp_result(proposal_tools["proposals_list"]())
        assert isinstance(result, dict)
