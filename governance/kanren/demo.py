"""
Kanren Constraint Engine Demo.

Per KAN-002: Demonstrate constraint DSL capabilities.
"""

from .models import AgentContext, TaskContext
from .trust import trust_level, requires_supervisor
from .tasks import valid_task_assignment
from .rag import filter_rag_chunks


def demo_kanren_constraints():
    """Demonstrate Kanren constraint engine."""
    print("=== Kanren Governance Constraints Demo ===\n")

    # Test trust levels
    print("1. Trust Level Validation (RULE-011):")
    for score in [0.95, 0.75, 0.55, 0.35]:
        level = trust_level(score)
        supervisor = requires_supervisor(level)
        print(f"   Score {score} -> {level}, needs_supervisor={supervisor[0]}")

    # Test task assignment
    print("\n2. Task Assignment Validation:")
    agents = [
        AgentContext("AGENT-001", "Claude Code", 0.95, "claude-code"),
        AgentContext("AGENT-002", "New Agent", 0.55, "sync-agent"),
    ]
    tasks = [
        TaskContext("TASK-001", "CRITICAL", True),
        TaskContext("TASK-002", "MEDIUM", False),
    ]

    for agent in agents:
        for task in tasks:
            result = valid_task_assignment(agent, task)
            print(f"   {agent.name} + {task.task_id} ({task.priority}): valid={result['valid']}")

    # Test RAG filtering
    print("\n3. RAG Chunk Filtering (RULE-007):")
    chunks = [
        {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
        {"id": 2, "source": "external", "verified": False, "type": "unknown"},
        {"id": 3, "source": "chromadb", "verified": True, "type": "evidence"},
    ]
    valid = filter_rag_chunks(chunks)
    print(f"   Input: {len(chunks)} chunks, Valid: {len(valid)} chunks")
    for chunk in valid:
        print(f"   OK Chunk {chunk['id']}: {chunk['source']}/{chunk['type']}")

    print("\nKanren constraint engine operational")


if __name__ == "__main__":
    demo_kanren_constraints()
