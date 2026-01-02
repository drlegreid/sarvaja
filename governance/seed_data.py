"""
Seed Data for Governance API.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-UI-008: Initial data for Tasks and Sessions.
Per P10.1-P10.3: TypeDB-first seeding with in-memory cache.

Created: 2024-12-28
Updated: 2024-12-28 - TypeDB-first migration (P10.1, P10.2, P10.3)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _get_typedb_client():
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

    Per P10.1: Tasks → TypeDB migration.
    Returns count of tasks seeded.
    """
    seed_tasks = _get_seed_tasks()
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

    Per P10.2: Sessions → TypeDB migration.
    Returns count of sessions seeded.
    """
    seed_sessions = _get_seed_sessions()
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

    Per P10.3: Agents → TypeDB migration.
    Returns count of agents seeded.
    """
    seed_agents = _get_seed_agents()
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


def sync_typedb_to_memory(client, tasks_store: Dict[str, Any], sessions_store: Dict[str, Any],
                          agents_store: Dict[str, Any] = None) -> None:
    """
    Sync TypeDB data to in-memory cache.

    Per P10.1/P10.2/P10.3: In-memory stores serve as cache for TypeDB.
    """
    # Sync tasks
    try:
        tasks = client.get_all_tasks()
        for task in tasks:
            tasks_store[task.id] = {
                "task_id": task.id,
                "description": task.name or task.description or "",
                "phase": task.phase or "",
                "status": task.status or "TODO",
                "agent_id": task.agent_id,
                "body": task.body,
                "linked_rules": task.linked_rules,
                "linked_sessions": task.linked_sessions,
                "gap_id": task.gap_id,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "claimed_at": task.claimed_at.isoformat() if task.claimed_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "evidence": task.evidence
            }
        logger.info(f"Synced {len(tasks)} tasks from TypeDB to memory")
    except Exception as e:
        logger.warning(f"Failed to sync tasks from TypeDB: {e}")

    # Sync sessions
    try:
        sessions = client.get_all_sessions()
        for session in sessions:
            sessions_store[session.id] = {
                "session_id": session.id,
                "start_time": session.started_at.isoformat() if session.started_at else None,
                "end_time": session.completed_at.isoformat() if session.completed_at else None,
                "status": session.status or "ACTIVE",
                "tasks_completed": session.tasks_completed or 0,
                "description": session.description or "",
                "agent_id": session.agent_id,
                "file_path": session.file_path,
                "evidence_files": session.evidence_files,
                "linked_rules_applied": session.linked_rules_applied,
                "linked_decisions": session.linked_decisions
            }
        logger.info(f"Synced {len(sessions)} sessions from TypeDB to memory")
    except Exception as e:
        logger.warning(f"Failed to sync sessions from TypeDB: {e}")

    # Sync agents (P10.3)
    if agents_store is not None:
        try:
            agents = client.get_all_agents()
            for agent in agents:
                agents_store[agent.id] = {
                    "agent_id": agent.id,
                    "name": agent.name,
                    "agent_type": agent.agent_type,
                    "status": agent.status or "ACTIVE",
                    "tasks_executed": agent.tasks_executed or 0,
                    "trust_score": agent.trust_score or 0.8,
                    "last_active": None  # Metrics loaded separately
                }
            logger.info(f"Synced {len(agents)} agents from TypeDB to memory")
        except Exception as e:
            logger.warning(f"Failed to sync agents from TypeDB: {e}")


def seed_tasks_and_sessions(tasks_store: Dict[str, Any], sessions_store: Dict[str, Any],
                           agents_store: Dict[str, Any] = None) -> None:
    """
    Seed TypeDB with initial data and sync to in-memory cache.

    Per GAP-UI-008: Tasks view shows empty table
    Per GAP-DATA-001: Tasks have full content
    Per P10.1/P10.2/P10.3: TypeDB-first seeding with in-memory cache
    """
    client = _get_typedb_client()

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
        _seed_to_memory_fallback(tasks_store, sessions_store, agents_store)


