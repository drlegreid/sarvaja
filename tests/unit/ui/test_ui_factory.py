"""
UI Factory Function Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests for UI factory function.
"""
import pytest


class TestFactoryFunction:
    """Tests for UI factory function."""

    @pytest.mark.unit
    def test_create_governance_dashboard(self):
        """Factory function should create dashboard."""
        from agent.governance_dashboard import create_governance_dashboard

        dashboard = create_governance_dashboard()
        assert dashboard is not None

    @pytest.mark.unit
    def test_factory_with_custom_port(self):
        """Factory should accept port parameter."""
        from agent.governance_dashboard import create_governance_dashboard

        dashboard = create_governance_dashboard(port=9090)
        assert dashboard.port == 9090

    @pytest.mark.unit
    def test_default_port(self):
        """Default port should be 8081."""
        from agent.governance_dashboard import create_governance_dashboard

        dashboard = create_governance_dashboard()
        assert dashboard.port == 8081
