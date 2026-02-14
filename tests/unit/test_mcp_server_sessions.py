"""Tests for governance/mcp_server_sessions.py — Sessions MCP server init.

Covers: FastMCP creation, tool registration (sessions, DSM, evidence, etc.),
module-level attributes, server name.
"""

import unittest


class TestMcpServerSessionsImport(unittest.TestCase):
    """Tests for mcp_server_sessions module-level setup."""

    def test_mcp_instance_exists(self):
        from governance.mcp_server_sessions import mcp
        self.assertIsNotNone(mcp)

    def test_mcp_server_name(self):
        from governance.mcp_server_sessions import mcp
        self.assertEqual(mcp.name, "governance-sessions")

    def test_logger_exists(self):
        from governance.mcp_server_sessions import logger
        self.assertIsNotNone(logger)

    def test_metrics_exists(self):
        from governance.mcp_server_sessions import metrics
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.server_name, "gov-sessions")

    def test_startup_start_captured(self):
        from governance.mcp_server_sessions import _startup_start
        self.assertIsInstance(_startup_start, float)
        self.assertGreater(_startup_start, 0)

    def test_server_name_constant(self):
        from governance.mcp_server_sessions import _SERVER_NAME
        self.assertEqual(_SERVER_NAME, "gov-sessions")


class TestSessionsToolRegistration(unittest.TestCase):
    """Tests that tools are registered on the mcp instance."""

    def test_has_tools(self):
        from governance.mcp_server_sessions import mcp
        tools = list(mcp._tool_manager._tools.keys())
        self.assertGreater(len(tools), 0)

    def test_has_session_tools(self):
        from governance.mcp_server_sessions import mcp
        tools = list(mcp._tool_manager._tools.keys())
        session_tools = [t for t in tools if "session" in t.lower()]
        self.assertGreater(len(session_tools), 0, f"No session tools in: {tools[:10]}")

    def test_has_dsm_tools(self):
        from governance.mcp_server_sessions import mcp
        tools = list(mcp._tool_manager._tools.keys())
        dsm_tools = [t for t in tools if "dsm" in t.lower()]
        self.assertGreater(len(dsm_tools), 0, f"No DSM tools in: {tools[:10]}")

    def test_has_evidence_tools(self):
        from governance.mcp_server_sessions import mcp
        tools = list(mcp._tool_manager._tools.keys())
        evidence_tools = [t for t in tools if "evidence" in t.lower()]
        self.assertGreater(len(evidence_tools), 0)

    def test_has_ingestion_tools(self):
        from governance.mcp_server_sessions import mcp
        tools = list(mcp._tool_manager._tools.keys())
        ingestion_tools = [t for t in tools if "ingest" in t.lower()]
        self.assertGreater(len(ingestion_tools), 0)


class TestAutoSessionTracking(unittest.TestCase):
    """Test auto-session tracking import."""

    def test_track_mcp_tool_call_imported(self):
        from governance.mcp_server_sessions import track_mcp_tool_call
        self.assertTrue(callable(track_mcp_tool_call))


if __name__ == "__main__":
    unittest.main()
