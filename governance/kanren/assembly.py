"""
Context Assembly Constraints.

Per KAN-002: Full context assembly with Kanren validation.
"""

from typing import Any, Dict, List

from .models import AgentContext, TaskContext
from .tasks import valid_task_assignment
from .rag import filter_rag_chunks


def assemble_context(agent: AgentContext, task: TaskContext,
                     available_chunks: List[Dict]) -> Dict[str, Any]:
    """
    Assemble validated context for LLM prompt.

    Combines trust validation, RAG filtering, and evidence requirements.
    """
    # Validate assignment
    assignment = valid_task_assignment(agent, task)

    # Filter RAG chunks
    valid_chunks = filter_rag_chunks(available_chunks)

    # Build context
    context = {
        "assignment_valid": assignment["valid"],
        "agent": {
            "id": agent.agent_id,
            "trust_level": assignment["trust_level"],
            "requires_supervisor": assignment["requires_supervisor"]
        },
        "task": {
            "id": task.task_id,
            "priority": task.priority,
            "requires_evidence": assignment["requires_evidence"]
        },
        "rag_chunks": valid_chunks,
        "constraints_applied": assignment["constraints_checked"] + ["RULE-007: RAG validation"]
    }

    return context
