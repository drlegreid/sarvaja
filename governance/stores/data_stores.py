"""
Governance Stores - In-Memory Data Stores.

Per RULE-032: Modularized from stores.py (503 lines).
Contains: Global stores (cache/fallback) and exceptions.
"""

from typing import Dict, Any, List


class TypeDBUnavailable(Exception):
    """Raised when TypeDB is required but unavailable."""
    pass


# =============================================================================
# DATA STORES (Hybrid: TypeDB primary, in-memory cache/fallback)
# =============================================================================

# Task store - serves as cache when TypeDB is primary, fallback when unavailable
# Per GAP-STUB-001/002: Prefer TypeDB wrappers for reads, but keep fallback active
# WARNING: Direct writes to this dict without syncing to TypeDB will cause inconsistency
_tasks_store: Dict[str, Dict[str, Any]] = {}

# Task execution events store (ORCH-007)
_execution_events_store: Dict[str, List[Dict[str, Any]]] = {}

# Session store - serves as cache when TypeDB is primary, fallback when unavailable
# Per GAP-STUB-003/004: Prefer TypeDB wrappers for reads, but keep fallback active
# WARNING: Direct writes to this dict without syncing to TypeDB will cause inconsistency
_sessions_store: Dict[str, Dict[str, Any]] = {}

# Chat sessions store (ORCH-006)
_chat_sessions: Dict[str, Dict[str, Any]] = {}
