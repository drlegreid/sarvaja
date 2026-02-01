"""Agent Service Layer - Single code path for all agent operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.

Created: 2026-02-01
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from governance.stores import (
    get_typedb_client,
    _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score,
)
from governance.stores.audit import record_audit

logger = logging.getLogger(__name__)


def _monitor(action: str, agent_id: str, source: str = "service", **extra):
    """Log agent monitoring event for MCP compliance."""
    try:
        from governance.mcp_tools.common import log_monitor_event
        log_monitor_event(
            event_type="agent_event",
            source=source,
            details={"agent_id": agent_id, "action": action, **extra},
            severity="INFO",
        )
    except Exception:
        pass


def _build_relations_lookup(client) -> Tuple[dict, dict, dict]:
    """Build lookup dicts for agent relations in a single batch."""
    from governance.routes.agents.helpers import (
        build_agent_relations_lookup,
    )
    return build_agent_relations_lookup(client)


def _get_relations(agent_id: str, sessions_by_agent, tasks_by_agent, task_count_by_agent):
    """Get agent's relations from pre-built lookup dicts."""
    from governance.routes.agents.helpers import get_agent_relations_from_lookup
    return get_agent_relations_from_lookup(
        agent_id, sessions_by_agent, tasks_by_agent, task_count_by_agent
    )


