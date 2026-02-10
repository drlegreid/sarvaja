"""
Seed Data Package
Created: 2024-12-28
Modularized: 2026-01-02 (RULE-032)

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-UI-008: Initial data for Tasks and Sessions.
Per P10.1-P10.3: TypeDB-first seeding with in-memory cache.

Usage:
    from governance.seed import seed_tasks_and_sessions

    # Initialize stores
    tasks_store = {}
    sessions_store = {}
    agents_store = {}

    # Seed data (TypeDB-first with memory fallback)
    seed_tasks_and_sessions(tasks_store, sessions_store, agents_store)
"""

import logging
from typing import Dict, Any

from governance.seed.data import get_seed_tasks, get_seed_sessions, get_seed_agents
from governance.stores.audit import record_audit
from governance.seed.typedb import (
    get_typedb_client,
    seed_tasks_to_typedb,
    seed_sessions_to_typedb,
    seed_agents_to_typedb,
)
from governance.seed.sync import sync_typedb_to_memory
from governance.seed.memory import seed_to_memory_fallback

logger = logging.getLogger(__name__)


def seed_tasks_and_sessions(tasks_store: Dict[str, Any], sessions_store: Dict[str, Any],
                            agents_store: Dict[str, Any] = None) -> None:
    """
    Seed TypeDB with initial data and sync to in-memory cache.

    Per GAP-UI-008: Tasks view shows empty table
    Per GAP-DATA-001: Tasks have full content
    Per P10.1/P10.2/P10.3: TypeDB-first seeding with in-memory cache
    """
    client = get_typedb_client()

    if client:
        # TypeDB-first: Seed to TypeDB
        tasks_seeded = seed_tasks_to_typedb(client)
        sessions_seeded = seed_sessions_to_typedb(client)
        agents_seeded = seed_agents_to_typedb(client)
        logger.info(f"Seeded {tasks_seeded} tasks, {sessions_seeded} sessions, {agents_seeded} agents to TypeDB")

        # Sync TypeDB to memory
        sync_typedb_to_memory(client, tasks_store, sessions_store, agents_store)
    else:
        # Fallback: Seed to in-memory only
        logger.warning("TypeDB unavailable, seeding to in-memory only")
        seed_to_memory_fallback(tasks_store, sessions_store, agents_store)

    # GAP-AUDIT-EMPTY-001: Record bootstrap audit entry so trail is never empty
    record_audit(
        action_type="BOOTSTRAP",
        entity_type="system",
        entity_id="governance-platform",
        actor_id="system",
        metadata={
            "tasks": len(tasks_store),
            "sessions": len(sessions_store),
            "agents": len(agents_store) if agents_store else 0,
            "source": "typedb" if client else "memory-fallback",
        },
    )


__all__ = [
    # Data getters
    "get_seed_tasks",
    "get_seed_sessions",
    "get_seed_agents",
    # TypeDB functions
    "get_typedb_client",
    "seed_tasks_to_typedb",
    "seed_sessions_to_typedb",
    "seed_agents_to_typedb",
    # Sync functions
    "sync_typedb_to_memory",
    "seed_to_memory_fallback",
    # Main entry point
    "seed_tasks_and_sessions",
]
