"""
Agent CRUD Exports (GAP-FILE-007)
=================================
Agent backward compatibility exports for test imports.

Per RULE-012: DSP Semantic Code Structure
Per P10.4: MCP Tools for CRUD
Per GAP-FILE-007: Extracted from mcp_server.py

Created: 2024-12-28
"""

import json
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client
from governance.client import Agent


def governance_create_agent(agent_id, name, agent_type, trust_score=0.8):
    """Create agent (backward compat export)."""
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
        return json.dumps({"error": f"Failed to create agent {agent_id}"})
    finally:
        client.close()


def governance_get_agent(agent_id):
    """Get agent (backward compat export)."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})
        agent = client.get_agent(agent_id)
        if agent:
            return json.dumps(asdict(agent), indent=2)
        return json.dumps({"error": f"Agent {agent_id} not found"})
    finally:
        client.close()


def governance_list_agents():
    """List agents (backward compat export)."""
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


def governance_update_agent_trust(agent_id, trust_score):
    """Update agent trust (backward compat export)."""
    if not 0.0 <= trust_score <= 1.0:
        return json.dumps({"error": "Trust score must be between 0.0 and 1.0"})
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})
        success = client.update_agent_trust(agent_id=agent_id, trust_score=trust_score)
        if success:
            agent = client.get_agent(agent_id)
            if agent:
                result = asdict(agent)
                result["message"] = f"Agent {agent_id} trust updated to {trust_score}"
                return json.dumps(result, indent=2)
            return json.dumps({"agent_id": agent_id, "message": "Trust updated"}, indent=2)
        return json.dumps({"error": f"Failed to update agent {agent_id}"})
    finally:
        client.close()
