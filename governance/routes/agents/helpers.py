"""
Agent Route Helpers.

Per DOC-SIZE-01-v1: Files under 300 lines.
Extracted from: governance/routes/agents.py

Created: 2026-01-14
"""

from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def build_agent_relations_lookup(client) -> Tuple[dict, dict, dict]:
    """
    Build lookup dicts for agent relations in a single batch.
    Per GAP-UI-048: Agent relations data.
    Per P11.3: Optimized to avoid N*M queries.

    Returns:
        Tuple of (sessions_by_agent, active_tasks_by_agent, task_count_by_agent)
    """
    sessions_by_agent = {}
    tasks_by_agent = {}
    task_count_by_agent = {}

    if not client:
        return sessions_by_agent, tasks_by_agent, task_count_by_agent

    try:
        # Fetch all sessions ONCE
        sessions = client.get_all_sessions()
        if sessions:
            for s in sessions:
                agent_id = getattr(s, 'agent_id', None)
                if agent_id:
                    if agent_id not in sessions_by_agent:
                        sessions_by_agent[agent_id] = []
                    sessions_by_agent[agent_id].append(s.id)

        # Fetch all tasks ONCE
        tasks = client.get_all_tasks()
        if tasks:
            for t in tasks:
                agent_id = getattr(t, 'agent_id', None)
                if agent_id:
                    # Count ALL tasks per agent for tasks_executed
                    task_count_by_agent[agent_id] = task_count_by_agent.get(agent_id, 0) + 1
                    # Track only active tasks for the active_tasks list
                    if getattr(t, 'status', '') in ("pending", "in_progress"):
                        if agent_id not in tasks_by_agent:
                            tasks_by_agent[agent_id] = []
                        tasks_by_agent[agent_id].append(t.id)

    except Exception as e:
        logger.warning(f"Failed to build agent relations lookup: {e}")

    return sessions_by_agent, tasks_by_agent, task_count_by_agent


def get_agent_relations_from_lookup(
    agent_id: str,
    sessions_by_agent: dict,
    tasks_by_agent: dict,
    task_count_by_agent: dict = None
) -> Tuple[List[str], List[str], int]:
    """
    Get agent's relations from pre-built lookup dicts.
    Per GAP-UI-048: Agent relations data.

    Returns:
        Tuple of (recent_sessions[:5], active_tasks[:5], total_task_count)
    """
    recent_sessions = sessions_by_agent.get(agent_id, [])[:5]
    active_tasks = tasks_by_agent.get(agent_id, [])[:5]
    total_tasks = (task_count_by_agent or {}).get(agent_id, 0)
    return recent_sessions, active_tasks, total_tasks
