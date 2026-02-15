"""Tests for Fix B: POST /api/agents endpoint.

Validates AgentCreate model, create_agent service, and POST route.
"""
from unittest.mock import MagicMock, patch
import pytest


def test_agent_create_model_validation():
    """AgentCreate model accepts valid input."""
    from governance.models import AgentCreate
    agent = AgentCreate(
        agent_id="gamedev-agent",
        name="Game Dev Agent",
        agent_type="gamedev",
        trust_score=0.85,
        capabilities=["godot", "shader"],
        rules=["TEST-GUARD-01"],
    )
    assert agent.agent_id == "gamedev-agent"
    assert agent.agent_type == "gamedev"
    assert agent.trust_score == 0.85


def test_agent_create_model_defaults():
    """AgentCreate model has sensible defaults."""
    from governance.models import AgentCreate
    agent = AgentCreate(agent_id="test-agent", name="Test")
    assert agent.agent_type == "custom"
    assert agent.trust_score == 0.8
    assert agent.capabilities == []
    assert agent.rules == []


@patch("governance.services.agents.get_typedb_client")
@patch("governance.services.agents.record_audit")
def test_create_agent_service_success(mock_audit, mock_client):
    """create_agent creates agent in memory and returns dict."""
    mock_client.return_value = None  # No TypeDB, pure in-memory

    from governance.services.agents import create_agent
    from governance.stores import _agents_store

    # Clean up if left from prior test
    _agents_store.pop("new-test-agent", None)

    result = create_agent(
        agent_id="new-test-agent",
        name="New Test Agent",
        agent_type="testing",
        trust_score=0.75,
        capabilities=["testing"],
        source="test",
    )

    assert result is not None
    assert result["agent_id"] == "new-test-agent"
    assert result["name"] == "New Test Agent"
    assert result["status"] == "PAUSED"
    mock_audit.assert_called_once()

    # Clean up
    _agents_store.pop("new-test-agent", None)


@patch("governance.services.agents.get_typedb_client")
@patch("governance.services.agents.record_audit")
def test_create_agent_duplicate_rejected(mock_audit, mock_client):
    """create_agent returns None for duplicate agent_id."""
    mock_client.return_value = None
    from governance.services.agents import create_agent
    from governance.stores import _agents_store

    _agents_store.pop("dupe-agent", None)

    # First creation succeeds
    result1 = create_agent(agent_id="dupe-agent", name="First", source="test")
    assert result1 is not None

    # Second creation fails (duplicate)
    result2 = create_agent(agent_id="dupe-agent", name="Second", source="test")
    assert result2 is None

    _agents_store.pop("dupe-agent", None)


@pytest.mark.asyncio
@patch("governance.services.agents.create_agent")
async def test_post_agents_route_success(mock_create):
    """POST /api/agents returns 201 on success."""
    mock_create.return_value = {
        "agent_id": "route-test",
        "name": "Route Test",
        "agent_type": "custom",
        "status": "PAUSED",
        "tasks_executed": 0,
        "trust_score": 0.8,
        "capabilities": [],
        "recent_sessions": [],
        "active_tasks": [],
    }
    from governance.routes.agents.crud import create_agent as route_create
    from governance.models import AgentCreate

    body = AgentCreate(agent_id="route-test", name="Route Test")
    result = await route_create(body)
    assert result.agent_id == "route-test"
    assert result.status == "PAUSED"


@pytest.mark.asyncio
@patch("governance.services.agents.create_agent")
async def test_post_agents_route_conflict(mock_create):
    """POST /api/agents returns 409 for duplicate."""
    mock_create.return_value = None  # Duplicate

    from governance.routes.agents.crud import create_agent as route_create
    from governance.models import AgentCreate
    from fastapi import HTTPException

    body = AgentCreate(agent_id="existing", name="Existing")
    with pytest.raises(HTTPException) as exc_info:
        await route_create(body)
    assert exc_info.value.status_code == 409
