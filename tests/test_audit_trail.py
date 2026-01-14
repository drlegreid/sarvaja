"""
Tests for RD-DEBUG-AUDIT: Audit Trail Debugability

TDD tests per RULE-004: Exploratory Testing & Executable Specification
Per: R&D-BACKLOG.md RD-DEBUG-AUDIT

Tests cover:
1. correlation_id for cross-agent request tracing
2. applied_rules for rule linkage per tool call

Note: MCP tools are registered via @mcp.tool decorator inside register functions,
so we test the SessionCollector directly.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


# =============================================================================
# Test 1: Session Collector correlation_id Support
# =============================================================================

class TestCorrelationIdCapture:
    """Tests for correlation_id tracking in session collector."""

    def test_capture_tool_call_accepts_correlation_id(self):
        """capture_tool_call method accepts correlation_id parameter."""
        from governance.session_collector import SessionCollector
        import inspect

        # Get the mixin's capture_tool_call method signature
        collector = SessionCollector("TEST")
        sig = inspect.signature(collector.capture_tool_call)
        params = sig.parameters

        assert "correlation_id" in params, "correlation_id parameter missing"

    def test_capture_tool_call_stores_correlation_id(self):
        """capture_tool_call stores correlation_id in event metadata."""
        from governance.session_collector import SessionCollector

        collector = SessionCollector("TEST")
        collector.capture_tool_call(
            tool_name="Read",
            arguments={"file": "test.md"},
            result="file content",
            correlation_id="CORR-12345"
        )

        assert len(collector.events) == 1
        event = collector.events[0]

        # Check correlation_id is stored
        if hasattr(event, 'metadata'):
            assert event.metadata.get("correlation_id") == "CORR-12345"
        elif hasattr(event, 'correlation_id'):
            assert event.correlation_id == "CORR-12345"
        else:
            # Check in content or other field
            assert "CORR-12345" in str(event)

    def test_correlation_id_propagates_through_tool_calls(self):
        """Same correlation_id links multiple tool calls."""
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

        assert len(collector.events) == 2

        # Both should have same correlation_id
        for event in collector.events:
            if hasattr(event, 'metadata'):
                assert event.metadata.get("correlation_id") == corr_id


# =============================================================================
# Test 2: Session Collector applied_rules Support
# =============================================================================

class TestAppliedRulesCapture:
    """Tests for applied_rules tracking in session collector."""

    def test_capture_tool_call_accepts_applied_rules(self):
        """capture_tool_call method accepts applied_rules parameter."""
        from governance.session_collector import SessionCollector
        import inspect

        collector = SessionCollector("TEST")
        sig = inspect.signature(collector.capture_tool_call)
        params = sig.parameters

        assert "applied_rules" in params, "applied_rules parameter missing"

    def test_capture_tool_call_stores_applied_rules(self):
        """capture_tool_call stores applied_rules in event metadata."""
        from governance.session_collector import SessionCollector

        collector = SessionCollector("TEST")
        rules = ["RULE-001", "SESSION-EVID-01-v1"]

        collector.capture_tool_call(
            tool_name="Write",
            arguments={"file": "evidence.md"},
            applied_rules=rules
        )

        assert len(collector.events) == 1
        event = collector.events[0]

        # Check applied_rules is stored
        if hasattr(event, 'metadata'):
            assert event.metadata.get("applied_rules") == rules
        elif hasattr(event, 'applied_rules'):
            assert event.applied_rules == rules
        else:
            # Check in content
            assert "RULE-001" in str(event)

    def test_applied_rules_links_decisions_to_governance(self):
        """applied_rules creates traceable link to governance rules."""
        from governance.session_collector import SessionCollector

        collector = SessionCollector("TEST")

        # Simulate agent decision following RULE-021
        collector.capture_tool_call(
            tool_name="governance_health",
            arguments={},
            result='{"status": "healthy"}',
            applied_rules=["RULE-021", "SAFETY-HEALTH-01-v1"]
        )

        event = collector.events[0]

        # Should be able to trace which rules influenced this action
        event_str = str(event)
        assert "RULE-021" in event_str or (
            hasattr(event, 'metadata') and
            "RULE-021" in event.metadata.get("applied_rules", [])
        )


# =============================================================================
# Test 3: Session Core MCP Tool Structure
# =============================================================================

class TestSessionCoreMCPStructure:
    """Tests for session_core MCP tool structure.

    Note: MCP tools are registered via @mcp.tool inside register_session_core_tools.
    We verify the registration function exists and check source for expected params.
    """

    def test_register_session_core_tools_exists(self):
        """register_session_core_tools function exists."""
        from governance.mcp_tools.sessions_core import register_session_core_tools
        assert register_session_core_tools is not None
        assert callable(register_session_core_tools)

    def test_session_tool_call_in_source(self):
        """session_tool_call tool is defined in source with correlation_id."""
        import inspect
        from governance.mcp_tools import sessions_core

        source = inspect.getsource(sessions_core)

        # Check function is defined with expected params
        assert "def session_tool_call" in source
        assert "correlation_id" in source
        assert "applied_rules" in source

    def test_mcp_tool_decorator_used(self):
        """MCP tools use @mcp.tool() decorator."""
        import inspect
        from governance.mcp_tools import sessions_core

        source = inspect.getsource(sessions_core)

        # Verify @mcp.tool() decorator is used
        assert "@mcp.tool()" in source


# =============================================================================
# Test 4: Session Visibility Integration
# =============================================================================

class TestSessionVisibilityAudit:
    """Tests for session visibility audit trail integration."""

    def test_session_visibility_tracks_rules(self):
        """Session visibility module tracks rules applied per task."""
        import sys
        from pathlib import Path

        # Add hooks directory to path
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from session_visibility import (
            start_session,
            start_task,
            record_rule_application,
            get_task_rules_summary
        )

        # Start session and task
        start_session("TEST-AUDIT-SESSION")
        start_task("TASK-001", "Test Task")

        # Record rule applications
        record_rule_application("TASK-001", "RULE-001")
        record_rule_application("TASK-001", "RULE-021")

        # Get summary
        summary = get_task_rules_summary("TASK-001")

        assert summary.get("task_id") == "TASK-001"
        assert "RULE-001" in summary.get("rules_applied", [])
        assert "RULE-021" in summary.get("rules_applied", [])

    def test_session_visibility_tracks_tool_calls(self):
        """Session visibility tracks tool calls per task."""
        import sys
        from pathlib import Path

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from session_visibility import (
            start_session,
            start_task,
            record_tool_call,
            record_rule_application,
            get_task_rules_summary
        )

        start_session("TEST-AUDIT-SESSION-2")
        start_task("TASK-002", "Tool Call Test")

        # First record rule application to session
        record_rule_application("TASK-002", "RULE-021")

        # Record tool call (rules tracked separately from tool call)
        record_tool_call(
            task_id="TASK-002",
            tool_name="governance_health",
            duration_ms=50,
            rules_applied=["RULE-021"],
            tokens=100
        )

        summary = get_task_rules_summary("TASK-002")

        assert summary.get("tool_calls", 0) >= 1
        assert "RULE-021" in summary.get("rules_applied", [])


# =============================================================================
# Test 5: End-to-End Audit Trail
# =============================================================================

class TestEndToEndAuditTrail:
    """Integration tests for complete audit trail flow."""

    def test_full_audit_trail_flow(self):
        """Complete flow: session -> task -> tool call -> rules -> evidence."""
        import sys
        from pathlib import Path

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from session_visibility import (
            start_session,
            start_task,
            record_rule_application,
            record_tool_call,
            complete_task,
            get_session_visibility
        )

        # 1. Start session
        session = start_session("TEST-E2E-AUDIT")
        assert session["session_id"] == "TEST-E2E-AUDIT"

        # 2. Start task
        task = start_task("E2E-TASK", "End to End Test")
        assert task.task_id == "E2E-TASK"

        # 3. Record rule applications
        record_rule_application("E2E-TASK", "RULE-001")
        record_rule_application("E2E-TASK", "RULE-004")

        # 4. Record tool calls
        record_tool_call(
            task_id="E2E-TASK",
            tool_name="Read",
            duration_ms=10,
            rules_applied=["RULE-001"],
            tokens=50
        )

        # 5. Complete task
        completed = complete_task("E2E-TASK")
        assert completed["status"] == "completed"

        # 6. Verify visibility report
        visibility = get_session_visibility()
        assert visibility["current_session"]["session_id"] == "TEST-E2E-AUDIT"
        assert "E2E-TASK" in visibility["current_session"]["tasks_worked"]


# =============================================================================
# Test 6: Commit Info Tracking (User Request)
# =============================================================================

class TestCommitInfoTracking:
    """Tests for commit info linking to tasks."""

    def test_record_commit_info_exists(self):
        """record_commit_info function exists."""
        import sys
        from pathlib import Path

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from session_visibility import record_commit_info
        assert record_commit_info is not None
        assert callable(record_commit_info)

    def test_get_task_commit_info_exists(self):
        """get_task_commit_info function exists."""
        import sys
        from pathlib import Path

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from session_visibility import get_task_commit_info
        assert get_task_commit_info is not None
        assert callable(get_task_commit_info)

    def test_commit_info_flow(self):
        """Record and retrieve commit info for a task."""
        import sys
        from pathlib import Path

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from session_visibility import (
            start_session,
            start_task,
            record_commit_info,
            get_task_commit_info
        )

        start_session("TEST-COMMIT-SESSION")
        start_task("COMMIT-TASK", "Commit Test")

        # Record commit info
        record_commit_info(
            task_id="COMMIT-TASK",
            commit_hash="abc123def",
            files_changed=["src/main.py", "tests/test_main.py"],
            commit_message="Fix authentication bug"
        )

        # Retrieve commit info
        info = get_task_commit_info("COMMIT-TASK")

        assert info.get("task_id") == "COMMIT-TASK"
        assert info.get("commit_count", 0) >= 1
        assert "src/main.py" in info.get("files_changed", [])
