"""Tests for governance/mcp_server_core.py — Core MCP server init.

Covers: FastMCP creation, tool registration (rules + decisions + quality),
QUALITY_AVAILABLE flag, mcp instance attributes.
"""

import unittest
from unittest.mock import patch, MagicMock


class TestMcpServerCoreImport(unittest.TestCase):
    """Tests for mcp_server_core module-level setup."""

    def test_mcp_instance_exists(self):
        from governance.mcp_server_core import mcp
        self.assertIsNotNone(mcp)

    def test_mcp_server_name(self):
        from governance.mcp_server_core import mcp
        self.assertEqual(mcp.name, "governance-core")

    def test_quality_available_flag(self):
        from governance.mcp_server_core import QUALITY_AVAILABLE
        self.assertIsInstance(QUALITY_AVAILABLE, bool)

    def test_logger_exists(self):
        from governance.mcp_server_core import logger
        self.assertIsNotNone(logger)

    def test_metrics_exists(self):
        from governance.mcp_server_core import metrics
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.server_name, "gov-core")


class TestToolRegistration(unittest.TestCase):
    """Tests that tools are registered on the mcp instance."""

    def test_rule_tools_registered(self):
        """register_rule_tools should have been called."""
        from governance.mcp_server_core import mcp
        # The mcp instance should have tools registered
        # Access internal tool manager
        tools = list(mcp._tool_manager._tools.keys())
        self.assertGreater(len(tools), 0)

    def test_has_governance_query_rules(self):
        from governance.mcp_server_core import mcp
        tools = list(mcp._tool_manager._tools.keys())
        # Rule tools include governance_query_rules or rules_query
        rule_tools = [t for t in tools if "rule" in t.lower() or "rules" in t.lower()]
        self.assertGreater(len(rule_tools), 0, f"No rule tools found in: {tools}")

    def test_has_decision_tools(self):
        from governance.mcp_server_core import mcp
        tools = list(mcp._tool_manager._tools.keys())
        decision_tools = [t for t in tools if "decision" in t.lower() or "health" in t.lower()]
        self.assertGreater(len(decision_tools), 0, f"No decision tools in: {tools}")


class TestMCPMetrics(unittest.TestCase):
    """Tests for MCPMetrics usage."""

    def test_metrics_server_name(self):
        from governance.mcp_server_core import metrics
        self.assertEqual(metrics.server_name, "gov-core")

    def test_metrics_has_record_startup(self):
        from governance.mcp_server_core import metrics
        self.assertTrue(hasattr(metrics, "record_startup"))
        self.assertTrue(callable(metrics.record_startup))


class TestStartupTiming(unittest.TestCase):
    """Tests for startup timing mechanism."""

    def test_startup_start_captured(self):
        from governance.mcp_server_core import _startup_start
        self.assertIsInstance(_startup_start, float)
        self.assertGreater(_startup_start, 0)


if __name__ == "__main__":
    unittest.main()
