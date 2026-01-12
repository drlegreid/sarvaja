"""
TypeDB Session Queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.
Per GAP-ARCH-002: Session TypeDB operations.

MODULARIZED: 2026-01-04 per RULE-032 (File Size Limit < 300 lines)
Original file was 606 lines, now split into sessions/ module:
- sessions/read.py: Session read queries
- sessions/crud.py: Session CRUD operations
- sessions/linking.py: Session linking operations

This file is a backward-compatible wrapper.
Import from governance.typedb.queries.sessions for all session operations.

Created: 2024-12-28
Modularized: 2026-01-04
"""

# Backward-compatible imports - all operations now in sessions/ submodule
from .sessions import (
    SessionQueries,
    SessionReadQueries,
    SessionCRUDOperations,
    SessionLinkingOperations,
)

__all__ = [
    'SessionQueries',
    'SessionReadQueries',
    'SessionCRUDOperations',
    'SessionLinkingOperations',
]
