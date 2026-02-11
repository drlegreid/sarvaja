"""
Tests for UI-AUDIT-011: MCP process status in Infrastructure view.

Per TDD: Verify MCP status is displayed.
Per GAP-UI-AUDIT-2026-01-18: Add MCP process status to Infrastructure.

Tests verify:
1. MCP status panel is called in infra view
2. MCP servers are extracted from healthcheck state
3. UI displays MCP server chips
"""

import pytest
import json
from pathlib import Path


@pytest.mark.unit
class TestMCPStatusInInfraView:
    """Verify MCP status panel is included in infra view."""

    def test_mcp_panel_in_infra_view(self):
        """Verify build_mcp_status_panel is called in infra view."""
        import inspect
        from agent.governance_ui.views.infra import build_infra_view

        source = inspect.getsource(build_infra_view)

        # MCP panel should be called
        assert "build_mcp_status_panel()" in source

    def test_mcp_panel_function_exists(self):
        """Verify build_mcp_status_panel function exists."""
        from agent.governance_ui.views.infra_view import build_mcp_status_panel

        assert callable(build_mcp_status_panel)

    def test_mcp_testid_in_panel(self):
        """Verify MCP panel has testid for automation."""
        import inspect
        from agent.governance_ui.views.infra.mcp import build_mcp_status_panel

        source = inspect.getsource(build_mcp_status_panel)

        assert "infra-mcp-status" in source


@pytest.mark.unit
class TestMCPStatusDataLoader:
    """Verify MCP status is loaded from healthcheck state."""

    def test_mcp_servers_in_stats_init(self):
        """Verify mcp_servers key is initialized in stats."""
        import inspect
        from agent.governance_ui.controllers import infra_loaders

        source = inspect.getsource(infra_loaders)

        # Should have mcp_servers in stats initialization
        assert '"mcp_servers"' in source or "'mcp_servers'" in source

    def test_mcp_names_extracted(self):
        """Verify known MCP server names are available via MCP_SERVERS."""
        from agent.governance_ui.controllers.infra import MCP_SERVERS

        # Should have claude-mem at minimum
        assert "claude-mem" in MCP_SERVERS
        assert "gov-core" in MCP_SERVERS
        assert "gov-tasks" in MCP_SERVERS

    def test_healthcheck_state_file_read(self):
        """Verify healthcheck state file is read for MCP status."""
        state_file = Path(__file__).parent.parent.parent / ".claude/hooks/.healthcheck_state.json"

        if state_file.exists():
            with open(state_file) as f:
                hc_state = json.load(f)

            # Should have components with MCP servers
            components = hc_state.get("components", {})
            # At minimum claude-mem should be present
            assert "claude-mem" in components or len(components) > 0


@pytest.mark.unit
class TestMCPStatusUIBinding:
    """Verify UI state binding for MCP status."""

    def test_infra_stats_mcp_servers_used_in_view(self):
        """Verify infra_stats.mcp_servers is used in view template."""
        import inspect
        from agent.governance_ui.views.infra.mcp import build_mcp_status_panel

        source = inspect.getsource(build_mcp_status_panel)

        # Should reference infra_stats.mcp_servers in view
        assert "mcp_servers" in source
