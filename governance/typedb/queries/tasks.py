"""
TypeDB Task Queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.
Per GAP-ARCH-001: Task TypeDB operations.

MODULARIZED: 2026-01-04 per RULE-032 (File Size Limit < 300 lines)
Original file was 652 lines, now split into tasks/ module:
- tasks/read.py: Task read queries
- tasks/crud.py: Task CRUD operations
- tasks/linking.py: Task linking operations

This file is a backward-compatible wrapper.
Import from governance.typedb.queries.tasks for all task operations.

Created: 2024-12-28
Modularized: 2026-01-04
"""

# Backward-compatible imports - all operations now in tasks/ submodule
from .tasks import (
    TaskQueries,
    TaskReadQueries,
    TaskCRUDOperations,
    TaskLinkingOperations,
)

__all__ = [
    'TaskQueries',
    'TaskReadQueries',
    'TaskCRUDOperations',
    'TaskLinkingOperations',
]
