"""
TypeDB Seeder Functions
Created: 2024-12-28
Modularized: 2026-01-02 (RULE-032)

Functions to seed data to TypeDB.
Per P10.1-P10.3: TypeDB-first seeding.
"""

import logging

from governance.seed.data import get_seed_tasks, get_seed_sessions, get_seed_agents

logger = logging.getLogger(__name__)


def get_typedb_client():
    """Get TypeDB client with connection check."""
    try:
        from governance.client import get_client
        client = get_client()
        if client and client.is_connected():
            return client
    except Exception as e:
        logger.warning(f"TypeDB connection failed: {e}")
    return None


def seed_tasks_to_typedb(client) -> int:
    """
    Seed tasks to TypeDB.

    Per P10.1: Tasks -> TypeDB migration.
    Returns count of tasks seeded.
    """
    seed_tasks = get_seed_tasks()
    count = 0

    for task in seed_tasks:
        try:
            # Check if task exists
            existing = client.get_task(task["task_id"])
            if existing:
                continue  # Skip existing tasks

            # Insert to TypeDB
            result = client.insert_task(
                task_id=task["task_id"],
                name=task["description"],
                status=task["status"],
                phase=task["phase"],
                body=task.get("body"),
                gap_id=task.get("gap_id"),
                linked_rules=task.get("linked_rules"),
                linked_sessions=task.get("linked_sessions")
            )
            if result:
                count += 1
        except Exception as e:
            logger.warning(f"Failed to seed task {task['task_id']}: {e}")

    return count


def seed_sessions_to_typedb(client) -> int:
    """
    Seed sessions to TypeDB.

    Per P10.2: Sessions -> TypeDB migration.
    Returns count of sessions seeded.
    """
    seed_sessions = get_seed_sessions()
    count = 0

    for session in seed_sessions:
        try:
            # Check if session exists
            existing = client.get_session(session["session_id"])
            if existing:
                continue  # Skip existing sessions

            # Insert to TypeDB
            result = client.insert_session(
                session_id=session["session_id"],
                name=session.get("description", ""),
                description=session.get("description", ""),
                agent_id=session.get("agent_id")
            )
            if result:
                count += 1
        except Exception as e:
            logger.warning(f"Failed to seed session {session['session_id']}: {e}")

    return count


def seed_agents_to_typedb(client) -> int:
    """
    Seed agents to TypeDB.

    Per P10.3: Agents -> TypeDB migration.
    Returns count of agents seeded.
    """
    seed_agents = get_seed_agents()
    count = 0

    for agent in seed_agents:
        try:
            # Check if agent exists
            existing = client.get_agent(agent["agent_id"])
            if existing:
                continue  # Skip existing agents

            # Insert to TypeDB
            result = client.insert_agent(
                agent_id=agent["agent_id"],
                name=agent["name"],
                agent_type=agent["agent_type"],
                trust_score=agent.get("base_trust", 0.8)
            )
            if result:
                count += 1
        except Exception as e:
            logger.warning(f"Failed to seed agent {agent['agent_id']}: {e}")

    return count
