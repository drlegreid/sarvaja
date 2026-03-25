"""
Kanren Constraint Engine for Governance Rules (KAN-002).

Maps TypeDB governance rules to Kanren relations for declarative
context engineering and constraint validation.

Per RULE-011: Multi-Agent Governance
Per RULE-028: Change Validation Protocol
Per DOC-SIZE-01-v1: Modular file structure (<300 lines each)

Package Structure:
- models.py: Domain dataclasses (AgentContext, TaskContext, RuleContext)
- trust.py: Trust level constraints (RULE-011)
- tasks.py: Task validation constraints (RULE-014, RULE-028)
- rag.py: RAG chunk validation (RULE-007)
- conflicts.py: Rule conflict detection
- filter.py: KanrenRAGFilter class (KAN-003)
- assembly.py: Context assembly functions
- loader.py: TypeDB -> Kanren loader (KAN-004)
- demo.py: Demonstration script

BUG-014: Conditional imports — kanren is optional. Without it, submodules
that depend on kanren are unavailable but pytest collection won't abort.
"""

import logging as _logging

_logger = _logging.getLogger(__name__)

# Domain models (no kanren dependency)
from .models import AgentContext, TaskContext, RuleContext

# Modules below depend on the `kanren` package. Guard imports so that
# pytest collection in environments without kanren (e.g. hatch test env)
# doesn't abort the entire session.
try:
    # Trust constraints (RULE-011)
    from .trust import trust_level, requires_supervisor, can_execute_priority

    # Task constraints (RULE-014, RULE-028)
    from .tasks import task_requires_evidence, valid_task_assignment, validate_agent_for_task

    # RAG validation (RULE-007)
    from .rag import ALLOWED_SOURCES, TRUSTED_TYPES, valid_rag_chunk, filter_rag_chunks

    # Rule conflicts
    from .conflicts import conflicting_priorities, find_rule_conflicts, scope_conflict, lifecycle_conflict

    # Context assembly
    from .assembly import assemble_context

    # RAG Filter (KAN-003)
    from .filter import KanrenRAGFilter

    # TypeDB Loader (KAN-004)
    from .loader import (
        RuleConstraint,
        TypeDBKanrenBridge,
        load_rules_from_typedb,
        populate_kanren_facts,
        query_critical_rules,
        query_rules_by_priority,
        query_foundational_rules,
        validate_rule_compliance,
    )

    # Benchmarks (KAN-005)
    from .benchmark import (
        BenchmarkResult,
        run_all_benchmarks,
        compare_kanren_vs_direct,
        print_benchmark_report,
    )

    # Demo
    from .demo import demo_kanren_constraints

    _KANREN_AVAILABLE = True
except ImportError:
    _logger.debug("kanren package not installed — kanren submodules unavailable")
    _KANREN_AVAILABLE = False

__all__ = [
    # Models
    "AgentContext",
    "TaskContext",
    "RuleContext",
    # Availability flag
    "_KANREN_AVAILABLE",
]

if _KANREN_AVAILABLE:
    __all__ += [
        # Trust
        "trust_level",
        "requires_supervisor",
        "can_execute_priority",
        # Tasks
        "task_requires_evidence",
        "valid_task_assignment",
        "validate_agent_for_task",
        # RAG
        "ALLOWED_SOURCES",
        "TRUSTED_TYPES",
        "valid_rag_chunk",
        "filter_rag_chunks",
        # Conflicts
        "conflicting_priorities",
        "find_rule_conflicts",
        "scope_conflict",
        "lifecycle_conflict",
        # Assembly
        "assemble_context",
        # Filter
        "KanrenRAGFilter",
        # Loader (KAN-004)
        "RuleConstraint",
        "TypeDBKanrenBridge",
        "load_rules_from_typedb",
        "populate_kanren_facts",
        "query_critical_rules",
        "query_rules_by_priority",
        "query_foundational_rules",
        "validate_rule_compliance",
        # Benchmarks (KAN-005)
        "BenchmarkResult",
        "run_all_benchmarks",
        "compare_kanren_vs_direct",
        "print_benchmark_report",
        # Demo
        "demo_kanren_constraints",
    ]
