"""
Governance Stores Module.

Per RULE-032: Modularized from stores.py (503 lines → 6 modules).

Public API (backward compatible):
- TypeDB Config: USE_TYPEDB, get_typedb_client
- Data Stores: _tasks_store, _sessions_store, _chat_sessions, _execution_events_store
- Exception: TypeDBUnavailable
- TypeDB Access: get_all_tasks_from_typedb, get_task_from_typedb, etc.
- Agents: _agents_store, _update_agent_metrics_on_claim, get_available_agents_for_chat
- Helpers: task_to_response, session_to_response, synthesize_execution_events, etc.

Module Structure:
- config.py: TypeDB configuration
- data_stores.py: Global stores and exceptions
- typedb_access.py: TypeDB data access functions
- agents.py: Agent config, metrics, trust
- helpers.py: Task/session/chat helpers
"""

# TypeDB Configuration
from .config import (
    USE_TYPEDB,
    get_typedb_client,
)

# Data Stores and Exception
from .data_stores import (
    TypeDBUnavailable,
    _tasks_store,
    _execution_events_store,
    _sessions_store,
    _chat_sessions,
)

# TypeDB Data Access
from .typedb_access import (
    get_all_tasks_from_typedb,
    get_task_from_typedb,
    get_all_sessions_from_typedb,
    get_session_from_typedb,
    get_task_count,
    get_session_count,
    _task_to_dict,
    _session_to_dict,
)

# Agent Configuration and Metrics
from .agents import (
    _AGENT_BASE_CONFIG,
    _agents_store,
    _load_agent_metrics,
    _save_agent_metrics,
    _calculate_trust_score,
    _update_agent_metrics_on_claim,
    _build_agents_store,
    get_available_agents_for_chat,
    get_agent,
    get_all_agents,
)

# Task, Session, Chat Helpers
from .helpers import (
    task_to_response,
    synthesize_execution_events,
    session_to_response,
    extract_session_id,
    generate_chat_session_id,
)

# Audit Trail (RD-DEBUG-AUDIT)
from .audit import (
    AuditEntry,
    generate_correlation_id,
    record_audit,
    query_audit_trail,
    get_audit_summary,
)

__all__ = [
    # TypeDB Config
    "USE_TYPEDB",
    "get_typedb_client",
    # Data Stores
    "TypeDBUnavailable",
    "_tasks_store",
    "_execution_events_store",
    "_sessions_store",
    "_chat_sessions",
    # TypeDB Access
    "get_all_tasks_from_typedb",
    "get_task_from_typedb",
    "get_all_sessions_from_typedb",
    "get_session_from_typedb",
    "get_task_count",
    "get_session_count",
    "_task_to_dict",
    "_session_to_dict",
    # Agents
    "_AGENT_BASE_CONFIG",
    "_agents_store",
    "_load_agent_metrics",
    "_save_agent_metrics",
    "_calculate_trust_score",
    "_update_agent_metrics_on_claim",
    "_build_agents_store",
    "get_available_agents_for_chat",
    "get_agent",
    "get_all_agents",
    # Helpers
    "task_to_response",
    "synthesize_execution_events",
    "session_to_response",
    "extract_session_id",
    "generate_chat_session_id",
    # Audit Trail (RD-DEBUG-AUDIT)
    "AuditEntry",
    "generate_correlation_id",
    "record_audit",
    "query_audit_trail",
    "get_audit_summary",
]
