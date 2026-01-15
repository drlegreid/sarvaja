"""
Kanren Constraint Engine - Backward Compatibility Layer.

DEPRECATED: This file is maintained for backward compatibility.
Use `from governance.kanren import ...` instead.

Per DOC-SIZE-01-v1: Modularized to governance/kanren/ package.
Original 464 lines split into 8 files under 300 lines each.

Migration:
    # OLD
    from governance.kanren_constraints import AgentContext, KanrenRAGFilter

    # NEW (preferred)
    from governance.kanren import AgentContext, KanrenRAGFilter
"""

# Re-export everything from the kanren package for backward compatibility
from governance.kanren import (
    # Models
    AgentContext,
    TaskContext,
    RuleContext,
    # Trust (RULE-011)
    trust_level,
    requires_supervisor,
    can_execute_priority,
    # Tasks (RULE-014, RULE-028)
    task_requires_evidence,
    valid_task_assignment,
    validate_agent_for_task,
    # RAG (RULE-007)
    ALLOWED_SOURCES,
    TRUSTED_TYPES,
    valid_rag_chunk,
    filter_rag_chunks,
    # Conflicts
    conflicting_priorities,
    find_rule_conflicts,
    # Assembly
    assemble_context,
    # Filter (KAN-003)
    KanrenRAGFilter,
    # Demo
    demo_kanren_constraints,
)

__all__ = [
    "AgentContext",
    "TaskContext",
    "RuleContext",
    "trust_level",
    "requires_supervisor",
    "can_execute_priority",
    "task_requires_evidence",
    "valid_task_assignment",
    "validate_agent_for_task",
    "ALLOWED_SOURCES",
    "TRUSTED_TYPES",
    "valid_rag_chunk",
    "filter_rag_chunks",
    "conflicting_priorities",
    "find_rule_conflicts",
    "assemble_context",
    "KanrenRAGFilter",
    "demo_kanren_constraints",
]

if __name__ == "__main__":
    demo_kanren_constraints()
