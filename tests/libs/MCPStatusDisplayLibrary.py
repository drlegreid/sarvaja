"""
RF-004: Robot Framework Library for MCP Status Display.

Wraps tests/unit/test_mcp_status_display.py tests for Robot Framework.
Per UI-AUDIT-011: MCP process status in Infrastructure view.
"""

import sys
import inspect
import json
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class MCPStatusDisplayLibrary:
    """Robot Framework library for MCP Status Display testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # MCP Panel in Infra View Tests
    # =========================================================================

    def mcp_panel_in_infra_view(self) -> Dict[str, Any]:
        """Verify build_mcp_status_panel is called in infra view."""
        from agent.governance_ui.views import infra_view
        source = inspect.getsource(infra_view)
        return {
            "panel_called": "build_mcp_status_panel()" in source
        }

    def mcp_panel_function_exists(self) -> Dict[str, Any]:
        """Verify build_mcp_status_panel function exists."""
        from agent.governance_ui.views.infra_view import build_mcp_status_panel
        return {
            "callable": callable(build_mcp_status_panel)
        }

    def mcp_testid_in_panel(self) -> Dict[str, Any]:
        """Verify MCP panel has testid for automation."""
        from agent.governance_ui.views import infra_view
        source = inspect.getsource(infra_view)
        return {
            "has_testid": "infra-mcp-status" in source
        }

    # =========================================================================
    # MCP Status Data Loader Tests
    # =========================================================================

    def mcp_servers_in_stats_init(self) -> Dict[str, Any]:
        """Verify mcp_servers key is initialized in stats."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        return {
            "has_mcp_servers": '"mcp_servers"' in source or "'mcp_servers'" in source
        }

    def mcp_names_extracted(self) -> Dict[str, Any]:
        """Verify known MCP server names are extracted."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        return {
            "has_claude_mem": "claude-mem" in source
        }

    def healthcheck_state_file_exists(self) -> Dict[str, Any]:
        """Verify healthcheck state file exists."""
        state_file = PROJECT_ROOT / ".claude/hooks/.healthcheck_state.json"
        return {
            "exists": state_file.exists(),
            "path": str(state_file)
        }

    def healthcheck_state_has_components(self) -> Dict[str, Any]:
        """Verify healthcheck state file has components."""
        state_file = PROJECT_ROOT / ".claude/hooks/.healthcheck_state.json"

        if not state_file.exists():
            return {"skipped": True, "reason": "State file not found"}

        with open(state_file) as f:
            hc_state = json.load(f)

        components = hc_state.get("components", {})
        return {
            "has_components": len(components) > 0,
            "component_count": len(components),
            "has_claude_mem": "claude-mem" in components
        }

    # =========================================================================
    # MCP Status UI Binding Tests
    # =========================================================================

    def infra_stats_mcp_servers_used_in_view(self) -> Dict[str, Any]:
        """Verify infra_stats.mcp_servers is used in view template."""
        from agent.governance_ui.views import infra_view
        source = inspect.getsource(infra_view)
        return {
            "has_mcp_servers": "mcp_servers" in source
        }
