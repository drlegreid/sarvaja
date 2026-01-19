"""
UI Module Existence Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py (395 lines).
Tests that governance UI module exists and is properly structured.
"""
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AGENT_DIR = PROJECT_ROOT / "agent"


class TestGovernanceUIModuleExists:
    """Verify P9.2 governance UI module exists."""

    @pytest.mark.unit
    def test_governance_ui_package_exists(self):
        """Governance UI package must exist."""
        ui_dir = AGENT_DIR / "governance_ui"
        assert ui_dir.exists(), "agent/governance_ui/ package not found"
        assert (ui_dir / "__init__.py").exists(), "__init__.py not found"
        assert (ui_dir / "data_access.py").exists(), "data_access.py not found"
        assert (ui_dir / "state.py").exists(), "state.py not found"

    @pytest.mark.unit
    def test_governance_dashboard_exists(self):
        """Governance dashboard module must exist."""
        dashboard_file = AGENT_DIR / "governance_dashboard.py"
        assert dashboard_file.exists(), "agent/governance_dashboard.py not found"

    @pytest.mark.unit
    def test_governance_dashboard_class_importable(self):
        """GovernanceDashboard class must be importable."""
        from agent.governance_dashboard import GovernanceDashboard

        dashboard = GovernanceDashboard()
        assert dashboard is not None
        assert hasattr(dashboard, 'build_ui')
        assert hasattr(dashboard, 'run')
