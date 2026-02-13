"""
Tests for infrastructure MCP server status panels.

Per UI-AUDIT-011: MCP server readiness and tool counts.
Batch 162: New coverage for views/infra/mcp.py (0→8 tests).
"""
import inspect

import pytest


class TestMcpViewComponents:
    def test_build_mcp_status_callable(self):
        from agent.governance_ui.views.infra.mcp import build_mcp_status_panel
        assert callable(build_mcp_status_panel)

    def test_build_mcp_detail_callable(self):
        from agent.governance_ui.views.infra.mcp import build_mcp_detail_dialog
        assert callable(build_mcp_detail_dialog)


class TestMcpViewContent:
    def test_has_mcp_status_testid(self):
        from agent.governance_ui.views.infra import mcp
        source = inspect.getsource(mcp)
        assert "infra-mcp-status" in source

    def test_has_server_column(self):
        from agent.governance_ui.views.infra import mcp
        source = inspect.getsource(mcp)
        assert "Server" in source

    def test_has_tools_column(self):
        from agent.governance_ui.views.infra import mcp
        source = inspect.getsource(mcp)
        assert "Tools" in source

    def test_has_ready_column(self):
        from agent.governance_ui.views.infra import mcp
        source = inspect.getsource(mcp)
        assert "Ready" in source

    def test_has_detail_dialog(self):
        from agent.governance_ui.views.infra import mcp
        source = inspect.getsource(mcp)
        assert "show_mcp_detail" in source

    def test_has_dependencies_column(self):
        from agent.governance_ui.views.infra import mcp
        source = inspect.getsource(mcp)
        assert "Dependencies" in source
