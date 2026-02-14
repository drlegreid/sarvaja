"""Tests for governance/mcp_server_agents.py — Agents MCP server init.

Covers: FastMCP creation, tool registration (agents, trust, proposals),
module-level attributes, server name.
"""

import unittest


class TestMcpServerAgentsImport(unittest.TestCase):
    """Tests for mcp_server_agents module-level setup."""

    def test_mcp_instance_exists(self):
        from governance.mcp_server_agents import mcp
        self.assertIsNotNone(mcp)

    def test_mcp_server_name(self):
        from governance.mcp_server_agents import mcp
        self.assertEqual(mcp.name, "governance-agents")

    def test_logger_exists(self):
        from governance.mcp_server_agents import logger
        self.assertIsNotNone(logger)

    def test_metrics_exists(self):
        from governance.mcp_server_agents import metrics
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.server_name, "gov-agents")

    def test_startup_start_captured(self):
        from governance.mcp_server_agents import _startup_start
        self.assertIsInstance(_startup_start, float)
        self.assertGreater(_startup_start, 0)


class TestAgentsToolRegistration(unittest.TestCase):
    """Tests that tools are registered on the mcp instance."""

    def test_has_tools(self):
        from governance.mcp_server_agents import mcp
        tools = list(mcp._tool_manager._tools.keys())
        self.assertGreater(len(tools), 0)

    def test_has_agent_tools(self):
        from governance.mcp_server_agents import mcp
        tools = list(mcp._tool_manager._tools.keys())
        agent_tools = [t for t in tools if "agent" in t.lower()]
        self.assertGreater(len(agent_tools), 0, f"No agent tools in: {tools[:10]}")

    def test_has_trust_tools(self):
        from governance.mcp_server_agents import mcp
        tools = list(mcp._tool_manager._tools.keys())
        trust_tools = [t for t in tools if "trust" in t.lower()]
        self.assertGreater(len(trust_tools), 0)

    def test_has_proposal_tools(self):
        from governance.mcp_server_agents import mcp
        tools = list(mcp._tool_manager._tools.keys())
        proposal_tools = [t for t in tools if "proposal" in t.lower()]
        self.assertGreater(len(proposal_tools), 0)


if __name__ == "__main__":
    unittest.main()
