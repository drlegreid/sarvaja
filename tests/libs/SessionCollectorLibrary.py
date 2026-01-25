"""
Robot Framework Library for SessionCollector Tests.

Per P4.2: Session Collector.
Migrated from tests/test_session_collector.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- SessionCollectorCoreLibrary.py (Unit tests, event/decision/task capture, serialization)
- SessionCollectorLogLibrary.py (Log generation, markdown output, sections)
- SessionCollectorRegistryLibrary.py (Session registry, MCP session tools)
"""

from SessionCollectorCoreLibrary import SessionCollectorCoreLibrary
from SessionCollectorLogLibrary import SessionCollectorLogLibrary
from SessionCollectorRegistryLibrary import SessionCollectorRegistryLibrary


class SessionCollectorLibrary(
    SessionCollectorCoreLibrary,
    SessionCollectorLogLibrary,
    SessionCollectorRegistryLibrary
):
    """
    Facade library combining all SessionCollector test modules.

    Inherits from:
    - SessionCollectorCoreLibrary: Core functionality tests
    - SessionCollectorLogLibrary: Log generation tests
    - SessionCollectorRegistryLibrary: Registry and MCP tests

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
