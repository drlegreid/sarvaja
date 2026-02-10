"""
TypeDB to Memory Sync
Created: 2024-12-28
Modularized: 2026-01-02 (RULE-032)

Sync TypeDB data to in-memory cache.
Per P10.1/P10.2/P10.3: In-memory stores serve as cache for TypeDB.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


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
    # Per GAP-AGENT-PAUSE-001: preserve existing in-memory status (tracks toggles/defaults)
    if agents_store is not None:
        try:
            agents = client.get_all_agents()
            for agent in agents:
                existing_status = agents_store.get(agent.id, {}).get("status")
                agents_store[agent.id] = {
                    "agent_id": agent.id,
                    "name": agent.name,
                    "agent_type": agent.agent_type,
                    "status": existing_status or "PAUSED",
                    "tasks_executed": agent.tasks_executed or 0,
                    "trust_score": agent.trust_score or 0.8,
                    "last_active": None  # Metrics loaded separately
                }
            logger.info(f"Synced {len(agents)} agents from TypeDB to memory")
        except Exception as e:
            logger.warning(f"Failed to sync agents from TypeDB: {e}")
