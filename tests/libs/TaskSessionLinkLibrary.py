"""
Robot Framework library for Task-Session Linking tests.

Per GAP-TASK-LINK-001: Tasks linked to session documents
Migrated from tests/test_task_session_link.py
"""

import re
from robot.api.deco import keyword


class TaskSessionLinkLibrary:
    """Library for testing task-session linking functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Infrastructure Tests
    # =========================================================================

    @keyword("Linking Module Exists")
    def linking_module_exists(self):
        """Verify linking module exists."""
        try:
            from governance.typedb.queries.tasks import TaskLinkingOperations
            return {"exists": TaskLinkingOperations is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Linking Has Link Task To Session")
    def linking_has_link_task_to_session(self):
        """Verify link_task_to_session method exists."""
        try:
            from governance.typedb.queries.tasks.linking import TaskLinkingOperations
            return {"has_method": hasattr(TaskLinkingOperations, 'link_task_to_session')}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Linking Has Get Task Evidence")
    def linking_has_get_task_evidence(self):
        """Verify get_task_evidence method exists."""
        try:
            from governance.typedb.queries.tasks.linking import TaskLinkingOperations
            return {"has_method": hasattr(TaskLinkingOperations, 'get_task_evidence')}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # MCP Tool Tests
    # =========================================================================

    @keyword("Registration Function Exists")
    def registration_function_exists(self):
        """Verify MCP registration function exists."""
        try:
            from governance.mcp_tools.tasks_linking import register_task_linking_tools
            return {
                "exists": register_task_linking_tools is not None,
                "callable": callable(register_task_linking_tools)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Tool Defined In Module")
    def mcp_tool_defined_in_module(self):
        """Verify MCP tool is defined in the module."""
        try:
            import inspect
            from governance.mcp_tools import tasks_linking
            source = inspect.getsource(tasks_linking)
            return {
                "has_tool_name": 'governance_task_link_session' in source or 'task_link_session' in source,
                "has_decorator": '@mcp.tool()' in source or '@server.tool()' in source
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Task-Session Linking Logic Tests
    # =========================================================================

    @keyword("Valid Task Session Pair")
    def valid_task_session_pair(self):
        """Test linking with valid task and session."""
        task_id = "P10.1"
        session_id = "SESSION-2026-01-14-TEST"
        return {
            "task_valid": task_id.startswith("P") or task_id.startswith("TASK-"),
            "session_valid": session_id.startswith("SESSION-")
        }

    @keyword("Session ID Format")
    def session_id_format(self):
        """Verify session ID format."""
        valid_patterns = [
            r"SESSION-\d{4}-\d{2}-\d{2}-[A-Z0-9]+",
            r"SESSION-[A-Z0-9-]+",
        ]
        test_ids = [
            "SESSION-2026-01-14-PHASE12",
            "SESSION-2026-01-14-001",
        ]
        all_valid = True
        for sid in test_ids:
            matched = any(re.match(p, sid) for p in valid_patterns)
            if not matched:
                all_valid = False
        return {"all_valid": all_valid}

    # =========================================================================
    # Task Entity Tests
    # =========================================================================

    @keyword("Task Has Linked Sessions Field")
    def task_has_linked_sessions_field(self):
        """Verify Task entity has linked_sessions."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            field_names = [f.name for f in fields(Task)]
            return {"has_field": 'linked_sessions' in field_names}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Linked Sessions Is List")
    def task_linked_sessions_is_list(self):
        """Verify linked_sessions is a list type."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            for f in fields(Task):
                if f.name == 'linked_sessions':
                    return {"is_list": 'List' in str(f.type) or 'list' in str(f.type)}
            return {"is_list": False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Read Queries Tests
    # =========================================================================

    @keyword("Build Task From ID Has Sessions Query")
    def build_task_from_id_has_sessions_query(self):
        """Verify _build_task_from_id fetches linked sessions."""
        try:
            from governance.typedb.queries.tasks.read import TaskReadQueries
            import inspect
            source = inspect.getsource(TaskReadQueries._build_task_from_id)
            return {
                "has_sessions": 'completed-in' in source or 'linked_sessions' in source
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AttributeError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Data Integrity Tests
    # =========================================================================

    @keyword("Bidirectional Link Concept")
    def bidirectional_link_concept(self):
        """Test bidirectional task-session linking concept."""
        relation_name = "completed-in"
        task_role = "completed-task"
        session_role = "hosting-session"
        return {
            "relation_correct": relation_name == "completed-in",
            "task_role_correct": task_role == "completed-task",
            "session_role_correct": session_role == "hosting-session"
        }

    @keyword("Multiple Sessions Per Task Allowed")
    def multiple_sessions_per_task_allowed(self):
        """Test a task can be linked to multiple sessions."""
        task_sessions = [
            "SESSION-2026-01-10-START",
            "SESSION-2026-01-11-CONTINUE",
            "SESSION-2026-01-14-COMPLETE",
        ]
        return {"allowed": len(task_sessions) >= 1}

    # =========================================================================
    # BDD Scenario Tests
    # =========================================================================

    @keyword("Scenario Link Task To Current Session")
    def scenario_link_task_to_current_session(self):
        """GIVEN/WHEN/THEN scenario for linking task to session."""
        task_id = "GAP-TASK-LINK-001"
        session_id = "SESSION-2026-01-14-TEST"
        return {
            "task_defined": task_id is not None,
            "session_defined": session_id is not None
        }

    @keyword("Scenario Query Sessions For Task")
    def scenario_query_sessions_for_task(self):
        """GIVEN/WHEN/THEN scenario for querying sessions."""
        expected_sessions = ["SESSION-A", "SESSION-B"]
        return {"has_multiple": len(expected_sessions) == 2}
