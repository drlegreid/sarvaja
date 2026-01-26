"""
Robot Framework Library for Task UI Tests.

Per: Phase 6.1, RULE-019 (UI/UX Design Standards), DOC-SIZE-01-v1.
Migrated from tests/test_task_ui.py

REFACTORED per DOC-SIZE-01-v1: This file is a facade that imports from:
- TaskUIEventTypesLibrary.py (Event types, AGUIEvent, SSE format tests)
- TaskUIStoreLibrary.py (TaskSubmission, TaskStore tests)
- TaskUIRouterLibrary.py (Router, Integration, Response, Result tests)
- TaskUIExecutionLibrary.py (Async tests, execute_task tests)
"""

from TaskUIEventTypesLibrary import TaskUIEventTypesLibrary
from TaskUIStoreLibrary import TaskUIStoreLibrary
from TaskUIRouterLibrary import TaskUIRouterLibrary
from TaskUIExecutionLibrary import TaskUIExecutionLibrary


class TaskUILibrary(
    TaskUIEventTypesLibrary,
    TaskUIStoreLibrary,
    TaskUIRouterLibrary,
    TaskUIExecutionLibrary
):
    """
    Facade library combining all Task UI test modules.

    Inherits from:
    - TaskUIEventTypesLibrary: AG-UI event types, AGUIEvent, SSE format
    - TaskUIStoreLibrary: TaskSubmission, TaskStore operations
    - TaskUIRouterLibrary: Router, Integration, Response models
    - TaskUIExecutionLibrary: Async tests, task execution

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
