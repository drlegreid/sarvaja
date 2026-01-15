"""
Task Validation Constraints (RULE-014, RULE-028).

Per RULE-014: Task sequencing
Per RULE-028: Change Validation Protocol
"""

from typing import Any, Dict, Tuple
from kanren import run, var, eq, conde

from .models import AgentContext, TaskContext
from .trust import trust_level, requires_supervisor, can_execute_priority


def task_requires_evidence(priority: str) -> Tuple:
    """
    Check if task priority requires evidence per RULE-028.

    Per RULE-028: CRITICAL and HIGH tasks require validation evidence.
    """
    x = var()
    return run(1, x, conde(
        [eq(priority, 'CRITICAL'), eq(x, True)],
        [eq(priority, 'HIGH'), eq(x, True)],
        [eq(priority, 'MEDIUM'), eq(x, False)],
        [eq(priority, 'LOW'), eq(x, False)]
    ))


def valid_task_assignment(agent: AgentContext, task: TaskContext) -> Dict[str, Any]:
    """
    Validate task assignment per governance rules.

    Returns validation result with constraints checked.
    """
    trust = trust_level(agent.trust_score)

    can_execute = can_execute_priority(trust, task.priority)
    needs_supervisor = requires_supervisor(trust)
    needs_evidence = task_requires_evidence(task.priority)

    return {
        "valid": len(can_execute) > 0 and can_execute[0],
        "agent_id": agent.agent_id,
        "task_id": task.task_id,
        "trust_level": trust,
        "can_execute": can_execute[0] if can_execute else False,
        "requires_supervisor": needs_supervisor[0] if needs_supervisor else True,
        "requires_evidence": needs_evidence[0] if needs_evidence else True,
        "constraints_checked": [
            "RULE-011: Trust-based execution",
            "RULE-014: Task sequencing",
            "RULE-028: Evidence requirements"
        ]
    }


def validate_agent_for_task(agent_id: str, trust_score: float,
                            task_priority: str) -> Dict[str, Any]:
    """Quick validation of agent for task."""
    agent = AgentContext(agent_id, agent_id, trust_score, "claude-code")
    task = TaskContext(f"TASK-{agent_id}", task_priority, False)
    return valid_task_assignment(agent, task)
