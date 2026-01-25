"""
Robot Framework Library for Delegation Protocol Tests.

Per ORCH-004: Agent delegation protocol.
Migrated from tests/test_delegation.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- DelegationTypesLibrary.py (DelegationType, DelegationPriority, DelegationContext)
- DelegationRequestLibrary.py (DelegationRequest, DelegationResult)
- DelegationProtocolLibrary.py (DelegationProtocol, convenience functions)
"""

from DelegationTypesLibrary import DelegationTypesLibrary
from DelegationRequestLibrary import DelegationRequestLibrary
from DelegationProtocolLibrary import DelegationProtocolLibrary


class DelegationLibrary(
    DelegationTypesLibrary,
    DelegationRequestLibrary,
    DelegationProtocolLibrary
):
    """
    Facade library combining all Delegation test modules.

    Inherits from:
    - DelegationTypesLibrary: Type, priority, and context tests
    - DelegationRequestLibrary: Request and result tests
    - DelegationProtocolLibrary: Protocol and convenience function tests

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
