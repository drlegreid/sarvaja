"""
Robot Framework Library for DSMTracker Phase Transition Tests.

Per RULE-012: Deep Sleep Protocol.
Migrated from tests/test_dsm_tracker_phases.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- DSMTrackerPhaseNavLibrary.py (Phase navigation, sequence traversal, phase transitions)
- DSMTrackerCycleLibrary.py (Cycle lifecycle, checkpoints, abort cycle)
- DSMTrackerFindingLibrary.py (Finding management, status reporting)
"""

from DSMTrackerPhaseNavLibrary import DSMTrackerPhaseNavLibrary
from DSMTrackerCycleLibrary import DSMTrackerCycleLibrary
from DSMTrackerFindingLibrary import DSMTrackerFindingLibrary


class DSMTrackerPhasesLibrary(
    DSMTrackerPhaseNavLibrary,
    DSMTrackerCycleLibrary,
    DSMTrackerFindingLibrary
):
    """
    Facade library combining all DSMTracker phase test modules.

    Inherits from:
    - DSMTrackerPhaseNavLibrary: Phase navigation and transition tests
    - DSMTrackerCycleLibrary: Cycle lifecycle and checkpoint tests
    - DSMTrackerFindingLibrary: Finding and status tests

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
