"""Robot Framework library for MCP audit tool E2E testing.

Calls the EXACT same Python functions that the MCP protocol invokes,
giving true MCP-level E2E tests against live audit store.

Per SRVJ-FEAT-AUDIT-TRAIL-01 P2: Audit trail must be queryable via MCP.
Per DELIVER-QA-MOAT-01-v1: Real MCP path, not just REST API.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

os.environ["MCP_OUTPUT_FORMAT"] = "json"

_tools = {}


def _ensure_tools():
    """Register MCP audit tools into _tools dict (once)."""
    if _tools:
        return

    class _CaptureMCP:
        def tool(self):
            def decorator(fn):
                _tools[fn.__name__] = fn
                return fn
            return decorator

    mcp = _CaptureMCP()

    from governance.mcp_tools.audit import register_audit_tools
    register_audit_tools(mcp)


def _call(tool_name, **kwargs):
    """Call an MCP tool and return parsed JSON result."""
    _ensure_tools()
    if tool_name not in _tools:
        raise RuntimeError(f"MCP tool '{tool_name}' not registered. Available: {list(_tools.keys())}")
    raw = _tools[tool_name](**kwargs)
    return json.loads(raw)


class mcp_audit:
    """Robot Framework keywords for MCP audit tool testing."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def mcp_audit_query(self, entity_id=None, entity_type=None,
                        action_type=None, limit=20):
        """Query audit trail via MCP tool."""
        kwargs = dict(limit=limit)
        if entity_id:
            kwargs["entity_id"] = entity_id
        if entity_type:
            kwargs["entity_type"] = entity_type
        if action_type:
            kwargs["action_type"] = action_type
        return _call("audit_query", **kwargs)

    def mcp_audit_entity_trail(self, entity_id):
        """Get full audit trail for an entity via MCP tool."""
        return _call("audit_entity_trail", entity_id=entity_id)

    def mcp_audit_summary(self):
        """Get audit summary statistics via MCP tool."""
        return _call("audit_summary")

    def mcp_audit_trace(self, correlation_id):
        """Trace correlated operations via MCP tool."""
        return _call("audit_trace", correlation_id=correlation_id)

    def mcp_audit_archive_query(self, entity_id=None, action_type=None,
                                 date_from=None, date_to=None, limit=100):
        """Query cold audit archive via MCP tool."""
        kwargs = dict(limit=limit)
        if entity_id:
            kwargs["entity_id"] = entity_id
        if action_type:
            kwargs["action_type"] = action_type
        if date_from:
            kwargs["date_from"] = date_from
        if date_to:
            kwargs["date_to"] = date_to
        return _call("audit_archive_query", **kwargs)

    def audit_trail_should_contain_action(self, trail_result, action_type):
        """Assert audit trail contains at least one entry with given action_type."""
        entries = trail_result.get("entries", [])
        actions = [e.get("action_type") for e in entries]
        if action_type not in actions:
            raise AssertionError(
                f"Expected action_type '{action_type}' in trail but found: {actions}"
            )

    def audit_trail_should_not_contain_action(self, trail_result, action_type):
        """Assert audit trail does NOT contain given action_type."""
        entries = trail_result.get("entries", [])
        actions = [e.get("action_type") for e in entries]
        if action_type in actions:
            raise AssertionError(
                f"action_type '{action_type}' should NOT be in trail but found it"
            )

    def get_audit_entry_by_action(self, trail_result, action_type):
        """Return first entry matching action_type, or fail."""
        for e in trail_result.get("entries", []):
            if e.get("action_type") == action_type:
                return e
        raise AssertionError(
            f"No entry with action_type '{action_type}' found in trail"
        )

    def audit_entry_metadata_should_contain(self, entry, key, expected_value=None):
        """Assert audit entry metadata contains key (optionally with expected value)."""
        metadata = entry.get("metadata", {})
        if key not in metadata:
            raise AssertionError(
                f"metadata missing key '{key}'. Keys present: {list(metadata.keys())}"
            )
        if expected_value is not None and str(metadata[key]) != str(expected_value):
            raise AssertionError(
                f"metadata['{key}'] = {metadata[key]!r}, expected {expected_value!r}"
            )

    def audit_entry_linked_entity_should_be(self, entry, entity_type, entity_id):
        """Assert LINK/UNLINK entry metadata.linked_entity matches."""
        linked = entry.get("metadata", {}).get("linked_entity", {})
        if linked.get("type") != entity_type:
            raise AssertionError(
                f"linked_entity.type = {linked.get('type')!r}, expected {entity_type!r}"
            )
        if linked.get("id") != entity_id:
            raise AssertionError(
                f"linked_entity.id = {linked.get('id')!r}, expected {entity_id!r}"
            )
