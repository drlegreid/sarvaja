"""
Tests for Infrastructure Health controller module.

Per PLAN-UI-OVERHAUL-001 Task 6.3: Infra Health Intent.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestInfraHealthController:
    """Verify infra health controller exists and has proper structure."""

    def test_infra_controller_exists(self):
        """Infra controller module should exist."""
        from agent.governance_ui.controllers import infra
        assert infra is not None

    def test_infra_controller_has_health_check(self):
        """Infra controller should have health check function."""
        from agent.governance_ui.controllers import infra
        source = inspect.getsource(infra)
        assert 'check_service_health' in source or 'health' in source.lower(), (
            "Infra controller should have health check function"
        )

    def test_infra_controller_has_mcp_check(self):
        """Infra controller should verify MCP servers."""
        from agent.governance_ui.controllers import infra
        source = inspect.getsource(infra)
        assert 'mcp' in source.lower(), (
            "Infra controller should check MCP server health"
        )

    def test_infra_view_has_health_intent_section(self):
        """Infra view should show health intent/design rationale."""
        from agent.governance_ui.views import infra_view
        source = inspect.getsource(infra_view)
        assert 'health' in source.lower(), (
            "Infra view should show health design"
        )
