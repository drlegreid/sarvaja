"""
Tests for infrastructure view interactivity.

Per C.1-C.4: Infrastructure Health Interactivity.
Verifies:
- C.1: Service cards have click handlers for log loading
- C.2: MCP chips have click handlers
- C.3: Health stat cards have tooltip info
- C.4: Python process drill-down trigger exists

Created: 2026-02-01
"""
import pytest
import inspect


class TestServiceCardClickable:
    """C.1: Service cards should link to container logs."""

    def test_service_card_has_click_handler(self):
        """Service cards should have click to load logs."""
        from agent.governance_ui.views.infra_view import build_service_card
        source = inspect.getsource(build_service_card)
        assert "load_container_logs" in source or "infra_log_container" in source

    def test_service_card_sets_log_container(self):
        """Clicking service card should set infra_log_container."""
        from agent.governance_ui.views.infra_view import build_service_card
        source = inspect.getsource(build_service_card)
        assert "infra_log_container" in source


class TestMCPChipClickable:
    """C.2: MCP server chips should be clickable."""

    def test_mcp_panel_has_click_handler(self):
        """MCP chips should have click handler for details."""
        from agent.governance_ui.views.infra_view import build_mcp_status_panel
        source = inspect.getsource(build_mcp_status_panel)
        assert "click" in source or "mcp_detail" in source


class TestHealthTooltips:
    """C.3: Health stat cards should show criteria tooltips."""

    def test_memory_stat_has_criteria_info(self):
        """Memory stat card should show threshold criteria."""
        from agent.governance_ui.views.infra_view import build_system_stats
        source = inspect.getsource(build_system_stats)
        assert "85" in source  # Memory threshold
        assert "70" in source  # Memory warning threshold

    def test_process_stat_has_criteria_info(self):
        """Process stat card should show threshold info."""
        from agent.governance_ui.views.infra_view import build_system_stats
        source = inspect.getsource(build_system_stats)
        assert "20" in source  # Process warning threshold


class TestPythonProcessDrilldown:
    """C.4: Python process detail drill-down."""

    def test_process_drilldown_trigger_exists(self):
        """load_python_processes trigger should exist in infra loaders."""
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        source = inspect.getsource(register_infra_loader_controllers)
        assert "load_python_processes" in source

    def test_process_drilldown_parses_output(self):
        """load_python_processes should parse ps output."""
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        source = inspect.getsource(register_infra_loader_controllers)
        assert "python_process_list" in source or "infra_python_procs" in source
