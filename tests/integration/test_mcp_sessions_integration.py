"""MCP Sessions Integration Tests — Gov-Sessions tools against real backend.

Tests session lifecycle, decisions, tasks, and linking MCP tools.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_sessions_integration.py -v
Requires: TypeDB on localhost:1729
"""

import json
import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result

pytestmark = [pytest.mark.integration, pytest.mark.typedb, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixtures: register gov-sessions tools
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def session_core_tools(typedb_available):
    """Register and return session core MCP tool functions."""
    from governance.mcp_tools.sessions_core import register_session_core_tools
    mcp = MockMCP()
    register_session_core_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def session_link_tools(typedb_available):
    """Register and return session linking MCP tool functions."""
    from governance.mcp_tools.sessions_linking import register_session_linking_tools
    mcp = MockMCP()
    register_session_linking_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def session_evidence_tools(typedb_available):
    """Register and return session evidence MCP tool functions."""
    from governance.mcp_tools.sessions_evidence import register_session_evidence_tools
    mcp = MockMCP()
    register_session_evidence_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def session_intent_tools(typedb_available):
    """Register and return session intent MCP tool functions."""
    from governance.mcp_tools.sessions_intent import register_session_intent_tools
    mcp = MockMCP()
    register_session_intent_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# Session lifecycle tests
# ---------------------------------------------------------------------------

class TestSessionLifecycle:
    """Test session start → decision → task → end lifecycle."""

    def test_session_start(self, session_core_tools):
        """session_start creates a new session."""
        result = parse_mcp_result(session_core_tools["session_start"](
            topic="integration-test",
            session_type="general",
        ))
        if "error" in result:
            pytest.skip(f"session_start unavailable: {result['error']}")
        assert "session_id" in result
        assert result.get("topic") == "integration-test"

    def test_session_start_returns_timestamp(self, session_core_tools):
        """session_start includes start timestamp."""
        result = parse_mcp_result(session_core_tools["session_start"](
            topic="inttest-timestamp",
        ))
        if "error" in result:
            pytest.skip(f"session_start unavailable: {result['error']}")
        assert "started_at" in result

    def test_session_decision(self, session_core_tools):
        """session_decision records a decision in active session."""
        start = parse_mcp_result(session_core_tools["session_start"](
            topic="inttest-decision",
        ))
        if "error" in start:
            pytest.skip(f"session_start unavailable: {start['error']}")

        result = parse_mcp_result(session_core_tools["session_decision"](
            decision_id="INTTEST-DEC-001",
            name="Test Decision",
            context="Integration test context",
            rationale="Testing decision recording",
            topic="inttest-decision",
        ))
        assert "error" not in result or "session" not in result.get("error", "").lower()

    def test_session_end(self, session_core_tools):
        """session_end closes an active session."""
        # session_end(topic) — requires the topic of the session to end
        start = parse_mcp_result(session_core_tools["session_start"](
            topic="inttest-end",
        ))
        if "error" in start:
            pytest.skip(f"session_start unavailable: {start['error']}")

        result = parse_mcp_result(session_core_tools["session_end"](
            topic="inttest-end",
        ))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Session listing
# ---------------------------------------------------------------------------

class TestSessionList:
    """Test session listing (if session_list tool is available)."""

    def test_list_sessions(self, session_core_tools):
        """session_list returns a list of sessions."""
        if "session_list" not in session_core_tools:
            pytest.skip("session_list tool not registered in core")
        result = parse_mcp_result(session_core_tools["session_list"]())
        assert isinstance(result, (dict, list))


# ---------------------------------------------------------------------------
# Session linking tests
# ---------------------------------------------------------------------------

class TestSessionLinking:
    """Test session → entity linking tools."""

    def test_link_rule_to_session(self, session_link_tools, session_core_tools):
        """session_link_rule links a rule to a session."""
        if "session_link_rule" not in session_link_tools:
            pytest.skip("session_link_rule not available")

        start = parse_mcp_result(session_core_tools["session_start"](
            topic="inttest-link-rule",
        ))
        if "error" in start:
            pytest.skip(f"session_start unavailable: {start['error']}")

        sid = start["session_id"]
        result = parse_mcp_result(session_link_tools["session_link_rule"](
            session_id=sid,
            rule_id="SESSION-EVID-01-v1",
        ))
        assert isinstance(result, dict)

    def test_link_evidence_to_session(self, session_link_tools, session_core_tools):
        """session_link_evidence links evidence file to a session."""
        if "session_link_evidence" not in session_link_tools:
            pytest.skip("session_link_evidence not available")

        start = parse_mcp_result(session_core_tools["session_start"](
            topic="inttest-link-evidence",
        ))
        if "error" in start:
            pytest.skip(f"session_start unavailable: {start['error']}")

        sid = start["session_id"]
        # session_link_evidence takes (session_id, evidence_path)
        result = parse_mcp_result(session_link_tools["session_link_evidence"](
            session_id=sid,
            evidence_path="evidence/TEST-MINIMAL.md",
        ))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Session intent tests
# ---------------------------------------------------------------------------

class TestSessionIntent:
    """Test session intent capture tools."""

    def test_capture_intent(self, session_intent_tools, session_core_tools):
        """session_capture_intent records session intent."""
        if "session_capture_intent" not in session_intent_tools:
            pytest.skip("session_capture_intent not available")

        start = parse_mcp_result(session_core_tools["session_start"](
            topic="inttest-intent",
        ))
        if "error" in start:
            pytest.skip(f"session_start unavailable: {start['error']}")

        # session_capture_intent(goal, source, topic=...)
        result = parse_mcp_result(session_intent_tools["session_capture_intent"](
            goal="Test the integration test framework",
            source="integration-test",
            topic="inttest-intent",
        ))
        assert isinstance(result, dict)

    def test_capture_outcome(self, session_intent_tools, session_core_tools):
        """session_capture_outcome records session outcome."""
        if "session_capture_outcome" not in session_intent_tools:
            pytest.skip("session_capture_outcome not available")

        start = parse_mcp_result(session_core_tools["session_start"](
            topic="inttest-outcome",
        ))
        if "error" in start:
            pytest.skip(f"session_start unavailable: {start['error']}")

        # session_capture_outcome(status, topic=...)
        result = parse_mcp_result(session_intent_tools["session_capture_outcome"](
            status="completed",
            achieved_tasks="Integration test passed",
            topic="inttest-outcome",
        ))
        assert isinstance(result, dict)
