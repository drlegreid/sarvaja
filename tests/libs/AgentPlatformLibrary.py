"""
Robot Framework Library for Agent Platform Tests.

Per RD-AGENT-TESTING: Comprehensive test coverage for multi-agent governance.
Migrated from tests/test_agent_platform.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- AgentPlatformWorkflowLibrary.py (ATEST-002: E2E Workflow)
- AgentPlatformConcurrencyLibrary.py (ATEST-003: Concurrency)
- AgentPlatformKanrenLibrary.py (ATEST-006: Kanren Integration)
- AgentPlatformTrustLibrary.py (ATEST-005: Trust Evolution)
- AgentPlatformHandoffLibrary.py (ATEST-004: Handoff Chain)
- AgentPlatformBenchmarkLibrary.py (Benchmarks)
- AgentPlatformRecoveryLibrary.py (ATEST-008: Recovery)
"""

from AgentPlatformWorkflowLibrary import AgentPlatformWorkflowLibrary
from AgentPlatformConcurrencyLibrary import AgentPlatformConcurrencyLibrary
from AgentPlatformKanrenLibrary import AgentPlatformKanrenLibrary
from AgentPlatformTrustLibrary import AgentPlatformTrustLibrary
from AgentPlatformHandoffLibrary import AgentPlatformHandoffLibrary
from AgentPlatformBenchmarkLibrary import AgentPlatformBenchmarkLibrary
from AgentPlatformRecoveryLibrary import AgentPlatformRecoveryLibrary


class AgentPlatformLibrary(
    AgentPlatformWorkflowLibrary,
    AgentPlatformConcurrencyLibrary,
    AgentPlatformKanrenLibrary,
    AgentPlatformTrustLibrary,
    AgentPlatformHandoffLibrary,
    AgentPlatformBenchmarkLibrary,
    AgentPlatformRecoveryLibrary
):
    """
    Facade library combining all Agent Platform test modules.

    Inherits from:
    - AgentPlatformWorkflowLibrary: E2E workflow chain tests (ATEST-002)
    - AgentPlatformConcurrencyLibrary: Parallel agent operations (ATEST-003)
    - AgentPlatformKanrenLibrary: Kanren constraint validation (ATEST-006)
    - AgentPlatformTrustLibrary: Trust score evolution (ATEST-005)
    - AgentPlatformHandoffLibrary: Handoff chain integrity (ATEST-004)
    - AgentPlatformBenchmarkLibrary: Performance benchmarks
    - AgentPlatformRecoveryLibrary: Crash and timeout recovery (ATEST-008)

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
