"""
Agent Metrics Service — Task execution recording and trust recalculation.

Per DOC-SIZE-01-v1: Extracted from agents.py.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from governance.stores import (
    get_typedb_client,
    _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score,
)

logger = logging.getLogger(__name__)

__all__ = [
    "record_task_execution",
]


def _build_relations_lookup(client):
    """Build lookup dicts for agent relations in a single batch."""
    from governance.routes.agents.helpers import build_agent_relations_lookup
    return build_agent_relations_lookup(client)


def _get_relations(agent_id, sessions_by_agent, tasks_by_agent, task_count_by_agent):
    """Get agent's relations from pre-built lookup dicts."""
    from governance.routes.agents.helpers import get_agent_relations_from_lookup
    return get_agent_relations_from_lookup(
        agent_id, sessions_by_agent, tasks_by_agent, task_count_by_agent
    )


def _agent_to_dict(
    agent_id, name, agent_type, status, tasks_executed, trust_score,
    last_active=None, capabilities=None, recent_sessions=None, active_tasks=None,
):
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


def record_task_execution(agent_id: str, source: str = "rest") -> Optional[Dict[str, Any]]:
    """Record that an agent executed a task. Persists metrics and recalculates trust.

    Returns:
        Updated agent dict or None if not found.
    """
    from governance.services.agents import _monitor

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
            # BUG-473-AMT-1: Sanitize logger message + add exc_info for stack trace preservation
            logger.warning(f"Failed to update TypeDB trust for {agent_id}: {type(e).__name__}", exc_info=True)

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
        # BUG-473-AMT-2: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"Failed to persist agent metrics (non-critical): {type(e).__name__}", exc_info=True)

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
                agent_status = _agents_store.get(agent_id, {}).get("status") or "PAUSED"
                return _agent_to_dict(
                    agent_id=agent.id, name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent_status,
                    tasks_executed=tasks_executed,
                    trust_score=new_trust_score,
                    last_active=now, capabilities=capabilities,
                    recent_sessions=recent_sessions, active_tasks=active_tasks,
                )
        except Exception as e:
            # BUG-473-AMT-3: Sanitize logger message + add exc_info for stack trace preservation
            logger.warning(f"Failed to get agent from TypeDB: {type(e).__name__}", exc_info=True)

    if agent_id in _agents_store:
        return dict(_agents_store[agent_id])
    return None
