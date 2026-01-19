"""Agents MCP Tools - Agent CRUD. Per RULE-011/012, DECISION-003."""

import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client

def register_agent_tools(mcp) -> None:
    """Register agent-related MCP tools."""

    @mcp.tool()
    def agent_create(agent_id: str, name: str, agent_type: str,
                     trust_score: float = 0.8) -> str:
        """Create a new agent in TypeDB."""
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
    def agent_get(agent_id: str) -> str:
        """Get agent by ID from TypeDB."""
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
    def agents_list() -> str:
        """List all agents from TypeDB."""
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
    def agent_trust_update(agent_id: str, trust_score: float) -> str:
        """Update agent trust score."""
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
    def agents_dashboard() -> str:
        """Get agent dashboard with stats and summaries."""
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
    def agent_activity(agent_id: Optional[str] = None, limit: int = 10) -> str:
        """Get agent activity (tasks executed)."""
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
        except Exception:
            # If relation doesn't exist, return empty
            return json.dumps({
                "activities": [],
                "count": 0,
                "filter": agent_id or "all",
                "note": "No task-execution relations found in TypeDB"
            }, indent=2)
        finally:
            client.close()