def _get_seed_tasks():
    """Get seed task data. Shared between TypeDB and in-memory seeding."""
    return [
        # Phase 3: Stabilization
        {"task_id": "P3.1", "description": "Hybrid query router (TypeDB + ChromaDB)", "phase": "P3", "status": "DONE",
         "body": "Implement router that dispatches queries to TypeDB for structured data and ChromaDB for semantic search.",
         "linked_rules": ["RULE-007"], "created_at": "2024-12-23T09:00:00"},
        {"task_id": "P3.5", "description": "Performance benchmarks (governance/benchmark.py)", "phase": "P3", "status": "DONE",
         "body": "Create benchmark suite for TypeDB query performance.",
         "linked_rules": ["RULE-009"], "created_at": "2024-12-24T10:00:00"},

        # Phase 4: Cross-Workspace Integration
        {"task_id": "P4.1", "description": "MCP -> Agno @tool wrapping", "phase": "P4", "status": "DONE",
         "body": "Wrap MCP server tools as Agno @tool decorators for seamless integration.",
         "linked_rules": ["RULE-007"], "created_at": "2024-12-24T08:00:00"},
        {"task_id": "P4.2", "description": "Session Evidence Collection via MCP", "phase": "P4", "status": "DONE",
         "body": "Implement SessionCollector MCP tool for gathering session artifacts.",
         "linked_rules": ["RULE-001", "RULE-012"], "created_at": "2024-12-24T10:00:00"},

        # Phase 9: Agentic Platform UI/MCP
        {"task_id": "P9.1", "description": "Task/Session/Evidence MCP Tools", "phase": "P9", "status": "DONE",
         "body": "7 MCP tools for artifact viewing.",
         "linked_rules": ["RULE-007", "RULE-001"], "created_at": "2024-12-25T08:00:00"},
        {"task_id": "P9.2", "description": "Governance Dashboard UI (Trame-based)", "phase": "P9", "status": "DONE",
         "body": "Build Governance Dashboard with Trame: rules browser, decisions viewer.",
         "linked_rules": ["RULE-019", "RULE-011"], "created_at": "2024-12-25T08:00:00"},

        # Phase 10: Architecture Debt Resolution
        {"task_id": "P10.1", "description": "Tasks -> TypeDB Migration", "phase": "P10", "status": "IN_PROGRESS",
         "body": "Migrate _tasks_store from in-memory dict to TypeDB.",
         "linked_rules": ["RULE-007"], "gap_id": "GAP-ARCH-001", "created_at": "2024-12-26T08:00:00"},
        {"task_id": "P10.2", "description": "Sessions -> TypeDB Migration", "phase": "P10", "status": "IN_PROGRESS",
         "body": "Migrate _sessions_store to TypeDB.",
         "linked_rules": ["RULE-007"], "gap_id": "GAP-ARCH-002", "created_at": "2024-12-26T08:30:00"},

        # R&D Tasks
        {"task_id": "RD-001", "description": "Haskell MCP Research", "phase": "R&D", "status": "TODO",
         "body": "Research Haskell-based MCP server implementation.",
         "linked_rules": ["RULE-007"], "created_at": "2024-12-26T10:00:00"},

        # Current Sprint Tasks
        {"task_id": "TODO-6", "description": "Agent Task Backlog UI", "phase": "P1", "status": "DONE",
         "body": "Build UI for agent task backlog visualization.",
         "linked_rules": ["RULE-019"], "gap_id": "GAP-005", "created_at": "2024-12-26T08:00:00"},
        {"task_id": "TODO-7", "description": "Sync Agent Implementation", "phase": "P1", "status": "DONE",
         "body": "Implement sync agent skeleton with ChromaDB-TypeDB synchronization.",
         "linked_rules": ["RULE-007"], "gap_id": "GAP-006", "created_at": "2024-12-26T08:00:00"},
    ]


