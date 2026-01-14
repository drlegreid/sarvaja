"""
Agents CRUD Routes.

Per DOC-SIZE-01-v1: Files under 300 lines.
Extracted from: governance/routes/agents.py

Created: 2026-01-14
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from governance.models import AgentResponse, AgentTaskAssign
from governance.stores import (
    get_typedb_client,
    _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score
)
from .helpers import build_agent_relations_lookup, get_agent_relations_from_lookup

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agents"])


@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    sort_by: str = Query("trust_score", description="Sort by: agent_id, name, trust_score, status"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, INACTIVE")
):
    """
    List agents with pagination, sorting, and filtering.

    Per GAP-ARCH-003: Queries TypeDB for agent registry, merges with local metrics.
    Per GAP-UI-048: Includes recent_sessions and active_tasks relations.
    Per GAP-UI-036: Pagination support.
    Per P11.3: Optimized to batch relations queries (avoids N*M problem).
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            typedb_agents = client.get_all_agents()
            if typedb_agents:
                metrics = _load_agent_metrics()

                # Build relations lookup ONCE for all agents (optimization)
                sessions_by_agent, tasks_by_agent = build_agent_relations_lookup(client)

                result = []
                for agent in typedb_agents:
                    agent_metrics = metrics.get(agent.id, {})
                    tasks_executed = agent_metrics.get("tasks_executed", agent.tasks_executed or 0)
                    last_active = agent_metrics.get("last_active", None)
                    base_trust = _AGENT_BASE_CONFIG.get(agent.id, {}).get("base_trust", agent.trust_score or 0.8)

                    # Get relations from pre-built lookup (GAP-UI-048)
                    recent_sessions, active_tasks = get_agent_relations_from_lookup(
                        agent.id, sessions_by_agent, tasks_by_agent
                    )

                    # Get capabilities from config (GAP-AGENT-004)
                    capabilities = _AGENT_BASE_CONFIG.get(agent.id, {}).get("capabilities", [])

                    result.append(AgentResponse(
                        agent_id=agent.id,
                        name=agent.name,
                        agent_type=agent.agent_type,
                        status=agent.status or "ACTIVE",
                        tasks_executed=tasks_executed,
                        trust_score=_calculate_trust_score(agent.id, tasks_executed, base_trust),
                        last_active=last_active,
                        capabilities=capabilities,
                        recent_sessions=recent_sessions,
                        active_tasks=active_tasks
                    ))

                # Apply filters
                if agent_type:
                    result = [a for a in result if a.agent_type == agent_type]
                if status:
                    result = [a for a in result if a.status == status]

                # Apply sorting
                valid_sort_fields = ["agent_id", "name", "trust_score", "status", "tasks_executed"]
                sort_field = sort_by if sort_by in valid_sort_fields else "trust_score"
                reverse = order.lower() == "desc"
                result.sort(key=lambda a: getattr(a, sort_field) or "", reverse=reverse)

                # Apply pagination
                result = result[offset:offset + limit]

                return result
        except Exception as e:
            logger.warning(f"TypeDB agents query failed, using fallback: {e}")

    # Fallback to in-memory (no relations available)
    agents = [AgentResponse(**a) for a in _agents_store.values()]
    return agents[offset:offset + limit]


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

                # Get relations using batch lookup (2 queries total, not N*M)
                sessions_by_agent, tasks_by_agent = build_agent_relations_lookup(client)
                recent_sessions, active_tasks = get_agent_relations_from_lookup(
                    agent_id, sessions_by_agent, tasks_by_agent
                )

                # Get capabilities from config (GAP-AGENT-004)
                capabilities = _AGENT_BASE_CONFIG.get(agent_id, {}).get("capabilities", [])

                return AgentResponse(
                    agent_id=agent.id,
                    name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent.status or "ACTIVE",
                    tasks_executed=tasks_executed,
                    trust_score=_calculate_trust_score(agent_id, tasks_executed, base_trust),
                    last_active=last_active,
                    capabilities=capabilities,
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
                # Get relations using batch lookup
                sessions_by_agent, tasks_by_agent = build_agent_relations_lookup(client)
                recent_sessions, active_tasks = get_agent_relations_from_lookup(
                    agent_id, sessions_by_agent, tasks_by_agent
                )
                # Get capabilities from config (GAP-AGENT-004)
                capabilities = _AGENT_BASE_CONFIG.get(agent_id, {}).get("capabilities", [])
                return AgentResponse(
                    agent_id=agent.id,
                    name=agent.name,
                    agent_type=agent.agent_type,
                    status=agent.status or "ACTIVE",
                    tasks_executed=tasks_executed,
                    trust_score=new_trust_score,
                    last_active=now,
                    capabilities=capabilities,
                    recent_sessions=recent_sessions,
                    active_tasks=active_tasks
                )
        except Exception as e:
            logger.warning(f"Failed to get agent from TypeDB: {e}")

    # Fallback to in-memory
    if agent_id not in _agents_store:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**_agents_store[agent_id])
