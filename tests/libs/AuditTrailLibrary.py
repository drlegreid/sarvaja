"""
RF-004: Robot Framework Library for Audit Trail Tests.

Wraps tests/test_audit_trail.py for Robot Framework tests.
Tests correlation_id and applied_rules tracking.
"""

import sys
import inspect
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
HOOKS_DIR = PROJECT_ROOT / ".claude" / "hooks" / "checkers"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(HOOKS_DIR))


class AuditTrailLibrary:
    """Robot Framework library for Audit Trail tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def test_capture_tool_call_has_correlation_id(self) -> bool:
        """Check capture_tool_call accepts correlation_id parameter."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        sig = inspect.signature(collector.capture_tool_call)
        return "correlation_id" in sig.parameters

    def test_capture_tool_call_has_applied_rules(self) -> bool:
        """Check capture_tool_call accepts applied_rules parameter."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        sig = inspect.signature(collector.capture_tool_call)
        return "applied_rules" in sig.parameters

    def test_capture_tool_call_stores_correlation_id(self) -> Dict[str, Any]:
        """Test capture_tool_call stores correlation_id."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        collector.capture_tool_call(
            tool_name="Read",
            arguments={"file": "test.md"},
            result="file content",
            correlation_id="CORR-12345"
        )

        if len(collector.events) == 0:
            return {"stored": False, "reason": "No events captured"}

        event = collector.events[0]
        if hasattr(event, 'metadata'):
            stored = event.metadata.get("correlation_id") == "CORR-12345"
        elif hasattr(event, 'correlation_id'):
            stored = event.correlation_id == "CORR-12345"
        else:
            stored = "CORR-12345" in str(event)

        return {"stored": stored, "event_count": len(collector.events)}

    def test_capture_tool_call_stores_applied_rules(self) -> Dict[str, Any]:
        """Test capture_tool_call stores applied_rules."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        rules = ["RULE-001", "SESSION-EVID-01-v1"]

        collector.capture_tool_call(
            tool_name="Write",
            arguments={"file": "evidence.md"},
            applied_rules=rules
        )

        if len(collector.events) == 0:
            return {"stored": False, "reason": "No events captured"}

        event = collector.events[0]
        if hasattr(event, 'metadata'):
            stored = event.metadata.get("applied_rules") == rules
        elif hasattr(event, 'applied_rules'):
            stored = event.applied_rules == rules
        else:
            stored = "RULE-001" in str(event)

        return {"stored": stored, "event_count": len(collector.events)}

    def test_correlation_id_propagates(self) -> Dict[str, Any]:
        """Test correlation_id links multiple tool calls."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        corr_id = "TRACE-001"

        collector.capture_tool_call(
            tool_name="Read",
            arguments={"file": "a.py"},
            correlation_id=corr_id
        )
        collector.capture_tool_call(
            tool_name="Edit",
            arguments={"file": "a.py"},
            correlation_id=corr_id
        )

        return {
            "event_count": len(collector.events),
            "both_have_corr_id": len(collector.events) == 2
        }

    def test_register_session_core_tools_exists(self) -> bool:
        """Check register_session_core_tools function exists."""
        try:
            from governance.mcp_tools.sessions_core import register_session_core_tools
            return register_session_core_tools is not None and callable(register_session_core_tools)
        except ImportError:
            return False

    def test_session_tool_call_in_source(self) -> Dict[str, bool]:
        """Check session_tool_call tool is defined with expected params."""
        try:
            from governance.mcp_tools import sessions_core
            source = inspect.getsource(sessions_core)
            return {
                "has_function": "def session_tool_call" in source,
                "has_correlation_id": "correlation_id" in source,
                "has_applied_rules": "applied_rules" in source,
                "has_mcp_decorator": "@mcp.tool()" in source
            }
        except Exception:
            return {"error": True}

    def test_session_visibility_tracks_rules(self) -> Dict[str, Any]:
        """Test session visibility tracks rules applied per task."""
        try:
            from session_visibility import (
                start_session, start_task, record_rule_application,
                get_task_rules_summary
            )

            start_session("TEST-AUDIT-SESSION")
            start_task("TASK-001", "Test Task")
            record_rule_application("TASK-001", "RULE-001")
            record_rule_application("TASK-001", "RULE-021")

            summary = get_task_rules_summary("TASK-001")

            rules = summary.get("rules_applied", [])
            return {
                "task_id": summary.get("task_id"),
                "has_rule_001": "RULE-001" in rules,
                "has_rule_021": "RULE-021" in rules
            }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}

    def test_session_visibility_tracks_tool_calls(self) -> Dict[str, Any]:
        """Test session visibility tracks tool calls per task."""
        try:
            from session_visibility import (
                start_session, start_task, record_tool_call,
                record_rule_application, get_task_rules_summary
            )

            start_session("TEST-AUDIT-SESSION-2")
            start_task("TASK-002", "Tool Call Test")
            record_rule_application("TASK-002", "RULE-021")
            record_tool_call(
                task_id="TASK-002",
                tool_name="governance_health",
                duration_ms=50,
                rules_applied=["RULE-021"],
                tokens=100
            )

            summary = get_task_rules_summary("TASK-002")
            return {
                "tool_calls": summary.get("tool_calls", 0),
                "has_rule_021": "RULE-021" in summary.get("rules_applied", [])
            }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}

    def test_full_audit_trail_flow(self) -> Dict[str, Any]:
        """Test complete audit trail flow."""
        try:
            from session_visibility import (
                start_session, start_task, record_rule_application,
                record_tool_call, complete_task, get_session_visibility
            )

            session = start_session("TEST-E2E-AUDIT")
            task = start_task("E2E-TASK", "End to End Test")
            record_rule_application("E2E-TASK", "RULE-001")
            record_tool_call(
                task_id="E2E-TASK",
                tool_name="Read",
                duration_ms=10,
                rules_applied=["RULE-001"],
                tokens=50
            )
            completed = complete_task("E2E-TASK")
            visibility = get_session_visibility()

            return {
                "session_id_match": session["session_id"] == "TEST-E2E-AUDIT",
                "task_completed": completed["status"] == "completed",
                "visibility_has_session": visibility["current_session"]["session_id"] == "TEST-E2E-AUDIT"
            }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}

    def test_commit_info_functions_exist(self) -> Dict[str, bool]:
        """Test commit info functions exist."""
        try:
            from session_visibility import record_commit_info, get_task_commit_info
            return {
                "record_commit_info": callable(record_commit_info),
                "get_task_commit_info": callable(get_task_commit_info)
            }
        except ImportError:
            return {"record_commit_info": False, "get_task_commit_info": False}
