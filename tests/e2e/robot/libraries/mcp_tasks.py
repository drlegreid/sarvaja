"""Robot Framework library for MCP task tool E2E testing.

Calls the EXACT same Python functions that the MCP protocol invokes,
giving true MCP-level E2E tests against live TypeDB.

Per SRVJ-CHORE-DOGFOOD-SWEEP-01: MCP tools must round-trip through TypeDB.
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
    """Register MCP tools into _tools dict (once)."""
    if _tools:
        return

    class _CaptureMCP:
        def tool(self):
            def decorator(fn):
                _tools[fn.__name__] = fn
                return fn
            return decorator

    mcp = _CaptureMCP()

    from governance.mcp_tools.tasks_crud import register_task_crud_tools
    from governance.mcp_tools.tasks_linking import register_task_linking_tools
    register_task_crud_tools(mcp)
    register_task_linking_tools(mcp)


def _call(tool_name, **kwargs):
    """Call an MCP tool and return parsed JSON result."""
    _ensure_tools()
    if tool_name not in _tools:
        raise RuntimeError(f"MCP tool '{tool_name}' not registered. Available: {list(_tools.keys())}")
    raw = _tools[tool_name](**kwargs)
    return json.loads(raw)


class mcp_tasks:
    """Robot Framework keywords for MCP task tool testing."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def mcp_task_create(self, name, task_id="", task_type="test",
                        priority="LOW", workspace_id=None, description=""):
        """Create a task via MCP tool (same path as Claude Code)."""
        kwargs = dict(name=name, task_id=task_id, task_type=task_type,
                      priority=priority, description=description)
        if workspace_id:
            kwargs["workspace_id"] = workspace_id
        return _call("task_create", **kwargs)

    def mcp_task_get(self, task_id):
        """Get a task via MCP tool."""
        return _call("task_get", task_id=task_id)

    def mcp_task_update(self, task_id, **kwargs):
        """Update a task via MCP tool."""
        return _call("task_update", task_id=task_id, **kwargs)

    def mcp_task_delete(self, task_id, confirm=True):
        """Delete a task via MCP tool."""
        return _call("task_delete", task_id=task_id, confirm=confirm)

    def mcp_task_link_session(self, task_id, session_id):
        """Link task to session via MCP tool."""
        return _call("task_link_session", task_id=task_id, session_id=session_id)

    def mcp_task_link_rule(self, task_id, rule_id):
        """Link task to rule via MCP tool."""
        return _call("task_link_rule", task_id=task_id, rule_id=rule_id)

    def mcp_task_link_document(self, task_id, document_path):
        """Link document to task via MCP tool."""
        return _call("task_link_document", task_id=task_id, document_path=document_path)

    def mcp_task_link_evidence(self, task_id, evidence_path):
        """Link evidence to task via MCP tool."""
        return _call("task_link_evidence", task_id=task_id, evidence_path=evidence_path)

    def mcp_task_link_commit(self, task_id, commit_sha, commit_message=None):
        """Link commit to task via MCP tool."""
        return _call("task_link_commit", task_id=task_id,
                      commit_sha=commit_sha, commit_message=commit_message)

    def mcp_task_search(self, query, limit=10):
        """Search tasks via MCP tool."""
        return _call("task_search", query=query, limit=limit)

    def mcp_task_verify(self, task_id, verification_method, evidence, test_passed=True):
        """Verify task via MCP tool."""
        return _call("task_verify", task_id=task_id,
                      verification_method=verification_method,
                      evidence=evidence, test_passed=test_passed)

    def mcp_task_sync_pending(self):
        """Sync pending tasks via MCP tool."""
        return _call("task_sync_pending")

    def mcp_result_should_succeed(self, result):
        """Assert MCP result indicates success (no error key)."""
        if "error" in result:
            raise AssertionError(f"MCP call failed: {result['error']}")

    def mcp_result_should_fail(self, result, expected_code=None):
        """Assert MCP result indicates failure."""
        if "error" not in result:
            raise AssertionError(f"Expected error but got success: {result}")
        if expected_code and result.get("error_code") != expected_code:
            raise AssertionError(
                f"Expected error_code '{expected_code}' but got '{result.get('error_code')}'"
            )
