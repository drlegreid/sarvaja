"""
Agents MCP Tools
================
Agent CRUD operations for P10.4 - TypeDB Integration.

Per RULE-012: DSP Semantic Code Structure
Per DECISION-003: TypeDB-First Strategy
Per RULE-011: Multi-Agent Governance
"""

import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client


def register_agent_tools(mcp) -> None:
    """Register agent-related MCP tools."""

    @mcp.tool()
    def governance_create_agent(
        agent_id: str,
        name: str,
        agent_type: str,
        trust_score: float = 0.8
    ) -> str:
        """
        Create a new agent in TypeDB.

        Args:
            agent_id: Agent ID (e.g., "claude-code", "sync-agent")
            name: Agent display name
            agent_type: Agent type (claude-code, docker-agent, sync-agent)
            trust_score: Initial trust score (0.0 to 1.0)

        Returns:
            JSON object with created agent confirmation
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.insert_agent(
                agent_id=agent_id,
                name=name,
                agent_type=agent_type,
                trust_score=trust_score
            )

            if success:
                return json.dumps({
                    "agent_id": agent_id,
                    "name": name,
                    "agent_type": agent_type,
                    "trust_score": trust_score,
                    "message": f"Agent {agent_id} created successfully"
                }, indent=2)
            else:
                return json.dumps({"error": f"Failed to create agent {agent_id}"})
        finally:
            client.close()

    @mcp.tool()
    def governance_get_agent(agent_id: str) -> str:
        """
        Get a specific agent by ID from TypeDB.

        Args:
            agent_id: Agent ID

        Returns:
            JSON object with agent details or error if not found
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            agent = client.get_agent(agent_id)
            if agent:
                return json.dumps(asdict(agent), indent=2)
            else:
                return json.dumps({"error": f"Agent {agent_id} not found"})
        finally:
            client.close()

    @mcp.tool()
    def governance_list_agents() -> str:
        """
        List all agents from TypeDB.

        Returns:
            JSON array of all agents with ID, name, type, trust score
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            agents = client.get_all_agents()
            return json.dumps({
                "agents": [asdict(a) for a in agents],
                "count": len(agents),
                "source": "typedb"
            }, indent=2)
        finally:
            client.close()

    @mcp.tool()
    def governance_update_agent_trust(
        agent_id: str,
        trust_score: float
    ) -> str:
        """
        Update an agent's trust score in TypeDB.

        Args:
            agent_id: Agent ID to update
            trust_score: New trust score (0.0 to 1.0)

        Returns:
            JSON object with updated agent confirmation
        """
        if not 0.0 <= trust_score <= 1.0:
            return json.dumps({"error": "Trust score must be between 0.0 and 1.0"})

        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.update_agent_trust(
                agent_id=agent_id,
                trust_score=trust_score
            )

            if success:
                agent = client.get_agent(agent_id)
                if agent:
                    result = asdict(agent)
                    result["message"] = f"Agent {agent_id} trust updated to {trust_score}"
                    return json.dumps(result, indent=2)
                return json.dumps({
                    "agent_id": agent_id,
                    "trust_score": trust_score,
                    "message": f"Agent {agent_id} trust updated"
                }, indent=2)
            else:
                return json.dumps({"error": f"Failed to update agent {agent_id}"})
        finally:
            client.close()
