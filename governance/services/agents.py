"""Agent Service Layer - Single code path for all agent operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.
Per DOC-SIZE-01-v1: Task execution metrics in agents_metrics.py.

Created: 2026-02-01
"""
import logging
from typing import Optional, Dict, Any, List, Tuple

from governance.stores import (
    get_typedb_client,
    _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score,
)
from governance.stores.audit import record_audit

# Re-export for backward compatibility
from governance.services.agents_metrics import record_task_execution  # noqa: F401

logger = logging.getLogger(__name__)

__all__ = [
    "create_agent",
    "list_agents",
    "get_agent",
    "delete_agent",
    "toggle_agent_status",
    # Re-export from agents_metrics
    "record_task_execution",
]


def _persist_agent_status(agent_id: str, status: str) -> None:
    """Persist agent status to metrics file (survives container restarts).

    Per ASSESS-PLATFORM-GAPS-2026-02-15 Fix G: Agent status was in-memory only.
    Now persists to the same agent_metrics.json file used for task counts.
    """
    try:
        metrics = _load_agent_metrics()
        if agent_id not in metrics:
            metrics[agent_id] = {}
        metrics[agent_id]["status"] = status
        _save_agent_metrics(metrics)
    except Exception as e:
        logger.warning(f"Failed to persist agent status for {agent_id}: {e}")


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
    except Exception as e:
        # BUG-MONITOR-SILENT-001: Log instead of silently swallowing
        logger.warning(f"Monitor event failed for agent {agent_id}: {e}")


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


def create_agent(
    agent_id: str,
    name: str,
    agent_type: str = "custom",
    trust_score: float = 0.8,
    capabilities: Optional[List[str]] = None,
    rules: Optional[List[str]] = None,
    source: str = "rest",
) -> Optional[Dict[str, Any]]:
    """Create a new agent in TypeDB and in-memory store.

    Returns:
        Agent dict or None if creation failed.
    """
    # Check for duplicates
    if agent_id in _agents_store:
        return None

    client = get_typedb_client()
    if client:
        try:
            existing = client.get_agent(agent_id)
            if existing:
                return None
            client.insert_agent(agent_id, name, agent_type, trust_score)
        except Exception as e:
            logger.warning(f"TypeDB agent create failed for {agent_id}: {e}")

    # Always populate in-memory store
    _agents_store[agent_id] = {
        "agent_id": agent_id,
        "name": name,
        "agent_type": agent_type,
        "status": "PAUSED",
        "trust_score": trust_score,
        "tasks_executed": 0,
        "capabilities": capabilities or [],
        "recent_sessions": [],
        "active_tasks": [],
    }

    record_audit("CREATE", "agent", agent_id, metadata={
        "source": source, "agent_type": agent_type, "trust_score": trust_score,
        "capabilities": capabilities or [], "rules": rules or [],
    })
    _monitor("create", agent_id, source=source, agent_type=agent_type)

    return get_agent(agent_id, source=source)


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
    # BUG-327-AGT-001: Clamp offset/limit at service layer (route has Query(ge/le)
    # but MCP tools may bypass routes and call service directly)
    offset = max(0, offset)
    limit = max(1, min(limit, 200))
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
                    # BUG-286-TRUST-001: Use 'is not None' instead of 'or' to preserve 0.0 trust scores
                    base_trust = _AGENT_BASE_CONFIG.get(agent.id, {}).get(
                        "base_trust",
                        agent.trust_score if agent.trust_score is not None else 0.8
                    )

                    recent_sessions, active_tasks, task_count = _get_relations(
                        agent.id, sessions_by_agent, tasks_by_agent, task_count_by_agent
                    )
                    store_count = _agents_store.get(agent.id, {}).get("tasks_executed", 0)
                    tasks_executed = task_count or store_count or agent_metrics.get("tasks_executed", 0)
                    capabilities = _AGENT_BASE_CONFIG.get(agent.id, {}).get("capabilities", [])

                    # Per GAP-AGENT-PAUSE-001: prefer in-memory status (tracks toggles)
                    agent_status = _agents_store.get(agent.id, {}).get("status") or "PAUSED"
                    result.append(_agent_to_dict(
                        agent_id=agent.id, name=agent.name,
                        agent_type=agent.agent_type,
                        status=agent_status,
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
                # BUG-215-AGT-004: Use type-aware fallback (0.0 is falsy, 'or ""' crashes)
                def _sort_key(a):
                    v = a.get(sort_field)
                    if v is None:
                        return (1, "")  # Nones sort last
                    return (0, v)
                result.sort(key=_sort_key, reverse=order.lower() == "desc")

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

                # Per GAP-AGENT-PAUSE-001: prefer in-memory status (tracks toggles)
                agent_status = _agents_store.get(agent_id, {}).get("status") or "PAUSED"
                return _agent_to_dict(
                    agent_id=agent.id, name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent_status,
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


def toggle_agent_status(agent_id: str, source: str = "rest") -> Optional[Dict[str, Any]]:
    """Toggle agent between PAUSED and ACTIVE.

    Per GAP-AGENT-PAUSE-001: Agents default PAUSED, operators toggle via UI.
    Status is in-memory only (not in TypeDB schema).

    Returns:
        Updated agent dict with new status, or None if not found.
    """
    # BUG-UI-AGENTS-001: Check TypeDB if agent not in memory store
    if agent_id not in _agents_store:
        client = get_typedb_client()
        if client:
            try:
                agent = client.get_agent(agent_id)
                if agent:
                    # Backfill to memory store so subsequent toggles are fast
                    _agents_store[agent_id] = {
                        "agent_id": agent_id,
                        "name": agent.name,
                        "agent_type": agent.agent_type,
                        "status": "PAUSED",
                        "trust_score": agent.trust_score or 0.8,
                        "capabilities": _AGENT_BASE_CONFIG.get(agent_id, {}).get("capabilities", []),
                    }
                else:
                    return None
            # BUG-195-012: Log the exception instead of silently swallowing
            except Exception as e:
                logger.warning(f"TypeDB toggle_agent_status failed for {agent_id}: {e}")
                return None
        else:
            return None

    current_status = _agents_store[agent_id].get("status", "PAUSED")
    new_status = "ACTIVE" if current_status == "PAUSED" else "PAUSED"
    _agents_store[agent_id]["status"] = new_status

    # Per Fix G: Persist status to metrics file (survives restarts)
    _persist_agent_status(agent_id, new_status)

    record_audit(
        "UPDATE", "agent", agent_id,
        metadata={"source": source, "field": "status", "old": current_status, "new": new_status},
    )
    _monitor("toggle_status", agent_id, source=source, old_status=current_status, new_status=new_status)

    return get_agent(agent_id, source=source)
