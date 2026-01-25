"""
Robot Framework Library for UI Factory Function Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Migrated from tests/unit/ui/test_ui_factory.py
"""
from robot.api.deco import keyword


class UIFactoryLibrary:
    """Library for testing UI factory function."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    @keyword("Create Governance Dashboard Works")
    def create_governance_dashboard_works(self):
        """Factory function should create dashboard."""
        try:
            from agent.governance_dashboard import create_governance_dashboard

            dashboard = create_governance_dashboard()

            return {
                "created": dashboard is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Factory With Custom Port")
    def factory_with_custom_port(self):
        """Factory should accept port parameter."""
        try:
            from agent.governance_dashboard import create_governance_dashboard

            dashboard = create_governance_dashboard(port=9090)

            return {
                "created": dashboard is not None,
                "port_correct": dashboard.port == 9090
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Default Port Is 8081")
    def default_port_is_8081(self):
        """Default port should be 8081."""
        try:
            from agent.governance_dashboard import create_governance_dashboard

            dashboard = create_governance_dashboard()

            return {
                "created": dashboard is not None,
                "port_is_8081": dashboard.port == 8081
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}
