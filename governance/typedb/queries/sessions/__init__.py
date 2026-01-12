"""
TypeDB Session Queries Module.

Per RULE-032: File Size Limit (< 300 lines)
Modularized from: governance/typedb/queries/sessions.py (606 lines)

Created: 2026-01-04

This module combines all session-related query mixins:
- SessionReadQueries: Session read operations
- SessionCRUDOperations: Create/update/delete/end sessions
- SessionLinkingOperations: Link sessions to rules, decisions, evidence
"""

from .read import SessionReadQueries
from .crud import SessionCRUDOperations
from .linking import SessionLinkingOperations


class SessionQueries(
    SessionReadQueries,
    SessionCRUDOperations,
    SessionLinkingOperations
):
    """
    Combined session query and CRUD operations for TypeDB.

    Combines all session-related mixins:
    - SessionReadQueries: get_all_sessions, get_session, _build_session_from_id
    - SessionCRUDOperations: insert_session, end_session, update_session, delete_session
    - SessionLinkingOperations: link_evidence_to_session, link_rule_to_session,
      link_decision_to_session, get_session_evidence, get_session_rules, get_session_decisions

    Requires a client with:
    - _execute_query(query)
    - _client (TypeDB client)
    - database (property for database name)

    Uses mixin pattern for TypeDBClient composition.
    """
    pass


__all__ = [
    'SessionQueries',
    'SessionReadQueries',
    'SessionCRUDOperations',
    'SessionLinkingOperations',
]
