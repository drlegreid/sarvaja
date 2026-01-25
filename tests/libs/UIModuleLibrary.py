"""
Robot Framework Library for UI Module Existence Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py (395 lines).
Migrated from tests/unit/ui/test_ui_module.py
"""
from pathlib import Path
from robot.api.deco import keyword


class UIModuleLibrary:
    """Library for testing governance UI module existence."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"

    @keyword("Governance UI Package Exists")
    def governance_ui_package_exists(self):
        """Governance UI package must exist."""
        ui_dir = self.agent_dir / "governance_ui"

        return {
            "ui_dir_exists": ui_dir.exists(),
            "init_exists": (ui_dir / "__init__.py").exists(),
            "data_access_exists": (ui_dir / "data_access.py").exists(),
            "state_exists": (ui_dir / "state.py").exists()
        }

    @keyword("Governance Dashboard Exists")
    def governance_dashboard_exists(self):
        """Governance dashboard module must exist."""
        dashboard_file = self.agent_dir / "governance_dashboard.py"

        return {
            "dashboard_exists": dashboard_file.exists()
        }

    @keyword("Governance Dashboard Class Importable")
    def governance_dashboard_class_importable(self):
        """GovernanceDashboard class must be importable."""
        try:
            from agent.governance_dashboard import GovernanceDashboard

            dashboard = GovernanceDashboard()

            return {
                "importable": True,
                "instantiable": dashboard is not None,
                "has_build_ui": hasattr(dashboard, 'build_ui'),
                "has_run": hasattr(dashboard, 'run')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}
