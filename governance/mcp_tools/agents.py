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
                return json.dumps(asdict(agent), indent=2, default=str)
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
            }, indent=2, default=str)
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
                    return json.dumps(result, indent=2, default=str)
                return json.dumps({
                    "agent_id": agent_id,
                    "trust_score": trust_score,
                    "message": f"Agent {agent_id} trust updated"
                }, indent=2)
            else:
                return json.dumps({"error": f"Failed to update agent {agent_id}"})
        finally:
            client.close()

    @mcp.tool()
    def governance_agent_dashboard() -> str:
        """
        Get agent observability dashboard.

        Returns summary of all agents including:
        - Active agent count
        - Task execution stats
        - Trust score distribution
        - Handoff flow status

        Per GAP-006: Agent observability for functional platform.

        Returns:
            JSON object with agent dashboard data
        """
        from governance.orchestrator.handoff import get_pending_handoffs

        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            agents = client.get_all_agents()

            # Compute stats
            active_agents = [a for a in agents if getattr(a, 'status', 'ACTIVE') == 'ACTIVE']
            trust_scores = [a.trust_score for a in agents if hasattr(a, 'trust_score')]
            avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0

            # Get task execution counts
            total_tasks = sum(getattr(a, 'tasks_executed', 0) for a in agents)

            # Get pending handoffs count
            try:
                handoffs = get_pending_handoffs()
                pending_handoffs = len(handoffs)
            except Exception:
                pending_handoffs = 0

            # Build dashboard
            dashboard = {
                "summary": {
                    "total_agents": len(agents),
                    "active_agents": len(active_agents),
                    "avg_trust_score": round(avg_trust, 2),
                    "total_tasks_executed": total_tasks,
                    "pending_handoffs": pending_handoffs
                },
                "agents": [
                    {
                        "id": a.id,
                        "name": getattr(a, 'name', a.id),
                        "type": getattr(a, 'agent_type', 'unknown'),
                        "trust": a.trust_score,
                        "tasks": getattr(a, 'tasks_executed', 0),
                        "last_active": str(getattr(a, 'last_active', None))
                    }
                    for a in agents
                ],
                "trust_distribution": {
                    "high": len([a for a in agents if a.trust_score >= 0.8]),
                    "medium": len([a for a in agents if 0.5 <= a.trust_score < 0.8]),
                    "low": len([a for a in agents if a.trust_score < 0.5])
                }
            }

            return json.dumps(dashboard, indent=2, default=str)
        finally:
            client.close()

    @mcp.tool()
    def governance_agent_activity(agent_id: Optional[str] = None, limit: int = 10) -> str:
        """
        Get recent agent activity (tasks executed, handoffs processed).

        Args:
            agent_id: Optional agent ID to filter by (None = all agents)
            limit: Maximum number of activities to return (default: 10)

        Returns:
            JSON array of recent agent activities
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            # Get tasks linked to agents
            query = """
                match
                $task isa task, has task-id $tid, has name $name, has status $status;
                $agent isa agent, has agent-id $aid;
                (executor: $agent, executed: $task) isa task-execution;
            """
            if agent_id:
                query += f'$agent has agent-id "{agent_id}";'

            query += """
                fetch
                $tid; $name; $status; $aid;
            """

            results = client.execute_fetch(query)

            activities = []
            for r in results[:limit]:
                activities.append({
                    "task_id": r.get("tid", {}).get("value", ""),
                    "task_name": r.get("name", {}).get("value", ""),
                    "status": r.get("status", {}).get("value", ""),
                    "agent_id": r.get("aid", {}).get("value", "")
                })

            return json.dumps({
                "activities": activities,
                "count": len(activities),
                "filter": agent_id or "all"
            }, indent=2)
        except Exception as e:
            # If relation doesn't exist, return empty
            return json.dumps({
                "activities": [],
                "count": 0,
                "filter": agent_id or "all",
                "note": "No task-execution relations found in TypeDB"
            }, indent=2)
        finally:
            client.close()
