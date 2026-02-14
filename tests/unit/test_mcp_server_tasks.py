"""Tests for governance/mcp_server_tasks.py — Tasks MCP server init.

Covers: FastMCP creation, tool registration (tasks, workspace, gaps, etc.),
module-level attributes, server name.
"""

import unittest


class TestMcpServerTasksImport(unittest.TestCase):
    """Tests for mcp_server_tasks module-level setup."""

    def test_mcp_instance_exists(self):
        from governance.mcp_server_tasks import mcp
        self.assertIsNotNone(mcp)

    def test_mcp_server_name(self):
        from governance.mcp_server_tasks import mcp
        self.assertEqual(mcp.name, "governance-tasks")

    def test_logger_exists(self):
        from governance.mcp_server_tasks import logger
        self.assertIsNotNone(logger)

    def test_metrics_exists(self):
        from governance.mcp_server_tasks import metrics
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.server_name, "gov-tasks")

    def test_startup_start_captured(self):
        from governance.mcp_server_tasks import _startup_start
        self.assertIsInstance(_startup_start, float)
        self.assertGreater(_startup_start, 0)

    def test_server_name_constant(self):
        from governance.mcp_server_tasks import _SERVER_NAME
        self.assertEqual(_SERVER_NAME, "gov-tasks")


class TestTasksToolRegistration(unittest.TestCase):
    """Tests that tools are registered on the mcp instance."""

    def test_has_tools(self):
        from governance.mcp_server_tasks import mcp
        tools = list(mcp._tool_manager._tools.keys())
        self.assertGreater(len(tools), 0)

    def test_has_task_tools(self):
        from governance.mcp_server_tasks import mcp
        tools = list(mcp._tool_manager._tools.keys())
        task_tools = [t for t in tools if "task" in t.lower()]
        self.assertGreater(len(task_tools), 0, f"No task tools in: {tools[:10]}")

    def test_has_workspace_tools(self):
        from governance.mcp_server_tasks import mcp
        tools = list(mcp._tool_manager._tools.keys())
        ws_tools = [t for t in tools if "workspace" in t.lower()]
        self.assertGreater(len(ws_tools), 0)

    def test_has_gap_tools(self):
        from governance.mcp_server_tasks import mcp
        tools = list(mcp._tool_manager._tools.keys())
        gap_tools = [t for t in tools if "gap" in t.lower() or "backlog" in t.lower()]
        self.assertGreater(len(gap_tools), 0)

    def test_has_audit_tools(self):
        from governance.mcp_server_tasks import mcp
        tools = list(mcp._tool_manager._tools.keys())
        audit_tools = [t for t in tools if "audit" in t.lower()]
        self.assertGreater(len(audit_tools), 0)

    def test_has_handoff_tools(self):
        from governance.mcp_server_tasks import mcp
        tools = list(mcp._tool_manager._tools.keys())
        handoff_tools = [t for t in tools if "handoff" in t.lower()]
        self.assertGreater(len(handoff_tools), 0)


class TestAutoSessionTracking(unittest.TestCase):
    def test_track_mcp_tool_call_imported(self):
        from governance.mcp_server_tasks import track_mcp_tool_call
        self.assertTrue(callable(track_mcp_tool_call))


if __name__ == "__main__":
    unittest.main()
