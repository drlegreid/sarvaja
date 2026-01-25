"""
Robot Framework Library for Kanren Constraint Engine Tests.

Per KAN-002: Kanren Constraint Engine.
Migrated from tests/test_kanren_constraints.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- KanrenTrustLibrary.py (Trust Level, Supervisor, Can Execute, Validate Agent)
- KanrenTaskLibrary.py (Task Evidence, Task Assignment)
- KanrenRAGLibrary.py (RAG Validation, RAG Filtering, KAN-003)
- KanrenAdvancedLibrary.py (Rule Conflicts, KAN-004 Loader, KAN-005 Benchmark)

Note: kanren is an optional dependency. Tests skip if not installed.
"""

from KanrenTrustLibrary import KanrenTrustLibrary
from KanrenTaskLibrary import KanrenTaskLibrary
from KanrenRAGLibrary import KanrenRAGLibrary
from KanrenAdvancedLibrary import KanrenAdvancedLibrary


class KanrenConstraintsLibrary(
    KanrenTrustLibrary,
    KanrenTaskLibrary,
    KanrenRAGLibrary,
    KanrenAdvancedLibrary
):
    """
    Facade library combining all Kanren constraint test modules.

    Inherits from:
    - KanrenTrustLibrary: Trust levels, supervisor requirements, priority execution
    - KanrenTaskLibrary: Task evidence requirements, task assignment validation
    - KanrenRAGLibrary: RAG chunk validation, filtering, KAN-003 filter
    - KanrenAdvancedLibrary: Rule conflicts, KAN-004 loader, KAN-005 benchmark

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
