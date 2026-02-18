"""
Chat Delegation Protocol Integration (ORCH-006).

Per DOC-SIZE-01-v1: Extracted from endpoints.py.
DelegationProtocol initialization and async task delegation.

Created: 2026-02-11
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from governance.client import get_client
from governance.stores import _agents_store, _tasks_store

logger = logging.getLogger(__name__)

_delegation_protocol = None
_orchestrator_engine = None


def _get_delegation_protocol():
    """Get or create the DelegationProtocol instance."""
    global _delegation_protocol, _orchestrator_engine

    if _delegation_protocol is not None:
        return _delegation_protocol

    try:
        from agent.orchestrator.delegation import DelegationProtocol
        from agent.orchestrator.engine import OrchestratorEngine, AgentInfo, AgentRole

        client = get_client()
        _orchestrator_engine = OrchestratorEngine(client)

        for agent_data in _agents_store.values():
            try:
                role = AgentRole(agent_data.get("agent_type", "research").lower())
            except ValueError:
                role = AgentRole.RESEARCH

            agent_info = AgentInfo(
                agent_id=agent_data.get("agent_id"),
                name=agent_data.get("name", "Unknown"),
                role=role,
                trust_score=agent_data.get("trust_score", 0.5),
            )
            _orchestrator_engine.register_agent(agent_info)

        _delegation_protocol = DelegationProtocol(_orchestrator_engine)
        logger.info("DelegationProtocol initialized for chat")
        return _delegation_protocol

    except Exception as e:
        # BUG-469-DEL-001: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"DelegationProtocol not available: {type(e).__name__}", exc_info=True)
        return None


async def delegate_task_async(task_desc: str, agent_id: str) -> str:
    """Delegate a task using the DelegationProtocol."""
    protocol = _get_delegation_protocol()

    # Create task in store
    task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
    _tasks_store[task_id] = {
        "task_id": task_id,
        "name": task_desc[:50],
        "description": task_desc,
        "status": "pending",
        "priority": "MEDIUM",
        "created_at": datetime.now().isoformat(),
    }

    if protocol is None:
        return (
            f"Task created: {task_id}\n"
            f"Description: {task_desc}\n"
            f"Status: Pending (DelegationProtocol not available)"
        )

    try:
        result = await protocol.delegate_research(
            task_id=task_id,
            source_agent_id=agent_id,
            query=task_desc,
        )

        if result.success:
            _tasks_store[task_id]["status"] = "in_progress"
            _tasks_store[task_id]["agent_id"] = result.target_agent_id
            return (
                f"Task delegated successfully!\n"
                f"- Task ID: {task_id}\n"
                f"- Assigned to: {result.target_agent_id}\n"
                f"- Duration: {result.duration_ms}ms\n"
                f"- Message: {result.message}"
            )
        else:
            return (
                f"Delegation failed:\n"
                f"- Task ID: {task_id}\n"
                f"- Reason: {result.message}\n"
                f"- Status: Task remains pending"
            )
    except Exception as e:
        # BUG-469-DEL-002: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"Delegation error: {type(e).__name__}", exc_info=True)
        return (
            f"Task created: {task_id}\n"
            f"Delegation error: {str(e)}\n"
            f"Status: Pending manual assignment"
        )