def _get_seed_sessions():
    """Get seed session data. Shared between TypeDB and in-memory seeding."""
    return [
        {
            "session_id": "SESSION-2024-12-24-001",
            "start_time": "2024-12-24T09:00:00",
            "end_time": "2024-12-24T18:00:00",
            "status": "COMPLETED",
            "tasks_completed": 5,
            "description": "Phase 3-4: Stabilization and Cross-Workspace Integration",
            "linked_rules_applied": ["RULE-001", "RULE-007", "RULE-012"],
            "linked_decisions": ["DECISION-001"],
            "evidence_files": [
                "evidence/DECISION-001-Opik-Removal.md",
                "evidence/SESSION-2024-12-24-PHASE-3-4.md"
            ],
        },
        {
            "session_id": "SESSION-2024-12-25-001",
            "start_time": "2024-12-25T08:00:00",
            "end_time": "2024-12-25T22:00:00",
            "status": "COMPLETED",
            "tasks_completed": 12,
            "description": "Phase 9: Governance Dashboard UI + Agent Trust Dashboard",
            "linked_rules_applied": ["RULE-011", "RULE-019", "RULE-020"],
            "linked_decisions": ["DECISION-003"],
            "evidence_files": [
                "evidence/DECISION-003-TypeDB-First.md",
                "evidence/SESSION-2024-12-25-PHASE-9.md"
            ],
        },
        {
            "session_id": "SESSION-2024-12-26-001",
            "start_time": "2024-12-26T08:00:00",
            "status": "ACTIVE",
            "tasks_completed": 8,
            "description": "Phase 10-11: REST API, CRUD fixes, Data Integrity Resolution",
            "linked_rules_applied": ["RULE-001", "RULE-007", "RULE-019"],
            "evidence_files": [
                "evidence/SESSION-2024-12-26-PHASE-10-11.md"
            ],
        },
        {
            "session_id": "SESSION-2024-12-28-001",
            "start_time": "2024-12-28T08:00:00",
            "status": "ACTIVE",
            "tasks_completed": 5,
            "description": "Phase 10: TypeDB-First Migration + GAP-FILE Resolution",
            "linked_rules_applied": ["RULE-007", "RULE-012", "RULE-030"],
            "evidence_files": [
                "evidence/SESSION-2024-12-28-PHASE-10.md",
                "docs/gaps/GAP-INDEX.md"
            ],
        },
    ]


def _get_seed_agents():
    """
    Get seed agent data. Shared between TypeDB and in-memory seeding.

    Per P10.3: Base agent definitions for TypeDB-first migration.
    """
    return [
        {"agent_id": "task-orchestrator", "name": "Task Orchestrator", "agent_type": "orchestrator", "base_trust": 0.95},
        {"agent_id": "rules-curator", "name": "Rules Curator", "agent_type": "curator", "base_trust": 0.90},
        {"agent_id": "research-agent", "name": "Research Agent", "agent_type": "researcher", "base_trust": 0.85},
        {"agent_id": "code-agent", "name": "Code Agent", "agent_type": "coder", "base_trust": 0.88},
        {"agent_id": "local-assistant", "name": "Local Assistant", "agent_type": "assistant", "base_trust": 0.92},
    ]


def _seed_to_memory_fallback(tasks_store: Dict[str, Any], sessions_store: Dict[str, Any],
                             agents_store: Dict[str, Any] = None) -> None:
    """Fallback: Seed directly to in-memory stores when TypeDB is unavailable."""
    # Seed tasks
    if not tasks_store:
        for task in _get_seed_tasks():
            tasks_store[task["task_id"]] = task

    # Seed sessions
    if not sessions_store:
        for session in _get_seed_sessions():
            sessions_store[session["session_id"]] = session

    # Seed agents (P10.3)
    if agents_store is not None and not agents_store:
        for agent in _get_seed_agents():
            agents_store[agent["agent_id"]] = {
                "agent_id": agent["agent_id"],
                "name": agent["name"],
                "agent_type": agent["agent_type"],
                "status": "ACTIVE",
                "tasks_executed": 0,
                "trust_score": agent["base_trust"],
                "last_active": None
            }
