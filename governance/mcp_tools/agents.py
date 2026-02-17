"""Agents MCP Tools - Agent CRUD. Per RULE-011/012, DECISION-003."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client, format_mcp_result

# Monitoring instrumentation per GAP-MONITOR-INSTRUMENT-001
try:
    from agent.governance_ui.data_access.monitoring import log_monitor_event
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

def register_agent_tools(mcp) -> None:
    """Register agent-related MCP tools."""

    @mcp.tool()
    def agent_create(agent_id: str, name: str, agent_type: str,
                     trust_score: float = 0.8) -> str:
        """Create a new agent in TypeDB."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.insert_agent(
                agent_id=agent_id,
                name=name,
                agent_type=agent_type,
                trust_score=trust_score
            )

            if success:
                # Instrument agent creation
                if MONITORING_AVAILABLE:
                    log_monitor_event(
                        event_type="agent_event",
                        source="mcp-agent-create",
                        details={"agent_id": agent_id, "action": "create", "agent_type": agent_type, "trust_score": trust_score}
                    )
                return format_mcp_result({
                    "agent_id": agent_id,
                    "name": name,
                    "agent_type": agent_type,
                    "trust_score": trust_score,
                    "message": f"Agent {agent_id} created successfully"
                })
            else:
                return format_mcp_result({"error": f"Failed to create agent {agent_id}"})
        # BUG-192-001: Add except to prevent raw TypeDB errors to MCP caller
        except Exception as e:
            return format_mcp_result({"error": f"agent_create failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def agent_get(agent_id: str) -> str:
        """Get agent by ID from TypeDB."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            agent = client.get_agent(agent_id)
            if agent:
                # Instrument agent query
                if MONITORING_AVAILABLE:
                    log_monitor_event(
                        event_type="agent_event",
                        source="mcp-agent-get",
                        details={"agent_id": agent_id, "action": "query", "found": True}
                    )
                return format_mcp_result(asdict(agent))
            else:
                return format_mcp_result({"error": f"Agent {agent_id} not found"})
        # BUG-192-001: Add except to prevent raw TypeDB errors to MCP caller
        except Exception as e:
            return format_mcp_result({"error": f"agent_get failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def agents_list() -> str:
        """List all agents from TypeDB."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            agents = client.get_all_agents()
            return format_mcp_result({
                "agents": [asdict(a) for a in agents],
                "count": len(agents),
                "source": "typedb"
            })
        # BUG-192-001: Add except to prevent raw TypeDB errors to MCP caller
        except Exception as e:
            return format_mcp_result({"error": f"agents_list failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def agent_trust_update(agent_id: str, trust_score: float) -> str:
        """Update agent trust score."""
        if not 0.0 <= trust_score <= 1.0:
            return format_mcp_result({"error": "Trust score must be between 0.0 and 1.0"})

        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.update_agent_trust(
                agent_id=agent_id,
                trust_score=trust_score
            )

            if success:
                # Instrument trust update (important for monitoring)
                if MONITORING_AVAILABLE:
                    log_monitor_event(
                        event_type="trust_change",
                        source="mcp-agent-trust-update",
                        details={"agent_id": agent_id, "action": "trust_update", "new_trust": trust_score},
                        severity="WARNING"
                    )
                agent = client.get_agent(agent_id)
                if agent:
                    result = asdict(agent)
                    result["message"] = f"Agent {agent_id} trust updated to {trust_score}"
                    return format_mcp_result(result)
                return format_mcp_result({
                    "agent_id": agent_id,
                    "trust_score": trust_score,
                    "message": f"Agent {agent_id} trust updated"
                })
            else:
                return format_mcp_result({"error": f"Failed to update agent {agent_id}"})
        # BUG-192-001: Add except to prevent raw TypeDB errors to MCP caller
        except Exception as e:
            return format_mcp_result({"error": f"agent_trust_update failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def agents_dashboard() -> str:
        """Get agent dashboard with stats and summaries."""
        from governance.orchestrator.handoff import get_pending_handoffs

        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

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
            except Exception as e:
                logger.debug(f"Failed to get pending handoffs: {e}")
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

            return format_mcp_result(dashboard)
        # BUG-192-001: Add except to prevent raw TypeDB errors to MCP caller
        except Exception as e:
            return format_mcp_result({"error": f"agents_dashboard failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def agent_activity(agent_id: Optional[str] = None, limit: int = 10) -> str:
        """Get agent activity (tasks executed)."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # Get tasks linked to agents
            query = """
                match
                $task isa task, has task-id $tid, has name $name, has status $status;
                $agent isa agent, has agent-id $aid;
                (executor: $agent, executed: $task) isa task-execution;
            """
            if agent_id:
                # BUG-342-AGT-001: Escape backslash FIRST then quotes (canonical two-step
                # TypeQL escape — previous version missed backslash, allowing malformed literals)
                agent_id_escaped = agent_id.replace('\\', '\\\\').replace('"', '\\"')
                query += f'$agent has agent-id "{agent_id_escaped}";'

            query += """
                fetch
                $tid; $name; $status; $aid;
            """

            results = client.execute_fetch(query)

            activities = []
            # BUG-MCP-001: Null-safe — execute_fetch may return None
            for r in (results or [])[:limit]:
                activities.append({
                    "task_id": r.get("tid", {}).get("value", ""),
                    "task_name": r.get("name", {}).get("value", ""),
                    "status": r.get("status", {}).get("value", ""),
                    "agent_id": r.get("aid", {}).get("value", "")
                })

            return format_mcp_result({
                "activities": activities,
                "count": len(activities),
                "filter": agent_id or "all"
            })
        except Exception as e:
            logger.debug(f"Agent activity query failed: {e}")
            return format_mcp_result({
                "activities": [],
                "count": 0,
                "filter": agent_id or "all",
                "note": "No task-execution relations found in TypeDB"
            })
        finally:
            client.close()
