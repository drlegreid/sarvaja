"""
Session Evidence Collector - Backward Compatibility Wrapper.

Per RULE-032: This file was modularized into governance/session_collector/ module.
Original: 591 lines → Now: ~30 lines (98% reduction).

The actual implementation is in:
- governance/session_collector/models.py      (data models)
- governance/session_collector/capture.py     (capture methods)
- governance/session_collector/sync.py        (TypeDB/ChromaDB sync)
- governance/session_collector/render.py      (markdown rendering)
- governance/session_collector/registry.py    (session registry)
- governance/session_collector/collector.py   (main class)

This file re-exports all public symbols for backward compatibility.
"""

# Re-export all public symbols from the module
from governance.session_collector import (
    # Main class
    SessionCollector,
    # Data models
    SessionEvent,
    Task,
    Decision,
    # Registry functions
    get_or_create_session,
    end_session,
    list_active_sessions,
    get_session,
    clear_all_sessions,
    _active_sessions,  # For tests (backward compat)
    # Constants
    TYPEDB_AVAILABLE,
)

__all__ = [
    "SessionCollector",
    "SessionEvent",
    "Task",
    "Decision",
    "get_or_create_session",
    "end_session",
    "list_active_sessions",
    "get_session",
    "clear_all_sessions",
    "_active_sessions",
    "TYPEDB_AVAILABLE",
]
