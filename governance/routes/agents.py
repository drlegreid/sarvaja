"""
Agents Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-ARCH-003: TypeDB-first with in-memory fallback.

Created: 2024-12-28
"""

from fastapi import APIRouter, HTTPException
from typing import List
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
# AGENTS CRUD
# =============================================================================

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents():
    """
    List all agents.

    Per GAP-ARCH-003: Queries TypeDB for agent registry, merges with local metrics.
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

                    result.append(AgentResponse(
                        agent_id=agent.id,
                        name=agent.name,
                        agent_type=agent.agent_type,
                        status=agent.status or "ACTIVE",
                        tasks_executed=tasks_executed,
                        trust_score=_calculate_trust_score(agent.id, tasks_executed, base_trust),
                        last_active=last_active
                    ))
                return result
        except Exception as e:
            logger.warning(f"TypeDB agents query failed, using fallback: {e}")

    # Fallback to in-memory
    return [AgentResponse(**a) for a in _agents_store.values()]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """
    Get a specific agent.

    Per GAP-ARCH-003: Queries TypeDB first, merges with local metrics.
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

                return AgentResponse(
                    agent_id=agent.id,
                    name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent.status or "ACTIVE",
                    tasks_executed=tasks_executed,
                    trust_score=_calculate_trust_score(agent_id, tasks_executed, base_trust),
                    last_active=last_active
                )
        except Exception as e:
            logger.warning(f"TypeDB agent query failed, using fallback: {e}")

    # Fallback to in-memory
    if agent_id not in _agents_store:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**_agents_store[agent_id])


@router.put("/agents/{agent_id}/task", response_model=AgentResponse)
async def record_agent_task(agent_id: str):
    """
    Record that an agent executed a task.
    Per P11.9: Persists metrics and recalculates trust_score.
    """
    if agent_id not in _agents_store:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Update in-memory store
    _agents_store[agent_id]["tasks_executed"] += 1
    _agents_store[agent_id]["last_active"] = datetime.now().isoformat()

    # Recalculate trust score
    base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", 0.85)
    _agents_store[agent_id]["trust_score"] = _calculate_trust_score(
        agent_id,
        _agents_store[agent_id]["tasks_executed"],
        base_trust
    )

    # Persist metrics
    metrics = _load_agent_metrics()
    metrics[agent_id] = {
        "tasks_executed": _agents_store[agent_id]["tasks_executed"],
        "last_active": _agents_store[agent_id]["last_active"]
    }
    _save_agent_metrics(metrics)

    return AgentResponse(**_agents_store[agent_id])
