"""
Robot Framework Library for Data Integrity Validation Tests (P10.7)
Migrated from tests/test_data_integrity.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- DataIntegrityEntityLibrary.py (Entity validation: rule, task, decision, gap, agent, session)
- DataIntegrityRelationLibrary.py (Relation validation, entity sets, cross-entity consistency)
- DataIntegrityReportLibrary.py (Reports, ValidationResult, ID patterns, validation levels)
"""

from DataIntegrityEntityLibrary import DataIntegrityEntityLibrary
from DataIntegrityRelationLibrary import DataIntegrityRelationLibrary
from DataIntegrityReportLibrary import DataIntegrityReportLibrary


class DataIntegrityLibrary(
    DataIntegrityEntityLibrary,
    DataIntegrityRelationLibrary,
    DataIntegrityReportLibrary
):
    """
    Facade library combining all Data Integrity test modules.

    Inherits from:
    - DataIntegrityEntityLibrary: Entity validation tests
    - DataIntegrityRelationLibrary: Relation and set validation tests
    - DataIntegrityReportLibrary: Report, pattern, and level tests

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
