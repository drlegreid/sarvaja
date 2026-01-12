"""
Governance API Shared Stores - Backward Compatibility Wrapper.

Per RULE-032: This file was modularized into governance/stores/ module.
Original: 503 lines → Now: ~50 lines (90% reduction).

The actual implementation is in:
- governance/stores/config.py        (TypeDB configuration)
- governance/stores/data_stores.py   (global stores, exceptions)
- governance/stores/typedb_access.py (TypeDB data access)
- governance/stores/agents.py        (agent config, metrics)
- governance/stores/helpers.py       (task/session/chat helpers)

This file re-exports all public symbols for backward compatibility.
"""

# Re-export all public symbols from the module
from governance.stores import (
    # TypeDB Config
    USE_TYPEDB,
    get_typedb_client,
    # Data Stores
    TypeDBUnavailable,
    _tasks_store,
    _execution_events_store,
    _sessions_store,
    _chat_sessions,
    # TypeDB Access
    get_all_tasks_from_typedb,
    get_task_from_typedb,
    get_all_sessions_from_typedb,
    get_session_from_typedb,
    get_task_count,
    get_session_count,
    _task_to_dict,
    _session_to_dict,
    # Agents
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
    # Helpers
    task_to_response,
    synthesize_execution_events,
    session_to_response,
    extract_session_id,
    generate_chat_session_id,
)

# Also import logger for backward compatibility
import logging
logger = logging.getLogger(__name__)

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
    # Logger
    "logger",
]
