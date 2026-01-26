"""
Robot Framework Library for DSM Tracker Integration Tests.

Per: RULE-012 (DSP), DOC-SIZE-01-v1.
Migrated from tests/test_dsm_tracker_integration.py

REFACTORED per DOC-SIZE-01-v1: This file is a facade that imports from:
- DSMTrackerIntegrationStateLibrary.py (State persistence tests)
- DSMTrackerIntegrationEvidenceLibrary.py (Evidence generation tests)
- DSMTrackerIntegrationWorkflowLibrary.py (Full cycle + metrics tests)
- DSMTrackerIntegrationMCPLibrary.py (MCP tool existence + functionality)
- DSMTrackerIntegrationComplianceLibrary.py (RULE-012 compliance tests)
"""

from DSMTrackerIntegrationStateLibrary import DSMTrackerIntegrationStateLibrary
from DSMTrackerIntegrationEvidenceLibrary import DSMTrackerIntegrationEvidenceLibrary
from DSMTrackerIntegrationWorkflowLibrary import DSMTrackerIntegrationWorkflowLibrary
from DSMTrackerIntegrationMCPLibrary import DSMTrackerIntegrationMCPLibrary
from DSMTrackerIntegrationComplianceLibrary import DSMTrackerIntegrationComplianceLibrary


class DSMTrackerIntegrationLibrary(
    DSMTrackerIntegrationStateLibrary,
    DSMTrackerIntegrationEvidenceLibrary,
    DSMTrackerIntegrationWorkflowLibrary,
    DSMTrackerIntegrationMCPLibrary,
    DSMTrackerIntegrationComplianceLibrary
):
    """
    Facade library combining all DSM Tracker Integration test modules.

    Inherits from:
    - DSMTrackerIntegrationStateLibrary: State persistence (save/load)
    - DSMTrackerIntegrationEvidenceLibrary: Evidence file generation
    - DSMTrackerIntegrationWorkflowLibrary: Full cycle workflow + metrics
    - DSMTrackerIntegrationMCPLibrary: MCP tool existence + functionality
    - DSMTrackerIntegrationComplianceLibrary: RULE-012 compliance

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
