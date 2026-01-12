"""
TypeDB Rule Queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.

MODULARIZED: 2026-01-04 per RULE-032 (File Size Limit < 300 lines)
Original file was 699 lines, now split into rules/ module:
- rules/read.py: Rule read queries
- rules/inference.py: Dependency/conflict queries
- rules/crud.py: Rule CRUD operations
- rules/archive.py: Archive operations
- rules/decisions.py: Decision queries and CRUD

This file is a backward-compatible wrapper.
Import from governance.typedb.queries.rules for all rule operations.

Created: 2024-12-28
Modularized: 2026-01-04
"""

# Backward-compatible imports - all operations now in rules/ submodule
from .rules import (
    RuleQueries,
    RuleReadQueries,
    RuleInferenceQueries,
    RuleCRUDOperations,
    RuleArchiveOperations,
    DecisionQueries,
    ARCHIVE_DIR,
)

__all__ = [
    'RuleQueries',
    'RuleReadQueries',
    'RuleInferenceQueries',
    'RuleCRUDOperations',
    'RuleArchiveOperations',
    'DecisionQueries',
    'ARCHIVE_DIR',
]
