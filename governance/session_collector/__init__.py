"""
Session Collector Module.

Per RULE-032: Modularized from session_collector.py (591 lines → 6 modules).

Public API (backward compatible):
- SessionCollector: Main collector class
- SessionEvent, Task, Decision: Data models
- get_or_create_session: Get/create session by topic
- end_session: End session and generate log
- list_active_sessions: List active session IDs

Module Structure:
- models.py: Data models (SessionEvent, Task, Decision)
- capture.py: Capture methods mixin
- sync.py: TypeDB/ChromaDB sync mixin
- render.py: Markdown rendering mixin
- registry.py: Global session registry
- collector.py: Main SessionCollector class
"""

# Public API - maintain backward compatibility
from .models import (
    SessionEvent,
    Task,
    Decision,
    SessionIntent,
    SessionOutcome,
    TYPEDB_AVAILABLE,
)
from .collector import SessionCollector
from .registry import (
    get_or_create_session,
    end_session,
    list_active_sessions,
    get_session,
    clear_all_sessions,
    _active_sessions,  # Exposed for tests (backward compat)
)

__all__ = [
    # Main class
    "SessionCollector",
    # Data models
    "SessionEvent",
    "Task",
    "Decision",
    "SessionIntent",
    "SessionOutcome",
    # Registry functions
    "get_or_create_session",
    "end_session",
    "list_active_sessions",
    "get_session",
    "clear_all_sessions",
    "_active_sessions",  # For tests
    # Constants
    "TYPEDB_AVAILABLE",
]
