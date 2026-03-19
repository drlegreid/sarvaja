"""
TypeDB Client Wrapper for Sarvaja Governance.

Provides high-level API for rule inference and knowledge queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Modular TypeDB client architecture.

Created: 2024-12-24 (DECISION-003)
Updated: 2024-12-28 (Modular refactoring)

Original implementation: 1389 lines
Refactored: ~70 lines (95% reduction)
"""

# Re-export entities for backward compatibility
from governance.typedb.entities import (
    Rule,
    Task,
    Session,
    Agent,
    Decision,
    InferenceResult,
    Project,
    Plan,
    Epic,
)

# Re-export ARCHIVE_DIR for backward compatibility (used by tests)

# Import modular components
from governance.typedb.base import TypeDBBaseClient
from governance.typedb.queries import (
    TaskQueries,
    SessionQueries,
    RuleQueries,
    AgentQueries,
    ProjectQueries,
    ProposalQueries,
    CapabilityQueries,
)


class TypeDBClient(
    TypeDBBaseClient,
    TaskQueries,
    SessionQueries,
    RuleQueries,
    AgentQueries,
    ProjectQueries,
    ProposalQueries,
    CapabilityQueries,
):
    """
    High-level TypeDB client for governance queries.

    Composes base client with all query mixins for complete functionality.

    Usage:
        client = TypeDBClient()
        client.connect()

        # Get all active rules
        rules = client.get_active_rules()

        # Find rule dependencies
        deps = client.get_rule_dependencies("RULE-006")

        # Find conflicting rules
        conflicts = client.find_conflicts()

        # Task operations (P10.1 - TypeDB Migration)
        tasks = client.get_all_tasks()
        available = client.get_available_tasks()

        # Session operations (P10.2 - TypeDB Migration)
        sessions = client.get_all_sessions()
        session = client.get_session("SESSION-001")

        # Agent operations (P10.3 - TypeDB Integration)
        agents = client.get_all_agents()

        client.close()
    """
    pass


# Module-level client cache for singleton pattern
_client_instance = None


def get_client() -> TypeDBClient:
    """
    Get or create a singleton TypeDB client instance.

    Returns:
        Connected TypeDBClient or None if connection fails.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = TypeDBClient()
        if not _client_instance.connect():
            _client_instance = None
    return _client_instance


def reset_client():
    """Reset the singleton client (for testing)."""
    global _client_instance
    if _client_instance:
        _client_instance.close()
        _client_instance = None


def quick_health() -> bool:
    """Quick health check for TypeDB.

    Uses socket connection to verify TypeDB is reachable.
    """
    import socket
    from governance.typedb.base import TYPEDB_HOST, TYPEDB_PORT
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # BUG-SOCKET-001: Use try/finally to ensure socket cleanup
        try:
            sock.settimeout(2)
            result = sock.connect_ex((TYPEDB_HOST, TYPEDB_PORT))
            return result == 0
        finally:
            sock.close()
    except Exception:
        return False


__all__ = [
    # Entities
    "Rule",
    "Task",
    "Session",
    "Agent",
    "Decision",
    "InferenceResult",
    # Client
    "TypeDBClient",
    # Singleton functions
    "get_client",
    "reset_client",
    "quick_health",
]
