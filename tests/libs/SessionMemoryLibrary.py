"""
Robot Framework Library for Session Memory Tests.

Per P11.4: Session memory integration for amnesia recovery.
Migrated from tests/test_session_memory.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- SessionMemoryContextLibrary.py (SessionContext creation, serialization, metadata)
- SessionMemoryManagerLibrary.py (Manager init, tracking, save/recovery payloads)
- SessionMemoryIntegrationLibrary.py (DSP Integration, Global Manager singleton)
"""

from SessionMemoryContextLibrary import SessionMemoryContextLibrary
from SessionMemoryManagerLibrary import SessionMemoryManagerLibrary
from SessionMemoryIntegrationLibrary import SessionMemoryIntegrationLibrary


class SessionMemoryLibrary(
    SessionMemoryContextLibrary,
    SessionMemoryManagerLibrary,
    SessionMemoryIntegrationLibrary
):
    """
    Facade library combining all Session Memory test modules.

    Inherits from:
    - SessionMemoryContextLibrary: SessionContext tests
    - SessionMemoryManagerLibrary: SessionMemoryManager tests
    - SessionMemoryIntegrationLibrary: DSP integration and global manager tests

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
