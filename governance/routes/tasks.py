"""
Tasks Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-STUB-001/002: TypeDB is source of truth (in-memory fallback deprecated).

MODULARIZED: 2026-01-04 per RULE-032 (File Size Limit < 300 lines)
Original file was 475 lines, now split into tasks/ module:
- tasks/crud.py: CRUD operations (list, create, update, delete)
- tasks/workflow.py: Workflow operations (available, claim, complete)
- tasks/execution.py: Execution log (ORCH-007)

This file is a backward-compatible wrapper.
Import from governance.routes.tasks for all task operations.

Created: 2024-12-28
Updated: 2025-01-01 (TypeDB-first refactoring)
Modularized: 2026-01-04 (GAP-FILE-020)
"""

# Backward-compatible imports - all operations now in tasks/ submodule
from .tasks import router

# Re-export for backward compatibility
__all__ = ['router']
