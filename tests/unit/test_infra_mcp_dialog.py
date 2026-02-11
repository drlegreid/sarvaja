"""
Tests for MCP chip click dialog (C.2) and Python process drill-down (C.4).

Verifies:
- MCP detail dialog state variables exist
- MCP table rows have click handler
- Python process panel exists in view
- Python process loader populates state
- Infra view includes new components

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import inspect


# Path to the infra view package (DOC-SIZE-01 split)
INFRA_VIEW_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..", "agent", "governance_ui", "views", "infra",
))


def _read_infra_view_source() -> str:
    """Read all infra view package source for inspection."""
    source_parts = []
    for fname in sorted(os.listdir(INFRA_VIEW_DIR)):
        if fname.endswith(".py"):
            with open(os.path.join(INFRA_VIEW_DIR, fname)) as f:
                source_parts.append(f.read())
    return "\n".join(source_parts)


class TestMcpDetailDialog:
    """C.2: MCP server chips should be clickable with detail dialog."""

    def test_mcp_table_rows_clickable(self):
        """MCP table rows should have click handler to open dialog."""
        source = _read_infra_view_source()
        assert "mcp_selected_server = sname" in source
        assert "show_mcp_detail = true" in source

    def test_mcp_dialog_exists(self):
        """MCP detail dialog should be defined."""
        source = _read_infra_view_source()
        assert "build_mcp_detail_dialog" in source
        assert "show_mcp_detail" in source

    def test_mcp_dialog_shows_command(self):
        """MCP dialog should display server command."""
        source = _read_infra_view_source()
        assert "Command" in source
        assert "mcp_selected_server" in source

    def test_mcp_dialog_shows_tools(self):
        """MCP dialog should show registered tool count."""
        source = _read_infra_view_source()
        assert "Registered Tools" in source

    def test_mcp_dialog_shows_dependencies(self):
        """MCP dialog should show backend dependencies."""
        source = _read_infra_view_source()
        assert "Dependencies" in source
        assert "depends_on" in source

    def test_state_has_mcp_dialog_vars(self):
        """Initial state should include MCP dialog variables."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "show_mcp_detail" in state
        assert "mcp_selected_server" in state
        assert state["show_mcp_detail"] is False


class TestPythonProcsPanel:
    """C.4: Python process drill-down panel."""

    def test_python_procs_panel_exists(self):
        """Python process panel should be defined in infra view."""
        source = _read_infra_view_source()
        assert "build_python_procs_panel" in source
        assert "infra_python_procs" in source

    def test_python_procs_table_has_columns(self):
        """Process table should show PID, CPU, MEM, Command."""
        source = _read_infra_view_source()
        assert "proc.pid" in source
        assert "proc.cpu" in source
        assert "proc.mem" in source
        assert "proc.command" in source

    def test_python_procs_triggers_load(self):
        """Expansion panel should trigger load_python_processes."""
        source = _read_infra_view_source()
        assert "load_python_processes" in source

    def test_state_has_python_procs_vars(self):
        """Initial state should include Python process variables."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "infra_python_procs" in state
        assert "show_python_procs" in state
        assert state["infra_python_procs"] == []

    def test_python_procs_loader_exists(self):
        """Controller should have load_python_processes trigger."""
        from agent.governance_ui.controllers import infra_loaders
        source = inspect.getsource(infra_loaders)
        assert "load_python_processes" in source
        assert "ps" in source


class TestInfraViewIntegration:
    """Verify new components are wired into main view."""

    def test_main_view_calls_mcp_dialog(self):
        """build_infra_view should call build_mcp_detail_dialog."""
        source = _read_infra_view_source()
        # Find within build_infra_view function body
        view_fn_start = source.index("def build_infra_view")
        view_body = source[view_fn_start:]
        assert "build_mcp_detail_dialog()" in view_body

    def test_main_view_calls_python_procs(self):
        """build_infra_view should call build_python_procs_panel."""
        source = _read_infra_view_source()
        view_fn_start = source.index("def build_infra_view")
        view_body = source[view_fn_start:]
        assert "build_python_procs_panel()" in view_body
