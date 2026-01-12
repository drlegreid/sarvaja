"""
Memory Fallback Seeder
Created: 2024-12-28
Modularized: 2026-01-02 (RULE-032)

Fallback seeding to in-memory stores when TypeDB is unavailable.
"""

from typing import Dict, Any

from governance.seed.data import get_seed_tasks, get_seed_sessions, get_seed_agents


def seed_to_memory_fallback(tasks_store: Dict[str, Any], sessions_store: Dict[str, Any],
                            agents_store: Dict[str, Any] = None) -> None:
    """Fallback: Seed directly to in-memory stores when TypeDB is unavailable."""
    # Seed tasks
    if not tasks_store:
        for task in get_seed_tasks():
            tasks_store[task["task_id"]] = task

    # Seed sessions
    if not sessions_store:
        for session in get_seed_sessions():
            sessions_store[session["session_id"]] = session

    # Seed agents (P10.3)
    if agents_store is not None and not agents_store:
        for agent in get_seed_agents():
            agents_store[agent["agent_id"]] = {
                "agent_id": agent["agent_id"],
                "name": agent["name"],
                "agent_type": agent["agent_type"],
                "status": "ACTIVE",
                "tasks_executed": 0,
                "trust_score": agent["base_trust"],
                "last_active": None
            }
