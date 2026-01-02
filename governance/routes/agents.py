"""
Agents Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-ARCH-003: TypeDB-first with in-memory fallback.
Per GAP-STUB-005: TypeDB agent store migration.
Per GAP-UI-048: Agent relations (recent_sessions, active_tasks).

Created: 2024-12-28
Updated: 2026-01-02
"""

from fastapi import APIRouter, HTTPException
from typing import List, Tuple
from datetime import datetime
import logging

from governance.models import AgentResponse, AgentTaskAssign
from governance.stores import (
    get_typedb_client,
    _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agents"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_agent_relations(client, agent_id: str) -> Tuple[List[str], List[str]]:
    """
    Get agent's recent sessions and active tasks from TypeDB.
    Per GAP-UI-048: Agent relations data.

    Returns:
        Tuple of (recent_sessions, active_tasks)
    """
    recent_sessions = []
    active_tasks = []

    if not client:
        return recent_sessions, active_tasks

    try:
        # Get sessions where this agent is referenced
        sessions = client.get_all_sessions()
        if sessions:
            agent_sessions = [
                s.id for s in sessions
                if s.agent_id == agent_id
            ]
            # Take most recent 5
            recent_sessions = agent_sessions[:5]

        # Get active tasks for this agent
        tasks = client.get_all_tasks()
        if tasks:
            agent_tasks = [
                t.id for t in tasks
                if t.agent_id == agent_id and t.status in ("pending", "in_progress")
            ]
            active_tasks = agent_tasks[:5]

    except Exception as e:
        logger.warning(f"Failed to get agent relations for {agent_id}: {e}")

    return recent_sessions, active_tasks


# =============================================================================
# AGENTS CRUD
# =============================================================================

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents():
    """
    List all agents.

    Per GAP-ARCH-003: Queries TypeDB for agent registry, merges with local metrics.
    Per GAP-UI-048: Includes recent_sessions and active_tasks relations.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            typedb_agents = client.get_all_agents()
            if typedb_agents:
                metrics = _load_agent_metrics()
                result = []
                for agent in typedb_agents:
                    agent_metrics = metrics.get(agent.id, {})
                    tasks_executed = agent_metrics.get("tasks_executed", agent.tasks_executed or 0)
                    last_active = agent_metrics.get("last_active", None)
                    base_trust = _AGENT_BASE_CONFIG.get(agent.id, {}).get("base_trust", agent.trust_score or 0.8)

                    # Get relations (GAP-UI-048)
                    recent_sessions, active_tasks = _get_agent_relations(client, agent.id)

                    result.append(AgentResponse(
                        agent_id=agent.id,
                        name=agent.name,
                        agent_type=agent.agent_type,
                        status=agent.status or "ACTIVE",
                        tasks_executed=tasks_executed,
                        trust_score=_calculate_trust_score(agent.id, tasks_executed, base_trust),
                        last_active=last_active,
                        recent_sessions=recent_sessions,
                        active_tasks=active_tasks
                    ))
                return result
        except Exception as e:
            logger.warning(f"TypeDB agents query failed, using fallback: {e}")

    # Fallback to in-memory (no relations available)
    return [AgentResponse(**a) for a in _agents_store.values()]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """
    Get a specific agent.

    Per GAP-ARCH-003: Queries TypeDB first, merges with local metrics.
    Per GAP-UI-048: Includes recent_sessions and active_tasks relations.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            agent = client.get_agent(agent_id)
            if agent:
                metrics = _load_agent_metrics()
                agent_metrics = metrics.get(agent_id, {})
                tasks_executed = agent_metrics.get("tasks_executed", agent.tasks_executed or 0)
                last_active = agent_metrics.get("last_active", None)
                base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", agent.trust_score or 0.8)

                # Get relations (GAP-UI-048)
                recent_sessions, active_tasks = _get_agent_relations(client, agent_id)

                return AgentResponse(
                    agent_id=agent.id,
                    name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent.status or "ACTIVE",
                    tasks_executed=tasks_executed,
                    trust_score=_calculate_trust_score(agent_id, tasks_executed, base_trust),
                    last_active=last_active,
                    recent_sessions=recent_sessions,
                    active_tasks=active_tasks
                )
        except Exception as e:
            logger.warning(f"TypeDB agent query failed, using fallback: {e}")

    # Fallback to in-memory (no relations available)
    if agent_id not in _agents_store:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**_agents_store[agent_id])


@router.put("/agents/{agent_id}/task", response_model=AgentResponse)
async def record_agent_task(agent_id: str):
    """
    Record that an agent executed a task.
    Per P11.9: Persists metrics and recalculates trust_score.
    Per GAP-STUB-005: Updates TypeDB trust score.
    """
    client = get_typedb_client()
    now = datetime.now().isoformat()

    # Load current metrics
    metrics = _load_agent_metrics()
    agent_metrics = metrics.get(agent_id, {"tasks_executed": 0})
    tasks_executed = agent_metrics.get("tasks_executed", 0) + 1

    # Calculate new trust score
    base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", 0.85)
    new_trust_score = _calculate_trust_score(agent_id, tasks_executed, base_trust)

    # Update TypeDB (GAP-STUB-005)
    if client:
        try:
            client.update_agent_trust(agent_id, new_trust_score)
            logger.info(f"Updated TypeDB trust for {agent_id}: {new_trust_score:.3f}")
        except Exception as e:
            logger.warning(f"Failed to update TypeDB trust for {agent_id}: {e}")

    # Update in-memory store if exists
    if agent_id in _agents_store:
        _agents_store[agent_id]["tasks_executed"] = tasks_executed
        _agents_store[agent_id]["last_active"] = now
        _agents_store[agent_id]["trust_score"] = new_trust_score

    # Persist metrics to JSON
    metrics[agent_id] = {
        "tasks_executed": tasks_executed,
        "last_active": now
    }
    _save_agent_metrics(metrics)

    # Return updated agent data
    if client:
        try:
            agent = client.get_agent(agent_id)
            if agent:
                recent_sessions, active_tasks = _get_agent_relations(client, agent_id)
                return AgentResponse(
                    agent_id=agent.id,
                    name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent.status or "ACTIVE",
                    tasks_executed=tasks_executed,
                    trust_score=new_trust_score,
                    last_active=now,
                    recent_sessions=recent_sessions,
                    active_tasks=active_tasks
                )
        except Exception as e:
            logger.warning(f"Failed to get agent from TypeDB: {e}")

    # Fallback to in-memory
    if agent_id not in _agents_store:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**_agents_store[agent_id])
