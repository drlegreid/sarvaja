"""
Seed Data (DEPRECATED - use governance.seed package)
Created: 2024-12-28
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.seed instead:

    from governance.seed import seed_tasks_and_sessions

Per RULE-012: DSP Semantic Code Structure.
Per RULE-032: Files >300 lines MUST be modularized.
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.seed import (
    get_seed_tasks,
    get_seed_sessions,
    get_seed_agents,
    get_typedb_client,
    seed_tasks_to_typedb,
    seed_sessions_to_typedb,
    seed_agents_to_typedb,
    sync_typedb_to_memory,
    seed_to_memory_fallback,
    seed_tasks_and_sessions,
)

# Private function aliases for backward compatibility
_get_typedb_client = get_typedb_client
_get_seed_tasks = get_seed_tasks
_get_seed_sessions = get_seed_sessions
_get_seed_agents = get_seed_agents
_seed_to_memory_fallback = seed_to_memory_fallback

__all__ = [
    "get_seed_tasks",
    "get_seed_sessions",
    "get_seed_agents",
    "get_typedb_client",
    "seed_tasks_to_typedb",
    "seed_sessions_to_typedb",
    "seed_agents_to_typedb",
    "sync_typedb_to_memory",
    "seed_to_memory_fallback",
    "seed_tasks_and_sessions",
    # Private aliases
    "_get_typedb_client",
    "_get_seed_tasks",
    "_get_seed_sessions",
    "_get_seed_agents",
    "_seed_to_memory_fallback",
]

# Emit deprecation warning on import
warnings.warn(
    "governance.seed_data is deprecated. "
    "Use 'from governance.seed import seed_tasks_and_sessions' instead.",
    DeprecationWarning,
    stacklevel=2
)
