"""Robot Framework library for MCP session tool E2E testing.

Calls the EXACT same Python functions that the MCP protocol invokes,
giving true MCP-level E2E tests against live TypeDB.

Per SRVJ-BUG-SESSION-INGEST-01: Verify CC-ingested sessions are visible.
Per DELIVER-QA-MOAT-01-v1: Real MCP path, not just REST API.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Force JSON output for MCP tools (not TOON) so we can parse results
os.environ["MCP_OUTPUT_FORMAT"] = "json"

# Lazy-loaded tool registry — populated on first use
_tools = {}


def _ensure_tools():
    """Register MCP session tools into _tools dict (once)."""
    if _tools:
        return

    class _CaptureMCP:
        def tool(self):
            def decorator(fn):
                _tools[fn.__name__] = fn
                return fn
            return decorator

    mcp = _CaptureMCP()

    from governance.mcp_tools.sessions_core import register_session_core_tools
    register_session_core_tools(mcp)


def _call(tool_name, **kwargs):
    """Call an MCP tool and return parsed JSON result."""
    _ensure_tools()
    if tool_name not in _tools:
        raise RuntimeError(
            f"MCP tool '{tool_name}' not registered. Available: {list(_tools.keys())}"
        )
    raw = _tools[tool_name](**kwargs)
    return json.loads(raw)


class mcp_sessions:
    """Robot Framework keywords for MCP session tool testing."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def mcp_session_list(self, status=None, limit=50):
        """List sessions via MCP tool with optional status filter."""
        kwargs = {}
        if status is not None:
            kwargs["status"] = status
        kwargs["limit"] = int(limit)
        return _call("session_list", **kwargs)

    def mcp_session_list_should_contain_cc_sessions(self, result):
        """Assert that session_list result contains CC-ingested sessions."""
        sessions = (
            result.get("sessions")
            or result.get("completed_sessions")
            or result.get("active_sessions")
            or []
        )
        cc_sessions = [s for s in sessions if "-CC-" in s]
        if not cc_sessions:
            raise AssertionError(
                f"No CC-ingested sessions found in {len(sessions)} sessions. "
                f"Session IDs: {sessions[:5]}..."
            )
        return cc_sessions

    def mcp_session_list_count_should_be_at_least(self, result, minimum):
        """Assert that session_list result has at least N sessions."""
        count = result.get("count", 0)
        minimum = int(minimum)
        if count < minimum:
            raise AssertionError(
                f"Expected at least {minimum} sessions, got {count}"
            )

    def mcp_result_should_succeed(self, result):
        """Assert MCP result has no error."""
        if "error" in result:
            raise AssertionError(f"MCP call failed: {result['error']}")
