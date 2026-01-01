"""
Backward Compatibility Package (GAP-FILE-007)
==============================================
Package exports for backward compatibility functions from mcp_server.py.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-007: Modularized from mcp_server.py (897→~50 lines in main)

Created: 2024-12-28

Modules:
- core.py: Core query functions (rules, sessions, decisions, tasks, evidence)
- dsm.py: DSM tracker exports (RULE-012)
- sessions.py: Session collector exports
- quality.py: Rule quality analyzer exports
- tasks.py: Task CRUD exports (P10.4)
- agents.py: Agent CRUD exports (P10.4)
- documents.py: Document viewing exports (P10.8)
"""

# Core query functions
from .core import (
    governance_query_rules,
    governance_list_sessions,
    governance_get_session,
    governance_list_decisions,
    governance_get_decision,
    governance_list_tasks,
    governance_get_task_deps,
    governance_evidence_search,
)

# DSM tracker exports
from .dsm import (
    dsm_start,
    dsm_advance,
    dsm_checkpoint,
    dsm_status,
    dsm_complete,
    dsm_finding,
    dsm_metrics,
)

# Session collector exports
from .sessions import (
    session_start,
    session_decision,
    session_task,
    session_end,
    session_list,
)

# Rule quality exports
from .quality import (
    governance_analyze_rules,
    governance_rule_impact,
    governance_find_issues,
)

# Task CRUD exports
from .tasks import (
    governance_create_task,
    governance_get_task,
    governance_update_task,
    governance_delete_task,
)

# Agent CRUD exports
from .agents import (
    governance_create_agent,
    governance_get_agent,
    governance_list_agents,
    governance_update_agent_trust,
)

# Document viewing exports
from .documents import (
    governance_get_document,
    governance_list_documents,
    governance_get_rule_document,
    governance_get_task_document,
)

__all__ = [
    # Core
    'governance_query_rules',
    'governance_list_sessions',
    'governance_get_session',
    'governance_list_decisions',
    'governance_get_decision',
    'governance_list_tasks',
    'governance_get_task_deps',
    'governance_evidence_search',
    # DSM
    'dsm_start',
    'dsm_advance',
    'dsm_checkpoint',
    'dsm_status',
    'dsm_complete',
    'dsm_finding',
    'dsm_metrics',
    # Sessions
    'session_start',
    'session_decision',
    'session_task',
    'session_end',
    'session_list',
    # Quality
    'governance_analyze_rules',
    'governance_rule_impact',
    'governance_find_issues',
    # Tasks
    'governance_create_task',
    'governance_get_task',
    'governance_update_task',
    'governance_delete_task',
    # Agents
    'governance_create_agent',
    'governance_get_agent',
    'governance_list_agents',
    'governance_update_agent_trust',
    # Documents
    'governance_get_document',
    'governance_list_documents',
    'governance_get_rule_document',
    'governance_get_task_document',
]