def _agent_to_dict(
    agent_id: str,
    name: str,
    agent_type: str,
    status: str,
    tasks_executed: int,
    trust_score: float,
    last_active: Optional[str] = None,
    capabilities: Optional[List[str]] = None,
    recent_sessions: Optional[List[str]] = None,
    active_tasks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build standardized agent response dict."""
    return {
        "agent_id": agent_id,
        "name": name,
        "agent_type": agent_type,
        "status": status,
        "tasks_executed": tasks_executed,
        "trust_score": trust_score,
        "last_active": last_active,
        "capabilities": capabilities or [],
        "recent_sessions": recent_sessions or [],
        "active_tasks": active_tasks or [],
    }


def list_agents(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "trust_score",
    order: str = "desc",
    offset: int = 0,
    limit: int = 50,
    source: str = "rest",
) -> Dict[str, Any]:
    """List agents with pagination, sorting, and filtering.

    Returns:
        Dict with 'items' (list of agent dicts) and pagination metadata.
    """
    client = get_typedb_client()

    if client:
        try:
            typedb_agents = client.get_all_agents()
            if typedb_agents:
                metrics = _load_agent_metrics()
                sessions_by_agent, tasks_by_agent, task_count_by_agent = _build_relations_lookup(client)

                result = []
                for agent in typedb_agents:
                    agent_metrics = metrics.get(agent.id, {})
                    last_active = agent_metrics.get("last_active", None)
                    base_trust = _AGENT_BASE_CONFIG.get(agent.id, {}).get("base_trust", agent.trust_score or 0.8)

                    recent_sessions, active_tasks, task_count = _get_relations(
                        agent.id, sessions_by_agent, tasks_by_agent, task_count_by_agent
                    )
                    store_count = _agents_store.get(agent.id, {}).get("tasks_executed", 0)
                    tasks_executed = task_count or store_count or agent_metrics.get("tasks_executed", 0)
                    capabilities = _AGENT_BASE_CONFIG.get(agent.id, {}).get("capabilities", [])

                    result.append(_agent_to_dict(
                        agent_id=agent.id, name=agent.name,
                        agent_type=agent.agent_type,
                        status=agent.status or "ACTIVE",
                        tasks_executed=tasks_executed,
                        trust_score=_calculate_trust_score(agent.id, tasks_executed, base_trust),
                        last_active=last_active, capabilities=capabilities,
                        recent_sessions=recent_sessions, active_tasks=active_tasks,
                    ))

                if agent_type:
                    result = [a for a in result if a["agent_type"] == agent_type]
                if status:
                    result = [a for a in result if a["status"] == status]

                valid_sort_fields = ["agent_id", "name", "trust_score", "status", "tasks_executed"]
                sort_field = sort_by if sort_by in valid_sort_fields else "trust_score"
                result.sort(key=lambda a: a.get(sort_field) or "", reverse=order.lower() == "desc")

                total = len(result)
                paginated = result[offset: offset + limit]
                return {
                    "items": paginated,
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + limit) < total,
                }
        except Exception as e:
            logger.warning(f"TypeDB agents query failed, using fallback: {e}")

    # Fallback to in-memory
    agents = list(_agents_store.values())
    total = len(agents)
    paginated = agents[offset: offset + limit]
    return {
        "items": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
    }


def get_agent(agent_id: str, source: str = "rest") -> Optional[Dict[str, Any]]:
    """Get a specific agent by ID.

    Returns:
        Agent dict or None if not found.
    """
    client = get_typedb_client()

    if client:
        try:
            agent = client.get_agent(agent_id)
            if agent:
                if agent_id in _agents_store:
                    last_active = _agents_store[agent_id].get("last_active", None)
                else:
                    metrics = _load_agent_metrics()
                    last_active = metrics.get(agent_id, {}).get("last_active", None)

                base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", agent.trust_score or 0.8)
                sessions_by_agent, tasks_by_agent, task_count_by_agent = _build_relations_lookup(client)
                recent_sessions, active_tasks, task_count = _get_relations(
                    agent_id, sessions_by_agent, tasks_by_agent, task_count_by_agent
                )
                capabilities = _AGENT_BASE_CONFIG.get(agent_id, {}).get("capabilities", [])

                return _agent_to_dict(
                    agent_id=agent.id, name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent.status or "ACTIVE",
                    tasks_executed=task_count,
                    trust_score=_calculate_trust_score(agent_id, task_count, base_trust),
                    last_active=last_active, capabilities=capabilities,
                    recent_sessions=recent_sessions, active_tasks=active_tasks,
                )
        except Exception as e:
            logger.warning(f"TypeDB agent query failed, using fallback: {e}")

    if agent_id in _agents_store:
        return dict(_agents_store[agent_id])
    return None


def delete_agent(agent_id: str, source: str = "rest") -> bool:
    """Delete an agent from TypeDB and in-memory store.

    Returns:
        True if deleted, False if not found.
    """
    deleted = False
    client = get_typedb_client()
    if client:
        try:
            existing = client.get_agent(agent_id)
            if existing and client.delete_agent(agent_id):
                deleted = True
        except Exception as e:
            logger.warning(f"TypeDB delete failed for agent {agent_id}: {e}")

    if agent_id in _agents_store:
        _agents_store.pop(agent_id, None)
        deleted = True

    if deleted:
        record_audit("DELETE", "agent", agent_id, metadata={"source": source})
        _monitor("delete", agent_id, source=source)
    return deleted


def record_task_execution(agent_id: str, source: str = "rest") -> Optional[Dict[str, Any]]:
    """Record that an agent executed a task. Persists metrics and recalculates trust.

    Returns:
        Updated agent dict or None if not found.
    """
    client = get_typedb_client()
    now = datetime.now().isoformat()

    # Get TypeDB task count as base
    typedb_count = 0
    if client:
        try:
            _, _, task_count_by_agent = _build_relations_lookup(client)
            typedb_count = task_count_by_agent.get(agent_id, 0)
        except Exception:
            pass
    tasks_executed = typedb_count + 1

    base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", 0.85)
    new_trust_score = _calculate_trust_score(agent_id, tasks_executed, base_trust)

    # Update TypeDB
    if client:
        try:
            client.update_agent_trust(agent_id, new_trust_score)
        except Exception as e:
            logger.warning(f"Failed to update TypeDB trust for {agent_id}: {e}")

    # Update in-memory store
    if agent_id not in _agents_store:
        _agents_store[agent_id] = {"agent_id": agent_id, "name": agent_id, "tasks_executed": 0}
    _agents_store[agent_id]["tasks_executed"] = tasks_executed
    _agents_store[agent_id]["last_active"] = now
    _agents_store[agent_id]["trust_score"] = new_trust_score

    # Persist metrics to JSON
    try:
        metrics = _load_agent_metrics()
        metrics[agent_id] = {"tasks_executed": tasks_executed, "last_active": now}
        _save_agent_metrics(metrics)
    except Exception as e:
        logger.warning(f"Failed to persist agent metrics (non-critical): {e}")

    _monitor("record_task", agent_id, source=source, tasks_executed=tasks_executed)

    # Return enriched response
    if client:
        try:
            agent = client.get_agent(agent_id)
            if agent:
                sessions_by_agent, tasks_by_agent, task_count_by_agent = _build_relations_lookup(client)
                recent_sessions, active_tasks, _ = _get_relations(
                    agent_id, sessions_by_agent, tasks_by_agent, task_count_by_agent
                )
                capabilities = _AGENT_BASE_CONFIG.get(agent_id, {}).get("capabilities", [])
                return _agent_to_dict(
                    agent_id=agent.id, name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent.status or "ACTIVE",
                    tasks_executed=tasks_executed,
                    trust_score=new_trust_score,
                    last_active=now, capabilities=capabilities,
                    recent_sessions=recent_sessions, active_tasks=active_tasks,
                )
        except Exception as e:
            logger.warning(f"Failed to get agent from TypeDB: {e}")

    if agent_id in _agents_store:
        return dict(_agents_store[agent_id])
    return None
